"""
Author: Cluic
Update: 2024-07-22
Version: 3.9.11.17.4
"""

from . import uiautomation as uia
from .languages import *
from .utils import *
from .elements import *
from .errors import *
from .color import *
import time
import os
import re
try:
    from typing import Literal
except:
    from typing_extensions import Literal

class WeChat(WeChatBase):
    VERSION: str = '3.9.11.17'
    lastmsgid: str = None
    listen: dict = dict()
    SessionItemList: list = []

    def __init__(
            self, 
            language: Literal['cn', 'cn_t', 'en'] = 'cn', 
            debug: bool = False
        ) -> None:
        """微信UI自动化实例

        Args:
            language (str, optional): 微信客户端语言版本, 可选: cn简体中文  cn_t繁体中文  en英文, 默认cn, 即简体中文
        """
        # 优化：使用更快的win32gui先定位窗口
        import win32gui
        hwnd = None
        
        # 1. 快速查找窗口句柄
        for class_name in ['WeChatMainWndForPC', 'Qt51514QWindowIcon']:
            hwnd = win32gui.FindWindow(class_name, None)
            if hwnd != 0:
                break
        
        # 2. 如果通过类名找不到，尝试通过标题查找
        if hwnd == 0:
            hwnd = win32gui.FindWindow(None, '微信')
        
        # 3. 使用UIAutomation查找窗口（保持与原始代码兼容的方式）
        window_control = None
        
        # 优先使用原始方式创建UIA控件，确保窗口结构正确
        for class_name in ['WeChatMainWndForPC', 'Qt51514QWindowIcon']:
            try:
                window_control = uia.WindowControl(ClassName=class_name, searchDepth=1)
                if window_control.Exists():  # 检查窗口是否存在
                    break
            except:
                continue
        
        # 如果通过类名找不到，尝试通过标题查找
        if window_control is None or not window_control.Exists():
            window_control = uia.WindowControl(Name='微信', searchDepth=1)
        
        self.UiaAPI = window_control
        self.HWND = hwnd  # 保存窗口句柄供后续使用
        set_debug(debug)
        self.language = language
        # 初始化控件缓存字典
        self._control_cache = {}
        # self._checkversion()
        self._show()
        
        # 优化：更安全的窗口结构解析
        try:
            children = self.UiaAPI.GetChildren()
            # 查找主控制元素
            main_controls = [i for i in children if not i.ClassName]
            if not main_controls:
                # 如果找不到无类名的控件，尝试所有子控件
                main_controls = children
            
            MainControl1 = main_controls[0]
            MainControl2 = MainControl1.GetFirstChildControl()
            
            # 获取窗口布局控件
            layout_controls = MainControl2.GetChildren()
            
            # 兼容不同的窗口结构
            if len(layout_controls) >= 3:
                # 标准三栏布局
                self.NavigationBox, self.SessionBox, self.ChatBox = layout_controls[:3]
            elif len(layout_controls) == 1:
                # 可能是新的Qt布局，尝试获取更深层次的控件
                sub_controls = layout_controls[0].GetChildren()
                if len(sub_controls) >= 3:
                    self.NavigationBox, self.SessionBox, self.ChatBox = sub_controls[:3]
                else:
                    # 使用基本控件结构，确保程序能够运行
                    self.NavigationBox = layout_controls[0] if layout_controls else None
                    self.SessionBox = None
                    self.ChatBox = None
            else:
                # 默认赋值
                self.NavigationBox = layout_controls[0] if len(layout_controls) > 0 else None
                self.SessionBox = layout_controls[1] if len(layout_controls) > 1 else None
                self.ChatBox = layout_controls[2] if len(layout_controls) > 2 else None
                
        except Exception as e:
            print(f"窗口结构解析警告: {e}")
            print("将使用简化的控件结构")
            # 简化模式，确保程序能够继续运行
            self.NavigationBox = None
            self.SessionBox = None
            self.ChatBox = None
        
        # 初始化控件，添加错误处理以确保程序能够运行
        try:
            # 初始化导航栏，以A开头 | self.NavigationBox  -->  A_xxx
            if self.NavigationBox:
                self.A_MyIcon = self.NavigationBox.ButtonControl()
                self.A_ChatIcon = self.NavigationBox.ButtonControl(Name=self._lang('聊天'))
                self.A_ContactsIcon = self.NavigationBox.ButtonControl(Name=self._lang('通讯录'))
                self.A_FavoritesIcon = self.NavigationBox.ButtonControl(Name=self._lang('收藏'))
                self.A_FilesIcon = self.NavigationBox.ButtonControl(Name=self._lang('聊天文件'))
                self.A_MomentsIcon = self.NavigationBox.ButtonControl(Name=self._lang('朋友圈'))
                self.A_MiniProgram = self.NavigationBox.ButtonControl(Name=self._lang('小程序面板'))
                self.A_Phone = self.NavigationBox.ButtonControl(Name=self._lang('手机'))
                self.A_Settings = self.NavigationBox.ButtonControl(Name=self._lang('设置及其他'))
            else:
                # 创建虚拟控件引用，避免后续错误
                self.A_MyIcon = None
                self.A_ChatIcon = None
                self.A_ContactsIcon = None
                self.A_FavoritesIcon = None
                self.A_FilesIcon = None
                self.A_MomentsIcon = None
                self.A_MiniProgram = None
                self.A_Phone = None
                self.A_Settings = None
            
            # 初始化聊天列表，以B开头
            self.B_Search = self.SessionBox.EditControl(Name=self._lang('搜索')) if self.SessionBox else None
            
            # 初始化聊天栏，以C开头
            self.C_MsgList = self.ChatBox.ListControl(Name=self._lang('消息')) if self.ChatBox else None
            
            # 获取昵称
            self.nickname = self.A_MyIcon.Name if self.A_MyIcon else "未知"
            
            # 优化：延迟加载聊天记录，初始化时只获取昵称
            self.usedmsgid = []  # 初始化为空列表，在实际需要时再填充
            print(f'初始化成功，获取到已登录窗口：{self.nickname}')
            
        except Exception as e:
            print(f"控件初始化警告: {e}")
            print("程序已在简化模式下启动，部分功能可能受限")
            # 设置基本属性，确保程序能够继续运行
            self.nickname = "未知"
            self.usedmsgid = []
    
    def _checkversion(self):
        # 使用统一的窗口查找逻辑
        def find_wechat_hwnd():
            # 尝试标准类名
            hwnd = FindWindow(classname='WeChatMainWndForPC')
            if hwnd != 0:
                return hwnd
            
            # 尝试Qt类名（新版本微信可能使用）
            hwnd = FindWindow(classname='Qt51514QWindowIcon', name='微信')
            if hwnd != 0:
                return hwnd
            
            # 尝试通过标题查找
            hwnd = FindWindow(name='微信')
            return hwnd
        
        self.HWND = find_wechat_hwnd()
        if self.HWND == 0:
            raise RuntimeError("微信主窗口未找到，请确保微信已启动!")
            
        wxpath = GetPathByHwnd(self.HWND)
        wxversion = GetVersionByPath(wxpath)
        if wxversion != self.VERSION:
            Warnings.lightred(self._lang('版本不一致', 'WARNING').format(wxversion, self.VERSION), stacklevel=2)
            return False
    
    
    def _show(self):
        import win32gui  # 确保win32gui在所有代码路径中可用
        
        # 优化：如果已经有HWND，直接使用，避免重复查找
        if not hasattr(self, 'HWND') or self.HWND == 0:
            # 快速查找窗口句柄
            self.HWND = win32gui.FindWindow('WeChatMainWndForPC', None)
            if self.HWND == 0:
                self.HWND = win32gui.FindWindow('Qt51514QWindowIcon', '微信')
            if self.HWND == 0:
                self.HWND = win32gui.FindWindow(None, '微信')
        
        if self.HWND == 0:
            raise RuntimeError("微信主窗口未找到，请确保微信已启动!")
        
        # 优化：减少窗口操作次数
        win32gui.ShowWindow(self.HWND, 1)
        # 合并SetWindowPos调用，减少系统调用
        win32gui.SetWindowPos(self.HWND, -1, 0, 0, 0, 0, 3)  # 置顶
        win32gui.SetWindowPos(self.HWND, -2, 0, 0, 0, 0, 3)  # 取消置顶
        self.UiaAPI.SwitchToThisWindow()

    def _refresh(self):
        self.UiaAPI.SendKeys('{Ctrl}{Alt}w')
        self.UiaAPI.SendKeys('{Ctrl}{Alt}w')
        self._show()
        
    def _get_cached_control(self, cache_key, control_getter):
        """获取缓存的控件，如果不存在则创建并缓存
        
        Args:
            cache_key (str): 控件的缓存键
            control_getter (callable): 获取控件的函数
            
        Returns:
            control: 找到的控件
        """
        # 检查缓存中是否有该控件
        if cache_key in self._control_cache:
            # 验证缓存的控件是否仍然存在
            try:
                cached_control = self._control_cache[cache_key]
                if cached_control.Exists(0.01):  # 快速检查控件是否存在
                    return cached_control
            except:
                # 缓存的控件不存在，从缓存中移除
                del self._control_cache[cache_key]
        
        # 控件不在缓存中或已失效，获取新控件并缓存
        try:
            control = control_getter()
            # 验证控件是否有效
            if control and control.Exists(0.1):
                self._control_cache[cache_key] = control
                return control
        except Exception as e:
            wxlog.debug(f'获取控件失败 {cache_key}: {e}')
        
        return None

    def _get_friend_details(self):
        params = ['昵称：', '微信号：', '地区：', '备注', '电话', '标签', '共同群聊', '个性签名', '来源', '朋友权限', '描述', '实名', '企业']
        info = {}
        controls = GetAllControlList(self.ChatBox)
        for _, i in enumerate(controls):
            rect = i.BoundingRectangle
            text = i.Name
            if text in params or (rect.width() == 57 and rect.height() == 20):
                info[text.replace('：', '')] = controls[_+1].Name
        if '昵称' not in info:
            info['备注'] = ''
            info['昵称'] = controls[0].Name
        wxlog.debug(f'获取到好友详情：{info}')
        return info
    
    def _goto_first_friend(self):
        def find_letter_tag(self):
            items = self.SessionBox.ListControl().GetChildren()
            for index, item in enumerate(items[:-1]):
                if item.TextControl(RegexName='^[A-Z]$').Exists(0):
                    # print('>>> bingo!\n')
                    # GetAllControl(item)
                    return items[index+1]
        while True:
            item = find_letter_tag(self)
            if item is not None:
                self.SessionBox.WheelDown(wheelTimes=3)
                item.Click(simulateMove=False)
                break
            self.SessionBox.WheelDown(wheelTimes=3, interval=0)

    def GetFriendDetails(self, n=None, timeout=0xFFFFF):
        """获取所有好友详情信息
        
        Args:
            n (int, optional): 获取前n个好友详情信息, 默认为None，获取所有好友详情信息
            timeout (int, optional): 获取超时时间（秒），超过该时间则直接返回结果

        Returns:
            list: 所有好友详情信息
            
        注：1. 该方法运行时间较长，约0.5~1秒一个好友的速度，好友多的话可将n设置为一个较小的值，先测试一下
            2. 如果遇到企业微信的好友且为已离职状态，可能导致微信卡死，需重启（此为微信客户端BUG）
            3. 该方法未经过大量测试，可能存在未知问题，如有问题请微信群内反馈
        """
        t0 = time.time()
        self.SwitchToContact()
        self._goto_first_friend()
        details = []
        while True:
            if time.time() - t0 > timeout:
                wxlog.debug('获取好友详情超时，返回结果')
                return details
            _detail = self._get_friend_details()
            if details and _detail == details[-1]:
                return details
            details.append(_detail)
            self.SessionBox.SendKeys('{DOWN}')
            if n and len(details) >= n:
                return details

            
    def GetSessionAmont(self, SessionItem):
        """获取聊天对象名和新消息条数
        
        Args:
            SessionItem (uiautomation.ListItemControl): 聊天对象控件
            
        Returns:
            sessionname (str): 聊天对象名
            amount (int): 新消息条数
        """
        matchobj = re.search('\d+条新消息', SessionItem.Name)
        amount = 0
        if matchobj:
            try:
                amount = int([i for i in SessionItem.GetFirstChildControl().GetChildren() if type(i) == uia.TextControl][0].Name)
            except:
                pass
        sessionname = SessionItem.Name if SessionItem.ButtonControl().Name == 'SessionListItem' else SessionItem.ButtonControl().Name
        return sessionname, amount
    
    def CheckNewMessage(self):
        """是否有新消息"""
        self._show()
        return IsRedPixel(self.A_ChatIcon)
    
    def GetNextNewMessage(self, savepic=False, savefile=False, savevoice=False, timeout=10):
        """获取下一个新消息"""
        msgs_ = self.GetAllMessage()
        msgids = [i[-1] for i in msgs_]

        if not self.usedmsgid:
            self.usedmsgid = msgids
        
        newmsgids = [i for i in msgids if i not in self.usedmsgid]
        oldmsgids = [i for i in self.usedmsgid if i in msgids]
        if newmsgids and oldmsgids:
            MsgItems = self.C_MsgList.GetChildren()
            msgids = [''.join([str(i) for i in i.GetRuntimeId()]) for i in MsgItems]
            new = []
            for i in range(len(msgids)-1, -1, -1):
                if msgids[i] in self.usedmsgid:
                    new = msgids[i+1:]
                    break
            NewMsgItems = [
                i for i in MsgItems 
                if ''.join([str(i) for i in i.GetRuntimeId()]) in new
                and i.ControlTypeName == 'ListItemControl'
            ]
            if NewMsgItems:
                wxlog.debug('获取当前窗口新消息')
                msgs = self._getmsgs(NewMsgItems, savepic, savefile, savevoice)
                self.usedmsgid = msgids
                return {self.CurrentChat(): msgs}

        if self.CheckNewMessage():
            wxlog.debug('获取其他窗口新消息')
            t0 = time.time()
            while True:
                if time.time() - t0 > timeout:
                    wxlog.debug('获取新消息超时')
                    return {}
                self.A_ChatIcon.DoubleClick(simulateMove=False)
                sessiondict = self.GetSessionList(newmessage=True)
                if sessiondict:
                    break
            for session in sessiondict:
                self.ChatWith(session)
                NewMsgItems = self.C_MsgList.GetChildren()[-sessiondict[session]:]
                msgs = self._getmsgs(NewMsgItems, savepic, savefile, savevoice)
                msgs_ = self.GetAllMessage()
                self.usedmsgid = [i[-1] for i in msgs_]
                return {session:msgs}
        else:
            wxlog.debug('没有新消息')
            return {}
    
    def GetAllNewMessage(self, max_round=10):
        """获取所有新消息
        
        Args:
            max_round (int): 最大获取次数  * 这里是为了避免某几个窗口一直有新消息，导致无法停止
        """
        newmessages = {}
        for _ in range(max_round):
            newmsg = self.GetNextNewMessage()
            if newmsg:
                for session in newmsg:
                    if session not in newmessages:
                        newmessages[session] = []
                    newmessages[session].extend(newmsg[session])
            else:
                break
        return newmessages
    
    def GetSessionList(self, reset=False, newmessage=False):
        """获取当前聊天列表中的所有聊天对象
        
        Args:
            reset (bool): 是否重置SessionItemList
            newmessage (bool): 是否只获取有新消息的聊天对象
            
        Returns:
            SessionList (dict): 聊天对象列表，键为聊天对象名，值为新消息条数
        """
        self.SessionItem = self.SessionBox.ListItemControl()
        if reset:
            self.SessionItemList = []
        SessionList = {}
        for i in range(100):
            if self.SessionItem.BoundingRectangle.width() != 0:
                try:
                    name, amount = self.GetSessionAmont(self.SessionItem)
                except:
                    break
                if name not in self.SessionItemList:
                    self.SessionItemList.append(name)
                if name not in SessionList:
                    SessionList[name] = amount
            self.SessionItem = self.SessionItem.GetNextSiblingControl()
            if not self.SessionItem:
                break
            
        if newmessage:
            return {i:SessionList[i] for i in SessionList if SessionList[i] > 0}
        return SessionList
    
    def GetSession(self):
        """获取当前聊天列表中的所有聊天对象

        Returns:
            SessionElement: 聊天对象列表

        Example:
            >>> wx = WeChat()
            >>> sessions = wx.GetSession()
            >>> for session in sessions:
            ...     print(f"聊天对象名称: {session.name}")
            ...     print(f"最后一条消息时间: {session.time}")
            ...     print(f"最后一条消息内容: {session.content}")
            ...     print(f"是否有新消息: {session.isnew}", end='\n\n')
        """
        sessions = self.SessionBox.ListControl()
        return [SessionElement(i) for i in sessions.GetChildren()]
    
    def ChatWith(self, who, timeout=1):  # 减少默认超时时间
        '''打开某个聊天框
        
        Args:
            who ( str ): 要打开的聊天框好友名;  * 最好完整匹配，不完全匹配只会选取搜索框第一个
            timeout ( num, optional ): 超时时间，默认1秒（优化）
            
        Returns:
            chatname ( str ): 匹配值第一个的完整名字
        '''
        self._show()
        
        # 快速检查会话列表中是否有目标
        try:
            # 直接查找会话项，避免获取整个会话列表（性能优化）
            session_item = self.SessionBox.ListItemControl(RegexName=who)
            if session_item.Exists(0.5):  # 快速检查
                session_item.Click(simulateMove=False)
                return who
        except:
            pass
        
        # 如果直接查找失败，使用搜索功能
        self.UiaAPI.SendKeys('{Ctrl}f', waitTime=0.2)  # 大幅减少等待时间
        self.B_Search.SendKeys(who, waitTime=0.5)  # 减少等待时间
        
        # 查找完全匹配项
        target_control = self.SessionBox.TextControl(Name=f"<em>{who}</em>")
        if target_control.Exists(timeout):
            wxlog.debug('选择完全匹配项')
            target_control.Click(simulateMove=False)
            return who
        else:
            # 尝试查找搜索结果
            try:
                # 优化搜索结果控件路径
                search_container = self.SessionBox.GetChildren()[1] if len(self.SessionBox.GetChildren()) > 1 else self.SessionBox
                search_result_control = search_container.GetChildren()[1].GetFirstChildControl() if len(search_container.GetChildren()) > 1 else None
                
                if search_result_control:
                    # 检查是否有搜索结果
                    if not search_result_control.PaneControl(searchDepth=1).TextControl(RegexName='联系人|群聊').Exists(0.05):  # 减少等待时间
                        wxlog.debug(f'未找到搜索结果: {who}')
                        self._refresh()
                        return False
                    
                    wxlog.debug('选择搜索结果第一个')
                    target_control = search_result_control.Control(RegexName=f'.*{who}.*')
                    chatname = target_control.Name
                    target_control.Click(simulateMove=False)
                    return chatname
            except Exception as e:
                wxlog.debug(f'选择搜索结果失败: {e}')
                self._refresh()
                return False
    
    def AtAll(self, msg=None, who=None):
        """@所有人
        
        Args:
            who (str, optional): 要发送给谁，如果为None，则发送到当前聊天页面。  *最好完整匹配，优先使用备注
            msg (str, optional): 要发送的文本消息
        """
        if FindWindow(name=who, classname='ChatWnd'):
            chat = ChatWnd(who, self.language)
            chat.AtAll(msg)
            return None
        
        self._show()
        if who:
            try:
                editbox = self.ChatBox.EditControl(searchDepth=10)
                if who in self.CurrentChat() and who in editbox.Name:
                    pass
                else:
                    self.ChatWith(who)
                    editbox = self.ChatBox.EditControl(Name=who, searchDepth=10)
            except:
                self.ChatWith(who)
                editbox = self.ChatBox.EditControl(Name=who, searchDepth=10)
        else:
            editbox = self.ChatBox.EditControl(searchDepth=10)
        editbox.SendKeys('@')
        atwnd = self.UiaAPI.PaneControl(ClassName='ChatContactMenu')
        if atwnd.Exists(maxSearchSeconds=0.1):
            atwnd.ListItemControl(Name='所有人').Click(simulateMove=False)
            if msg:
                if not msg.startswith('\n'):
                    msg = '\n' + msg
                self.SendMsg(msg, who=who, clear=False)
            else:
                editbox.SendKeys('{Enter}')

    def SendMsg(self, msg, who=None, clear=True, at=None):
        """发送文本消息

        Args:
            msg (str): 要发送的文本消息
            who (str): 要发送给谁，如果为None，则发送到当前聊天页面。  *最好完整匹配，优先使用备注
            clear (bool, optional): 是否清除原本的内容，
            at (str|list, optional): 要@的人，可以是一个人或多个人，格式为str或list，例如："张三"或["张三", "李四"]
        """
        if FindWindow(name=who, classname='ChatWnd'):
            chat = ChatWnd(who, self.language)
            chat.SendMsg(msg, at=at)
            return None
        if not msg and not at:
            return None
            
        # 缓存编辑框控件，避免重复查找
        editbox = None
        
        if who:
            # 检查当前聊天窗口是否已经是目标对象
            current_chat = self.CurrentChat()
            if current_chat and who in current_chat:
                # 如果当前聊天已经是目标，使用缓存获取编辑框
                editbox = self._get_cached_control(
                    f'editbox_{current_chat}',
                    lambda: self.ChatBox.EditControl(searchDepth=5)
                )
            else:
                # 需要切换聊天对象
                self.ChatWith(who)
                # 切换后使用缓存获取编辑框
                current_chat = self.CurrentChat() or who
                editbox = self._get_cached_control(
                    f'editbox_{current_chat}',
                    lambda: self.ChatBox.EditControl(searchDepth=5)
                )
        else:
            # 发送到当前聊天窗口，使用缓存获取编辑框
            current_chat = self.CurrentChat() or 'default'
            editbox = self._get_cached_control(
                f'editbox_{current_chat}',
                lambda: self.ChatBox.EditControl(searchDepth=5)
            )
        
        # 添加空值检查和回退机制
        if not editbox:
            wxlog.debug('缓存获取编辑框失败，尝试直接获取')
            try:
                # 尝试直接获取编辑框，不使用缓存
                editbox = self.ChatBox.EditControl(searchDepth=10)
            except Exception as e:
                raise RuntimeError(f"无法获取编辑框控件: {e}")
        
        if clear:
            editbox.SendKeys('{Ctrl}a', waitTime=0)  # 减少等待时间
            
        # 确保窗口可见
        self._show()
        
        # 确保编辑框获得焦点
        if not editbox.HasKeyboardFocus:
            editbox.Click(simulateMove=False)  # 不模拟鼠标移动，加快速度
        
        # 处理@功能
        if at:
            if isinstance(at, str):
                at = [at]
            for i in at:
                editbox.SendKeys('@'+i, waitTime=0.1)  # 减少等待时间
                atwnd = self.UiaAPI.PaneControl(ClassName='ChatContactMenu')
                if atwnd.Exists(maxSearchSeconds=0.05):  # 减少搜索时间
                    atwnd.SendKeys('{ENTER}', waitTime=0)
                    if msg and not msg.startswith('\n'):
                        msg = '\n' + msg

        # 处理消息内容
        if msg:
            # 使用更高效的方式设置文本，减少重试循环
            SetClipboardText(msg)
            editbox.SendKeys('{Ctrl}v', waitTime=0)
            
            # 快速验证文本是否已设置
            if not editbox.GetValuePattern().Value:
                # 只重试一次，而不是无限循环
                SetClipboardText(msg)
                editbox.SendKeys('{Ctrl}v', waitTime=0)
        
        # 发送消息
        editbox.SendKeys('{Enter}', waitTime=0)  # 减少等待时间
        
    def SendFiles(self, filepath, who=None):
        """向当前聊天窗口发送文件
        
        Args:
            filepath (str|list): 要复制文件的绝对路径  
            who (str): 要发送给谁，如果为None，则发送到当前聊天页面。  *最好完整匹配，优先使用备注
            
        Returns:
            bool: 是否成功发送文件
        """
        if FindWindow(name=who, classname='ChatWnd'):
            chat = ChatWnd(who, self.language)
            chat.SendFiles(filepath)
            return None
        filelist = []
        if isinstance(filepath, str):
            if not os.path.exists(filepath):
                Warnings.lightred(f'未找到文件：{filepath}，无法成功发送', stacklevel=2)
                return False
            else:
                filelist.append(os.path.realpath(filepath))
        elif isinstance(filepath, (list, tuple, set)):
            for i in filepath:
                if os.path.exists(i):
                    filelist.append(i)
                else:
                    Warnings.lightred(f'未找到文件：{i}', stacklevel=2)
        else:
            Warnings.lightred(f'filepath参数格式错误：{type(filepath)}，应为str、list、tuple、set格式', stacklevel=2)
            return False
        
        if filelist:
            self._show()
            if who:
                try:
                    if who in self.CurrentChat() and who in self.ChatBox.EditControl(searchDepth=10).Name:
                        pass
                    else:
                        self.ChatWith(who)
                except:
                    self.ChatWith(who)
                editbox = self.ChatBox.EditControl(Name=who)
            else:
                editbox = self.ChatBox.EditControl()
            editbox.SendKeys('{Ctrl}a', waitTime=0)
            t0 = time.time()
            while True:
                if time.time() - t0 > 5:  # 减少超时时间
                    raise TimeoutError(f'发送文件超时 --> {filelist}')
                SetClipboardFiles(filelist)
                # 减少等待时间，提高检查频率
                editbox.SendKeys('{Ctrl}v', waitTime=0)  # 立即发送粘贴命令
                # 快速检查是否成功
                if editbox.GetValuePattern().Value:
                    break
                time.sleep(0.05)  # 极短的等待时间
            editbox.SendKeys('{Enter}')
            return True
        else:
            Warnings.lightred('所有文件都无法成功发送', stacklevel=2)
            return False
            
    def GetAllMessage(self, savepic=False, savefile=False, savevoice=False):
        '''获取当前窗口中加载的所有聊天记录
        
        Args:
            savepic (bool): 是否自动保存聊天图片
            
        Returns:
            list: 聊天记录信息
        '''
        if not self.C_MsgList.Exists(0.2):
            return []
        MsgItems = self.C_MsgList.GetChildren()
        msgs = self._getmsgs(MsgItems, savepic, savefile=savefile, savevoice=savevoice)
        return msgs
    
    def LoadMoreMessage(self):
        """加载当前聊天页面更多聊天信息
        
        Returns:
            bool: 是否成功加载更多聊天信息
        """
        loadmore = self.C_MsgList.GetFirstChildControl()
        loadmore_top = loadmore.BoundingRectangle.top
        top = self.C_MsgList.BoundingRectangle.top
        while True:
            if loadmore.BoundingRectangle.top > top or loadmore.Name == '':
                isload = True
                break
            else:
                self.C_MsgList.WheelUp(wheelTimes=10, waitTime=0.1)
                if loadmore.BoundingRectangle.top == loadmore_top:
                    isload = False
                    break
                else:
                    loadmore_top = loadmore.BoundingRectangle.top
        self.C_MsgList.WheelUp(wheelTimes=1, waitTime=0.1)
        return isload
    
    def CurrentChat(self):
        '''获取当前聊天对象名'''
        try:
            # 设置更短的超时时间
            uia.SetGlobalSearchTimeout(0.3)
            
            # 使用控件缓存获取当前聊天控件
            chat_text_control = self._get_cached_control(
                'current_chat_text',
                lambda: self.ChatBox.TextControl(searchDepth=5)
            )
            
            if chat_text_control:
                return chat_text_control.Name
            return None
        except Exception as e:
            wxlog.debug(f'获取当前聊天失败: {e}')
            return None
        finally:
            # 恢复默认超时设置
            uia.SetGlobalSearchTimeout(10)

    def GetNewFriends(self):
        """获取新的好友申请列表
        
        Returns:
            list: 新的好友申请列表，元素为NewFriendsElement对象，可直接调用Accept方法

        Example:
            >>> wx = WeChat()
            >>> newfriends = wx.GetNewFriends()
            >>> tags = ['标签1', '标签2']
            >>> for friend in newfriends:
            ...     remark = f'备注{friend.name}'
            ...     friend.Accept(remark=remark, tags=tags)  # 接受好友请求，并设置备注和标签
        """
        self._show()
        self.SwitchToContact()
        self.SessionBox.ButtonControl(Name='ContactListItem').Click(simulateMove=False)
        NewFriendsList = [NewFriendsElement(i, self) for i in self.ChatBox.ListControl(Name='新的朋友').GetChildren()]
        AcceptableNewFriendsList = [i for i in NewFriendsList if i.acceptable]
        wxlog.debug(f'获取到 {len(AcceptableNewFriendsList)} 条新的好友申请')
        return AcceptableNewFriendsList
    
    def AddListenChat(self, who, savepic=False, savefile=False, savevoice=False):
        """添加监听对象
        
        Args:
            who (str): 要监听的聊天对象名
            savepic (bool, optional): 是否自动保存聊天图片，只针对该聊天对象有效
            savefile (bool, optional): 是否自动保存聊天文件，只针对该聊天对象有效
            savevoice (bool, optional): 是否自动保存聊天语音，只针对该聊天对象有效
        """
        exists = uia.WindowControl(searchDepth=1, ClassName='ChatWnd', Name=who).Exists(maxSearchSeconds=0.1)
        if not exists:
            self.ChatWith(who)
            self.SessionBox.ListItemControl(RegexName=who).DoubleClick(simulateMove=False)
        self.listen[who] = ChatWnd(who, self.language)
        self.listen[who].savepic = savepic
        self.listen[who].savefile = savefile
        self.listen[who].savevoice = savevoice

    def GetListenMessage(self, who=None):
        """获取监听对象的新消息
        
        Args:
            who (str, optional): 要获取消息的聊天对象名，如果为None，则获取所有监听对象的消息

        Returns:
            str|dict: 如果
        """
        if who and who in self.listen:
            chat = self.listen[who]
            msg = chat.GetNewMessage(savepic=chat.savepic, savefile=chat.savefile, savevoice=chat.savevoice)
            return msg
        msgs = {}
        for who in self.listen:
            chat = self.listen[who]
            msg = chat.GetNewMessage(savepic=chat.savepic, savefile=chat.savefile, savevoice=chat.savevoice)
            if msg:
                msgs[chat] = msg
        return msgs

    def SwitchToContact(self):
        """切换到通讯录页面"""
        self._show()
        self.A_ContactsIcon.Click(simulateMove=False)

    def SwitchToChat(self):
        """切换到聊天页面"""
        self._show()
        self.A_ChatIcon.Click(simulateMove=False)

    # def DownloadFiles(self, who, amount=1):
    #     """切换到聊天文件页面
        
    #     Args:
    #         who (str): 要下载文件的聊天对象名
    #         amount (int): 要下载的文件数量
    #     """
    #     self._show()
    #     self.A_FilesIcon.Click(simulateMove=False)
    #     files = WeChatFiles()
    #     files.ChatWithFile(who)
    #     files.DownloadFiles(who, amount)
    #     files.Close()

    def GetGroupMembers(self):
        """获取当前聊天群成员

        Returns:
            list: 当前聊天群成员列表
        """
        ele = self.ChatBox.PaneControl(searchDepth=7, foundIndex=6).ButtonControl(Name='聊天信息')
        try:
            uia.SetGlobalSearchTimeout(1)
            rect = ele.BoundingRectangle
            Click(rect)
        except:
            return 
        finally:
            uia.SetGlobalSearchTimeout(10)
        roominfoWnd = self.UiaAPI.Control(ClassName='SessionChatRoomDetailWnd', searchDepth=1)
        more = roominfoWnd.ButtonControl(Name='查看更多', searchDepth=8)
        try:
            uia.SetGlobalSearchTimeout(1)
            rect = more.BoundingRectangle
            Click(rect)
        except:
            pass
        finally:
            uia.SetGlobalSearchTimeout(10)
        members = [i.Name for i in roominfoWnd.ListControl(Name='聊天成员').GetChildren()]
        while members[-1] in ['添加', '移出']:
            members = members[:-1]
        roominfoWnd.SendKeys('{Esc}')
        return members

    def GetAllFriends(self, keywords=None):
        """获取所有好友列表
        注：
            1. 该方法运行时间取决于好友数量，约每秒6~8个好友的速度
            2. 该方法未经过大量测试，可能存在未知问题，如有问题请微信群内反馈
        
        Args:
            keywords (str, optional): 搜索关键词，只返回包含关键词的好友列表
            
        Returns:
            list: 所有好友列表
        """
        self._show()
        self.SwitchToContact()
        self.SessionBox.ListControl(Name="联系人").ButtonControl(Name="通讯录管理").Click(simulateMove=False)
        contactwnd = ContactWnd()
        if keywords:
            contactwnd.Search(keywords)
        friends = contactwnd.GetAllFriends()
        contactwnd.Close()
        self.SwitchToChat()
        return friends
    
    def GetAllListenChat(self):
        """获取所有监听对象"""
        return self.listen
    
    def RemoveListenChat(self, who):
        """移除监听对象"""
        if who in self.listen:
            del self.listen[who]
        else:
            Warnings.lightred(f'未找到监听对象：{who}', stacklevel=2)

    def AddNewFriend(self, keywords, addmsg=None, remark=None, tags=None):
        """添加新的好友

        Args:
            keywords (str): 搜索关键词，微信号、手机号、QQ号
            addmsg (str, optional): 添加好友的消息
            remark (str, optional): 备注名
            tags (list, optional): 标签列表

        Example:
            >>> wx = WeChat()
            >>> keywords = '13800000000'      # 微信号、手机号、QQ号
            >>> addmsg = '你好，我是xxxx'      # 添加好友的消息
            >>> remark = '备注名字'            # 备注名
            >>> tags = ['朋友', '同事']        # 标签列表
            >>> wx.AddNewFriend(keywords, addmsg=addmsg, remark=remark, tags=tags)
        """
        self._show()
        self.SwitchToContact()
        self.SessionBox.ButtonControl(Name='添加朋友').Click(simulateMove=False)
        edit = self.SessionBox.EditControl(Name='微信号/手机号')
        edit.Click(simulateMove=False)
        edit.SendKeys(keywords)
        self.SessionBox.TextControl(Name=f'搜索：{keywords}').Click(simulateMove=False)

        ContactProfileWnd = uia.PaneControl(ClassName='ContactProfileWnd')
        if ContactProfileWnd.Exists(maxSearchSeconds=2):
            # 点击添加到通讯录
            ContactProfileWnd.ButtonControl(Name='添加到通讯录').Click(simulateMove=False)
        else:
            wxlog.debug('未找到联系人')
            return False

        NewFriendsWnd = self.UiaAPI.WindowControl(ClassName='WeUIDialog')
        if NewFriendsWnd.Exists(maxSearchSeconds=2):
            if addmsg:
                msgedit = NewFriendsWnd.TextControl(Name="发送添加朋友申请").GetParentControl().EditControl()
                msgedit.Click(simulateMove=False)
                msgedit.SendKeys('{Ctrl}a', waitTime=0)
                msgedit.SendKeys(addmsg)

            if remark:
                remarkedit = NewFriendsWnd.TextControl(Name='备注名').GetParentControl().EditControl()
                remarkedit.Click(simulateMove=False)
                remarkedit.SendKeys('{Ctrl}a', waitTime=0)
                remarkedit.SendKeys(remark)

            if tags:
                tagedit = NewFriendsWnd.TextControl(Name='标签').GetParentControl().EditControl()
                for tag in tags:
                    tagedit.Click(simulateMove=False)
                    tagedit.SendKeys(tag)
                    NewFriendsWnd.PaneControl(ClassName='DropdownWindow').TextControl().Click(simulateMove=False)

            NewFriendsWnd.ButtonControl(Name='确定').Click(simulateMove=False)
        return True
    
class WeChatFiles:
    def __init__(self, language='cn') -> None:
        self.language = language
        self.api = uia.WindowControl(ClassName='FileListMgrWnd', searchDepth=1)
        MainControl3 = [i for i in self.api.GetChildren() if not i.ClassName][0]
        self.FileBox ,self.Search ,self.SessionBox = MainControl3.GetChildren()

        self.allfiles = self.SessionBox.ButtonControl(Name=self._lang('全部'))
        self.recentfiles = self.SessionBox.ButtonControl(Name=self._lang('最近使用'))
        self.whofiles = self.SessionBox.ButtonControl(Name=self._lang('发送者'))
        self.chatfiles = self.SessionBox.ButtonControl(Name=self._lang('聊天'))
        self.typefiles = self.SessionBox.ButtonControl(Name=self._lang('类型'))

    def GetSessionName(self, SessionItem):
        """获取聊天对象的名字

        Args:
            SessionItem (uiautomation.ListItemControl): 聊天对象控件

        Returns:
            sessionname (str): 聊天对象名
        """
        return SessionItem.Name

    def GetSessionList(self, reset=False):
        """获取当前聊天列表中的所有聊天对象的名字

        Args:
            reset (bool): 是否重置SessionItemList

        Returns:
            session_names (list): 对象名称列表
        """
        self.SessionItem = self.SessionBox.ListControl(Name='',searchDepth=3).GetChildren()
        if reset:
            self.SessionItemList = []
        session_names = []
        for i in range(len(self.SessionItem)):
            session_names.append(self.GetSessionName(self.SessionItem[i]))

        return session_names

    def __repr__(self) -> str:
        return f"<wxauto WeChat Image at {hex(id(self))}>"

    def _lang(self, text):
        return FILE_LANGUAGE[text][self.language]

    def _show(self):
        HWND = FindWindow(classname='ImagePreviewWnd')
        win32gui.ShowWindow(HWND, 1)
        self.api.SwitchToThisWindow()

    def ChatWithFile(self, who):
        '''打开某个聊天会话

        Args:
            who ( str ): 要打开的聊天框好友名。

        Returns:
            chatname ( str ): 打开的聊天框的名字。
        '''
        self._show()
        self.chatfiles.Click(simulateMove=False)
        sessiondict = self.GetSessionList(True)

        if who in sessiondict:
            # 直接点击已存在的聊天框
            self.SessionBox.ListItemControl(Name=who).Click(simulateMove=False)
            return who
        else:
            # 如果聊天框不在列表中，则抛出异常
            raise TargetNotFoundError(f'未查询到目标：{who}')

    def DownloadFiles(self, who, amount, deadline=None, size=None):
        '''开始下载文件

        Args:
            who ( str )：聊天名称
            amount ( num )：下载的文件数量限制。
            deadline ( str )：截止日期限制。
            size ( str )：文件大小限制。

        Returns:
            result ( bool )：下载是否成功

        '''
        self._show()
        itemlist = self.GetSessionList()
        if who in itemlist:
            self.item = self.SessionBox.ListItemControl(Name=who)
            self.item.Click(simulateMove=False)
        else:
            wxlog.debug(f'未查询到目标：{who}')
        itemfileslist = []

        item = self.SessionBox.ListControl(Name='', searchDepth=7).GetParentControl()
        item = item.GetNextSiblingControl()
        item = item.ListControl(Name='', searchDepth=5).GetChildren()
        del item[0]

        for i in range(amount):
            try:

                itemfileslist.append(item[i].Name)
                self.itemfiles = item[i]
                self.itemfiles.Click(simulateMove=False)
                time.sleep(0.1)  # 大幅减少等待时间
            except:
                pass

    def Close(self):
        self._show()
        self.api.SendKeys('{Esc}')
