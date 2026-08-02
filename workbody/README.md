# workbody

基于 Selenium 的「2026 年信息素养大赛 Python 复赛」试卷爬虫与整理工具集。项目用于自动进入在线考试系统，抓取各套试卷的全部题目（单选、多选、编程题等），将结果整理汇总成文本，供备考复习使用。目录中同时保留了抓取到的试卷题目文本与调试文件。

## 功能特性

- **自动进入试卷**：Selenium 驱动 Chrome 打开考试系统链接，自动填写姓名并开始考试
- **全题型抓取**：抓取单选题、多选题、编程题等所有题型
- **多试卷批量处理**：按考试 ID 列表逐个爬取，支持无头（headless）模式
- **结果整理**：将抓取结果汇总为「完整汇总」「最终报告」等文本文件
- **多种实现**：包含多个迭代版本的爬虫脚本，从简单到完整逐步完善
- **调试文件**：保存页面源码与抓取文本，便于排查问题

## 环境要求

- Python 3.8+
- Selenium、Chrome 浏览器及对应版本驱动

```bash
pip install selenium
```

## 项目结构

```
workbody/
├── final_scraper.py             # 完整版爬虫（无头模式，批量抓取）
├── comprehensive_scraper.py     # 全题型爬虫
├── auto_scraper.py / simple_auto_scraper.py  # 自动批量版本
├── simple_scraper.py / improved_scraper.py / interactive_scraper.py  # 迭代版本
├── fill_name_scraper.py         # 自动填写姓名版本
├── exam_scraper.py / test_single_exam.py     # 单卷测试
├── 所有试卷题目_完整版.txt / 所有试卷题目汇总.txt   # 汇总结果
├── Python复赛模拟题_完整汇总.txt / _最终报告.txt     # 整理报告
├── 2026年信息素养大赛Python复赛卷*.txt              # 各卷题目文本
├── 试卷1_271.txt ~ 试卷9_269.txt / 试卷_带姓名.txt   # 抓取结果
├── debug_*.html / exam_*.html / test_*.html         # 调试页面
└── README.md
```

## 使用说明

### 完整抓取所有试卷

```bash
python final_scraper.py
```

### 抓取单份试卷

```bash
python test_single_exam.py
```

## 工作流程

1. 配置考试系统链接与考试 ID
2. 脚本启动无头 Chrome，打开试卷页面
3. 自动填写姓名、点击「开始考试」
4. 逐题抓取并保存题目内容
5. 汇总所有试卷，输出整理后的文本报告

## 注意事项

- 请仅在本人拥有访问权限的考试系统上使用
- 控制抓取频率，避免对在线系统造成压力
- 调试 HTML 文件为排查爬虫问题所用，可忽略

## 许可证

本项目仅供学习交流使用。
