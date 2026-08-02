# python 天气可视化

基于 Tkinter + Matplotlib 的天气查询与可视化工具。输入城市名即可实时查询天气数据，支持多日天气可视化图表展示，并可保存常用城市。

## 功能特性

- **天气查询**：输入城市名（支持中文，自动转拼音），从天气网站抓取实时天气信息
- **可视化图表**：使用 Matplotlib 绘制温度趋势等多日天气图表
- **城市保存**：记住上次查询的城市，下次启动自动填充
- **GUI 界面**：Tkinter + ttk 构建的现代化界面，图表内嵌展示
- **导航工具栏**：图表支持缩放、平移、保存等操作

## 环境要求

- Python 3.8+
- requests、BeautifulSoup4、pypinyin、matplotlib、Pillow

```bash
pip install requests beautifulsoup4 pypinyin matplotlib
```

## 安装与运行

```bash
cd "python 天气可视化"
python main.py
```

## 项目结构

```
python 天气可视化/
├── main.py        # 主程序：天气查询与可视化
├── test.py        # 辅助测试脚本
├── place.txt      # 保存的查询城市（生成）
├── output/        # 图表输出目录
├── html.html / weather.html   # 天气网页模板
├── ico.svg        # 图标文件
└── README.md
```

## 使用说明

1. 运行 `main.py` 启动程序
2. 输入城市名称（如「北京」），点击查询
3. 程序通过拼音转换调用天气网站接口，获取并解析天气数据
4. 多日天气以 Matplotlib 图表形式展示，可缩放、保存

### 城市记忆

- 查询后勾选保存，城市会写入 `place.txt`
- 下次启动自动读取并填入查询框

## 数据来源

天气数据来自天气网站接口（`https://www.tianqi.com/tianqi/headweather/`），请求时携带浏览器 UA 头。

## 许可证

本项目仅供学习交流使用。
