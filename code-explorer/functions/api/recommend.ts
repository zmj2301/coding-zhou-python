// POST /api/recommend - AI-powered project recommendations
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

  return `你是一个项目推荐助手。用户会告诉你他们的兴趣，你需要从以下项目列表中推荐最匹配的项目。

项目列表：
${projectList}

请严格按以下 JSON 格式返回（不要返回其他内容）：
[{"path": "项目路径", "reason": "推荐理由（中文，一句话）"}]

每次推荐 3-5 个最相关的项目，按相关度从高到低排列。如果用户没有明确兴趣，推荐最受欢迎的项目。`;
}

async function getAIRecommendation(userInput: string, projects: any[], env: any): Promise<any[]> {
  const kv = env.CODE_EXPLORER_KV;
  const cacheKey = `cache:ai-recommend:${simpleHash(userInput)}`;

  try {
    const cached = await kv.get(cacheKey, { type: 'json' });
    if (cached && cached.timestamp && (Date.now() - cached.timestamp < CACHE_TTL * 1000)) {
      return cached.results;
    }
  } catch {}

  if (env.AI) {
    try {
      const systemPrompt = buildSystemPrompt(projects);
      const response = await env.AI.run(AI_MODEL, {
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `我的兴趣：${userInput}` }
        ],
        max_tokens: 500,
        temperature: 0.7
      });

      let text = '';
      if (typeof response === 'string') text = response;
      else if (response.response) text = response.response;
      else if (response.content) text = typeof response.content === 'string' ? response.content : JSON.stringify(response.content);

      const results = parseRecommendations(text, projects);
      try {
        await kv.put(cacheKey, JSON.stringify({ results, timestamp: Date.now() }), { expirationTtl: CACHE_TTL });
      } catch {}
      return results;
    } catch (e: any) {
      console.error('AI recommendation failed:', e);
      return getRuleBasedRecommendation(userInput, projects);
    }
  }

  return getRuleBasedRecommendation(userInput, projects);
}

function parseRecommendations(text: string, projects: any[]): any[] {
  try {
    const jsonMatch = text.match(/\[[\s\S]*?\]/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (Array.isArray(parsed)) {
        return parsed.filter((r: any) => r.path && r.reason).map((r: any) => {
          const project = projects.find((p: any) => p.path === r.path);
          return { path: r.path, reason: r.reason, name: project?.name || r.path };
        }).slice(0, 5);
      }
    }
  } catch {}
  return getRuleBasedRecommendation(text, projects);
}

function getRuleBasedRecommendation(input: string, projects: any[]): any[] {
  const lower = input.toLowerCase();
  const keywords = lower.split(/[\s,，、]+/).filter(Boolean);

  const scored = projects.map((p: any) => {
    let score = 0;
    const fields = [p.name, p.path, p.description, p.type].join(' ').toLowerCase();

    if (p.likes) score += (p.likes || 0) * 0.1;
    if (p.comments) score += (p.comments || 0) * 0.2;

    for (const kw of keywords) {
      if (fields.includes(kw)) score += 10;
    }

    return { ...p, score };
  });

  scored.sort((a: any, b: any) => b.score - a.score);

  return scored.slice(0, 5).map((p: any) => ({
    path: p.path,
    name: p.name,
    reason: p.score > 0 ? `匹配你的兴趣关键词` : '热门推荐项目'
  }));
}

export async function onRequestPost(context: any): Promise<Response> {
  try {
    const { request, env } = context;
    const body = await request.json() as { input?: string };
    const userInput = body.input?.trim();

    if (!userInput) {
      return errorResponse('请输入你的兴趣或需求', 400);
    }

    if (!userInput || userInput.length > 200) {
      return errorResponse('输入内容过长', 400);
    }

    const projects = await loadProjects(env);
    if (projects.length === 0) {
      return errorResponse('项目列表为空', 503);
    }

    const recommendations = await getAIRecommendation(userInput, projects, env);
    return jsonResponse({ success: true, recommendations });
  } catch (e: any) {
    return errorResponse(`推荐失败: ${e.message || e}`, 500);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
