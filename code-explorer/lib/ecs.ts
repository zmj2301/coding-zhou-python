// ECS 服务器代理：普通代理 + SSE 流式代理

import { Env } from './types';

export async function fetchFromEcs(path: string, env: Env, request: Request): Promise<Response> {
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165';
  const url = `${ecsUrl}${path}`;
  const headers = new Headers(request.headers);
  headers.set('Host', new URL(ecsUrl).host);
  // 保留 Cookie 用于认证
  const cookie = request.headers.get('Cookie');
  if (cookie) {
    headers.set('Cookie', cookie);
  }
  return fetch(url, { method: request.method, headers });
}

export async function proxyStreamToEcs(path: string, env: Env, request: Request): Promise<Response> {
  const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165';
  const url = `${ecsUrl}${path}`;
  const headers = new Headers();
  const contentType = request.headers.get('Content-Type');
  if (contentType) headers.set('Content-Type', contentType);
  const cookie = request.headers.get('Cookie');
  if (cookie) headers.set('Cookie', cookie);
  headers.set('Accept', 'text/event-stream');
  const body = request.method === 'POST' ? await request.text() : undefined;
  const ecsResp = await fetch(url, {
    method: request.method,
    headers,
    body,
  });
  // 使用 TransformStream 确保不缓冲，立即转发
  const { readable, writable } = new TransformStream({
    transform(chunk, controller) {
      controller.enqueue(chunk);
    },
  });
  ecsResp.body?.pipeTo(writable).catch(() => {});
  const responseHeaders = new Headers();
  responseHeaders.set('Content-Type', 'text/event-stream; charset=utf-8');
  responseHeaders.set('Cache-Control', 'no-cache, no-transform');
  responseHeaders.set('Connection', 'keep-alive');
  responseHeaders.set('Access-Control-Allow-Origin', '*');
  responseHeaders.set('X-Accel-Buffering', 'no');
  responseHeaders.delete('Content-Length');
  responseHeaders.delete('Content-Encoding');
  return new Response(readable, { status: ecsResp.status, headers: responseHeaders });
}
