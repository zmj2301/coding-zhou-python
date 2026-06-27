// GET /api/files/search
import { checkAuth, jsonResponse, errorResponse } from '../../_utils';

function searchInTree(tree: any[], query: string, basePath: string = ''): any[] {
  const results: any[] = [];
  query = query.toLowerCase();

  for (const item of tree) {
    if (item.type === 'file') {
      if (item.name.toLowerCase().includes(query)) {
        results.push({
          name: item.name,
          path: item.path,
          ext: item.ext
        });
      }
    } else if (item.type === 'directory' && item.children) {
      results.push(...searchInTree(item.children, query, item.path));
    }
  }

  return results;
}

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  const url = new URL(request.url);
  const query = (url.searchParams.get('q') || '').toLowerCase();
  if (!query) {
    return jsonResponse([]);
  }

  try {
    const treeResponse = await env.ASSETS.fetch(new Request('/file-tree.json', request));
    if (!treeResponse.ok) {
      return jsonResponse([]);
    }
    const tree = await treeResponse.json();
    const results = searchInTree(tree, query);
    return jsonResponse(results.slice(0, 100));
  } catch (e) {
    return errorResponse('搜索失败', 500);
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
