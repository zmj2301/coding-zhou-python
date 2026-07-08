// POST /api/recommend
// AI 个性化推荐接口 - 使用 Cloudflare Workers AI（免费额度）
import { jsonResponse, errorResponse, corsOptionsResponse } from '../_utils';

const AI_MODEL = '@cf/meta/llama-3.1-8b-instruct-fp8';
const CACHE_TTL = 3600; // 1 小时缓存

// ------------------------------------------------------------
// 工具函数
// ------------------------------------------------------------

function fetchAsset(path: string, env: any): Promise<Response> {
  try {
    if (env.ASSETS && typeof env.ASSETS.fetch === 'function') {
      const cleanPath = path.startsWith('/') ? path.substring(1) : path;
      return env.ASSETS.fetch(new Request('/' + cleanPath));
    }
  } catch {}
  const repo = env.GITHUB_REPO || 'zmj2301/coding-zhou-python';
  const branch = env.GITHUB_BRANCH || 'main';
  const url = `https://raw.githubusercontent.com/${repo}/${branch}/code-explorer/public${path}`;
  return fetch(url);
}

async function simpleHash(str: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 12);
}

// ------------------------------------------------------------
// 项目数据加载（带 KV 缓存）
// ------------------------------------------------------------

interface Project {
  name: string;
  path: string;
  type: string;
  label: string;
  desc: string;
  mainFile: string;
  fileCount: number;
  themeColor: string;
  popupUrl?: string | null;
  webGameUrl?: string | null;
}

async function loadProjects(env: any): Promise<Project[]> {
  const kv = env.CODE_EXPLORER_KV;
  const CACHE_KEY = 'cache:recommend-projects';

  // 尝试从 KV 缓存加载
  try {
    const cached = await kv.get(CACHE_KEY, { type: 'json' });
    if (cached && Array.isArray(cached)) {
      return cached as Project[];
    }
  } catch {}

  // 从 GitHub / Assets 加载
  try {
    const resp = await fetchAsset('/project-list.json', env);
    if (!resp.ok) return [];
    const projects = await resp.json() as Project[];

    // 写入 KV 缓存（24 小时）
    try {
      await kv.put(CACHE_KEY, JSON.stringify(projects), {
        expirationTtl: 86400
      });
    } catch {}

    return projects;
  } catch {
    return [];
  }
}

// ------------------------------------------------------------
// Prompt 构造
// ------------------------------------------------------------

function buildProjectSummary(projects: Project[]): string {
  return projects
    .filter(p => p.type !== 'system-file')
    .map(p => {
      const info = [p.name, `(${p.label})`];
      if (p.desc) info.push(`- ${p.desc}`);
      info.push(`${p.fileCount}个文件`);
      return `  - ${info.join(' ')}`;
    })
    .join('\n');
}

function buildSystemPrompt(projectSummary: string): string {
  return `你是一个智能项目推荐助手，负责根据用户偏好从以下项目库中推荐最合适的 3-5 个项目。

项目库列表：
${projectSummary}

请严格遵循以下规则：
1. 只从上面的项目库列表中推荐项目，不要推荐列表之外的项目
2. 每个推荐必须包含项目名称和推荐理由（一句话）
3. 根据用户偏好精准匹配，如果用户没给偏好则推荐多样且有趣的项目
4. 回复格式为 JSON 数组，每个元素包含 name（项目名称）和 reason（推荐理由）两个字段
5. 只输出 JSON，不要输出其他文字

示例回复格式：
[
  {"name": "Python射击游戏", "reason": "如果你喜欢射击类游戏，这个项目有丰富的敌人和武器系统"},
  {"name": "python海龟汤", "reason": "有趣的文字推理游戏，适合休闲时光"}
]`;
}

// ------------------------------------------------------------
// AI 调用（带 KV 缓存）
// ------------------------------------------------------------

async function getAIRecommendation(
  env: any,
  systemPrompt: string,
  userMessage: string,
  currentProject: string | null
): Promise<string> {
  const kv = env.CODE_EXPLORER_KV;

  // 构造缓存 key
  const cacheInput = `${userMessage}|${currentProject || ''}`;
  const hash = await simpleHash(cacheInput);
  const cacheKey = `cache:ai-recommend:${hash}`;

  // 尝试命中缓存
  try {
    const cached = await kv.get(cacheKey);
    if (cached) {
      return cached;
    }
  } catch {}

  // 检查 AI binding 是否可用
  if (!env.AI) {
    // Fallback：无 AI binding 时返回基于规则的推荐
    return getFallbackRecommendation(userMessage, currentProject);
  }

  try {
    const messages: Array<{ role: string; content: string }> = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userMessage }
    ];

    const response = await env.AI.run(AI_MODEL, { messages });

    let result = '';
    if (response && response.response) {
      result = typeof response.response === 'string'
        ? response.response
        : JSON.stringify(response.response);
    } else if (typeof response === 'string') {
      result = response;
    }

    // 写入 KV 缓存
    try {
      await kv.put(cacheKey, result, { expirationTtl: CACHE_TTL });
    } catch {}

    return result;
  } catch (e) {
    // AI 调用失败时 fallback
    return getFallbackRecommendation(userMessage, currentProject);
  }
}

// ------------------------------------------------------------
// Fallback：基于规则的简单推荐（AI 不可用时）
// ------------------------------------------------------------

function getFallbackRecommendation(
  userMessage: string,
  currentProject: string | null
): string {
  const msg = (userMessage || '').toLowerCase();
  let typeFilter: string | null = null;
  let keywordHint = '';

  if (msg.includes('游戏') || msg.includes('game')) {
    typeFilter = 'game';
    keywordHint = '游戏';
  } else if (msg.includes('ai') || msg.includes('人工智能') || msg.includes('智能')) {
    typeFilter = 'ai';
    keywordHint = 'AI';
  } else if (msg.includes('工具') || msg.includes('tool') || msg.includes('实用')) {
    typeFilter = 'tool';
    keywordHint = '工具';
  } else if (msg.includes('网页') || msg.includes('web')) {
    typeFilter = 'web-game';
    keywordHint = '网页游戏';
  }

  if (typeFilter) {
    return JSON.stringify([
      { name: '', reason: `根据你对「${keywordHint}」的兴趣，推荐以下项目。请浏览项目列表中类型为「${keywordHint}」的项目。` }
    ]);
  }

  return JSON.stringify([
    { name: 'Python射击游戏', reason: '经典射击游戏，拥有丰富的敌人和武器系统' },
    { name: 'python海龟汤', reason: '有趣的文字推理游戏，适合和朋友一起玩' },
    { name: 'Python AI象棋对战', reason: 'AI 对弈中国象棋，体验人机对战' },
    { name: 'python植物大战僵尸', reason: '经典塔防游戏的 Python 实现' },
    { name: 'Python桌面宠物', reason: '可爱的桌面宠物陪伴你的工作时光' }
  ]);
}

// ------------------------------------------------------------
// 解析 AI 返回的 JSON
// ------------------------------------------------------------

interface Recommendation {
  name: string;
  reason: string;
}

function parseRecommendations(raw: string): Recommendation[] {
  try {
    // 尝试提取 JSON 数组
    const jsonMatch = raw.match(/\[[\s\S]*\]/);
    if (!jsonMatch) return [];

    const parsed = JSON.parse(jsonMatch[0]);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .filter((item: any) => item && typeof item.name === 'string')
      .map((item: any) => ({
        name: item.name.trim(),
        reason: (item.reason || '').trim()
      }));
  } catch {
    return [];
  }
}

// ------------------------------------------------------------
// 路由处理
// ------------------------------------------------------------

export async function onRequestPost(context: any): Promise<Response> {
  const { request, env } = context;

  try {
    const data = await request.json();
    const preferences: string = data.preferences || '';
    const currentProject: string | null = data.currentProject || null;

    // 加载项目列表
    const projects = await loadProjects(env);

    // 构造 prompt
    const projectSummary = buildProjectSummary(projects);
    const systemPrompt = buildSystemPrompt(projectSummary);

    // 构造用户消息
    let userMessage = preferences || '请推荐一些有趣的项目';
    if (currentProject) {
      userMessage += `\n\n我目前正在浏览项目「${currentProject}」，请推荐与我当前浏览项目相关或类似的项目。`;
    }

    // 调用 AI（带缓存）
    const rawResult = await getAIRecommendation(env, systemPrompt, userMessage, currentProject);

    // 解析结果
    const recommendations = parseRecommendations(rawResult);

    // 将推荐项目名匹配到实际项目路径
    const enrichedRecommendations = recommendations.map(rec => {
      const matchedProject = projects.find(
        p => p.name === rec.name || p.path === rec.name
      );
      return {
        name: rec.name,
        reason: rec.reason,
        path: matchedProject ? matchedProject.path : null,
        type: matchedProject ? matchedProject.type : null,
        themeColor: matchedProject ? matchedProject.themeColor : null,
        popupUrl: matchedProject?.popupUrl || null,
        webGameUrl: matchedProject?.webGameUrl || null
      };
    });

    return jsonResponse({
      success: true,
      recommendations: enrichedRecommendations,
      cached: false,
      model: AI_MODEL
    });
  } catch (e) {
    return errorResponse(`推荐服务出错: ${e}`, 500);
  }
}

export async function onRequestOptions(): Promise<Response> {
  return corsOptionsResponse();
}
