# python海龟汤

一款基于大模型的「海龟汤」推理游戏。海龟汤（情境猜谜）中，主持人给出一个看似荒诞的情境，玩家通过提问逐步推理还原真相。本项目使用 Tkinter 构建界面，调用硅基流动（SiliconFlow）的 Qwen 大模型扮演主持人，玩家打字提问，AI 只回答「是 / 否 / 是也不是」，直到玩家猜出完整故事。

## 功能特性

- **AI 主持人**：调用 Qwen/QwQ-32B 模型扮演海龟汤主持人
- **游戏规则**：主持人仅回答「是 / 否 / 是也不是」，引导玩家推理
- **GUI 界面**：Tkinter 聊天界面，实时显示对话历史
- **语音播报**：集成 pyttsx3，可朗读主持人的回答
- **人设定制**：可配置不同的主持人性格/扮演角色
- **水浒元素**：附带《水浒传》一百单八将数据（`shuihu.py` / `show.py`），可玩「猜梁山好汉」变体
- **本地模型支持**：提供 Ollama 本地大模型调用脚本（`ollama_qwen.py`）

## 环境要求

- Python 3.8+
- requests、tkinter（内置）
- pyttsx3（语音播报，可选）
- 硅基流动 API Key（通过 `DEEPSEEK_API_KEY` 环境变量传递）
- 可选：Ollama 本地模型

```bash
pip install requests pyttsx3
```

## 安装与运行

```bash
cd "python海龟汤"
set DEEPSEEK_API_KEY=你的密钥
python Turtle_Soup.py
```

使用本地 Ollama 模型：

```bash
python run_ollama.py
```

## 项目结构

```
python海龟汤/
├── Turtle_Soup.py      # 主程序：海龟汤推理游戏
├── Turtle_Soup copy.py # 备份版本
├── shuihu.py           # 水浒一百单八将数据（天罡）
├── show.py             # 水浒一百单八将数据（含绰号/星号）
├── say.py              # 语音播报模块（pyttsx3）
├── ollama_qwen.py      # Ollama 本地模型调用
├── run_ollama.py       # Ollama 运行脚本
├── requests_p.py / os.py / test_*.py  # 辅助与测试脚本
├── users.json          # 用户数据
└── README.md
```

## 核心实现

### AI 调用（Turtle_Soup.py）

- 调用 `https://api.siliconflow.cn/v1/chat/completions`
- 模型：`Qwen/QwQ-32B`
- 通过 `player` 人设提示词约束主持人「只能回答是与否」

### 语音播报（say.py）

- `speak(text)`：将文本转语音播放
- 语速 140 字/分钟，音量 0.8

## 使用说明

1. 运行 `Turtle_Soup.py` 启动游戏
2. 主持人出题（一个荒诞的情境）
3. 玩家在输入框提问，AI 回答「是 / 否 / 是也不是」
4. 通过不断提问还原故事真相，直至猜出完整经过

## 许可证

本项目仅供学习交流使用。
