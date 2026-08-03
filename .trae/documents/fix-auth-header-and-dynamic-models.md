# 修复 Bearer 认证头错误 + 精简模型列表

## 总结

两个修改：1) 后端 `OPENROUTER_API_KEY` 读取时 `.strip()` 去掉 `\r` 字符；2) 前端模型选择下拉框只保留 `openrouter/free` 一个默认模型，移除所有其他选项。

## 当前状态分析

### 问题一：`Invalid header value b'Bearer \r'`

**根因**：`ecs-env.sh` 文件在 Windows 上编辑后上传到 ECS Linux 服务器，文件包含 Windows 换行符（`\r\n`）。当部署脚本执行 `. ./ecs-env.sh` 时，`\r` 被读入环境变量值，导致 API Key 变成 `\r`。

**修复**：`ecs-server.py` 第 116 行 `OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()`

### 问题二：精简模型列表

前端模型选择下拉框当前有 7 个选项（含 `optgroup` 分组），用户要求只保留 `openrouter/free` 一个默认模型，移除所有其他模型选项。

## 修改方案

### 修改 1：后端修复 `\r` 字符

**文件**：`e:\coding-zhou\Python\code-explorer\ecs-server.py`
**位置**：第 116 行
```python
# 旧
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
# 新
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()
```

### 修改 2：前端精简模型下拉框

**文件**：`e:\coding-zhou\Python\index.html`
**位置**：第 3562-3571 行

将：
```html
<select class="ai-asst-model-select" id="aiAsstModel" onchange="aiAsstSetModel(this.value)">
  <optgroup label="OpenRouter (免费)">
    <option value="openrouter/free">🌐 Free Auto-Route</option>
    <option value="nvidia/nemotron-3-super-120b-a12b:free">🟢 Nemotron 3 Super 120B</option>
    <option value="nvidia/nemotron-3-ultra:free">🟢 Nemotron 3 Ultra</option>
    <option value="google/gemma-4-31b:free">🔵 Gemma 4 31B</option>
    <option value="openai/gpt-oss-20b:free">⚪ GPT-OSS 20B</option>
    <option value="qwen/qwen3-8b:free">🟠 Qwen3 8B</option>
  </optgroup>
</select>
```

改为：
```html
<select class="ai-asst-model-select" id="aiAsstModel" onchange="aiAsstSetModel(this.value)">
  <option value="openrouter/free">🌐 Free Auto-Route</option>
</select>
```

### 修改 3：更新 changelog.json

**位置**：`e:\coding-zhou\Python\changelog.json`
**新增**：v1.9.6 版本记录

## 验证步骤

1. 测试 `/api/recommend` 端点，确认不再出现 `Bearer \r` 错误
2. 打开前端 AI 助手，确认模型下拉框只显示 `openrouter/free` 一个选项
3. 提交到 GitHub、部署 Cloudflare Worker、清除 KV 缓存