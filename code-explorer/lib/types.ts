// 共享类型定义

export interface Env {
  CODE_EXPLORER_KV: KVNamespace;
  USER_PASSWORD: string;
  ADMIN_PASSWORD: string;
  JWT_SECRET: string;
  GITHUB_REPO: string;
  GITHUB_BRANCH: string;
  ZHIPU_API_KEY: string;
  ECS_SERVER_URL: string;
  ASSETS: {
    fetch: (request: Request) => Promise<Response>;
  };
}

export interface ApiModule {
  match(path: string, method: string): boolean;
  handle(request: Request, env: Env, path: string): Promise<Response>;
}
