import { Env } from '../lib/types';
import { jsonResponse, errorResponse } from '../lib/http';
import { checkAuth, checkAdmin, getTokenFromRequest, verifyJwt } from '../lib/auth';

export const match = (path: string, method: string): boolean =>
  path.startsWith('/api/feedback');

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  if (path === '/api/feedback' && request.method === 'POST') {
    const authenticated = await checkAuth(request, env);
    if (!authenticated) return errorResponse('请先登录', 401);
    try {
      const data: any = await request.json();
      const content = (data.content || '').toString().trim();
      const type = ['bug', 'feature', 'suggestion', 'praise', 'other'].includes(data.type) ? data.type : 'other';
      const rating = Math.max(1, Math.min(5, parseInt(data.rating, 10) || 0));
      const project = (data.project || '').toString().trim().slice(0, 100);
      if (!content) return errorResponse('请输入反馈内容', 400);
      if (content.length < 5) return errorResponse('反馈内容至少 5 个字', 400);
      if (!rating) return errorResponse('请选择评分', 400);

      const token = getTokenFromRequest(request);
      const payload = token ? await verifyJwt(token, env.JWT_SECRET || 'default-secret-change-me') : null;
      const username = payload?.sub || (payload?.username as string) || '用户';
      const id = `fb_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

      const item = {
        id, username, type,
        content: content.slice(0, 2000),
        rating, project,
        created_at: Math.floor(Date.now() / 1000),
        status: 'new'
      };
      await env.CODE_EXPLORER_KV.put(`feedback:${id}`, JSON.stringify(item));
      return jsonResponse({ success: true, id, message: '反馈提交成功' });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  if (path === '/api/feedback/list') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    const items: any[] = [];
    try {
      let cursor: string | undefined = undefined;
      do {
        const list = await env.CODE_EXPLORER_KV.list({ prefix: 'feedback:', cursor });
        for (const key of list.keys) {
          const raw = await env.CODE_EXPLORER_KV.get(key.name);
          if (raw) {
            try { items.push(JSON.parse(raw)); } catch {}
          }
        }
        cursor = list.cursor as string | undefined;
      } while (cursor);
    } catch {}
    items.sort((a, b) => (b.created_at || 0) - (a.created_at || 0));
    return jsonResponse({ feedback: items });
  }

  if (path === '/api/feedback/delete' && request.method === 'POST') {
    const isAdmin = await checkAdmin(request, env);
    if (!isAdmin) return errorResponse('需要管理员权限', 401);
    try {
      const data: any = await request.json();
      const id = (data.id || '').toString();
      if (!id) return errorResponse('缺少反馈 ID', 400);
      await env.CODE_EXPLORER_KV.delete(`feedback:${id}`);
      return jsonResponse({ success: true });
    } catch {
      return errorResponse('无效的请求', 400);
    }
  }

  return errorResponse('未找到接口', 404);
}
