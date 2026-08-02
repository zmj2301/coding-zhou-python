# python-stroop训练

基于 Tkinter 的 Stroop 效应训练程序。Stroop 效应是指当文字含义与显示颜色不一致时（如「红色」用蓝色显示），人们的反应速度会变慢、出错率升高。本程序通过这一经典心理学范式训练玩家的注意力与反应抑制能力，并记录每次训练的成绩。

## 功能特性

- **经典 Stroop 任务**：显示彩色文字，玩家需点击「文字显示的颜色」而非文字本身
- **十种颜色**：红色、蓝色、绿色、黄色、紫色、橙色、粉色、青色、棕色、灰色等
- **计时计分**：记录每题的作答时间与正确性，计算最终得分
- **成绩持久化**：训练结果保存到 `stroop_records.json`，支持查看历史成绩
- **成绩对比**：生成 `stroop_comparison.html` 对比图表，直观查看进步曲线
- **AI 报告（可选）**：集成智谱 AI，可生成训练结果分析报告
- **10 题一轮**：每轮 10 道题，适合日常碎片化训练

## 环境要求

- Python 3.8+
- requests（可选，AI 报告功能需要）

```bash
pip install requests
```

## 安装与运行

```bash
cd "python-stroop训练"
python stroop_trainer.py
```

## 项目结构

```
python-stroop训练/
├── stroop_trainer.py          # 主程序
├── test_stroop_trainer.py     # 单元测试
├── zhipu_demo.py              # 智谱 AI 调用示例
├── stroop_records.json        # 训练成绩记录（生成）
├── stroop_comparison.html     # 成绩对比图表（生成）
├── 冒泡排序.cpp               # 辅助程序
├── 测试结果.txt               # 测试结果记录
└── README.md
```

## 核心实现

### 颜色判断

- `COLORS` 列表定义颜色名与十六进制色值
- `text_fg_for_bg(bg_hex)` 根据背景亮度自动选择白/黑文字，保证可读性

### 计分逻辑

- 每题限时作答，正确得分、错误不得分
- 记录作答耗时，用于分析反应速度

### 数据保存

训练完成后将成绩追加写入 `stroop_records.json`，可生成历史对比图表。

## 使用说明

1. 运行 `stroop_trainer.py` 进入训练
2. 根据提示「请点击文字显示的颜色，而不是文字内容！」作答
3. 完成 10 题后查看得分与用时
4. 设置 `ZHIPUAI_API_KEY` 环境变量可启用 AI 结果分析

## 许可证

本项目仅供学习交流使用。
