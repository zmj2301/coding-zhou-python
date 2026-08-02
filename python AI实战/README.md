# python AI实战

一个可语音交互的本地 AI 智能助手（ZCLAW）。集成了大模型对话、语音识别（Vosk 离线）、语音合成、技能执行（命令行操作）、视频通话、人脸检测与 Web 前端界面，支持通过「技能」自动执行各种系统任务。

## 功能特性

- **大模型对话**：支持 DeepSeek 与智谱 GLM-4-Flash，OpenAI 兼容接口
- **语音交互**：Vosk 离线中文语音识别（麦克风输入）+ TTS 语音合成播报
- **技能系统**：通过 `SKILL.md` 定义技能，AI 输出「命令:xxx」即自动执行，支持：
  - 获取新闻（Google News RSS）
  - 下载视频（yt-dlp）
  - 安装工具（pip install）
  - 查询磁盘空间
  - 视频通话（打开联系人视频界面）
  - 人脸检测（打开摄像头）
- **Web 界面**：Flask 后端 + 前端页面，支持浏览器交互
- **语音识别 API**：Flask Blueprint 提供离线语音识别 HTTP 接口
- **打包兼容**：适配 Nuitka / PyInstaller 打包环境，自动处理中文路径

## 环境要求

- Python 3.8+
- Flask、flask-cors、openai、requests
- pyaudio、vosk（语音识别，模型 `vosk-model-small-cn-0.22`）
- edge-tts / pyttsx3（语音合成）
- opencv-python、Pillow（摄像头与图像处理）
- yt-dlp（视频下载技能）

## 安装与运行

```bash
cd "python AI实战"
python install_dependencies.py
python Agent_zp.py
```

启动 Web 服务：

```bash
python ZCLAW.py
```

## 项目结构

```
python AI实战/
├── Agent_zp.py               # 语音助手主程序（对话 + 命令执行）
├── ZCLAW.py                  # Flask Web 服务端
├── LLM.py / deepseek.py      # 大模型调用模块
├── Microphone.py / TTS.py    # 语音识别 / 合成模块
├── speech_api.py             # Flask 语音识别 API（Blueprint）
├── skill_executor.py         # 技能命令执行器
├── video_call.py             # 视频通话模块
├── test_env.py               # 人脸检测（摄像头）
├── SKILL.md                  # 技能定义文件
├── install_dependencies.py   # 依赖自动安装脚本
├── vosk-model-small-cn-0.22/ # 离线中文语音模型
├── back-end/app.py           # 后端应用
├── front-end/                # Web 前端页面
├── sever/                    # 文件助手服务
└── README.md
```

## 核心模块

| 模块 | 职责 |
|------|------|
| `Agent_zp.py` | 语音对话循环：识别语音 → 调用 LLM → 执行命令/播报 |
| `skill_executor.py` | 解析 AI 输出的「命令:xxx」，执行系统命令，处理 `{项目路径}` 占位符，识别 GUI 程序 |
| `speech_api.py` | 提供离线语音识别 HTTP API，静音 3 秒自动停止录音 |
| `video_call.py` | 基于 OpenCV + PyAudio 的本地视频通话界面 |
| `test_env.py` | Haar 级联人脸检测，实时标注人脸框 |

## 技能系统说明

`SKILL.md` 中定义技能与触发词，AI 会按格式输出命令或完成信息：

```
技能：获取新闻；触发词：获取新闻、新闻内容
curl -L -A "Mozilla/5.0" "https://news.google.com/rss/search?q=XXX&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
```

- AI 输出 `命令:xxx` → 执行器调用 `execute_command` 执行
- AI 输出 `完成:xxx` → 直接总结信息给用户
- Windows 专用命令说明已注入系统提示词

## 使用说明

1. 设置环境变量：`ZHIPUAI_API_KEY`（智谱）或 `DEEPSEEK_API_KEY`（DeepSeek）
2. 运行 `Agent_zp.py`，通过语音或文字提问
3. 对 AI 说「获取新闻」等技能触发词，AI 自动执行对应命令并汇报结果

## 许可证

本项目仅供学习交流使用。
