import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import io
import os
from rembg import remove, new_session
import threading
import numpy as np
from numba import jit  # 用于加速计算

# region
class AdvancedBackgroundRemovalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("高级抠图工具 - 右键菜单版")
        self.root.geometry("1500x800")
        self.root.resizable(True, True)
        
        # 支持的模型列表及其说明
        self.models = {
            "u2net": "通用模型，适合大多数场景（默认）",
            "u2netp": "轻量版U2NET，速度更快但精度稍低",
            "u2net_human_seg": "专门用于人体分割，对人物抠图效果好",
            "u2net_cloth_seg": "专门用于衣物分割，适合服装类图片",
            "silueta": "快速分割模型，适合简单背景"
        }
        
        # 支持的抠图对象类型
        self.object_types = {
            "auto": "自动检测（默认）",
            "person": "人物（自动选择人体模型）",
            "animal": "动物（使用通用模型优化）",
            "plant": "植物（使用通用模型优化）",
            "product": "产品/物品（使用通用模型优化）",
            "clothing": "服装（自动选择衣物模型）"
        }
        
        # 当前选中的模型和对象类型
        self.current_model = "u2net"
        self.current_object = "auto"
        self.model_session = new_session(self.current_model)
        
        # 手动抠图工具变量
        self.brush_size = 10
        self.brush_color = (255, 0, 0)  # 红色画笔
        self.eraser_size = 10
        self.drawing = False
        self.mask = None  # 手动绘制的掩码
        self.temp_mask = None  # 临时掩码用于显示
        self.tool_mode = "brush"  # brush, eraser, rectangle
        self.draw = None  # 初始化draw为None
        
        # 颜色扣除相关变量 - 提前初始化，解决AttributeError
        self.color_remove_var = tk.BooleanVar(value=False)
        self.color_to_remove = (255, 255, 255)  # 默认扣除白色
        self.color_tolerance = 30  # 颜色容差
        self.use_color_removal = False  # 是否启用颜色扣除模式
        
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TButton", font=("SimHei", 10))
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TListbox", font=("SimHei", 10))
        self.style.configure("TCombobox", font=("SimHei", 10))
        
        # 初始化变量
        self.input_image_paths = []
        self.output_images = {}
        self.current_image_path = None
        self.original_image = None
        self.processed_image = None
        self.display_image = None  # 用于显示的带掩码的图像
        self.processing = False
        self.zoom_factor = 1.0  # 缩放因子，用于优化显示速度
        
        # 选择区域变量
        self.selection_start = None
        self.selection_rect = None
        self.selected_region = None  # 存储最终选择的区域 (x1, y1, x2, y2)
        
        # 创建保存文件夹
        self.save_dir = "save"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        # 创建右键菜单（现在color_remove_var已经初始化）
        self._create_right_click_menu()
        
        # 创建UI
        self._create_widgets()
        
    def _create_right_click_menu(self):
        """创建右键菜单"""
        self.right_click_menu = tk.Menu(self.root, tearoff=0)
        
        # 工具子菜单
        self.tool_submenu = tk.Menu(self.right_click_menu, tearoff=0)
        self.tool_submenu.add_command(label="画笔工具", command=lambda: self.set_tool_mode("brush"))
        self.tool_submenu.add_command(label="橡皮擦", command=lambda: self.set_tool_mode("eraser"))
        self.tool_submenu.add_command(label="矩形选择", command=lambda: self.set_tool_mode("rectangle"))
        self.right_click_menu.add_cascade(label="工具", menu=self.tool_submenu)
        
        # 颜色扣除子菜单
        self.color_submenu = tk.Menu(self.right_click_menu, tearoff=0)
        self.color_submenu.add_checkbutton(
            label="启用颜色扣除", 
            variable=self.color_remove_var,
            command=self.toggle_color_removal
        )
        self.color_submenu.add_command(label="选择扣除颜色", command=self.choose_color)
        self.right_click_menu.add_cascade(label="颜色扣除", menu=self.color_submenu)
        
        # 主要操作
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="自动抠图", command=self.process_full_image)
        self.right_click_menu.add_command(label="应用手动抠图", command=self.process_manual_mask)
        self.right_click_menu.add_command(label="应用颜色扣除", command=self.process_color_removal)
        self.right_click_menu.add_command(label="智能优化边缘", command=self.optimize_mask)
        
        # 其他操作
        self.right_click_menu.add_separator()
        self.right_click_menu.add_command(label="清除掩码", command=self.clear_mask)
        self.right_click_menu.add_command(label="保存当前结果", command=self.save_current_image)
        
    def _create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮框架
        top_button_frame = ttk.Frame(main_frame, padding="5")
        top_button_frame.pack(fill=tk.X, pady=5)
        
        # 选择图片按钮
        self.select_btn = ttk.Button(
            top_button_frame, 
            text="选择多张图片", 
            command=self.select_images
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # 对象类型选择框架
        object_frame = ttk.LabelFrame(top_button_frame, text="抠图对象", padding="5")
        object_frame.pack(side=tk.LEFT, padx=5)
        
        # 对象类型选择下拉框
        self.object_var = tk.StringVar(value=self.current_object)
        self.object_combobox = ttk.Combobox(
            object_frame,
            textvariable=self.object_var,
            values=list(self.object_types.keys()),
            state="readonly",
            width=12
        )
        self.object_combobox.pack(side=tk.LEFT, padx=5)
        self.object_combobox.bind("<<ComboboxSelected>>", self.on_object_change)
        
        # 对象类型说明标签
        self.object_desc_var = tk.StringVar(value=self.object_types[self.current_object])
        self.object_desc_label = ttk.Label(
            object_frame, 
            textvariable=self.object_desc_var,
            wraplength=200
        )
        self.object_desc_label.pack(side=tk.LEFT, padx=5)
        
        # 模型选择框架
        model_frame = ttk.LabelFrame(top_button_frame, text="抠图模型", padding="5")
        model_frame.pack(side=tk.LEFT, padx=5)
        
        # 模型选择下拉框
        self.model_var = tk.StringVar(value=self.current_model)
        self.model_combobox = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=list(self.models.keys()),
            state="readonly",
            width=15
        )
        self.model_combobox.pack(side=tk.LEFT, padx=5)
        self.model_combobox.bind("<<ComboboxSelected>>", self.on_model_change)
        
        # 模型说明标签
        self.model_desc_var = tk.StringVar(value=self.models[self.current_model])
        self.model_desc_label = ttk.Label(
            model_frame, 
            textvariable=self.model_desc_var,
            wraplength=250
        )
        self.model_desc_label.pack(side=tk.LEFT, padx=5)
        
        # 批量处理按钮
        self.batch_process_btn = ttk.Button(
            top_button_frame, 
            text="批量全图抠图", 
            command=self.batch_process_images,
            state=tk.DISABLED
        )
        self.batch_process_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存当前按钮
        self.save_current_btn = ttk.Button(
            top_button_frame, 
            text="保存当前结果", 
            command=self.save_current_image,
            state=tk.DISABLED
        )
        self.save_current_btn.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            top_button_frame,
            variable=self.progress_var,
            maximum=100,
            length=150
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        
        # 中间内容框架
        content_frame = ttk.Frame(main_frame, padding="5")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧图片列表框架
        list_frame = ttk.LabelFrame(content_frame, text="图片列表", padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 图片列表
        self.image_listbox = tk.Listbox(
            list_frame, 
            width=30, 
            height=30,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        scrollbar.config(command=self.image_listbox.yview)
        
        # 右侧工作区框架
        work_frame = ttk.Frame(content_frame, padding="5")
        work_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具按钮框架
        tool_frame = ttk.LabelFrame(work_frame, text="工具设置", padding="5")
        tool_frame.pack(fill=tk.X, pady=5)
        
        # 画笔大小调节
        ttk.Label(tool_frame, text="画笔大小:").pack(side=tk.LEFT, padx=5)
        self.brush_size_var = tk.IntVar(value=self.brush_size)
        self.brush_size_scale = ttk.Scale(
            tool_frame,
            from_=1,
            to=50,
            variable=self.brush_size_var,
            command=self.update_brush_size,
            length=100,
            state=tk.DISABLED
        )
        self.brush_size_scale.pack(side=tk.LEFT, padx=5)
        self.brush_size_label = ttk.Label(tool_frame, text=str(self.brush_size))
        self.brush_size_label.pack(side=tk.LEFT, padx=5)
        
        # 颜色容差调节
        ttk.Label(tool_frame, text="颜色容差:").pack(side=tk.LEFT, padx=5)
        self.color_tolerance_var = tk.IntVar(value=self.color_tolerance)
        self.color_tolerance_scale = ttk.Scale(
            tool_frame,
            from_=0,
            to=100,
            variable=self.color_tolerance_var,
            command=self.update_color_tolerance,
            length=100,
            state=tk.DISABLED
        )
        self.color_tolerance_scale.pack(side=tk.LEFT, padx=5)
        self.color_tolerance_label = ttk.Label(tool_frame, text=str(self.color_tolerance))
        self.color_tolerance_label.pack(side=tk.LEFT, padx=5)
        
        # 当前工具提示
        self.tool_info_var = tk.StringVar(value="右键图片打开操作菜单")
        self.tool_info_label = ttk.Label(tool_frame, textvariable=self.tool_info_var, foreground="green")
        self.tool_info_label.pack(side=tk.RIGHT, padx=20)
        
        # 图片预览框架
        preview_frame = ttk.Frame(work_frame, padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # 原始图片标签
        self.original_label = ttk.Label(preview_frame, text="原始图片 (右键打开菜单，选择工具勾勒需要保留的区域)")
        self.original_label.pack(side=tk.TOP)
        
        # 原始图片显示区域（带绘制功能）
        self.original_canvas = tk.Canvas(preview_frame, bg="lightgray", width=600, height=350)
        self.original_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # 绑定鼠标事件用于绘制和右键菜单
        self.original_canvas.bind("<ButtonPress-1>", self.on_drawing_start)
        self.original_canvas.bind("<B1-Motion>", self.on_drawing_drag)
        self.original_canvas.bind("<ButtonRelease-1>", self.on_drawing_end)
        self.original_canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # 鼠标滚轮缩放
        self.original_canvas.bind("<Button-3>", self.show_right_click_menu)  # 右键菜单
        
        # 处理后图片标签
        self.processed_label = ttk.Label(preview_frame, text="处理后图片 (右键打开菜单)")
        self.processed_label.pack(side=tk.TOP)
        
        # 处理后图片显示区域
        self.processed_canvas = tk.Canvas(preview_frame, bg="lightgray", width=600, height=350)
        self.processed_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.processed_canvas.bind("<Button-3>", self.show_right_click_menu)  # 右键菜单
        
        # 状态标签
        self.status_var = tk.StringVar()
        self.status_var.set("就绪：请先选择图片，右键图片打开操作菜单")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side=tk.BOTTOM, pady=5)
        
        # 初始化工具模式
        self.set_tool_mode("brush")
    
    def show_right_click_menu(self, event):
        """显示右键菜单"""
        try:
            # 根据当前状态启用/禁用菜单项
            has_image = self.current_image_path is not None
            has_processed = self.current_image_path in self.output_images
            has_mask = self.mask is not None and np.any(np.array(self.mask))
            
            # 更新菜单项状态
            self.right_click_menu.entryconfig("自动抠图", state=tk.NORMAL if has_image else tk.DISABLED)
            self.right_click_menu.entryconfig("应用手动抠图", state=tk.NORMAL if has_image and has_mask else tk.DISABLED)
            self.right_click_menu.entryconfig("应用颜色扣除", state=tk.NORMAL if has_image and self.use_color_removal else tk.DISABLED)
            self.right_click_menu.entryconfig("智能优化边缘", state=tk.NORMAL if has_processed or has_mask else tk.DISABLED)
            self.right_click_menu.entryconfig("清除掩码", state=tk.NORMAL if has_mask else tk.DISABLED)
            self.right_click_menu.entryconfig("保存当前结果", state=tk.NORMAL if has_processed else tk.DISABLED)
            
            # 颜色扣除子菜单状态
            self.color_submenu.entryconfig("选择扣除颜色", state=tk.NORMAL if has_image else tk.DISABLED)
            
            # 在鼠标位置显示菜单
            self.right_click_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.status_var.set(f"右键菜单错误: {str(e)}")
    
    # 颜色扣除相关方法
    def toggle_color_removal(self):
        """切换颜色扣除模式的启用状态"""
        self.use_color_removal = self.color_remove_var.get()
        state = tk.NORMAL if self.use_color_removal else tk.DISABLED
        
        self.color_tolerance_scale.config(state=state)
        
        if self.use_color_removal:
            self.status_var.set(f"已启用颜色扣除模式，当前扣除颜色: RGB{self.color_to_remove}，容差: {self.color_tolerance}")
        else:
            self.status_var.set("已禁用颜色扣除模式")
    
    def choose_color(self):
        """选择要扣除的颜色"""
        if not self.original_image:
            messagebox.showwarning("提示", "请先选择图片")
            return
            
        # 打开颜色选择器
        color = colorchooser.askcolor(title="选择要扣除的颜色")[0]
        if color:
            self.color_to_remove = (int(color[0]), int(color[1]), int(color[2]))
            self.status_var.set(f"已选择扣除颜色: RGB{self.color_to_remove}，容差: {self.color_tolerance}")
    
    def update_color_tolerance(self, value):
        """更新颜色容差"""
        self.color_tolerance = int(float(value))
        self.color_tolerance_label.config(text=str(self.color_tolerance))
        self.status_var.set(f"当前扣除颜色: RGB{self.color_to_remove}，容差: {self.color_tolerance}")
    
    # 速度优化：使用numba加速颜色扣除计算
    @staticmethod
    @jit(nopython=True)  # 编译为机器码加速
    def _color_removal_kernel(data, r, g, b, tolerance):
        """颜色扣除的核心计算函数"""
        height, width, _ = data.shape
        for i in range(height):
            for j in range(width):
                r_diff = abs(data[i, j, 0] - r)
                g_diff = abs(data[i, j, 1] - g)
                b_diff = abs(data[i, j, 2] - b)
                
                if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                    data[i, j, 3] = 0  # 设置为透明
        return data
    
    def process_color_removal(self):
        """应用颜色扣除"""
        if not self.current_image_path or not self.original_image:
            messagebox.showerror("错误", "请先选择图片")
            return
            
        if self.processing:
            messagebox.showinfo("提示", "正在处理中，请稍候...")
            return
            
        self.processing = True
        self.status_var.set(f"正在扣除颜色 {self.color_to_remove} ...")
        self._disable_all_tools()
        
        # 在新线程中处理
        threading.Thread(target=self._apply_color_removal, daemon=True).start()
    
    def _apply_color_removal(self):
        """执行颜色扣除算法"""
        try:
            # 对大图片进行缩放处理以提高速度
            img = self.original_image.copy()
            max_size = 1024  # 限制最大尺寸，平衡速度和质量
            if max(img.size) > max_size:
                scale = max_size / max(img.size)
                new_size = tuple(int(dim * scale) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 转换为RGBA模式并获取数组数据
            img = img.convert("RGBA")
            data = np.array(img, dtype=np.uint8)
            
            # 获取要扣除的颜色通道值
            r, g, b = self.color_to_remove
            
            # 应用颜色扣除（使用加速的内核函数）
            data = self._color_removal_kernel(data, r, g, b, self.color_tolerance)
            
            # 如果进行了缩放，恢复原始尺寸
            if img.size != self.original_image.size:
                result_img = Image.fromarray(data).resize(
                    self.original_image.size, 
                    Image.Resampling.LANCZOS
                )
            else:
                result_img = Image.fromarray(data)
            
            # 保存处理结果
            self.output_images[self.current_image_path] = result_img
            
            # 更新预览
            self.processed_image = result_img
            self.root.after(0, lambda: self._display_image(result_img, self.processed_canvas))
            self.root.after(0, lambda: self.save_current_btn.config(state=tk.NORMAL))
            
            # 显示完成提示
            filename = os.path.basename(self.current_image_path)
            complete_msg = f"颜色扣除已完成!\n图片: {filename}\n扣除颜色: RGB{self.color_to_remove}"
            self.root.after(0, lambda: self.status_var.set(f"颜色扣除完成: {filename}"))
            self.root.after(100, lambda: messagebox.showinfo("处理完成", complete_msg))
            
        except Exception as e:
            error_msg = f"颜色扣除出错: {str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            self.processing = False
            self.root.after(0, lambda: self._enable_drawing_tools())
    
    # 工具模式设置
    def set_tool_mode(self, mode):
        """设置当前工具模式"""
        self.tool_mode = mode
        
        # 更新工具信息
        if mode == "brush":
            self.tool_info_var.set(f"当前工具：画笔 (大小: {self.brush_size}) - 涂抹需要保留的区域")
            self.status_var.set(f"当前工具：画笔 (大小: {self.brush_size}) - 涂抹需要保留的区域")
        elif mode == "eraser":
            self.tool_info_var.set(f"当前工具：橡皮擦 (大小: {self.eraser_size}) - 擦除错误涂抹的区域")
            self.status_var.set(f"当前工具：橡皮擦 (大小: {self.eraser_size}) - 擦除错误涂抹的区域")
        elif mode == "rectangle":
            self.tool_info_var.set("当前工具：矩形选择 - 拖动鼠标绘制矩形保留区域")
            self.status_var.set("当前工具：矩形选择 - 拖动鼠标绘制矩形保留区域")
    
    def update_brush_size(self, value):
        """更新画笔和橡皮擦大小"""
        self.brush_size = int(float(value))
        self.eraser_size = int(float(value))
        self.brush_size_label.config(text=str(self.brush_size))
        
        # 更新工具信息
        if self.tool_mode == "brush":
            self.tool_info_var.set(f"当前工具：画笔 (大小: {self.brush_size}) - 涂抹需要保留的区域")
            self.status_var.set(f"当前工具：画笔 (大小: {self.brush_size}) - 涂抹需要保留的区域")
        elif self.tool_mode == "eraser":
            self.tool_info_var.set(f"当前工具：橡皮擦 (大小: {self.eraser_size}) - 擦除错误涂抹的区域")
            self.status_var.set(f"当前工具：橡皮擦 (大小: {self.eraser_size}) - 擦除错误涂抹的区域")
    
    def on_object_change(self, event):
        """切换抠图对象类型"""
        selected_object = self.object_var.get()
        if selected_object == self.current_object:
            return
            
        self.current_object = selected_object
        self.object_desc_var.set(self.object_types[selected_object])
        
        # 根据对象类型自动推荐合适的模型
        recommended_model = self.current_model
        if selected_object == "person":
            recommended_model = "u2net_human_seg"
        elif selected_object == "clothing":
            recommended_model = "u2net_cloth_seg"
        elif selected_object == "auto":
            recommended_model = "u2net"
            
        # 如果推荐模型与当前模型不同，提示用户切换
        if recommended_model != self.current_model:
            self.model_var.set(recommended_model)
            self.on_model_change(None)  # 手动触发模型切换
            messagebox.showinfo("模型自动切换", 
                               f"根据选择的'{selected_object}'对象类型，已自动切换到推荐模型'{recommended_model}'")
        
        self.status_var.set(f"已选择抠图对象: {selected_object}，当前模型：{self.current_model}")
    
    def on_model_change(self, event):
        """切换抠图模型"""
        selected_model = self.model_var.get()
        if selected_model == self.current_model:
            return
            
        # 显示模型切换中提示
        self.status_var.set(f"正在切换到 {selected_model} 模型...")
        self.root.update_idletasks()
        
        try:
            # 创建新的模型会话
            self.model_session = new_session(selected_model)
            self.current_model = selected_model
            
            # 更新模型说明
            self.model_desc_var.set(self.models[selected_model])
            
            # 根据模型自动推荐对象类型
            recommended_object = self.current_object
            if selected_model == "u2net_human_seg":
                recommended_object = "person"
            elif selected_model == "u2net_cloth_seg":
                recommended_object = "clothing"
                
            if recommended_object != self.current_object:
                self.object_var.set(recommended_object)
                self.current_object = recommended_object
                self.object_desc_var.set(self.object_types[recommended_object])
            
            # 提示用户模型已切换
            self.status_var.set(f"已切换到 {selected_model} 模型，适合：{self.models[selected_model]}")
            
            # 如果已有处理结果，提示用户重新处理
            if self.current_image_path in self.output_images:
                messagebox.showinfo("模型已切换", 
                                   f"已成功切换到 {selected_model} 模型\n"
                                   "请重新处理图片以应用新模型")
                                   
        except Exception as e:
            # 切换失败，恢复原来的模型
            self.model_var.set(self.current_model)
            error_msg = f"切换模型失败: {str(e)}\n可能需要下载模型，请确保网络连接正常"
            self.status_var.set(error_msg)
            messagebox.showerror("模型切换失败", error_msg)
    
    def select_images(self):
        """选择并显示多个原始图片"""
        file_paths = filedialog.askopenfilenames(
            filetypes=[
                ("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_paths:
            # 清空现有列表
            self.image_listbox.delete(0, tk.END)
            self.input_image_paths = list(file_paths)
            
            # 添加到列表框
            for path in self.input_image_paths:
                self.image_listbox.insert(tk.END, os.path.basename(path))
            
            self.status_var.set(f"已选择 {len(self.input_image_paths)} 张图片，当前对象：{self.current_object}，当前模型：{self.current_model}")
            
            # 更新按钮状态
            self.batch_process_btn.config(state=tk.NORMAL)
            self._disable_drawing_tools()
            self.save_current_btn.config(state=tk.DISABLED)
            
            # 清空预览区域
            self.original_canvas.delete("all")
            self.processed_canvas.delete("all")
            self.current_image_path = None
            self.output_images.clear()
            self.mask = None
            self.display_image = None
            self.zoom_factor = 1.0  # 重置缩放因子
    
    def on_image_select(self, event):
        """当用户选择列表中的图片时显示预览"""
        selection = self.image_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index >= len(self.input_image_paths):
            return
            
        self.current_image_path = self.input_image_paths[index]
        self.selected_region = None  # 重置选择区域
        self.status_var.set(f"已选择: {os.path.basename(self.current_image_path)}，右键图片打开操作菜单")
        
        # 显示原始图片
        try:
            self.original_image = Image.open(self.current_image_path).convert("RGBA")
            self._init_mask()  # 初始化掩码
            self._update_display_image()  # 更新显示图像
            self._display_image(self.display_image, self.original_canvas, is_original=True)
            
            # 更新按钮状态
            self._enable_drawing_tools()
            
            # 如果有处理后的图片，显示它
            if self.current_image_path in self.output_images:
                self.processed_image = self.output_images[self.current_image_path]
                self._display_image(self.processed_image, self.processed_canvas)
                self.save_current_btn.config(state=tk.NORMAL)
            else:
                self.processed_canvas.delete("all")
                self.processed_image = None
                self.save_current_btn.config(state=tk.DISABLED)
        except Exception as e:
            self.status_var.set(f"加载图片失败: {str(e)}")
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def _init_mask(self):
        """初始化掩码（优化版本）- 同时初始化draw对象"""
        # 对大图片创建较小的掩码以提高绘制性能
        max_mask_size = 1024
        if max(self.original_image.size) > max_mask_size:
            scale = max_mask_size / max(self.original_image.size)
            mask_size = tuple(int(dim * scale) for dim in self.original_image.size)
        else:
            mask_size = self.original_image.size
            scale = 1.0
            
        self.mask = Image.new('L', mask_size, 0)
        self.temp_mask = self.mask.copy()
        self.mask_scale = scale  # 记录掩码缩放比例，用于坐标转换
        # 初始化draw对象，这是修复错误的关键
        self.draw = ImageDraw.Draw(self.temp_mask)
    
    def _enable_drawing_tools(self):
        """启用绘图工具"""
        self.brush_size_scale.config(state=tk.NORMAL)
        self.color_tolerance_scale.config(state=tk.NORMAL if self.use_color_removal else tk.DISABLED)
        self.batch_process_btn.config(state=tk.NORMAL if self.input_image_paths else tk.DISABLED)
    
    def _disable_drawing_tools(self):
        """禁用绘图工具"""
        self.brush_size_scale.config(state=tk.DISABLED)
        self.color_tolerance_scale.config(state=tk.DISABLED)
    
    def clear_mask(self):
        """清除当前掩码"""
        if self.original_image:
            self._init_mask()  # 重新初始化掩码和draw对象
            self._update_display_image()
            self._display_image(self.display_image, self.original_canvas, is_original=True)
            self.status_var.set("已清除掩码，请右键选择工具重新勾勒需要保留的区域")
    
    def optimize_mask(self):
        """优化掩码边缘"""
        if not self.mask or not self.original_image:
            return
            
        self.status_var.set("正在优化掩码边缘...")
        self.root.update_idletasks()
        
        # 对掩码进行轻微模糊以平滑边缘
        optimized_mask = self.mask.filter(ImageFilter.GaussianBlur(radius=2))
        self.mask = optimized_mask
        self.temp_mask = self.mask.copy()
        self.draw = ImageDraw.Draw(self.temp_mask)  # 重新初始化draw对象
        
        self._update_display_image()
        self._display_image(self.display_image, self.original_canvas, is_original=True)
        self.status_var.set("掩码边缘优化完成，可继续手动调整或应用抠图")
    
    def _update_display_image(self):
        """更新显示图像（原图+掩码叠加）"""
        if not self.original_image or not self.mask:
            return
            
        # 创建掩码的可视化版本（红色半透明）
        mask_visual = Image.new('RGBA', self.original_image.size, (255, 0, 0, 0))
        
        # 计算掩码缩放
        if hasattr(self, 'mask_scale') and self.mask_scale != 1.0:
            scaled_mask = self.mask.resize(self.original_image.size, Image.Resampling.LANCZOS)
        else:
            scaled_mask = self.mask
        
        # 将掩码转换为红色半透明区域
        mask_array = np.array(scaled_mask)
        for y in range(mask_array.shape[0]):
            for x in range(mask_array.shape[1]):
                if mask_array[y, x] > 0:
                    mask_visual.putpixel((x, y), (255, 0, 100, 100))
        
        # 叠加原图和掩码可视化
        self.display_image = Image.alpha_composite(self.original_image, mask_visual)
    
    def on_drawing_start(self, event):
        """开始绘制"""
        if not self.original_image or self.processing or self.draw is None:
            return
            
        self.drawing = True
        x, y = self._canvas_to_image_coords(event.x, event.y)
        
        if self.tool_mode == "rectangle":
            self.selection_start = (x, y)
        else:
            # 画笔或橡皮擦，先画一个点
            self._draw_at(x, y)
    
    def on_drawing_drag(self, event):
        """拖动绘制"""
        if not self.drawing or not self.original_image or self.processing or self.draw is None:
            return
            
        x, y = self._canvas_to_image_coords(event.x, event.y)
        
        if self.tool_mode == "rectangle" and self.selection_start:
            # 绘制矩形预览（在画布上临时显示）
            self.original_canvas.delete("temp_rect")
            canvas_x1, canvas_y1 = self._image_to_canvas_coords(
                self.selection_start[0], self.selection_start[1])
            canvas_x2, canvas_y2 = event.x, event.y
            self.original_canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                outline="red", dash=(5, 2), width=2, tags="temp_rect"
            )
        else:
            # 画笔或橡皮擦，连续绘制
            self._draw_at(x, y)
    
    def on_drawing_end(self, event):
        """结束绘制"""
        if not self.drawing or not self.original_image or self.processing or self.draw is None:
            self.drawing = False
            return
            
        x, y = self._canvas_to_image_coords(event.x, event.y)
        
        if self.tool_mode == "rectangle" and self.selection_start:
            # 完成矩形绘制，应用到掩码
            x1, y1 = self.selection_start
            x2, y2 = x, y
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            
            # 缩放坐标以匹配掩码尺寸
            if hasattr(self, 'mask_scale') and self.mask_scale != 1.0:
                x1 = int(x1 * self.mask_scale)
                y1 = int(y1 * self.mask_scale)
                x2 = int(x2 * self.mask_scale)
                y2 = int(y2 * self.mask_scale)
            
            # 在掩码上绘制实心矩形
            self.draw.rectangle([x1, y1, x2, y2], fill=255)
            self.mask = self.temp_mask.copy()
            
            # 清除画布上的临时矩形
            self.original_canvas.delete("temp_rect")
            self.selection_start = None
        else:
            # 完成画笔/橡皮擦绘制
            self.mask = self.temp_mask.copy()
        
        # 更新显示图像
        self._update_display_image()
        self._display_image(self.display_image, self.original_canvas, is_original=True)
        
        self.drawing = False
        self.status_var.set(f"已完成绘制，当前工具：{self.tool_mode} - 右键选择'应用手动抠图'生成结果")
    
    def _draw_at(self, x, y):
        """在指定位置绘制（画笔或橡皮擦）"""
        # 检查draw对象是否存在
        if self.draw is None:
            self.status_var.set("绘制工具未初始化，请重新选择图片")
            return
            
        # 缩放坐标以匹配掩码尺寸
        if hasattr(self, 'mask_scale') and self.mask_scale != 1.0:
            x = int(x * self.mask_scale)
            y = int(y * self.mask_scale)
            size = int(self.brush_size * self.mask_scale)
        else:
            size = self.brush_size
        
        if self.tool_mode == "brush":
            # 画笔 - 绘制白色（表示保留）
            self.draw.ellipse([
                x - size//2, y - size//2,
                x + size//2, y + size//2
            ], fill=255)
        elif self.tool_mode == "eraser":
            # 橡皮擦 - 绘制黑色（表示删除）
            self.draw.ellipse([
                x - size//2, y - size//2,
                x + size//2, y + size//2
            ], fill=0)
    
    def on_mouse_wheel(self, event):
        """鼠标滚轮缩放图像（优化显示性能）"""
        if not self.original_image:
            return
            
        # 调整缩放因子
        if event.delta > 0:
            self.zoom_factor *= 1.1  # 放大
        else:
            self.zoom_factor /= 1.1  # 缩小
            
        # 限制缩放范围
        self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
        
        # 更新显示
        self._update_display_image()
        self._display_image(self.display_image, self.original_canvas, is_original=True)
        if self.processed_image:
            self._display_image(self.processed_image, self.processed_canvas)
    
    def _canvas_to_image_coords(self, x, y):
        """将画布坐标转换为原始图像坐标（考虑缩放和偏移）"""
        # 获取画布上的图像位置
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()
        img_width, img_height = self.original_image.size
        
        # 计算图像在画布上的位置（居中显示）
        display_width = int(img_width * self.zoom_factor)
        display_height = int(img_height * self.zoom_factor)
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2
        
        # 转换坐标
        img_x = int((x - offset_x) / self.zoom_factor)
        img_y = int((y - offset_y) / self.zoom_factor)
        
        # 确保坐标在图像范围内
        img_x = max(0, min(img_x, img_width - 1))
        img_y = max(0, min(img_y, img_height - 1))
        
        return (img_x, img_y)
    
    def _image_to_canvas_coords(self, x, y):
        """将原始图像坐标转换为画布坐标（考虑缩放和偏移）"""
        # 获取画布上的图像位置
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()
        img_width, img_height = self.original_image.size
        
        # 计算图像在画布上的位置（居中显示）
        display_width = int(img_width * self.zoom_factor)
        display_height = int(img_height * self.zoom_factor)
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2
        
        # 转换坐标
        canvas_x = int(x * self.zoom_factor + offset_x)
        canvas_y = int(y * self.zoom_factor + offset_y)
        
        return (canvas_x, canvas_y)
    
    def process_manual_mask(self):
        """应用手动绘制的掩码进行抠图"""
        if not self.current_image_path or not self.original_image or not self.mask:
            messagebox.showerror("错误", "请先选择图片并绘制掩码")
            return
            
        # 检查掩码是否为空
        if not np.any(np.array(self.mask)):
            messagebox.showwarning("警告", "掩码为空，请先绘制需要保留的区域")
            return
            
        if self.processing:
            messagebox.showinfo("提示", "正在处理中，请稍候...")
            return
            
        self.processing = True
        self.status_var.set(f"正在应用手动抠图: {os.path.basename(self.current_image_path)}")
        self._disable_all_tools()
        
        # 在新线程中处理，避免UI冻结
        threading.Thread(target=self._apply_manual_mask, daemon=True).start()
    
    def _apply_manual_mask(self):
        """应用手动掩码处理图片"""
        try:
            # 缩放掩码以匹配原始图像尺寸
            if hasattr(self, 'mask_scale') and self.mask_scale != 1.0:
                scaled_mask = self.mask.resize(self.original_image.size, Image.Resampling.LANCZOS)
            else:
                scaled_mask = self.mask
            
            # 创建结果图像
            result_img = Image.new('RGBA', self.original_image.size, (0, 0, 0, 0))
            
            # 将原图中掩码为白色的区域复制到结果图像
            result_img.paste(self.original_image, mask=scaled_mask)
            
            # 保存处理结果
            self.output_images[self.current_image_path] = result_img
            
            # 更新预览
            self.processed_image = result_img
            self.root.after(0, lambda: self._display_image(result_img, self.processed_canvas))
            self.root.after(0, lambda: self.save_current_btn.config(state=tk.NORMAL))
            
            # 显示完成提示
            filename = os.path.basename(self.current_image_path)
            complete_msg = f"手动抠图已完成!\n图片: {filename}\n可右键选择'保存当前结果'保存"
            self.root.after(0, lambda: self.status_var.set(f"手动抠图完成: {filename}"))
            self.root.after(100, lambda: messagebox.showinfo("处理完成", complete_msg))
            
        except Exception as e:
            error_msg = f"手动抠图出错: {str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            self.processing = False
            self.root.after(0, lambda: self._enable_drawing_tools())
    
    def process_full_image(self):
        """对整张图片进行自动抠图"""
        if not self.current_image_path:
            messagebox.showerror("错误", "请先选择图片")
            return
            
        if self.processing:
            messagebox.showinfo("提示", "正在处理中，请稍候...")
            return
            
        self.processing = True
        self.status_var.set(f"正在自动抠图: {os.path.basename(self.current_image_path)}")
        self._disable_all_tools()
        
        # 在新线程中处理，避免UI冻结
        threading.Thread(target=self._process_full_region, daemon=True).start()
    
    def batch_process_images(self):
        """批量处理所有图片（全图模式）"""
        if not self.input_image_paths:
            messagebox.showerror("错误", "请先选择图片")
            return
            
        if self.processing:
            messagebox.showinfo("提示", "正在处理中，请稍候...")
            return
            
        self.processing = True
        self.status_var.set(f"开始批量自动抠图...")
        self._disable_all_tools()
        self.progress_var.set(0)
        
        # 在新线程中处理，避免UI冻结
        threading.Thread(target=self._process_images_in_background, daemon=True).start()
    
    def _process_images_in_background(self):
        """后台批量处理图片"""
        total = len(self.input_image_paths)
        
        for i, image_path in enumerate(self.input_image_paths):
            try:
                # 更新状态
                self.status_var.set(f"正在处理 {i+1}/{total}: {os.path.basename(image_path)}")
                self.progress_var.set((i / total) * 100)
                self.root.update_idletasks()
                
                # 全图处理图片
                self._process_full_region(image_path=image_path)
                
            except Exception as e:
                self.status_var.set(f"处理 {os.path.basename(image_path)} 时出错: {str(e)}")
            
        # 处理完成
        self.progress_var.set(100)
        final_msg = f"批量处理完成，共处理 {len(self.output_images)}/{total} 张图片"
        self.status_var.set(final_msg)
        self.processing = False
        
        # 恢复UI状态
        self._enable_drawing_tools()
        
        # 显示批量处理完成提示
        self.root.after(0, lambda: messagebox.showinfo("处理完成", final_msg))
    
    def _process_full_region(self, image_path=None):
        """处理整张图片"""
        if image_path is None:
            image_path = self.current_image_path
            
        try:
            with open(image_path, 'rb') as f:
                input_data = f.read()
            
            # 使用选定的模型处理整张图片
            output_data = remove(input_data, session=self.model_session)
            output_image = Image.open(io.BytesIO(output_data))
            
            # 保存处理结果
            self.output_images[image_path] = output_image
            
            # 如果是当前显示的图片，更新预览
            if self.current_image_path == image_path:
                self.processed_image = output_image
                self.root.after(0, lambda: self._display_image(output_image, self.processed_canvas))
                self.root.after(0, lambda: self.save_current_btn.config(state=tk.NORMAL))
                
                # 显示完成提示
                filename = os.path.basename(image_path)
                complete_msg = f"自动抠图已完成!\n图片: {filename}\n使用模型: {self.current_model}\n可右键选择'保存当前结果'保存"
                self.root.after(0, lambda: self.status_var.set(f"自动抠图完成: {filename}"))
                self.root.after(100, lambda: messagebox.showinfo("处理完成", complete_msg))
                
        except Exception as e:
            error_msg = f"自动抠图出错: {str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            if image_path == self.current_image_path:  # 仅在处理当前图片时恢复按钮状态
                self.processing = False
                self.root.after(0, lambda: self._enable_drawing_tools())
    
    def save_current_image(self):
        """保存当前选中的处理后图片"""
        if not self.current_image_path or self.current_image_path not in self.output_images:
            messagebox.showerror("错误", "没有可保存的处理结果")
            return
        
        try:
            # 获取原始文件名
            original_filename = os.path.basename(self.current_image_path)
            name, ext = os.path.splitext(original_filename)
            
            # 根据处理方式添加不同的后缀
            if self.mask and np.any(np.array(self.mask)):
                save_filename = f"{name}_manual_{self.current_object}_no_bg.png"
            elif self.use_color_removal:
                save_filename = f"{name}_color_{self.current_object}_no_bg.png"
            else:
                save_filename = f"{name}_auto_{self.current_object}_{self.current_model}_no_bg.png"
                
            save_path = os.path.join(self.save_dir, save_filename)
            
            # 保存图片
            self.output_images[self.current_image_path].save(save_path)
            self.status_var.set(f"图片已保存至: {save_path}")
            messagebox.showinfo("成功", f"图片已成功保存至:\n{save_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存图片时出错: {str(e)}")
            self.status_var.set("保存失败")
    
    def _display_image(self, image, canvas, is_original=False):
        """显示图像（优化版本，支持缩放）"""
        if not image:
            return
            
        canvas.delete("all")
        
        # 根据缩放因子调整图像大小
        width, height = image.size
        new_width = int(width * self.zoom_factor)
        new_height = int(height * self.zoom_factor)
        
        # 调整大小时使用更高效的算法
        display_img = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=display_img)
        
        # 存储引用防止被垃圾回收
        if is_original:
            self.original_photo = photo
        else:
            self.processed_photo = photo
            
        # 在画布中心显示图像
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        canvas.create_image(x, y, anchor=tk.NW, image=photo)
        canvas.image = photo  # 保存引用
    
    def _disable_all_tools(self):
        """禁用所有工具"""
        self._disable_drawing_tools()
        self.select_btn.config(state=tk.DISABLED)
        self.batch_process_btn.config(state=tk.DISABLED)
        self.save_current_btn.config(state=tk.DISABLED)
        self.object_combobox.config(state="disabled")
        self.model_combobox.config(state="disabled")
# endregion

if __name__ == "__main__":
    # 提示用户安装必要的库
    try:
        import rembg
        import onnxruntime
        import numpy as np
        from numba import jit
    except ImportError as e:
        print(f"检测到缺少必要的库: {e}，正在尝试安装...")
        import subprocess
        import sys
        
        # 安装所需库
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg", "Pillow", "tkinter", "onnxruntime", "numpy", "numba"])
        
        # 安装rembg的模型（首次运行时需要）
        subprocess.check_call([sys.executable, "-m", "rembg", "download_models"])
    
    # 启动应用
    root = tk.Tk()
    app = AdvancedBackgroundRemovalApp(root)
    root.mainloop()
                