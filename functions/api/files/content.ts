// GET /api/files/content
import { checkAuth, jsonResponse, errorResponse } from '../../_utils';

function getLanguage(ext: string): string {
  const langMap: Record<string, string> = {
    '.py': 'python',
    '.cpp': 'cpp', '.c': 'c', '.h': 'c',
    '.java': 'java',
    '.js': 'javascript', '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.xml': 'xml',
    '.yaml': 'yaml', '.yml': 'yaml',
    '.md': 'markdown',
    '.sql': 'sql',
    '.sh': 'bash', '.bat': 'bash',
    '.rs': 'rust', '.go': 'go',
    '.rb': 'ruby', '.php': 'php',
    '.swift': 'swift', '.kt': 'kotlin',
    '.scala': 'scala', '.r': 'r',
    '.lua': 'lua', '.dart': 'dart',
    '.vue': 'html', '.svelte': 'html',
    '.toml': 'ini', '.ini': 'ini', '.cfg': 'ini',
    '.csv': 'plaintext', '.txt': 'plaintext',
    '.spec': 'plaintext'
  };
  return langMap[ext.toLowerCase()] || 'plaintext';
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

    const content = await ghResponse.text();
    const ext = '.' + (filePath.split('.').pop() || '').toLowerCase();
    const name = filePath.split('/').pop() || filePath;
    const size = new Blob([content]).size;

    return jsonResponse({
      path: filePath,
      name,
      content,
      language: getLanguage(ext),
      size
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
