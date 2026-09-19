// ============================================================
// Code Explorer - 主入口（路由分发）
// 从 worker.ts 拆分而来，所有功能分散在 lib/ + api/ + pages/ 模块中
// ============================================================

import { Env, ApiModule } from './lib/types';
import { errorResponse, optionsResponse } from './lib/http';
import { handleStatic } from './pages/static';

// API 模块导入
import * as auth from './api/auth.routes';
import * as files from './api/files.routes';
import * as run from './api/run.routes';
import * as comments from './api/comments.routes';
import * as feedback from './api/feedback.routes';
import * as ai from './api/ai.routes';
import * as resources from './api/resources.routes';

const apiModules: ApiModule[] = [auth, files, run, comments, feedback, ai, resources];

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // 同步清理旧缓存（await 确保后续路由读到干净的 KV）
    try {
      await Promise.all([
        env.CODE_EXPLORER_KV.delete('cache:home-page'),
        env.CODE_EXPLORER_KV.delete('cache:home-page-v2'),
        env.CODE_EXPLORER_KV.delete('cache:project-meta'),
      ]);
    } catch {}

    // OPTIONS 预检
    if (request.method === 'OPTIONS') return optionsResponse();

    // API 请求：按模块匹配
    if (path.startsWith('/api/')) {
      for (const mod of apiModules) {
        if (mod.match(path, request.method)) {
          return mod.handle(request, env, path);
        }
      }
      return errorResponse('未找到接口', 404);
    }

    // 静态文件 / 页面
    return handleStatic(request, env, path);
  }
};
