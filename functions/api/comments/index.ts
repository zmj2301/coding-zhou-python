// GET /api/comments  POST /api/comments
import { checkAuth, jsonResponse, errorResponse } from '../../_utils';

function safeProjectName(project: string): string {
  return project
    .replace(/\//g, '_')
    .replace(/\\/g, '_')
    .replace(/[:*?"<>|]/g, '_');
}

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  const url = new URL(request.url);
  const project = url.searchParams.get('project') || '';
  if (!project) {
    return errorResponse('缺少 project 参数');
  }

  const kv = env.CODE_EXPLORER_KV;
  const key = `comments:${safeProjectName(project)}`;

  try {
    const data = await kv.get(key);
    if (data) {
      try {
        const parsed = JSON.parse(data);
        return jsonResponse(parsed);
      } catch {
        return jsonResponse({ project, comments: [] });
      }
    }
    return jsonResponse({ project, comments: [] });
  } catch (e) {
    return errorResponse(`加载评论失败: ${e}`, 500);
  }
}

export async function onRequestPost(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  try {
    const data = await request.json();
    const project = data.project || '';
    const text = (data.text || '').trim();

    if (!project || !text) {
      return errorResponse('缺少 project 或 text 参数');
    }

    const kv = env.CODE_EXPLORER_KV;
    const key = `comments:${safeProjectName(project)}`;

    let projectData: any = { project, comments: [] };
    const existing = await kv.get(key);
    if (existing) {
      try {
        projectData = JSON.parse(existing);
      } catch {}
    }

    const commentId = Math.random().toString(36).substring(2, 10);
    const comment = {
      id: commentId,
      project,
      text,
      timestamp: Date.now(),
      image: null,
      likes: 0
    };

    projectData.comments.push(comment);
    await kv.put(key, JSON.stringify(projectData));

    return jsonResponse(comment, 201);
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
