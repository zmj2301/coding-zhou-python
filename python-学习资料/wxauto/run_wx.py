# https://plus.wxauto.org/docs/class/WeChat.html

from wxauto import WeChat
import time

a = time.time()
# 初始化微信实例
wx = WeChat()

# 发送消息
wx.SendMsg("你好", who="文件传输助")

# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()

for msg in msgs:
    print('==' * 30)
    print(f"{msg.sender}: {msg.content}")