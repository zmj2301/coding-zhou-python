// GET /api/admin/dashboard
import { checkAdmin, jsonResponse, errorResponse } from '../../_utils';

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const isAdmin = await checkAdmin(request, env);
  if (!isAdmin) {
    return errorResponse('管理员未登录', 401);
  }

  const kv = env.CODE_EXPLORER_KV;
  let totalComments = 0;
  let commentProjects = 0;
  let totalLikes = 0;
  let likeProjects = 0;

  try {
    const commentsList = await kv.list({ prefix: 'comments:' });
    commentProjects = commentsList.keys.length;
    for (const key of commentsList.keys) {
      const data = await kv.get(key.name);
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
    const likesList = await kv.list({ prefix: 'likes:' });
    likeProjects = likesList.keys.length;
    for (const key of likesList.keys) {
      const count = await kv.get(key.name);
      if (count) {
        totalLikes += parseInt(count, 10) || 0;
      }
    }
  } catch {}

  return jsonResponse({
    server: {
      uptime: 'Cloudflare Pages (无状态)',
      uptime_seconds: 0,
      base_dir: 'GitHub Repository',
      port: 443,
      total_files: 0
    },
    auth: {
      active_sessions: -1,
      admin_sessions: -1,
      password_set: Boolean(env.USER_PASSWORD),
      admin_password_set: Boolean(env.ADMIN_PASSWORD)
    },
    data: {
      likes_count: likeProjects,
      total_likes: totalLikes,
      comment_files: commentProjects,
      total_comments: totalComments
    }
  });
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
