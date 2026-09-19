import { Env } from '../lib/types';
import { errorResponse } from '../lib/http';
import { checkAuth } from '../lib/auth';
import { fetchFromEcs, proxyStreamToEcs } from '../lib/ecs';

export const match = (path: string, method: string): boolean =>
  path.startsWith('/api/run/');

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  const url = new URL(request.url);

  const authenticated = await checkAuth(request, env);
  if (!authenticated) return errorResponse('请先登录', 401);

  if (path === '/api/run/start') {
    return proxyStreamToEcs(path + (url.search || ''), env, request);
  }
  if (path === '/api/run/stop') {
    return fetchFromEcs(path, env, request);
  }

  return errorResponse('未找到接口', 404);
}
