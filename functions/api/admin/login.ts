// POST /api/admin/login
import { signJwt, jsonResponse, errorResponse, setCookieResponse } from '../../_utils';

export async function onRequestPost(context: any): Promise<Response> {
  const { request, env } = context;

  try {
    const data = await request.json();
    const password = data.password || '';

    if (!env.ADMIN_PASSWORD) {
      return errorResponse('服务器未设置管理员密码', 500);
    }

    if (password !== env.ADMIN_PASSWORD) {
      return errorResponse('管理员密码错误', 401);
    }

    const token = await signJwt(
      { sub: 'admin', is_admin: true },
      env.JWT_SECRET || 'default-secret-change-me',
      86400
    );

    const response = jsonResponse({ token });
    return setCookieResponse(response, 'wg_token', token, 86400 * 7);
  } catch (e) {
    return errorResponse('无效的请求', 400);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}
