# 每日励志语句

一组用于自动采集「每日励志语句」与内容素材的 Python 爬虫脚本，支持获取金山词霸每日一句、B 站用户动态页面以及 B 站视频列表信息，数据可保存为本地文件，供网页或程序调用展示。

## 功能特性

- **每日一句（中英对照）**：调用金山词霸开放接口，输出当天英文句子及中文释义
- **B 站动态抓取**：下载指定 B 站用户的动态页面 HTML 到本地
- **B 站视频列表**：分页抓取用户的全部视频信息（标题、简介、播放量、弹幕数、评论数、时长、封面等），保存为 JSON

## 环境要求

- Python 3.7+
- `requests` 库

```bash
pip install requests
```

## 脚本说明

| 脚本 | 功能 | 输出 |
|------|------|------|
| `get_sth.py` | 获取金山词霸每日一句 | 控制台打印「英文 / 中文」 |
| `get_conent.py` | 抓取 B 站用户动态页面 | `dynamic.html` |
| `get_videos.py` | 分页抓取 B 站用户全部视频信息 | `videos.json` |

## 使用说明

### 获取每日一句

```bash
python get_sth.py
```

输出示例：

```
英文：Keep moving forward.
中文：继续向前。
```

### 抓取 B 站动态

```bash
python get_conent.py
```

脚本会将指定空间（默认 UID 480205745）的动态页 HTML 保存为 `dynamic.html`。

### 抓取视频列表

```bash
python get_videos.py
```

脚本按每页 30 条分页抓取，页间间隔 2 秒，完成后将全部视频信息写入 `videos.json`：

```json
[
  {
    "bvid": "BV1xxxx",
    "title": "视频标题",
    "description": "简介",
    "play": 12345,
    "danmaku": 100,
    "comment": 20,
    "length": "3:45",
    "created": 1735000000,
    "pic": "https://..."
  }
]
```

## 注意事项

- B 站接口需要携带合法的 `User-Agent` 与 `Referer`，脚本已内置
- 请遵守目标网站的使用条款，控制抓取频率，避免对服务器造成压力
- 金山词霸接口与 B 站接口可能随网站更新而变化，如失效请更新接口地址

## 项目结构

```
每日励志语句/
├── get_sth.py       # 每日一句采集
├── get_conent.py    # B 站动态页面抓取
├── get_videos.py    # B 站视频列表抓取
├── dynamic.html     # 动态页抓取结果（生成）
├── videos.json      # 视频信息（生成）
└── README.md
```

## 许可证

本项目仅供学习交流使用。
