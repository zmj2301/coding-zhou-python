import { Env } from '../lib/types';
import { jsonResponse, errorResponse, optionsResponse } from '../lib/http';
import { fetchFromEcs } from '../lib/ecs';
import { fetchAsset } from '../lib/assets';

const AI_MODEL = '@cf/meta/llama-3.1-8b-instruct-fp8';
const ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
const ZHIPU_MODEL = 'glm-4.7-flash';

export const match = (path: string, method: string): boolean =>
  path === '/api/recommend' || path === '/api/ai-quota';

export async function handle(request: Request, env: Env, path: string): Promise<Response> {
  if (path === '/api/recommend' && request.method === 'OPTIONS') {
    return optionsResponse();
  }

  if (path === '/api/recommend' && request.method === 'POST') {
    try {
      const data = await request.json() as { messages?: { role: string; content: string }[]; input?: string; preferences?: string; context?: { folder?: string }; model?: string; needsProjects?: boolean };
      let messages = data.messages;

      if (!messages && (data.input || data.preferences)) {
        const userInput = (data.input || data.preferences || '').trim();
        if (!userInput) return errorResponse('请输入你的兴趣或需求', 400);
        messages = [{ role: 'user', content: `我的兴趣：${userInput}` }];
      }

      if (!messages || messages.length === 0) {
        return errorResponse('请输入消息', 400);
      }

      let aiResponse: { text: string; recommendations: any[]; reasoning?: string };
      let source: string = 'ollama';

      const ecsUrl = env.ECS_SERVER_URL || 'http://39.107.96.165';
      try {
        const proxyResp = await fetch(`${ecsUrl}/api/recommend`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Cookie': request.headers.get('Cookie') || '',
            'Host': new URL(ecsUrl).host,
          },
          body: JSON.stringify({
            messages,
            model: data.model || 'ollama',
            context: data.context,
          }),
          cf: { connectTimeout: 5, timeout: 120 },
        });

        if (proxyResp.ok) {
          const result = await proxyResp.json();
          if (result.response || result.recommendations?.length > 0) {
            aiResponse = {
              text: result.response || '',
              recommendations: result.recommendations || [],
              reasoning: result.reasoning || '',
            };
            source = 'ollama';
          } else {
            throw new Error('ECS 返回空响应');
          }
        } else {
          throw new Error(`ECS 返回 ${proxyResp.status}`);
        }
      } catch (ecsErr) {
        try {
          const projects = await loadProjectsForRecommend(env);
          aiResponse = await getConversationalAI(messages, projects, env, data.context, 'glm-4.7-flash');
          source = 'zhipu';
          if (!aiResponse.text && aiResponse.recommendations.length === 0) {
            aiResponse = await getConversationalAI(messages, projects, env, data.context);
            source = 'workers';
          }
        } catch (aiErr) {
          return errorResponse(`AI 服务暂不可用，请稍后再试`, 503);
        }
      }

      try {
        const today = new Date().toISOString().slice(0, 10);
        const usageKey = `ai-usage:${today}`;
        const currentUsage = parseInt(await env.CODE_EXPLORER_KV.get(usageKey) || '0', 10);
        await env.CODE_EXPLORER_KV.put(usageKey, String(currentUsage + 1), { expirationTtl: 86400 });
      } catch {}

      return jsonResponse({
        success: true,
        response: aiResponse.text,
        recommendations: aiResponse.recommendations || [],
        reasoning: aiResponse.reasoning || '',
        source,
      });
    } catch (e: any) {
      return errorResponse(`请求失败: ${e.message || e}`, 500);
    }
  }

  if (path === '/api/ai-quota') {
    try {
      const resp = await fetchFromEcs('/api/ai-quota', env, request);
      if (resp.ok) {
        return new Response(await resp.text(), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      const today = new Date().toISOString().slice(0, 10);
      const usageKey = `ai-usage:${today}`;
      const usage = parseInt(await env.CODE_EXPLORER_KV.get(usageKey) || '0', 10);
      const DAILY_LIMIT = 10000;
      const neuronsPerRequest = 100;
      const remaining = Math.max(0, DAILY_LIMIT - usage * neuronsPerRequest);
      return jsonResponse({ usage, remaining, limit: DAILY_LIMIT, neuronsPerRequest });
    } catch (e: any) {
      return jsonResponse({ usage: 0, remaining: 10000, limit: 10000, neuronsPerRequest: 100 });
    }
  }

  return errorResponse('未找到接口', 404);
}

async function loadProjectsForRecommend(env: Env): Promise<any[]> {
  const CACHE_KEY = 'cache:project-meta';
  try {
    const cached = await env.CODE_EXPLORER_KV.get(CACHE_KEY, { type: 'json' });
    if (cached && cached.projects) return cached.projects;
  } catch {}
  const listResp = await fetchAsset('/project-list.json', env);
  if (!listResp.ok) return [];
  try { return await listResp.json(); } catch { return []; }
}

function buildConversationalPrompt(projects: any[], contextInfo?: { folder?: string }): string {
  let projectSection = '';
  if (projects && projects.length > 0) {
    const projectList = projects.map((p: any) =>
      `- ${p.name} (path: ${p.path}, type: ${p.type || 'unknown'}, desc: ${p.description || 'none'})`
    ).join('\n');
    projectSection = `\n可用的项目列表：\n${projectList}\n`;
  }

  let contextNote = '';
  if (contextInfo?.folder) {
    contextNote = `\n用户当前关注的文件夹：${contextInfo.folder}\n`;
  }

  const recommendInstruction = projects && projects.length > 0
    ? `\n当用户表达兴趣或需求时，推荐 3-5 个最相关的项目。推荐时在回复末尾附上 JSON 格式：
---RECOMMEND---
[{"path": "项目路径", "reason": "推荐理由", "name": "项目名称"}]
---END---
没有推荐需求时正常聊天，不要强行推荐。`
    : '';

  return `你是一个热情友好的编程助手，名叫"小码"。你可以和用户自然地聊天、解答编程问题，也可以推荐项目。

你的性格：
- 说话语气像朋友一样自然，不要太正式
- 推荐项目时要说明推荐理由，让人觉得有说服力
- 如果用户问了具体需求，就帮他匹配最合适的项目
- 如果只是聊天，就轻松愉快地聊，不用每次都推荐项目
${projectSection}${contextNote}${recommendInstruction}`;
}

async function callZhipuAI(messages: { role: string; content: string }[], apiKey: string, projects: any[], contextInfo?: { folder?: string }, model: string = ZHIPU_MODEL): Promise<{ text: string; recommendations: any[]; reasoning?: string }> {
  const systemPrompt = buildConversationalPrompt(projects, contextInfo);
  const payload = {
    model,
    messages: [
      { role: 'system', content: systemPrompt },
      ...messages
    ],
    temperature: 0.7,
    max_tokens: 800,
    stream: false,
    thinking: { type: 'enabled' }
  };

  const resp = await fetch(ZHIPU_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Zhipu API error: ${resp.status} ${err}`);
  }

  const data = await resp.json();
  let text = data.choices?.[0]?.message?.content || '';
  const reasoning = data.choices?.[0]?.message?.reasoning_content || '';

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

  if (!text && recommendations.length > 0) {
    text = '为你推荐以下项目：';
  } else if (!text) {
    text = '抱歉，AI 暂时无法生成回复，请稍后再试。';
  }
  return { text, recommendations, reasoning };
}

async function getConversationalAI(messages: { role: string; content: string }[], projects: any[], env: Env, contextInfo?: { folder?: string }, model?: string): Promise<{ text: string; recommendations: any[]; reasoning?: string }> {
  if (model === 'glm-4.7-flash') {
    const apiKey = env.ZHIPU_API_KEY;
    if (apiKey) {
      try {
        return await callZhipuAI(messages, apiKey, projects, contextInfo);
      } catch (e: any) {
        console.error('Zhipu AI call failed:', e);
      }
    }
  }

  const ai = (env as any).AI;
  if (ai) {
    try {
      const systemPrompt = buildConversationalPrompt(projects, contextInfo);
      const response = await ai.run(AI_MODEL, {
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages
        ],
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

      if (!text && recommendations.length > 0) {
        text = '为你推荐以下项目：';
      } else if (!text) {
        text = '抱歉，AI 暂时无法生成回复，请稍后再试。';
      }
      return { text, recommendations };
    } catch (e: any) {
      console.error('AI call failed:', e);
    }
  }
  return { text: '', recommendations: [] };
}
