#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化软件资源整合管理器 v3.0 Modern UI
使用CustomTkinter实现现代化界面设计
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import threading
import requests
from urllib.parse import urlparse
import subprocess
from pathlib import Path
import time
from datetime import datetime
import webbrowser
from PIL import Image, ImageTk

# 设置CustomTkinter外观模式和颜色主题
ctk.set_appearance_mode("light")  # 可选: "light", "dark", "system"
ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class ModernSoftwareManager:
    def __init__(self):
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("🚀 软件资源整合管理器 v3.0 Modern")
        self.root.geometry("1500x1000")
        
        # 设置窗口图标和最小尺寸
        self.root.minsize(1200, 800)
        
        # 初始化数据
        self.software_data = {}
        self.filtered_data = {}
        self.selected_software = set()
        self.config = {}
        
        # 加载数据和配置
        self.load_software_data()
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置网格权重
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
    
    def load_software_data(self):
        """加载软件数据"""
        try:
            with open('software_data.json', 'r', encoding='utf-8') as f:
                self.software_data = json.load(f)
            self.filtered_data = self.software_data.copy()
        except FileNotFoundError:
            messagebox.showerror("错误", "软件数据文件不存在！")
            self.software_data = {}
            self.filtered_data = {}
    
    def load_config(self):
        """加载配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'download_path': str(Path.home() / 'Downloads'),
                'max_concurrent_downloads': 3,
                'theme': 'light'
            }
    
    def save_config(self):
        """保存配置"""
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        
        # 创建顶部标题栏
        self.create_header()
        
        # 创建内容区域
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # 创建左侧面板（软件分类）
        self.create_left_panel()
        
        # 创建右侧面板（已选软件和控制）
        self.create_right_panel()
        
        # 创建底部状态栏
        self.create_bottom_panel()
        
        # 设置网格权重
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def create_header(self):
        """创建顶部标题栏"""
        header_frame = ctk.CTkFrame(self.main_frame, height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_propagate(False)
        
        # 标题
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🚀 软件资源整合管理器",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # 搜索框
        search_frame = ctk.CTkFrame(header_frame)
        search_frame.grid(row=0, column=1, padx=20, pady=10, sticky="e")
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        
        search_label = ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=16))
        search_label.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="搜索软件...",
            width=300,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 10), pady=10)
        
        # 清除搜索按钮
        clear_btn = ctk.CTkButton(
            search_frame,
            text="✖",
            width=35,
            height=35,
            command=self.clear_search,
            font=ctk.CTkFont(size=12)
        )
        clear_btn.grid(row=0, column=2, padx=(0, 10), pady=10)
        
        header_frame.grid_columnconfigure(1, weight=1)
    
    def create_left_panel(self):
        """创建左侧软件分类面板"""
        left_frame = ctk.CTkFrame(self.content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 标题
        title_label = ctk.CTkLabel(
            left_frame,
            text="📂 软件分类浏览",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # 创建滚动框架
        self.scrollable_frame = ctk.CTkScrollableFrame(
            left_frame,
            label_text="",
            width=600,
            height=600
        )
        self.scrollable_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # 填充软件分类
        self.populate_categories()
        
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)
    
    def create_right_panel(self):
        """创建右侧面板"""
        right_frame = ctk.CTkFrame(self.content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # 已选软件列表
        self.create_selected_list(right_frame)
        
        # 控制按钮
        self.create_control_buttons(right_frame)
        
        right_frame.grid_rowconfigure(0, weight=1)
    
    def create_selected_list(self, parent):
        """创建已选软件列表"""
        # 标题
        title_label = ctk.CTkLabel(
            parent,
            text="✅ 已选择的软件",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # 软件列表框架
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        # 创建文本框显示已选软件
        self.selected_textbox = ctk.CTkTextbox(
            list_frame,
            width=400,
            height=400,
            font=ctk.CTkFont(size=12)
        )
        self.selected_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
    
    def create_control_buttons(self, parent):
        """创建控制按钮"""
        control_frame = ctk.CTkFrame(parent)
        control_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # 按钮样式配置
        button_config = {
            'height': 40,
            'font': ctk.CTkFont(size=14, weight="bold")
        }
        
        # 第一行按钮
        btn_frame1 = ctk.CTkFrame(control_frame)
        btn_frame1.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        download_btn = ctk.CTkButton(
            btn_frame1,
            text="⬇️ 开始下载",
            command=self.download_software,
            fg_color="#2E8B57",
            hover_color="#228B22",
            **button_config
        )
        download_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        clear_btn = ctk.CTkButton(
            btn_frame1,
            text="🗑️ 清空列表",
            command=self.clear_all_selected,
            fg_color="#DC143C",
            hover_color="#B22222",
            **button_config
        )
        clear_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 第二行按钮
        btn_frame2 = ctk.CTkFrame(control_frame)
        btn_frame2.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        export_btn = ctk.CTkButton(
            btn_frame2,
            text="📤 导出列表",
            command=self.export_software_list,
            fg_color="#4169E1",
            hover_color="#0000CD",
            **button_config
        )
        export_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        import_btn = ctk.CTkButton(
            btn_frame2,
            text="📥 导入列表",
            command=self.import_software_list,
            fg_color="#FF8C00",
            hover_color="#FF7F00",
            **button_config
        )
        import_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 第三行按钮
        btn_frame3 = ctk.CTkFrame(control_frame)
        btn_frame3.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        settings_btn = ctk.CTkButton(
            btn_frame3,
            text="⚙️ 设置",
            command=self.open_settings,
            fg_color="#708090",
            hover_color="#2F4F4F",
            **button_config
        )
        settings_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        help_btn = ctk.CTkButton(
            btn_frame3,
            text="❓ 帮助",
            command=self.show_help,
            fg_color="#9370DB",
            hover_color="#8A2BE2",
            **button_config
        )
        help_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 设置网格权重
        control_frame.grid_columnconfigure(0, weight=1)
        btn_frame1.grid_columnconfigure((0, 1), weight=1)
        btn_frame2.grid_columnconfigure((0, 1), weight=1)
        btn_frame3.grid_columnconfigure((0, 1), weight=1)
    
    def create_bottom_panel(self):
        """创建底部状态栏"""
        bottom_frame = ctk.CTkFrame(self.main_frame, height=60)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        bottom_frame.grid_propagate(False)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            bottom_frame,
            variable=self.progress_var,
            width=400,
            height=20
        )
        self.progress_bar.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="就绪",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, padx=20, pady=20, sticky="w")
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(
            bottom_frame,
            text="总软件: 0 | 已选择: 0",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.grid(row=0, column=2, padx=20, pady=20, sticky="e")
        
        bottom_frame.grid_columnconfigure(2, weight=1)
        
        # 更新统计信息
        self.update_stats()
    
    def populate_categories(self):
        """填充软件分类"""
        # 清空现有内容
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        row = 0
        for category, subcategories in self.filtered_data.items():
            # 创建分类标题
            category_frame = ctk.CTkFrame(self.scrollable_frame)
            category_frame.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
            
            category_label = ctk.CTkLabel(
                category_frame,
                text=f"📁 {category}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            category_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
            
            # 添加分类按钮
            add_category_btn = ctk.CTkButton(
                category_frame,
                text="➕ 添加全部",
                width=100,
                height=30,
                command=lambda cat=category: self.add_category(cat),
                font=ctk.CTkFont(size=12)
            )
            add_category_btn.grid(row=0, column=1, padx=15, pady=10, sticky="e")
            
            category_frame.grid_columnconfigure(0, weight=1)
            row += 1
            
            # 创建子分类
            for subcategory, software_list in subcategories.items():
                sub_frame = ctk.CTkFrame(self.scrollable_frame)
                sub_frame.grid(row=row, column=0, padx=20, pady=2, sticky="ew")
                
                sub_label = ctk.CTkLabel(
                    sub_frame,
                    text=f"📂 {subcategory} ({len(software_list)})",
                    font=ctk.CTkFont(size=14)
                )
                sub_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")
                
                # 添加子分类按钮
                add_sub_btn = ctk.CTkButton(
                    sub_frame,
                    text="➕",
                    width=30,
                    height=25,
                    command=lambda cat=category, sub=subcategory: self.add_subcategory(cat, sub),
                    font=ctk.CTkFont(size=10)
                )
                add_sub_btn.grid(row=0, column=1, padx=15, pady=8, sticky="e")
                
                sub_frame.grid_columnconfigure(0, weight=1)
                row += 1
                
                # 创建软件列表
                for software in software_list:
                    software_frame = ctk.CTkFrame(sub_frame)
                    software_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=1, sticky="ew")
                    
                    status_icon = "✅" if software['name'] in self.selected_software else "⭕"
                    software_label = ctk.CTkLabel(
                        software_frame,
                        text=f"{status_icon} {software['name']}",
                        font=ctk.CTkFont(size=12)
                    )
                    software_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
                    
                    # 添加/移除按钮
                    if software['name'] in self.selected_software:
                        action_btn = ctk.CTkButton(
                            software_frame,
                            text="➖",
                            width=25,
                            height=20,
                            command=lambda sw=software['name']: self.remove_software(sw),
                            fg_color="#DC143C",
                            hover_color="#B22222",
                            font=ctk.CTkFont(size=10)
                        )
                    else:
                        action_btn = ctk.CTkButton(
                            software_frame,
                            text="➕",
                            width=25,
                            height=20,
                            command=lambda sw=software['name']: self.add_software(sw),
                            fg_color="#2E8B57",
                            hover_color="#228B22",
                            font=ctk.CTkFont(size=10)
                        )
                    
                    action_btn.grid(row=0, column=1, padx=10, pady=5, sticky="e")
                    
                    software_frame.grid_columnconfigure(0, weight=1)
                    row += 1
        
        # 设置滚动框架的网格权重
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
    
    def on_search_change(self, *args):
        """搜索框内容变化事件"""
        search_term = self.search_var.get().lower().strip()
        
        if not search_term:
            self.filtered_data = self.software_data.copy()
        else:
            self.filtered_data = {}
            for category, subcategories in self.software_data.items():
                filtered_subcategories = {}
                for subcategory, software_list in subcategories.items():
                    filtered_software = [
                        software for software in software_list
                        if search_term in software['name'].lower() or 
                           search_term in software['description'].lower()
                    ]
                    if filtered_software:
                        filtered_subcategories[subcategory] = filtered_software
                
                if filtered_subcategories:
                    self.filtered_data[category] = filtered_subcategories
        
        self.populate_categories()
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set('')
    
    def add_software(self, software_name):
        """添加软件到选择列表"""
        self.selected_software.add(software_name)
        self.update_selected_list()
        self.populate_categories()  # 刷新界面
        self.update_stats()
    
    def remove_software(self, software_name):
        """从选择列表移除软件"""
        self.selected_software.discard(software_name)
        self.update_selected_list()
        self.populate_categories()  # 刷新界面
        self.update_stats()
    
    def add_category(self, category):
        """添加整个分类"""
        added_count = 0
        for subcategory, software_list in self.software_data[category].items():
            for software in software_list:
                if software['name'] not in self.selected_software:
                    self.selected_software.add(software['name'])
                    added_count += 1
        
        if added_count > 0:
            self.update_selected_list()
            self.populate_categories()
            self.update_stats()
            messagebox.showinfo("成功", f"已添加 {added_count} 个软件到选择列表")
    
    def add_subcategory(self, category, subcategory):
        """添加整个子分类"""
        added_count = 0
        for software in self.software_data[category][subcategory]:
            if software['name'] not in self.selected_software:
                self.selected_software.add(software['name'])
                added_count += 1
        
        if added_count > 0:
            self.update_selected_list()
            self.populate_categories()
            self.update_stats()
            messagebox.showinfo("成功", f"已添加 {added_count} 个软件到选择列表")
    
    def update_selected_list(self):
        """更新已选软件列表"""
        self.selected_textbox.delete("1.0", "end")
        
        if not self.selected_software:
            self.selected_textbox.insert("1.0", "暂无选择的软件\n\n点击左侧软件列表中的 ➕ 按钮添加软件")
        else:
            content = "已选择的软件列表:\n\n"
            for i, software in enumerate(sorted(self.selected_software), 1):
                content += f"{i:2d}. {software}\n"
            self.selected_textbox.insert("1.0", content)
    
    def clear_all_selected(self):
        """清空所有已选软件"""
        if self.selected_software:
            result = messagebox.askyesno("确认", "确定要清空所有已选择的软件吗？")
            if result:
                self.selected_software.clear()
                self.update_selected_list()
                self.populate_categories()
                self.update_stats()
    
    def update_stats(self):
        """更新统计信息"""
        total_software = sum(
            len(software_list)
            for subcategories in self.software_data.values()
            for software_list in subcategories.values()
        )
        selected_count = len(self.selected_software)
        
        self.stats_label.configure(text=f"总软件: {total_software} | 已选择: {selected_count}")
    
    def download_software(self):
        """下载软件"""
        if not self.selected_software:
            messagebox.showwarning("警告", "请先选择要下载的软件")
            return
        
        # 选择下载目录
        download_dir = filedialog.askdirectory(
            title="选择下载目录",
            initialdir=self.config.get('download_path', str(Path.home() / 'Downloads'))
        )
        
        if download_dir:
            self.config['download_path'] = download_dir
            self.save_config()
            
            # 开始下载
            threading.Thread(target=self.start_download, args=(download_dir,), daemon=True).start()
    
    def start_download(self, download_dir):
        """开始下载过程"""
        total_software = len(self.selected_software)
        downloaded = 0
        failed = 0
        
        self.status_label.configure(text="正在下载...")
        
        for software_name in self.selected_software:
            try:
                # 查找软件信息
                software_info = None
                for category in self.software_data:
                    for subcategory in self.software_data[category]:
                        for software in self.software_data[category][subcategory]:
                            if software['name'] == software_name:
                                software_info = software
                                break
                        if software_info:
                            break
                    if software_info:
                        break
                
                if not software_info:
                    raise Exception(f"找不到软件信息: {software_name}")
                
                # 获取下载URL
                download_url = software_info.get('download_url')
                if not download_url:
                    raise Exception(f"软件没有下载链接: {software_name}")
                
                self.status_label.configure(text=f"正在下载: {software_name}")
                
                # 确定文件名
                # 尝试从URL中提取文件名
                parsed_url = urlparse(download_url)
                url_path = parsed_url.path
                filename = os.path.basename(url_path)
                
                # 如果URL中没有文件名或文件名不包含扩展名
                if not filename or '.' not in filename:
                    # 尝试从URL路径中提取常见的软件扩展名
                    common_extensions = ['.exe', '.msi', '.zip', '.rar', '.7z', '.dmg', '.pkg', '.deb', '.rpm']
                    found_ext = None
                    for ext in common_extensions:
                        if ext in url_path:
                            found_ext = ext
                            break
                    
                    if found_ext:
                        # 使用软件名称和找到的扩展名
                        safe_name = ''.join(c if c.isalnum() else '_' for c in software_name)
                        filename = f"{safe_name}{found_ext}"
                    else:
                        # 默认使用.exe
                        safe_name = ''.join(c if c.isalnum() else '_' for c in software_name)
                        filename = f"{safe_name}.exe"
                
                file_path = os.path.join(download_dir, filename)
                
                # 开始下载
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 下载文件
                with open(file_path, 'wb') as f:
                    if total_size > 0:
                        downloaded_size = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                # 更新进度条
                                file_progress = downloaded_size / total_size
                                overall_progress = (downloaded + file_progress) / total_software
                                self.progress_var.set(overall_progress)
                                self.root.update_idletasks()
                    else:
                        # 如果无法获取文件大小，直接写入
                        f.write(response.content)
                
                downloaded += 1
                progress = (downloaded / total_software)
                self.progress_var.set(progress)
                
            except Exception as e:
                print(f"下载 {software_name} 失败: {e}")
                failed += 1
                messagebox.showerror("下载错误", f"下载 {software_name} 失败:\n{str(e)}")
        
        self.status_label.configure(text=f"下载完成！成功: {downloaded} 个，失败: {failed} 个")
        messagebox.showinfo("完成", f"下载完成！\n成功: {downloaded} 个，失败: {failed} 个\n下载目录:\n{download_dir}")
    
    def export_software_list(self):
        """导出软件列表"""
        if not self.selected_software:
            messagebox.showwarning("警告", "没有选择的软件可以导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存软件列表",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt")]
        )
        
        if file_path:
            try:
                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'software_list': list(self.selected_software)
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"软件列表已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def import_software_list(self):
        """导入软件列表"""
        file_path = filedialog.askopenfilename(
            title="选择软件列表文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                if 'software_list' in import_data:
                    imported_count = 0
                    for software_name in import_data['software_list']:
                        if software_name not in self.selected_software:
                            self.selected_software.add(software_name)
                            imported_count += 1
                    
                    self.update_selected_list()
                    self.populate_categories()
                    self.update_stats()
                    
                    messagebox.showinfo("成功", f"已导入 {imported_count} 个新软件")
                else:
                    messagebox.showerror("错误", "文件格式不正确")
                    
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("⚙️ 设置")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置内容
        main_frame = ctk.CTkFrame(settings_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ 应用设置",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # 下载路径设置
        path_frame = ctk.CTkFrame(main_frame)
        path_frame.pack(fill="x", padx=10, pady=10)
        
        path_label = ctk.CTkLabel(path_frame, text="下载路径:", font=ctk.CTkFont(size=14))
        path_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        path_entry = ctk.CTkEntry(
            path_frame,
            width=350,
            font=ctk.CTkFont(size=12)
        )
        path_entry.pack(padx=10, pady=(0, 10))
        path_entry.insert(0, self.config.get('download_path', ''))
        
        # 主题设置
        theme_frame = ctk.CTkFrame(main_frame)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        theme_label = ctk.CTkLabel(theme_frame, text="外观主题:", font=ctk.CTkFont(size=14))
        theme_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        theme_var = tk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            variable=theme_var,
            command=self.change_theme
        )
        theme_menu.pack(padx=10, pady=(0, 10))
        
        # 按钮
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=20)
        
        def save_settings():
            self.config['download_path'] = path_entry.get()
            self.save_config()
            messagebox.showinfo("成功", "设置已保存")
            settings_window.destroy()
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 保存设置",
            command=save_settings,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(side="left", padx=10, pady=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ 取消",
            command=settings_window.destroy,
            fg_color="#DC143C",
            hover_color="#B22222",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        cancel_btn.pack(side="right", padx=10, pady=10)
    
    def change_theme(self, theme):
        """更改主题"""
        ctk.set_appearance_mode(theme.lower())
    
    def show_help(self):
        """显示帮助信息"""
        help_window = ctk.CTkToplevel(self.root)
        help_window.title("❓ 帮助")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # 帮助内容
        main_frame = ctk.CTkFrame(help_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="❓ 使用帮助",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        help_text = ctk.CTkTextbox(
            main_frame,
            width=550,
            height=350,
            font=ctk.CTkFont(size=12)
        )
        help_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        help_content = """
🚀 软件资源整合管理器 v3.0 Modern 使用指南

📂 软件浏览:
• 左侧面板显示所有软件分类
• 点击 ➕ 按钮添加单个软件
• 点击 "➕ 添加全部" 添加整个分类
• 使用顶部搜索框快速查找软件

✅ 软件管理:
• 右侧面板显示已选择的软件
• 点击 ➖ 按钮移除软件
• 使用 "🗑️ 清空列表" 清除所有选择

⬇️ 下载功能:
• 点击 "⬇️ 开始下载" 开始下载
• 选择下载目录
• 查看下载进度

📤📥 导入导出:
• 导出软件列表为JSON文件
• 导入之前保存的软件列表

⚙️ 设置:
• 配置默认下载路径
• 更改应用主题（浅色/深色/系统）

🎨 界面特色:
• 现代化圆润设计
• 鲜活的色彩搭配
• 流畅的交互体验
• 响应式布局设计

💡 小贴士:
• 使用搜索功能快速定位软件
• 定期导出软件列表作为备份
• 根据个人喜好调整主题
        """
        
        help_text.insert("1.0", help_content)
        help_text.configure(state="disabled")
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            main_frame,
            text="关闭",
            command=help_window.destroy,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        close_btn.pack(pady=10)
    
    def on_closing(self):
        """程序关闭事件"""
        self.save_config()
        
        if self.selected_software:
            result = messagebox.askyesnocancel(
                "确认退出",
                f"您有 {len(self.selected_software)} 个软件尚未下载。\n\n是否要保存选择列表？"
            )
            
            if result is None:  # 取消
                return
            elif result:  # 是，保存
                self.export_software_list()
        
        self.root.destroy()
    
    def run(self):
        """运行程序"""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("错误", f"程序运行出错: {e}")

def main():
    """主函数"""
    try:
        app = ModernSoftwareManager()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("启动错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()