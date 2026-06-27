from wxauto import WeChat

wx = WeChat()
pyq = wx.Moments()   # 打开朋友圈并获取朋友圈窗口对象（如果为None则说明你没开启朋友圈，需要在手机端设置）