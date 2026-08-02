# Python文字转语音无AI版

使用 `pyttsx3` 本地引擎的离线文字转语音（TTS）工具。无需联网、无需 AI 接口，读取文本文件中的内容后直接朗读，可自定义语速、音量与音色。

## 功能特性

- **离线朗读**：基于系统内置 TTS 引擎，完全本地运行
- **文本读取**：自动读取 `test.txt` 文件内容并朗读
- **参数调节**：支持自定义语速（rate）、音量（volume）与音色（voice）

## 环境要求

- Python 3.7+
- pyttsx3

```bash
pip install pyttsx3
```

## 安装与运行

```bash
cd "Python文字转语音无AI版"
python TTS.py
```

## 项目结构

```
Python文字转语音无AI版/
├── TTS.py      # 主程序
├── test.txt    # 待朗读的文本
└── README.md
```

## 核心实现

```python
engine = pyttsx3.init()
text = open('test.txt', encoding='utf-8').read()
engine.say(text)
engine.setProperty('rate', 300)        # 语速
engine.setProperty('volume', 0.5)      # 音量
engine.setProperty('voice', 'zh-CN-YunxiuNeural-A')  # 音色
engine.runAndWait()
```

## 使用说明

1. 将需要朗读的文字写入 `test.txt`（UTF-8 编码）
2. 运行 `TTS.py`，程序自动朗读文件内容
3. 如需修改音色，可查看系统支持的语音列表后更换 `voice` 属性

## 许可证

本项目仅供学习交流使用。
