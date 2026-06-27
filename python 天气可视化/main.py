import tkinter as tk
from tkinter import messagebox
import requests
from pypinyin import lazy_pinyin, Style  # 新增拼音库导入
from bs4 import BeautifulSoup
import re
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# https://www.tianqi.com/tianqi/headweather/

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36' 
}

def save_place():
    if entry.get() == '':
        messagebox.showwarning('警告','请输入查询城市')
        checkbutton.deselect()
        return
    if messagebox.askokcancel('提示',f'确定保存{entry.get()}吗？'):
        with open('place.txt','w',encoding='utf-8') as f:
            f.write(entry.get())
    else:
        return

def check():
    with open('place.txt','r',encoding='utf-8') as f:
        place = f.read()
        if place == '':
            return
        else:
            entry.insert(0,place)
            return

def get_weather():
    global place
    if place == '':
        messagebox.showwarning('警告','请输入查询城市')
        checkbutton.deselect()
        return
    else:
        try:
            pinyin_list = lazy_pinyin(place, style=Style.NORMAL)
            pinyin = ''.join(pinyin_list)            
            data = requests.get(f'https://lishi.tianqi.com/{pinyin}/index.html', headers=headers)
            
            soup = BeautifulSoup(data.text, 'html.parser')
            items = soup.select('ul.tian_two li')  # 获取全部6个数据项
            
            if len(items) < 6:
                raise ValueError("天气数据不完整")

            # 解析所有数据项
            weather_data = {
                '平均高温': items[0].find_all('div', class_='tian_twoa')[0].text.strip('℃'),
                '平均低温': items[0].find_all('div', class_='tian_twoa')[1].text.strip('℃'),
                '极端高温': items[1].find('div', class_='tian_twoa').text.strip('℃'),
                '极端低温': items[2].find('div', class_='tian_twoa').text.strip('℃'),
                '平均空气质量': items[3].find('div', class_='tian_twoa').text,
                '空气最好': items[4].find('div', class_='tian_twoa').text,
                '空气最差': items[5].find('div', class_='tian_twoa').text
            }

            # 构建结果显示文本
            result_text = (
                f"平均温度: {weather_data['平均高温']}℃/{weather_data['平均低温']}℃\n"
                f"极端温度: {weather_data['极端高温']}℃（高）/{weather_data['极端低温']}℃（低）\n"
                f"空气质量: 平均 {weather_data['平均空气质量']}，最佳 {weather_data['空气最好']}，最差 {weather_data['空气最差']}"
            )
            
            messagebox.showinfo('查询结果', result_text)
            
        except Exception as e:
            messagebox.showerror('错误', f'数据解析失败: {str(e)}')
            print(f"详细错误: {e}")

def get_lishi_weater(year,month):
    pinyin_list = lazy_pinyin(place, style=Style.NORMAL)
    pinyin = ''.join(pinyin_list)   
    weather = requests.get(f'https://lishi.tianqi.com/{pinyin}/{year+month}.html', headers=headers)
    
    with open('weather.html','w',encoding='utf-8') as f:
        f.write(weather.text)
    soup = BeautifulSoup(weather.text, 'html.parser')
    script = soup.find('script', string=re.compile('var hightemp'))
    hightemp = re.search(r'var hightemp = (\[.*?\]);', script.text).group(1)
    hightemp = [float(x) if isinstance(x, str) else x for x in eval(hightemp)]
    
    # 在获取hightemp之后添加以下代码
    # 提取低温数据
    lowtemp = re.search(r'var lowtemp = (\[.*?\]);', script.text).group(1)
    lowtemp = [float(x) if isinstance(x, str) else x for x in eval(lowtemp)]
    
    # 提取时间轴数据
    timeaxis = re.search(r'var timeaxis = (\[.*?\]);', script.text).group(1)
    timeaxis = [int(x) for x in eval(timeaxis)]
    
    # 创建可视化图表
    plt.figure(figsize=(10, 6))
    # 替换原来的plt.show()代码
    # 创建图表窗口
    chart_window = tk.Toplevel()
    chart_window.title(f"{year}年{month}月温度趋势")

    ttk.Radiobutton(chart_window, text="关闭图表", command=chart_window.destroy).pack()
    
    # 创建Matplotlib图形
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    ax.plot(timeaxis, hightemp, marker='o', label='高温')
    ax.plot(timeaxis, lowtemp, marker='s', label='低温')
    
    # 修改数据点提示功能
    annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w", alpha=0.9),
                        arrowprops=dict(arrowstyle="->"),
                        visible=False)
    
    # 点击事件处理函数
    def on_click(event):
        if event.inaxes != ax:
            return
            
        for line in ax.lines:
            cont, ind = line.contains(event)
            if cont:
                x_val = line.get_xdata()[ind["ind"][0]]
                idx = timeaxis.index(x_val)
                high = hightemp[idx]
                low = lowtemp[idx]
                
                # 弹出消息框
                messagebox.showinfo(
                    "温度详情",
                    f"{year}年{month}月{x_val}日\n\n"
                    f"最高温度：{high}℃\n"
                    f"最低温度：{low}℃"
                )
                return
                
        annot.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('button_press_event', on_click)
    
    # 移除原有的hover事件绑定
    def update_annot(ind, line):
        x,y = line.get_data()
        annot.xy = (x[ind["ind"][0]], y[ind["ind"][0]])
        annot.set_text(f"{int(x[ind['ind'][0]])}\n{y[ind['ind'][0]]}")
    
    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            for line in [ax.lines[0], ax.lines[1]]:  # 遍历高温、低温两条曲线
                cont, ind = line.contains(event)
                if cont:
                    update_annot(ind, line)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
        if vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()
    
    fig.canvas.mpl_connect("motion_notify_event", hover)
    
    # 设置X轴刻度间隔
    ax.xaxis.set_major_locator(plt.MultipleLocator(1))  # 每天一个刻度
    plt.xticks(rotation=45)  # 旋转标签防止重叠
    
    ax.set_title(f'{year}年{month}月温度趋势')
    ax.set_xlabel('日期')
    ax.set_ylabel('温度(℃)')
    ax.legend()
    ax.grid(True)
    
    # 将图形嵌入到Tkinter界面
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    # 添加工具栏（可选）
    toolbar = NavigationToolbar2Tk(canvas, chart_window)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    # 关闭plt防止内存泄漏
    plt.close(fig)

def show_query_dialog(type_check):

    if type_check == "查询当天天气":
        get_weather()

    elif type_check == "查询以往天气":
        # 创建输入对话框
        date_dialog = tk.Toplevel()
        date_dialog.title("日期选择")
        date_dialog.protocol('WM_DELETE_WINDOW', date_dialog.quit)
        
        # 获取当前年月作为默认值
        from datetime import datetime
        current_year = datetime.now().strftime("%Y")
        current_month = datetime.now().strftime("%m")
        
        # 添加带默认值的输入框
        tk.Label(date_dialog, text="年份（YYYY）：").grid(row=0, column=0, padx=5, pady=5)
        year_entry = tk.Entry(date_dialog)
        year_entry.insert(0, current_year)  # 设置默认年份
        year_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(date_dialog, text="月份（MM）：").grid(row=1, column=0, padx=5, pady=5)
        month_entry = tk.Entry(date_dialog)
        month_entry.insert(0, current_month)  # 设置默认月份
        month_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 添加查询按钮
        def fetch_history():
            year = year_entry.get().zfill(4)
            month = month_entry.get().zfill(2)
            
            # 获取当前年月
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month

            # 加强输入验证
            if not (year.isdigit() and 1900 <= int(year) <= 2100):
                messagebox.showwarning("警告", "请输入有效的年份（1900-2100）")
                return
            if not (month.isdigit() and 1 <= int(month) <= 12):
                messagebox.showwarning("警告", "请输入有效的月份（1-12）")
                return
                
            # 新增时间范围校验
            input_year = int(year)
            input_month = int(month)
            if (input_year > current_year) or \
               (input_year == current_year and input_month > current_month):
                messagebox.showwarning("警告", 
                    f"日期不能超过当前年月（{current_year}-{current_month:02d}）")
                return

            date_dialog.destroy()
            get_lishi_weater(year, month)
            
        tk.Button(date_dialog, text="查询", command=fetch_history).grid(row=2, columnspan=2, pady=10)

    else:
        messagebox.showwarning('警告','错误')
        return

def next_check():
    global root_check,combo,place

    place = entry.get()
    root.destroy()
    root_check = tk.Tk()
    root_check.title("Sudoku Solver")
    root_check.protocol('WM_DELETE_WINDOW', root_check.quit)
    
    tk.Label(root_check, text="请输入查询方式").pack()
    combo = ttk.Combobox(root_check, values=["查询当天天气", "查询以往天气"])
    combo.current(0)
    combo.pack()

    # print(combo.get())

    # 在next_check函数中修改按钮绑定
    ttk.Button(root_check, text="完成", command=lambda: show_query_dialog(combo.get())).pack()



root = tk.Tk()
root.title("Sudoku Solver")
root.geometry("300x60")

tk.Label(root, text="请输入查询城市").place(x=10, y=0)
entry = tk.Entry(root)
entry.place(x=100, y=6)

button = tk.Button(root, text="完成",command=next_check)
button.place(x=250, y=0)

checkbutton = tk.Checkbutton(root, text="记住我",command=save_place)
checkbutton.place(x=230, y=30)

place = ''
check()

root.protocol('WM_DELETE_WINDOW', root.quit)

root.mainloop()