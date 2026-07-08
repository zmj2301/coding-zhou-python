// GET /api/files/tree
import { checkAuth, jsonResponse, errorResponse, corsOptionsResponse } from '../../_utils';

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  try {
    const treeResponse = await env.ASSETS.fetch(new Request('/file-tree.json', request));
    if (treeResponse.ok) {
      const data = await treeResponse.json();
      return jsonResponse(data);
    }
    return jsonResponse([]);
  } catch (e) {
    return errorResponse('加载文件树失败', 500);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
