import { Env } from '../lib/types';
import { jsonResponse, errorResponse, addCacheHeader } from '../lib/http';
import { fetchFromGitHub } from '../lib/github';
import { fetchAsset, getExt, CONTENT_TYPE_MAP } from '../lib/assets';

export const match = (path: string, method: string): boolean =>
  path.startsWith('/api/resources/') || path.startsWith('/api/proxy-download');

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  const url = new URL(request.url);

  if (path === '/api/resources/list') {
    try {
      const resp = await fetchAsset('/resource/resource.json', env);
      if (resp.ok) {
        const resources = await resp.json();
        const result = jsonResponse({ resources });
        addCacheHeader(result.headers, 300);
        return result;
      }
    } catch {}
    try {
      const ghResp = await fetchFromGitHub('public/resource/resources.json', env);
      if (ghResp.ok) {
        const resources = await ghResp.json();
        const result = jsonResponse({ resources });
        addCacheHeader(result.headers, 300);
        return result;
      }
    } catch {}
    return jsonResponse({ resources: [] });
  }

  if (path === '/api/resources/download') {
    const resourceName = url.searchParams.get('path') || '';
    if (!resourceName) return errorResponse('缺少 path 参数');
    if (resourceName.includes('..')) return errorResponse('访问被拒绝', 403);

    const safePath = 'resource/' + resourceName;
    const assetResp = await fetchAsset('/' + safePath, env);
    if (assetResp.ok) {
      const ext = getExt(resourceName);
      const contentType = CONTENT_TYPE_MAP[ext] || 'application/octet-stream';
      const headers = new Headers(assetResp.headers);
      headers.set('Content-Type', contentType);
      const encodedName = encodeURIComponent(resourceName);
      headers.set('Content-Disposition', `attachment; filename="${encodedName}"; filename*=UTF-8''${encodedName}`);
      return new Response(assetResp.body, { status: 200, headers });
    }

    try {
      const listResp = await fetchAsset('/resource/' + resourceName + '/index.html', env);
      if (listResp.ok) {
        return jsonResponse({ type: 'directory', name: resourceName, message: '这是一个文件夹，请逐个下载文件' });
      }
    } catch {}

    return errorResponse('资源不存在', 404);
  }

  if (path === '/api/proxy-download') {
    const targetUrl = url.searchParams.get('url') || '';
    if (!targetUrl) return errorResponse('缺少 url 参数', 400);

    const allowedDomains = ['github.com', 'ollama.com', 'objects.githubusercontent.com', 'codeload.github.com'];
    let target: URL;
    try {
      target = new URL(targetUrl);
    } catch {
      return errorResponse('无效的 URL', 400);
    }
    if (!allowedDomains.some(d => target.hostname.includes(d))) {
      return errorResponse('域名不被允许', 403);
    }

    try {
      const resp = await fetch(targetUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' },
        redirect: 'follow'
      });
      if (!resp.ok) return errorResponse(`下载失败: HTTP ${resp.status}`, 502);

      const headers = new Headers();
      const contentType = resp.headers.get('content-type') || 'application/octet-stream';
      headers.set('Content-Type', contentType);
      const contentLength = resp.headers.get('content-length');
      if (contentLength) headers.set('Content-Length', contentLength);

      return new Response(resp.body, { status: 200, headers });
    } catch (err: any) {
      return errorResponse(`代理下载失败: ${err.message}`, 502);
    }
  }

  if (path === '/api/proxy-download-status') {
    return jsonResponse({ status: 'ok', feature: 'proxy-download-available' });
  }

  return errorResponse('未找到接口', 404);
}
