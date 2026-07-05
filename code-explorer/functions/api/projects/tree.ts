// GET /api/projects/tree
import { checkAuth, jsonResponse, errorResponse, corsOptionsResponse } from '../../_utils';

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  try {
    const url = new URL(request.url);
    const path = url.searchParams.get('path') || '';

    if (!path) {
      return errorResponse('缺少 path 参数', 400);
    }

    const safeName = path.replace(/\//g, '__').replace(/\\/g, '__');
    const treePath = `/project-trees/${safeName}.json`;

    const treeResponse = await env.ASSETS.fetch(new Request(treePath, request));
    if (treeResponse.ok) {
      const data = await treeResponse.json();
      return jsonResponse(data);
    }

    return jsonResponse([]);
  } catch (e: any) {
    return errorResponse(`加载项目文件树失败: ${e.message || e}`, 500);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
