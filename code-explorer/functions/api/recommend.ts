import { jsonResponse, errorResponse, corsOptionsResponse } from '../_utils';

const AI_MODEL = '@cf/meta/llama-3.1-8b-instruct-fp8';
const CACHE_TTL = 3600;

async function fetchAsset(path: string, env: any): Promise<string | null> {
  try {
    const resp = await env.ASSETS.fetch(new Request(path, {}));
    if (resp.ok) return await resp.text();
  } catch {}
  return null;
}

function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return hash.toString(36);
}

async function loadProjects(env: any): Promise<any[]> {
  const kv = env.CODE_EXPLORER_KV;
  const cacheKey = `cache:project-meta`;
  try {
    const cached = await kv.get(cacheKey, { type: 'json' });
    if (cached && cached.projects) return cached.projects;
  } catch {}

  const listText = await fetchAsset('/project-list.json', env);
  if (listText) {
    try { return JSON.parse(listText); } catch {}
  }
  return [];
}

function buildSystemPrompt(projects: any[]): string {
  const projectList = projects.map((p: any) =>
    `- ${p.name} (path: ${p.path}, type: ${p.type || 'unknown'}, desc: ${p.description || 'none'})`
  ).join('\n');

  return `你是 Code Explorer 的 AI 编程助手。你可以和用户聊天、回答问题，也可以根据用户兴趣推荐项目。

项目列表：
${projectList}

当用户询问项目推荐时，请在你回复末尾附上 JSON 格式的推荐列表，格式如下：
---RECOMMEND---
[{"path": "项目路径", "reason": "推荐理由（中文，一句话）"}]
---END---

推荐 3-5 个最相关的项目。如果用户没有要求推荐，正常聊天即可。`;
}

async function runAI(messages: { role: string; content: string }[], env: any): Promise<{ text: string; recommendations: any[] }> {
  if (env.AI) {
    try {
      const response = await env.AI.run(AI_MODEL, {
        messages,
        max_tokens: 800,
        temperature: 0.7
      });

      let text = '';
      if (typeof response === 'string') text = response;
      else if (response.response) text = response.response;
      else if (response.content) text = typeof response.content === 'string' ? response.content : JSON.stringify(response.content);

      const recMatch = text.match(/---RECOMMEND---\n?([\s\S]*?)\n?---END---/);
      let recommendations: any[] = [];
      if (recMatch) {
        try {
          const parsed = JSON.parse(recMatch[1]);
          if (Array.isArray(parsed)) {
            recommendations = parsed.filter((r: any) => r.path && r.reason).map((r: any) => ({
              path: r.path, reason: r.reason, name: r.name || r.path
            })).slice(0, 5);
          }
        } catch {}
        text = text.replace(/---RECOMMEND---[\s\S]*?---END---/, '').trim();
      }

      return { text, recommendations };
    } catch (e: any) {
      console.error('AI call failed:', e);
    }
  }
  return { text: '', recommendations: [] };
}

function getRuleBasedResponse(userMessage: string, projects: any[]): { text: string; recommendations: any[] } {
  const lower = userMessage.toLowerCase();
  const keywords = lower.split(/[\s,，、。、!！?？~～]+/).filter((k: string) => k.length >= 2);

  const scored = projects.map((p: any) => {
    let score = 0;
    const fields = [p.name, p.path, p.description || '', p.type || ''].join(' ').toLowerCase();
    if (p.likes) score += (p.likes || 0) * 0.1;
    if (p.comments) score += (p.comments || 0) * 0.2;
    for (const kw of keywords) {
      if (fields.includes(kw)) score += 10;
    }
    return { ...p, score };
  });

  scored.sort((a: any, b: any) => b.score - a.score);
  const top = scored.slice(0, 5);

  if (top.some((p: any) => p.score > 0)) {
    const text = `我找到了这些可能符合你兴趣的项目：`;
    const recommendations = top.map((p: any) => ({
      path: p.path, name: p.name, reason: p.score > 0 ? `匹配你的兴趣关键词` : '热门推荐项目'
    }));
    return { text, recommendations };
  }

  return { text: '抱歉，我没有找到匹配的项目。请换个关键词试试，或者浏览项目列表看看有没有感兴趣的。', recommendations: [] };
}

export async function onRequestPost(context: any): Promise<Response> {
  try {
    const { request, env } = context;
    const body = await request.json() as { messages?: { role: string; content: string }[]; preferences?: string };
    let messages = body.messages;

    // backwards compatibility: accept single 'preferences' field
    if (!messages && body.preferences) {
      messages = [
        { role: 'system', content: '' },
        { role: 'user', content: `我的兴趣：${body.preferences}` }
      ];
    }

    if (!messages || messages.length === 0) {
      return errorResponse('请输入消息', 400);
    }

    const projects = await loadProjects(env);
    if (projects.length === 0) {
      return errorResponse('项目列表为空', 503);
    }

    const systemPrompt = buildSystemPrompt(projects);
    const fullMessages = [
      { role: 'system', content: systemPrompt },
      ...messages.map((m: any) => ({ role: m.role, content: m.content }))
    ];

    // Check if last message has total content > 1000
    const totalLen = fullMessages.reduce((s: number, m: any) => s + m.content.length, 0);
    if (totalLen > 8000) {
      return errorResponse('对话过长，请开始新对话', 400);
    }

    const result = await runAI(fullMessages, env);

    if (result.text || result.recommendations.length > 0) {
      try {
        const today = new Date().toISOString().slice(0, 10);
        const usageKey = `ai-usage:${today}`;
        const currentUsage = parseInt(await env.CODE_EXPLORER_KV.get(usageKey) || '0', 10);
        await env.CODE_EXPLORER_KV.put(usageKey, String(currentUsage + 1), { expirationTtl: 86400 });
      } catch {}
      return jsonResponse({ success: true, response: result.text, recommendations: result.recommendations });
    }

    const fallback = getRuleBasedResponse(messages[messages.length - 1].content, projects);
    return jsonResponse({ success: true, response: fallback.text, recommendations: fallback.recommendations });
  } catch (e: any) {
    return errorResponse(`请求失败: ${e.message || e}`, 500);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
