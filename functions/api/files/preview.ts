// GET /api/files/preview
import { checkAuth, errorResponse } from '../../_utils';

const CONTENT_TYPE_MAP: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon'
};

function getExt(filePath: string): string {
  const idx = filePath.lastIndexOf('.');
  return idx >= 0 ? filePath.substring(idx).toLowerCase() : '';
}

function rewriteHtmlResourcePaths(html: string, filePath: string): string {
  const ext = getExt(filePath);
  if (ext !== '.html' && ext !== '.htm') return html;

  const dirPath = filePath.substring(0, filePath.lastIndexOf('/') + 1);

  function makePreviewUrl(original: string): string | null {
    if (!original || original.startsWith('/') || original.startsWith('http://') ||
        original.startsWith('https://') || original.startsWith('data:') ||
        original.startsWith('#') || original.startsWith('mailto:')) {
      return null;
    }
    try {
      const resolved = new URL(original, 'http://base/' + dirPath).pathname.substring(1);
      return '/api/files/preview?path=' + encodeURIComponent(resolved);
    } catch {
      return null;
    }
  }

  return html.replace(
    /(src|href|srcset|data-src|poster|action)\s*=\s*(['"])([^'">]+?)\2/gi,
    (match, attr, quote, value) => {
      const newUrl = makePreviewUrl(value);
      return newUrl ? `${attr}=${quote}${newUrl}${quote}` : match;
    }
  ).replace(
    /url\(\s*(['"]?)([^)'"']+?)\1\s*\)/gi,
    (match, quote, value) => {
      const newUrl = makePreviewUrl(value.trim());
      return newUrl ? `url(${newUrl})` : match;
    }
  );
}

export async function onRequestGet(context: any): Promise<Response> {
  const { request, env } = context;

  const authenticated = await checkAuth(request, env);
  if (!authenticated) {
    return errorResponse('请先登录', 401);
  }

  const url = new URL(request.url);
  const filePath = url.searchParams.get('path') || '';
  if (!filePath) {
    return errorResponse('缺少 path 参数');
  }

  if (filePath.includes('..') || filePath.startsWith('/')) {
    return errorResponse('访问被拒绝：路径越界', 403);
  }

  const githubRepo = env.GITHUB_REPO || 'zmj2301/coding-zhou-python';
  const githubBranch = env.GITHUB_BRANCH || 'main';
  const rawUrl = `https://raw.githubusercontent.com/${githubRepo}/${githubBranch}/${encodeURI(filePath)}`;

  try {
    const ghResponse = await fetch(rawUrl);
    if (!ghResponse.ok) {
      if (ghResponse.status === 404) {
        return errorResponse('文件不存在', 404);
      }
      return errorResponse('读取文件失败', ghResponse.status);
    }

    const ext = getExt(filePath);
    const contentType = CONTENT_TYPE_MAP[ext] || 'application/octet-stream';
    let data: string | ArrayBuffer;

    if (ext === '.html' || ext === '.htm') {
      let html = await ghResponse.text();
      html = rewriteHtmlResourcePaths(html, filePath);
      data = html;
    } else if (contentType.startsWith('text/') || contentType.startsWith('application/')) {
      data = await ghResponse.text();
    } else {
      data = await ghResponse.arrayBuffer();
    }

    return new Response(data, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'no-store',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    });
  } catch (e) {
    return errorResponse(`读取文件失败: ${e}`, 500);
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
