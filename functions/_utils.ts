// 工具函数：JWT 认证、Cookie 解析、通用响应

export interface JwtPayload {
  sub: string;
  is_admin: boolean;
  iat: number;
  exp: number;
}

function base64UrlEncode(data: Uint8Array): string {
  let str = '';
  for (let i = 0; i < data.length; i++) {
    str += String.fromCharCode(data[i]);
  }
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(str: string): Uint8Array {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  const binary = atob(str);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function getKey(secret: string): Promise<CryptoKey> {
  const enc = new TextEncoder();
  return crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign', 'verify']
  );
}

export async function signJwt(
  payload: Record<string, any>,
  secret: string,
  expiresInSeconds: number = 86400
): Promise<string> {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const fullPayload = { ...payload, iat: now, exp: now + expiresInSeconds };

  const headerB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(header)));
  const payloadB64 = base64UrlEncode(new TextEncoder().encode(JSON.stringify(fullPayload)));

  const key = await getKey(secret);
  const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const signature = await crypto.subtle.sign('HMAC', key, data);
  const sigB64 = base64UrlEncode(new Uint8Array(signature));

  return `${headerB64}.${payloadB64}.${sigB64}`;
}

export async function verifyJwt(token: string, secret: string): Promise<JwtPayload | null> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const [headerB64, payloadB64, sigB64] = parts;
    const key = await getKey(secret);
    const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const signature = base64UrlDecode(sigB64);

    const isValid = await crypto.subtle.verify('HMAC', key, signature, data);
    if (!isValid) return null;

    const payload = JSON.parse(new TextDecoder().decode(base64UrlDecode(payloadB64)));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }

    return payload as JwtPayload;
  } catch {
    return null;
  }
}

export function parseCookies(cookieHeader: string | null): Record<string, string> {
  const cookies: Record<string, string> = {};
  if (!cookieHeader) return cookies;
  for (const cookie of cookieHeader.split(';')) {
    const [name, ...rest] = cookie.trim().split('=');
    if (name) {
      cookies[name] = rest.join('=');
    }
  }
  return cookies;
}

export function getTokenFromRequest(request: Request, env: any): string | null {
  const cookieHeader = request.headers.get('Cookie');
  const cookies = parseCookies(cookieHeader);
  return cookies['wg_token'] || null;
}

export async function checkAuth(request: Request, env: any): Promise<boolean> {
  const userPassword = env.USER_PASSWORD;
  if (!userPassword) return true;
  const token = getTokenFromRequest(request, env);
  if (!token) return false;
  const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
  return payload !== null;
}

export async function checkAdmin(request: Request, env: any): Promise<boolean> {
  const adminPassword = env.ADMIN_PASSWORD;
  if (!adminPassword) return false;
  const token = getTokenFromRequest(request, env);
  if (!token) return false;
  const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
  return payload !== null && payload.is_admin === true;
}

export function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

export function errorResponse(message: string, status: number = 400): Response {
  return jsonResponse({ error: message }, status);
}

export function setCookieResponse(
  response: Response,
  name: string,
  value: string,
  maxAge: number = 86400
): Response {
  const cookie = `${name}=${value}; Path=/; Max-Age=${maxAge}; HttpOnly; SameSite=Lax`;
  const newHeaders = new Headers(response.headers);
  newHeaders.append('Set-Cookie', cookie);
  return new Response(response.body, {
    status: response.status,
    headers: newHeaders
  });
}

export function clearCookieResponse(response: Response, name: string): Response {
  const cookie = `${name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`;
  const newHeaders = new Headers(response.headers);
  newHeaders.append('Set-Cookie', cookie);
  return new Response(response.body, {
    status: response.status,
    headers: newHeaders
  });
}

export function isBrowserRequest(request: Request): boolean {
  const accept = request.headers.get('Accept') || '';
  return accept.includes('text/html');
}

export function redirectResponse(url: string, status: number = 302): Response {
  return new Response(null, {
    status,
    headers: { Location: url }
  });
}
