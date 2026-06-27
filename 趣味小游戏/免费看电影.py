
import requests
import webbrowser

class FreeMovie:
    def __init__(self):
        self.jiexi_url = "https://jx.xmflv.cc/?url="
        self.aiqiyi_url = "https://www.iqiyi.com/"
        self.tenxun_url = "https://v.qq.com/"
        self.mangguo_url = "https://www.mgtv.com/"

    def open_URL(self,url):
        webbrowser.open(url)
    def query_movie(self,url):
        if url == "":
            return
        self.open_URL(self.jiexi_url + url)
        # 退出程序
        exit()
    def clear_entry(self,entry,tk):
        entry.delete(0,tk.END)
    def tkinter_room(self):
        import tkinter as tk
        root = tk.Tk()
        root.title("免费看电影")
        root.geometry("300x100")
        label = tk.Label(root, text="请输入电影网址",width=8,height=2)
        label.grid(row=0,column=0)
        entry_ = tk.Entry(root)
        entry_.grid(row=0,column=1)
        delet_button = tk.Button(root, text="清空", command=lambda: self.clear_entry(entry_,tk))
        delet_button.grid(row=0,column=2)
        aiqiyi_button = tk.Button(root, text="爱奇艺官网", command=lambda: self.open_URL(self.aiqiyi_url))
        aiqiyi_button.grid(row=1,column=0)
        tenxun_button = tk.Button(root, text="腾讯视频官网", command=lambda: self.open_URL(self.tenxun_url))
        tenxun_button.grid(row=1,column=1)
        mangguo_button = tk.Button(root, text="芒果视频官网", command=lambda: self.open_URL(self.mangguo_url))
        mangguo_button.grid(row=1,column=2)
        button = tk.Button(root, text="查询",command=lambda: self.query_movie(entry_.get()))
        button.grid(row=3,column=1)
        root.mainloop()

if __name__ == "__main__":
    free_movie = FreeMovie()
    free_movie.tkinter_room()
