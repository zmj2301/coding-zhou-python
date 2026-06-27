技能：获取新闻；触发词：获取新闻、新闻内容、新闻详情，其中xxx为用户希望搜索的关键词
curl -L -A "Mozilla/5.0" "https://news.google.com/rss/search?q=XXX&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
技能：下载视频
yt-dlp {视频网址}
技能：安装终端工具
pip install {工具名称}
技能：获取磁盘空间；触发词：磁盘空间、剩余空间、硬盘空间
wmic logicaldisk where "DeviceID='D:'" get FreeSpace,Size
技能：视频通话；触发词：打电话、视频通话、呼叫、通话
python "{项目路径}/video_call.py" {联系人姓名}
技能：人脸检测；触发词：人脸识别、检测人脸、打开摄像头
python "{项目路径}/test_env.py"