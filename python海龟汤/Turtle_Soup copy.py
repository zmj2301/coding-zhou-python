import tkinter as tk
import random
import os
import time
from tkinter.messagebox import askokcancel
import sys
import subprocess
from tkinter import simpledialog
import webbrowser
from tkinter import messagebox



from shuihu import water_margin_characters

# 尝试导入ollama，如果失败则使用模拟数据

from ollama import chat


class Choose_people():
    def __init__(self):
        self.title = "选择人物"
        self.geometry = "230x120+500+500"
        self.water_margin_characters = [
            # 三十六天罡星
            "宋江",
            "卢俊义",
            "吴用",
            "公孙胜",
            "关胜",
            "林冲",
            "秦明",
            "呼延灼",
            "花荣",
            "柴进",
            "李应",
            "朱仝",
            "鲁智深",
            "武松",
            "董平",
            "张清",
            "杨志",
            "徐宁",
            "索超",
            "戴宗",
            "刘唐",
            "李逵",
            "史进",
            "穆弘",
            "雷横",
            "李俊",
            "阮小二",
            "张横",
            "阮小五",
            "张顺",
            "阮小七",
            "杨雄",
            "石秀",
            "解珍",
            "解宝",

            # 七十二地煞星
            "燕青",
            "朱武",
            "黄信",
            "孙立",
            "宣赞",
            "郝思文",
            "韩滔",
            "彭玘",
            "单廷珪",
            "魏定国",
            "萧让",
            "裴宣",
            "欧鹏",
            "邓飞",
            "燕顺",
            "杨林",
            "凌振",
            "蒋敬",
            "吕方",
            "郭盛",
            "安道全",
            "皇甫端",
            "王英",
            "扈三娘",
            "鲍旭",
            "樊瑞",
            "孔明",
            "孔亮",
            "项充",
            "李衮",
            "金大坚",
            "马麟",
            "童威",
            "童猛",
            "孟康",
            "侯健",
            "陈达",
            "杨春",
            "郑天寿",
            "陶宗旺",
            "宋清",
            "乐和",
            "龚旺",
            "丁得孙",
            "穆春",
            "曹正",
            "宋万",
            "杜迁",
            "薛永",
            "施恩",
            "李忠",
            "周通",
            "汤隆",
            "杜兴",
            "邹渊",
            "邹润",
            "朱贵",
            "朱富",
            "蔡福",
            "蔡庆",
            "李云",
            "焦挺",
            "石勇",
            "孙新",
            "顾大嫂",
            "张青",
            "孙二娘",

            # 梁山相关重要人物
            "晁盖",
            "王伦",
            "柴皇城",

            # 朝廷官员
            "高俅",
            "蔡京",
            "童贯",
            "杨戬",
            "宿元景",
            "陈宗善",
            "高衙内",
            "梁中书",
            "蔡九知府",
            "慕容知府",
            "贺太守",

            # 重要配角
            "潘金莲",
            "西门庆",
            "武大郎",
            "阎婆惜",
            "潘巧云",
            "裴如海",
            "牛二",
            "镇关西",
            "金翠莲",
            "玉娇枝",
            "李瑞兰",
            "李巧奴",
            # 其他重要人物
            "方腊",
            "王庆",
            "田虎",
            "宋徽宗",
            "李师师",
            "赵鼎",
            "钱俶",
            "杜兴",
            "张顺",
        ]

    def main(self):
        # 将root_choose设置为实例变量，以便Game类可以访问
        self.root_choose = tk.Tk()
        self.root_choose.title(self.title)
        self.root_choose.geometry(self.geometry)
        labal_title = tk.Label(self.root_choose, text="按下开始按钮，停止切换人物并开始游戏。")
        labal_title.grid(row=0,column=0)
        
        # 一直切换直到按下开始按钮
        labal_people = tk.Label(self.root_choose, text=random.choice(self.water_margin_characters))
        labal_people.grid(row=1,column=0)
        
        # 切换控制标志
        self.is_switching = True
        
        # 定义切换函数
        self.after_id = None
        def switch_people():
            if self.is_switching:
                labal_people.config(text=random.choice(self.water_margin_characters))
                # 每100毫秒切换一次
                self.after_id = self.root_choose.after(100, switch_people)
        # 开始切换
        switch_people()
        
        # 开始按钮 - 停止切换
        def stop_switching():
            self.is_switching = False
            # 取消定时器，避免无效命令错误
            if self.after_id:
                self.root_choose.after_cancel(self.after_id)
            self.now_people = random.choice(self.water_margin_characters)
            self.root_choose.destroy()  # 在切换到游戏前销毁选择窗口
            print(self.now_people)
            game = Game()
            game.main()

        
        button_start = tk.Button(self.root_choose, text="开始", command=stop_switching)
        button_start.grid(row=2,column=0)

        self.root_choose.mainloop()

class Game(Choose_people):
    def __init__(self):
        super().__init__()
        self.now_people = choose_people.now_people
        self.ask_number = 0
        self.think_name = water_margin_characters
        self.heroes = [
            # 三十六天罡星
            {"星号": "天魁星", "绰号": "呼保义", "姓名": "宋江"},
            {"星号": "天罡星", "绰号": "玉麒麟", "姓名": "卢俊义"},
            {"星号": "天机星", "绰号": "智多星", "姓名": "吴用"},
            {"星号": "天闲星", "绰号": "入云龙", "姓名": "公孙胜"},
            {"星号": "天勇星", "绰号": "大刀", "姓名": "关胜"},
            {"星号": "天雄星", "绰号": "豹子头", "姓名": "林冲"},
            {"星号": "天猛星", "绰号": "霹雳火", "姓名": "秦明"},
            {"星号": "天威星", "绰号": "双鞭", "姓名": "呼延灼"},
            {"星号": "天英星", "绰号": "小李广", "姓名": "花荣"},
            {"星号": "天贵星", "绰号": "小旋风", "姓名": "柴进"},
            {"星号": "天富星", "绰号": "扑天雕", "姓名": "李应"},
            {"星号": "天满星", "绰号": "美髯公", "姓名": "朱仝"},
            {"星号": "天孤星", "绰号": "花和尚", "姓名": "鲁智深"},
            {"星号": "天伤星", "绰号": "行者", "姓名": "武松"},
            {"星号": "天立星", "绰号": "双枪将", "姓名": "董平"},
            {"星号": "天捷星", "绰号": "没羽箭", "姓名": "张清"},
            {"星号": "天暗星", "绰号": "青面兽", "姓名": "杨志"},
            {"星号": "天祐星", "绰号": "金枪手", "姓名": "徐宁"},
            {"星号": "天空星", "绰号": "急先锋", "姓名": "索超"},
            {"星号": "天速星", "绰号": "神行太保", "姓名": "戴宗"},
            {"星号": "天异星", "绰号": "赤发鬼", "姓名": "刘唐"},
            {"星号": "天杀星", "绰号": "黑旋风", "姓名": "李逵"},
            {"星号": "天微星", "绰号": "九纹龙", "姓名": "史进"},
            {"星号": "天究星", "绰号": "没遮拦", "姓名": "穆弘"},
            {"星号": "天退星", "绰号": "插翅虎", "姓名": "雷横"},
            {"星号": "天寿星", "绰号": "混江龙", "姓名": "李俊"},
            {"星号": "天剑星", "绰号": "立地太岁", "姓名": "阮小二"},
            {"星号": "天竟星", "绰号": "船火儿", "姓名": "张横"},
            {"星号": "天罪星", "绰号": "短命二郎", "姓名": "阮小五"},
            {"星号": "天损星", "绰号": "浪里白跳", "姓名": "张顺"},
            {"星号": "天败星", "绰号": "活阎罗", "姓名": "阮小七"},
            {"星号": "天牢星", "绰号": "病关索", "姓名": "杨雄"},
            {"星号": "天慧星", "绰号": "拚命三郎", "姓名": "石秀"},
            {"星号": "天暴星", "绰号": "两头蛇", "姓名": "解珍"},
            {"星号": "天哭星", "绰号": "双尾蝎", "姓名": "解宝"},
            {"星号": "天巧星", "绰号": "浪子", "姓名": "燕青"},
            # 七十二地煞星
            {"星号": "地魁星", "绰号": "神机军师", "姓名": "朱武"},
            {"星号": "地煞星", "绰号": "镇三山", "姓名": "黄信"},
            {"星号": "地勇星", "绰号": "病尉迟", "姓名": "孙立"},
            {"星号": "地杰星", "绰号": "丑郡马", "姓名": "宣赞"},
            {"星号": "地雄星", "绰号": "井木犴", "姓名": "郝思文"},
            {"星号": "地威星", "绰号": "百胜将", "姓名": "韩滔"},
            {"星号": "地英星", "绰号": "天目将", "姓名": "彭玘"},
            {"星号": "地奇星", "绰号": "圣水将", "姓名": "单廷圭"},
            {"星号": "地猛星", "绰号": "神火将", "姓名": "魏定国"},
            {"星号": "地文星", "绰号": "圣手书生", "姓名": "萧让"},
            {"星号": "地正星", "绰号": "铁面孔目", "姓名": "裴宣"},
            {"星号": "地阔星", "绰号": "摩云金翅", "姓名": "欧鹏"},
            {"星号": "地阖星", "绰号": "火眼狻猊", "姓名": "邓飞"},
            {"星号": "地强星", "绰号": "锦毛虎", "姓名": "燕顺"},
            {"星号": "地暗星", "绰号": "锦豹子", "姓名": "杨林"},
            {"星号": "地轴星", "绰号": "轰天雷", "姓名": "凌振"},
            {"星号": "地会星", "绰号": "神算子", "姓名": "蒋敬"},
            {"星号": "地佐星", "绰号": "小温侯", "姓名": "吕方"},
            {"星号": "地祐星", "绰号": "赛仁贵", "姓名": "郭盛"},
            {"星号": "地灵星", "绰号": "神医", "姓名": "安道全"},
            {"星号": "地兽星", "绰号": "紫髯伯", "姓名": "皇甫端"},
            {"星号": "地微星", "绰号": "矮脚虎", "姓名": "王英"},
            {"星号": "地慧星", "绰号": "一丈青", "姓名": "扈三娘"},
            {"星号": "地暴星", "绰号": "丧门神", "姓名": "鲍旭"},
            {"星号": "地然星", "绰号": "混世魔王", "姓名": "樊瑞"},
            {"星号": "地猖星", "绰号": "毛头星", "姓名": "孔明"},
            {"星号": "地狂星", "绰号": "独火星", "姓名": "孔亮"},
            {"星号": "地飞星", "绰号": "八臂那吒", "姓名": "项充"},
            {"星号": "地走星", "绰号": "飞天大圣", "姓名": "李衮"},
            {"星号": "地巧星", "绰号": "玉臂匠", "姓名": "金大坚"},
            {"星号": "地明星", "绰号": "铁笛仙", "姓名": "马麟"},
            {"星号": "地进星", "绰号": "出洞蛟", "姓名": "童威"},
            {"星号": "地退星", "绰号": "翻江蜃", "姓名": "童猛"},
            {"星号": "地满星", "绰号": "玉幡竿", "姓名": "孟康"},
            {"星号": "地遂星", "绰号": "通臂猿", "姓名": "侯健"},
            {"星号": "地周星", "绰号": "跳涧虎", "姓名": "陈达"},
            {"星号": "地隐星", "绰号": "白花蛇", "姓名": "杨春"},
            {"星号": "地异星", "绰号": "白面郎君", "姓名": "郑天寿"},
            {"星号": "地理星", "绰号": "九尾龟", "姓名": "陶宗旺"},
            {"星号": "地俊星", "绰号": "铁扇子", "姓名": "宋清"},
            {"星号": "地乐星", "绰号": "铁叫子", "姓名": "乐和"},
            {"星号": "地捷星", "绰号": "花项虎", "姓名": "龚旺"},
            {"星号": "地速星", "绰号": "中箭虎", "姓名": "丁得孙"},
            {"星号": "地镇星", "绰号": "小遮拦", "姓名": "穆春"},
            {"星号": "地嵇星", "绰号": "操刀鬼", "姓名": "曹正"},
            {"星号": "地魔星", "绰号": "云里金刚", "姓名": "宋万"},
            {"星号": "地妖星", "绰号": "摸着天", "姓名": "杜迁"},
            {"星号": "地幽星", "绰号": "病大虫", "姓名": "薛永"},
            {"星号": "地伏星", "绰号": "金眼彪", "姓名": "施恩"},
            {"星号": "地僻星", "绰号": "打虎将", "姓名": "李忠"},
            {"星号": "地空星", "绰号": "小霸王", "姓名": "周通"},
            {"星号": "地孤星", "绰号": "金钱豹子", "姓名": "汤隆"},
            {"星号": "地全星", "绰号": "鬼脸儿", "姓名": "杜兴"},
            {"星号": "地短星", "绰号": "出林龙", "姓名": "邹渊"},
            {"星号": "地角星", "绰号": "独角龙", "姓名": "邹润"},
            {"星号": "地囚星", "绰号": "旱地忽律", "姓名": "朱贵"},
            {"星号": "地藏星", "绰号": "笑面虎", "姓名": "朱富"},
            {"星号": "地平星", "绰号": "铁臂膊", "姓名": "蔡福"},
            {"星号": "地损星", "绰号": "一枝花", "姓名": "蔡庆"},
            {"星号": "地奴星", "绰号": "催命判官", "姓名": "李立"},
            {"星号": "地察星", "绰号": "青眼虎", "姓名": "李云"},
            {"星号": "地恶星", "绰号": "没面目", "姓名": "焦挺"},
            {"星号": "地丑星", "绰号": "石将军", "姓名": "石勇"},
            {"星号": "地数星", "绰号": "小尉迟", "姓名": "孙新"},
            {"星号": "地阴星", "绰号": "母大虫", "姓名": "顾大嫂"},
            {"星号": "地刑星", "绰号": "菜园子", "姓名": "张青"},
            {"星号": "地壮星", "绰号": "母夜叉", "姓名": "孙二娘"},
            {"星号": "地劣星", "绰号": "活闪婆", "姓名": "王定六"},
            {"星号": "地健星", "绰号": "险道神", "姓名": "郁保四"},
            {"星号": "地耗星", "绰号": "白日鼠", "姓名": "白胜"},
            {"星号": "地贼星", "绰号": "鼓上蚤", "姓名": "时迁"},
            {"星号": "地狗星", "绰号": "金毛犬", "姓名": "段景住"}
        ]

    def get_answer(self,quesion,player,model):

            # 调用AI模型获取回答
        try:

            from openai import OpenAI

            # 直接用 OpenAI 格式调用智谱 AI
            client = OpenAI(
                api_key=os.environ.get('ZHIPUAI_API_KEY', ''),  # 去 https://open.bigmodel.cn 申请
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            )

            response = client.chat.completions.create(
                model="GLM-4-Flash",  # 免费模型，速度快
                messages=[{"role": "user", "content": quesion}]
            ) 

            reply = response.choices[0].message.content


            return reply

        except ConnectionError:
            # 处理Ollama连接错误
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, "连接Ollama失败！请检查：\n1. Ollama是否已下载安装\n2. Ollama服务是否正在运行\n3. 网络连接是否正常\n")
            self.text_box.config(state=tk.DISABLED)
            os.system("start cmd")
            return "连接Ollama失败！请检查：\n1. Ollama是否已下载安装\n2. Ollama服务是否正在运行\n3. 网络连接是否正常"

        except Exception as e:
            # 处理其他错误
            return f"获取回答时发生错误：{str(e)}"

    def repeat_answer(self,quesion,player,model):
        # 禁用发送按钮，防止重复提交
        if hasattr(self, 'send_button'):
            self.send_button.config(state=tk.DISABLED)
            print("✅ 已禁用发送按钮")
        
        self.ask_number += 1
        if self.ask_number > 20:
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, f"游戏结束，你一共问了20个问题，正确答案是{self.now_people}。\n")
            self.text_box.config(state=tk.DISABLED)
            print(f"游戏结束，你一共问了{self.ask_number}个问题，正确答案是{self.now_people}。")
            # 启用发送按钮
            if hasattr(self, 'send_button'):
                self.send_button.config(state=tk.NORMAL)
                print("✅ 已启用发送按钮")
            return

        # 获取人物名称（去掉括号内容）
        if self.now_people in quesion:
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, f"游戏结束，你一共问了{self.ask_number}个问题，恭喜你回答正确，答案就是{self.now_people}。\n")
            self.text_box.config(state=tk.DISABLED)
            print(f"游戏结束，你一共问了{self.ask_number}个问题，恭喜你回答正确，答案就是{self.now_people}。")
            # 启用发送按钮
            if hasattr(self, 'send_button'):
                self.send_button.config(state=tk.NORMAL)
                print("✅ 已启用发送按钮")
            return

        # 显示加载状态
        self.text_box.config(state=tk.NORMAL)
        self.text_box.insert(tk.END, f"{player}: {quesion}\n")
        self.text_box.insert(tk.END, "AI: 思考中...\n")
        self.text_box.config(state=tk.DISABLED)
        self.text_box.see(tk.END)  # 自动滚动到最后

        # 同步处理AI回答
        import time
        start_time = time.time()
        
        # 减少获取次数，从4次减少到2次，提高速度
        ai_answers = []
        for i in range(2):  # 减少到2次
            try:
                answer = self.get_answer(self.now_people + quesion+"注意：只能回答是或否，其他啥也不要说", player, model)
                ai_answers.append(answer)
            except Exception as e:
                print(f"获取回答出错: {str(e)}")
                ai_answers.append("不知道")
        
        # 处理无效回答
        invalid_count = 0
        valid_answers = []
        for answer in ai_answers:
            if answer and "获取回答时发生错误" not in answer:
                valid_answers.append(answer)
            else:
                invalid_count += 1
        
        # 选择最佳回答
        if invalid_count >= len(ai_answers):
            answer = "不知道"
        else:
            answer = max(valid_answers, key=valid_answers.count)
        
        elapsed = time.time() - start_time
        print(f"✅ 获取AI回答完成，耗时: {elapsed:.3f}秒")
        
        # 更新UI
        self.text_box.config(state=tk.NORMAL)
        self.text_box.insert(tk.END, f"{player}: {quesion}\n")
        
        if self.now_people in answer:
            self.text_box.insert(tk.END, f"此问题违规，无法回答！！！\n")
            self.ask_number -= 1
        else:
            self.text_box.insert(tk.END, f"AI: {answer} ({self.ask_number}/20)\n")
        
        self.text_box.config(state=tk.DISABLED)
        self.text_box.see(tk.END)  # 自动滚动到最后
        self.entry.delete(0, tk.END)
        
        # 启用发送按钮
        if hasattr(self, 'send_button'):
            self.send_button.config(state=tk.NORMAL)
            print("✅ 已启用发送按钮")

    def print_answer(self):
        from tkinter import messagebox
        if askokcancel("确认", f"不在想想吗？"):
            self.text_box.config(state=tk.NORMAL)
            self.text_box.insert(tk.END, f"AI: 答案是{self.now_people}\n")
            self.text_box.config(state=tk.DISABLED)

    def find_people(self):
        self.toolbox_window.destroy()
        # 打开一个只能询问的窗口，搜索人名称
        find_name = simpledialog.askstring("搜索人物", "请输入要搜索的人物名称：")
        if find_name and find_name in self.water_margin_characters:
            if askokcancel("确认", f"确认搜索人物{find_name}吗？"):
                webbrowser.open(f"https://baike.baidu.com/item/{find_name}")
        else:
            messagebox.showinfo("提示", f"未搜索到人物{find_name}")

    def say_text(self,text):
        """
        将文本转换为语音并异步播放，不阻塞主线程
        使用多线程实现，确保语音播放不会影响GUI响应
        """
        import threading
        import pyttsx3
        
        def _speak():
            """内部函数，实际执行语音播放"""
            try:
                # 创建语音引擎实例
                engine = pyttsx3.init()
                # 设置语速（默认1.0，范围0.5-2.0）
                engine.setProperty('rate', 150)
                # 设置音量（默认1.0，范围0.0-1.0）
                engine.setProperty('volume', 0.8)
                # 合成语音
                engine.say(text)
                # 等待语音播放完成
                engine.runAndWait()
                print(f"已完成语音播放：{text}")
            except Exception as e:
                print(f"语音播放出错：{str(e)}")
        
        # 创建并启动线程，daemon=True表示线程会在主线程结束时自动退出
        speak_thread = threading.Thread(target=_speak, daemon=True)
        speak_thread.start()
        print(f"已启动语音播放线程：{text}")
        
    def think_no(self,think_name_index):
        if 'X' in self.think_name[think_name_index]:
            self.think_name[think_name_index] = self.think_name[think_name_index].replace('X','')
        else:
            self.think_name[think_name_index] += "X"
        # 播放语音
        # print(self.think_name[think_name_index])
        # 获取人物名称（去除可能的'X'标记）
        if 'X' in self.think_name[think_name_index]:
            say_heroes_name = self.think_name[think_name_index].replace('X','')
        else:
            say_heroes_name = self.think_name[think_name_index]
        
        # 在heroes列表中查找匹配的人物
        hero_info = None
        for hero in self.heroes:
            if hero['姓名'] == say_heroes_name:
                hero_info = hero
                break
        
        if hero_info:
            # 获取人物信息的各个字段
            star = hero_info['星号']
            nickname = hero_info['绰号']
            name = hero_info['姓名']
            # print(f"一百零八星宿，之，{star}，{nickname}，{name}")
            self.say_text(f"一百零八星宿，之，{star}，{nickname}，{name}")
        else:
            print(f"未找到人物：{say_heroes_name}的信息")
        
        # 更新按钮文本
        if hasattr(self, 'filter_buttons') and self.filter_buttons:
            self.filter_buttons[think_name_index].config(text=self.think_name[think_name_index])

    def filter_people(self,root_game):
        self.toolbox_window.destroy()
        filter_root = tk.Toplevel(root_game)
        filter_root.title("筛选器")
        filter_root.geometry("900x800")
        # 设置大小不可改变
        filter_root.resizable(False, False)
        self.label = tk.Label(filter_root, text="筛选器",font=self.FONT)
        self.label.grid(row=0,column=1)
        
        # 保存按钮引用的列表
        self.filter_buttons = []
        for i in range(len(self.think_name)):
            btn = tk.Button(filter_root, text=self.think_name[i],font=self.FONT,command=lambda x=i:self.think_no(x))
            btn.grid(row=i//9,column=i%9)
            self.filter_buttons.append(btn)
        filter_root.mainloop()

    def open_cmd(self):
        cmd2 = f'start cmd /k "ollama run minimax-m2.1:cloud"'
        # 执行命令（无需额外flags，start已强制新建窗口）
        subprocess.Popen(
            cmd2,
            shell=True,
            cwd=os.path.expanduser("~")  # 切换到用户主目录，避免路径问题
        )

        print(f"✅ 已弹出CMD窗口，执行命令：ollama run minimax-m2.1:cloud")

    def toolbox(self,root_game):
        self.toolbox_window = tk.Toplevel(root_game)
        self.toolbox_window.title("工具箱")
        self.toolbox_window.geometry("300x200")
        self.label = tk.Label(self.toolbox_window, text="工具箱",font=self.FONT)
        self.label.grid(row=0,column=1)
        self.find_people_button = tk.Button(self.toolbox_window, text="搜索人物", command=self.find_people)
        self.find_people_button.grid(row=1,column=0)
        self.filter_button = tk.Button(self.toolbox_window, text="筛选器(提供108个名字，便于筛选)", command=lambda: self.filter_people(root_game))
        self.filter_button.grid(row=1,column=1)
        self.open_button = tk.Button(self.toolbox_window, text="打开cmd版AI", command=self.open_cmd)
        self.open_button.grid(row=2,column=0)

    def main(self):    
        import requests
        import json
        import tkinter as tk
        import os
        self.FONT = ("Arial", 16)

        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)
        # 获取当前文件所在目录
        current_dir = os.path.dirname(current_file)

        # 创建主窗口
        root_game = tk.Tk()
        root_game.title("DeepSeek 聊天界面")
        root_game.resizable(False, False)

        label = tk.Label(root_game, text="deepseek 聊天界面",font=self.FONT)
        label.pack()


        # 创建滚动条
        scrollbar = tk.Scrollbar(root_game)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建多行文本框
        self.text_box = tk.Text(
            root_game,
            font=self.FONT,
            height=30,
            width=50,
            yscrollcommand=scrollbar.set
        )
        self.text_box.pack(padx=10, pady=10)
        self.text_box.config(state=tk.DISABLED)  # 初始状态设为禁用，防止用户编辑


        self.entry = tk.Entry(root_game, width=38)
        self.entry.pack(side='left')
        self.entry.insert(tk.END,"他是一百零八星宿之一吗？")

        button = tk.Button(root_game, text="发送", command=lambda: self.repeat_answer(f"{self.entry.get()}","system",1))
        button.pack(side='right')


        self.button_get = tk.Button(root_game, text="获取回答", command=self.print_answer)
        self.button_get.pack(side='right')


        
        self.find_people_button = tk.Button(root_game, text="工具箱", command=lambda: self.toolbox(root_game))
        self.find_people_button.pack(side='right',pady=20)
        
        self.text_box.config(state=tk.NORMAL)
        self.text_box.insert(tk.END, f"AI: 我已经想好了一个关于水浒传中的人物，下面赶快开始想我提问吧？\n")
        self.text_box.config(state=tk.DISABLED)



        # 配置滚动条
        scrollbar.config(command=self.text_box.yview)

        # get_answer("请你作为海龟汤游戏的出题者，提出一个简短、离奇的情境谜面（汤面），只需要输出谜面内容，不要包含任何其他解释或标记。","出题者",deepseek_key)

        # 运行主循环
        root_game.mainloop()


def 检查是否打开ollama服务():
    """
    检查ollama服务是否已启动（快速版本）
    """
    import time
    start_time = time.time()
    try:
        # 尝试执行ollama list，检查是否有响应
        subprocess.check_output(
            "ollama list",
            shell=True,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=0.5  # 减少超时时间到0.5秒
        )
        elapsed = time.time() - start_time
        print(f"✅ Ollama服务检查成功，耗时: {elapsed:.3f}秒")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"⚠️ 检查ollama服务失败：{str(e)}，耗时: {elapsed:.3f}秒")
        return False

def open_cmd_and_run_ollama():
    """
    强制弹出CMD窗口并执行ollama run（Windows专用，确保窗口可见）
    """
    # 第一步：检查是否为Windows系统
    if sys.platform != "win32":
        print("❌ 此方案仅支持Windows系统！")
        return
    
    # 第二步：先验证ollama是否安装并配置环境变量
    try:
        # 静默执行ollama --version，验证命令是否可用
        subprocess.check_output(
            "ollama --version",
            shell=True,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        print("❌ 未找到ollama命令！请先：")
        print("  1. 安装ollama（官网：https://ollama.com/）")
        print("  2. 配置ollama到系统环境变量（或重启电脑让环境变量生效）")
        return
    
    # 第三步：构造强制弹出CMD的命令（修复核心）
    # start cmd 是Windows强制新建窗口的命令，优先级最高
    cmd = f'start cmd /k "ollama serve"'
    cmd2 = f'start cmd /k "ollama run minimax-m2.1:cloud"'
    
    try:
        # 执行命令（无需额外flags，start已强制新建窗口）
        subprocess.Popen(
            cmd,
            shell=True,
            cwd=os.path.expanduser("~")  # 切换到用户主目录，避免路径问题
        )

        print(f"✅ 已弹出CMD窗口，执行命令：ollama run minimax-m2.1:cloud")
    except Exception as e:
        print(f"⚠️ 执行失败：{str(e)}")

if __name__ == "__main__":


    
    choose_people = Choose_people()
    choose_people.main()
