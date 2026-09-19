import { Env } from '../lib/types';
import { jsonResponse, errorResponse, optionsResponse, setCookie, clearCookie } from '../lib/http';
import { checkAuth, checkAdmin, getTokenFromRequest, signJwt, verifyJwt } from '../lib/auth';

export const match = (path: string, method: string): boolean =>
  path === '/api/auth-check' ||
  path === '/api/login' ||
  path === '/api/logout' ||
  path.startsWith('/api/admin/');

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  if (request.method === 'OPTIONS') return optionsResponse();

  if (path === '/api/auth-check') {
    const authenticated = await checkAuth(request, env);
    let user = null;
    if (authenticated) {
      const token = getTokenFromRequest(request);
      if (token) {
        const payload = await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me');
        if (payload) {
          user = {
            id: 1,
            username: payload.sub || 'user',
            role: payload.is_admin ? 'admin' : 'user'
          };
        }
      }
    }
    return jsonResponse({ authenticated, passwordSet: Boolean(env.USER_PASSWORD), user });
  }

  if (path === '/api/login' && request.method === 'POST') {
    try {
      const data = await request.json();
      const password = data.password || '';
      if (!env.USER_PASSWORD) return errorResponse('服务器未设置密码', 500);
      if (password !== env.USER_PASSWORD) return errorResponse('密码错误', 401);
      const token = await signJwt(
        { sub: data.username || 'user', is_admin: false },
        env.JWT_SECRET || 'default-secret-change-me',
        604800
      );
      const resp = jsonResponse({
        token,
        user: { id: 1, username: data.username || 'user', role: 'user' }
      });
      return setCookie(resp, 'wg_token', token, 604800);
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/logout' && request.method === 'POST') {
    const resp = jsonResponse({ success: true });
    return clearCookie(resp, 'wg_token');
  }

  if (path === '/api/admin/login' && request.method === 'POST') {
    try {
      const data = await request.json();
      const password = data.password || '';
      if (!env.ADMIN_PASSWORD) return errorResponse('服务器未设置管理员密码', 500);
      if (password !== env.ADMIN_PASSWORD) return errorResponse('管理员密码错误', 401);
      const token = await signJwt(
        { sub: 'admin', is_admin: true },
        env.JWT_SECRET || 'default-secret-change-me',
        604800
      );
      const resp = jsonResponse({
        token,
        user: { id: 0, username: 'admin', role: 'admin' }
      });
      return setCookie(resp, 'wg_token', token, 604800);
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/admin/clear-cache' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    let deletedCount = 0;
    try {
      let cursor: string | undefined = undefined;
      do {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: 'cache:', cursor });
        const deletePromises = list.keys.map(k => env.CODE_EXPLORER_KV.delete(k.name));
        await Promise.all(deletePromises);
        deletedCount += list.keys.length;
        cursor = list.cursor as string | undefined;
      } while (cursor);
    } catch {}
    return jsonResponse({ success: true, message: `缓存已清除，共删除 ${deletedCount} 个缓存项` });
  }

  // admin/dashboard 也在这里处理
  if (path === '/api/admin/dashboard') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('管理员未登录', 401);

    let totalComments = 0, commentProjects = 0, totalLikes = 0, likeProjects = 0;
    try {
      const commentsList = await env.CODE_EXPLORER_KV.list({ prefix: 'comments:' });
      commentProjects = commentsList.keys.length;
      for (const key of commentsList.keys) {
        const data = await env.CODE_EXPLORER_KV.get(key.name);
        if (data) {
          try {
            const parsed = JSON.parse(data);
            if (parsed.comments && Array.isArray(parsed.comments)) {
              totalComments += parsed.comments.length;
            }
          } catch {}
        }
      }
    } catch {}
    try {
      const likesList = await env.CODE_EXPLORER_KV.list({ prefix: 'likes:' });
      likeProjects = likesList.keys.length;
      for (const key of likesList.keys) {
        const count = await env.CODE_EXPLORER_KV.get(key.name);
        if (count) totalLikes += parseInt(count, 10) || 0;
      }
    } catch {}

    return jsonResponse({
      server: { uptime: 'Cloudflare Worker (无状态)', uptime_seconds: 0, base_dir: 'GitHub Repository', port: 443, total_files: 0 },
      auth: { active_sessions: '无状态', admin_sessions: '无状态', password_set: Boolean(env.USER_PASSWORD), admin_password_set: Boolean(env.ADMIN_PASSWORD) },
      data: {
        likes_count: likeProjects,
        total_likes: totalLikes,
        likes_label: '个项目有点赞',
        comment_files: commentProjects,
        total_comments: totalComments,
        comments_label: '个项目有评论',
        uploaded_files_count: 0,
        uploads_label: '暂未启用上传功能'
      }
    });
  }

  return errorResponse('未找到接口', 404);
}
