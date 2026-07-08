// 全局中间件：认证保护
// 保护路径：/api/files/*, /api/comments/*, /api/likes, /api/admin/*, /web-games/*, /fathers-day/*
// 公开路径：/api/login, /api/auth-check, /api/logout, /api/admin/login, 首页

import { checkAuth, errorResponse, isBrowserRequest, redirectResponse } from './_utils';

const PROTECTED_API_PREFIXES = [
  '/api/files/',
  '/api/comments',
  '/api/likes',
  '/api/admin/dashboard'
];

const PROTECTED_PAGE_PREFIXES = [
  '/web-games/',
  '/fathers-day/'
];

const PUBLIC_API_PATHS = [
  '/api/login',
  '/api/auth-check',
  '/api/logout',
  '/api/admin/login'
];

export async function onRequest(context: any): Promise<Response> {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  if (request.method === 'OPTIONS') {
    return next();
  }

  const isProtectedApi = PROTECTED_API_PREFIXES.some(prefix => path.startsWith(prefix)) &&
    !PUBLIC_API_PATHS.includes(path);

  if (isProtectedApi) {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) {
      return errorResponse('请先登录', 401);
    }
  }

  const isProtectedPage = PROTECTED_PAGE_PREFIXES.some(prefix => path.startsWith(prefix));
  if (isProtectedPage && isBrowserRequest(request)) {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) {
      return redirectResponse('/');
    }
  }

  return next();
}
