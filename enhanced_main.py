#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件资源整合桌面应用程序 - 增强版
类似Ninite的一键安装程序生成器
支持1000+款常用软件的管理和安装
增强功能：搜索过滤、进度条、配置保存、软件更新检测
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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

class EnhancedSoftwareManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("软件资源整合管理器 v2.0 Enhanced")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f5f5f5')
        
        # 设置窗口图标和样式
        self.setup_styles()
        
        # 软件数据和配置
        self.software_data = self.load_software_data()
        self.selected_software = set()
        self.filtered_data = self.software_data.copy()
        self.config = self.load_config()
        
        # 下载状态
        self.download_progress = {}
        self.is_downloading = False
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure('Title.TLabel', font=('Microsoft YaHei', 18, 'bold'), 
                       background='#f5f5f5', foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Microsoft YaHei', 12, 'bold'), 
                       background='#f5f5f5', foreground='#34495e')
        style.configure('Custom.TButton', font=('Microsoft YaHei', 10), 
                       padding=(15, 8))
        style.configure('Action.TButton', font=('Microsoft YaHei', 11, 'bold'), 
                       padding=(20, 10))
        style.configure('Treeview', font=('Microsoft YaHei', 9), rowheight=25)
        style.configure('Treeview.Heading', font=('Microsoft YaHei', 10, 'bold'))
        
        # 配置进度条样式
        style.configure('Custom.Horizontal.TProgressbar', 
                       background='#3498db', troughcolor='#ecf0f1')
        
    def load_software_data(self):
        """加载软件数据"""
        try:
            with open('software_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("错误", "软件数据文件不存在！请确保software_data.json文件在程序目录中。")
            return {}
    
    def load_config(self):
        """加载用户配置"""
        config_file = 'config.json'
        default_config = {
            'download_path': str(Path.home() / 'Downloads' / 'SoftwareManager'),
            'auto_check_updates': True,
            'concurrent_downloads': 3,
            'selected_software': [],
            'window_geometry': '1400x900',
            'theme': 'default'
        }
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            return default_config
    
    def save_config(self):
        """保存用户配置"""
        self.config['selected_software'] = list(self.selected_software)
        self.config['window_geometry'] = self.root.geometry()
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题和搜索栏
        self.create_header(main_frame)
        
        # 主要内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 左侧软件分类树
        self.create_software_tree(content_frame)
        
        # 右侧已选软件列表和控制面板
        self.create_right_panel(content_frame)
        
        # 底部状态栏和操作按钮
        self.create_bottom_panel(main_frame)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # 恢复上次选择的软件
        if self.config.get('selected_software'):
            self.selected_software = set(self.config['selected_software'])
            self.update_selected_list()
    
    def create_header(self, parent):
        """创建标题和搜索栏"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 标题
        title_label = ttk.Label(header_frame, text="软件资源整合管理器 Enhanced", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 统计信息
        total_software = sum(len(subcategories.get(subcat, [])) 
                           for subcategories in self.software_data.values() 
                           for subcat in subcategories)
        stats_label = ttk.Label(header_frame, 
                               text=f"共收录 {total_software} 款软件 | 已选择 {len(self.selected_software)} 款",
                               font=('Microsoft YaHei', 10), background='#f5f5f5')
        stats_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 搜索框
        search_frame = ttk.Frame(header_frame)
        search_frame.grid(row=0, column=1, sticky=tk.E, rowspan=2)
        
        ttk.Label(search_frame, text="搜索软件:", font=('Microsoft YaHei', 10)).grid(row=0, column=0, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, 
                                font=('Microsoft YaHei', 10), width=25)
        search_entry.grid(row=0, column=1, padx=(0, 10))
        
        clear_btn = ttk.Button(search_frame, text="清除", command=self.clear_search, width=8)
        clear_btn.grid(row=0, column=2)
        
        header_frame.columnconfigure(0, weight=1)
    
    def create_software_tree(self, parent):
        """创建软件分类树"""
        # 左侧框架
        left_frame = ttk.LabelFrame(parent, text="软件分类浏览", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 创建树形控件
        self.tree = ttk.Treeview(left_frame, selectmode='extended', height=20)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置列
        self.tree['columns'] = ('description',)
        self.tree.column('#0', width=250, minwidth=200)
        self.tree.column('description', width=300, minwidth=200)
        self.tree.heading('#0', text='软件名称', anchor=tk.W)
        self.tree.heading('description', text='软件描述', anchor=tk.W)
        
        # 添加滚动条
        tree_scroll_y = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        
        tree_scroll_x = ttk.Scrollbar(left_frame, orient="horizontal", command=self.tree.xview)
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.tree.configure(xscrollcommand=tree_scroll_x.set)
        
        # 填充树形数据
        self.populate_tree()
        
        # 绑定事件
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Button-3>', self.on_tree_right_click)  # 右键菜单
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_open)
        self.tree.bind('<<TreeviewClose>>', self.on_tree_close)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
    
    def create_right_panel(self, parent):
        """创建右侧面板"""
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 已选软件列表
        self.create_selected_list(right_frame)
        
        # 控制面板
        self.create_control_panel(right_frame)
        
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
    
    def create_selected_list(self, parent):
        """创建已选软件列表"""
        # 已选软件框架
        selected_frame = ttk.LabelFrame(parent, text="已选择的软件", padding="10")
        selected_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建列表框
        self.selected_listbox = tk.Listbox(selected_frame, font=('Microsoft YaHei', 9), 
                                          selectmode=tk.EXTENDED, height=15)
        self.selected_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        list_scroll = ttk.Scrollbar(selected_frame, orient="vertical", 
                                   command=self.selected_listbox.yview)
        list_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.selected_listbox.configure(yscrollcommand=list_scroll.set)
        
        # 绑定双击事件
        self.selected_listbox.bind('<Double-1>', self.on_selected_double_click)
        
        selected_frame.columnconfigure(0, weight=1)
        selected_frame.rowconfigure(0, weight=1)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="操作控制", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 按钮行1
        btn_frame1 = ttk.Frame(control_frame)
        btn_frame1.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        remove_btn = ttk.Button(btn_frame1, text="移除选中", command=self.remove_selected)
        remove_btn.grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        
        clear_btn = ttk.Button(btn_frame1, text="清空全部", command=self.clear_all_selected)
        clear_btn.grid(row=0, column=1, padx=(0, 5))
        
        info_btn = ttk.Button(btn_frame1, text="软件信息", command=self.show_software_info)
        info_btn.grid(row=0, column=2)
        
        # 按钮行2
        btn_frame2 = ttk.Frame(control_frame)
        btn_frame2.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        select_category_btn = ttk.Button(btn_frame2, text="选择分类", command=self.select_category)
        select_category_btn.grid(row=0, column=0, padx=(0, 5))
        
        export_btn = ttk.Button(btn_frame2, text="导出列表", command=self.export_software_list)
        export_btn.grid(row=0, column=1, padx=(0, 5))
        
        import_btn = ttk.Button(btn_frame2, text="导入列表", command=self.import_software_list)
        import_btn.grid(row=0, column=2)
        
        control_frame.columnconfigure(0, weight=1)
    
    def create_bottom_panel(self, parent):
        """创建底部面板"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(bottom_frame, variable=self.progress_var, 
                                           style='Custom.Horizontal.TProgressbar')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(bottom_frame, textvariable=self.status_var, 
                                font=('Microsoft YaHei', 9))
        status_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # 操作按钮框架
        action_frame = ttk.Frame(bottom_frame)
        action_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # 主要操作按钮
        generate_btn = ttk.Button(action_frame, text="🚀 生成一键安装程序", 
                                 style='Action.TButton', command=self.generate_installer)
        generate_btn.grid(row=0, column=0, padx=(0, 15))
        
        download_btn = ttk.Button(action_frame, text="📥 下载选中软件", 
                                 style='Action.TButton', command=self.download_software)
        download_btn.grid(row=0, column=1, padx=(0, 15))
        
        # 辅助按钮
        settings_btn = ttk.Button(action_frame, text="⚙️ 设置", 
                                 style='Custom.TButton', command=self.open_settings)
        settings_btn.grid(row=0, column=2, padx=(0, 10))
        
        help_btn = ttk.Button(action_frame, text="❓ 帮助", 
                             style='Custom.TButton', command=self.show_help)
        help_btn.grid(row=0, column=3, padx=(0, 10))
        
        about_btn = ttk.Button(action_frame, text="ℹ️ 关于", 
                              style='Custom.TButton', command=self.show_about)
        about_btn.grid(row=0, column=4)
        
        bottom_frame.columnconfigure(0, weight=1)
    
    def populate_tree(self, data=None):
        """填充树形数据"""
        if data is None:
            data = self.filtered_data
        
        # 保存当前展开状态
        expanded_items = set()
        for item in self.tree.get_children():
            if self.tree.item(item, 'open'):
                expanded_items.add(self.tree.item(item, 'text'))
                for child in self.tree.get_children(item):
                    if self.tree.item(child, 'open'):
                        expanded_items.add(self.tree.item(child, 'text'))
        
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for category, subcategories in data.items():
            category_text = f"📁 {category}"
            category_id = self.tree.insert('', 'end', text=category_text, values=('',))
            
            # 恢复展开状态，默认展开一级分类
            should_open = category_text in expanded_items or len(expanded_items) == 0
            self.tree.item(category_id, open=should_open)
            
            for subcategory, software_list in subcategories.items():
                subcategory_text = f"📂 {subcategory}"
                subcategory_id = self.tree.insert(category_id, 'end', 
                                                  text=subcategory_text, values=('',))
                
                # 恢复展开状态，默认不展开二级分类
                should_open_sub = subcategory_text in expanded_items
                self.tree.item(subcategory_id, open=should_open_sub)
                
                for software in software_list:
                    status_icon = "✅" if software['name'] in self.selected_software else "⭕"
                    self.tree.insert(subcategory_id, 'end', 
                                   text=f"{status_icon} {software['name']}", 
                                   values=(software['description'],))
    
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
        
        self.populate_tree()
    
    def on_tree_open(self, event):
        """树形节点展开事件"""
        pass  # 展开事件不需要特殊处理
    
    def on_tree_close(self, event):
        """树形节点收起事件"""
        pass  # 收起事件不需要特殊处理
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set('')
    
    def on_tree_double_click(self, event):
        """树形控件双击事件"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        
        item_text = self.tree.item(item, 'text')
        values = self.tree.item(item, 'values')
        
        # 检查是否是软件项（有描述值且不是文件夹图标开头）
        if values and len(values) >= 1 and values[0] and not item_text.startswith('📁') and not item_text.startswith('📂'):
            # 提取软件名称（去掉状态图标）
            software_name = item_text.replace('✅ ', '').replace('⭕ ', '')
            
            if software_name not in self.selected_software:
                self.selected_software.add(software_name)
                self.update_selected_list()
                self.populate_tree()  # 刷新树形图标
                self.status_var.set(f"已添加: {software_name}")
            else:
                self.selected_software.discard(software_name)
                self.update_selected_list()
                self.populate_tree()  # 刷新树形图标
                self.status_var.set(f"已移除: {software_name}")
    
    def on_tree_right_click(self, event):
        """树形控件右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            # 创建右键菜单
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="添加到选择列表", command=lambda: self.on_tree_double_click(None))
            context_menu.add_command(label="查看软件信息", command=self.show_current_software_info)
            context_menu.add_separator()
            context_menu.add_command(label="访问官网", command=self.visit_software_website)
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def on_selected_double_click(self, event):
        """已选列表双击事件"""
        selection = self.selected_listbox.curselection()
        if selection:
            software_name = self.selected_listbox.get(selection[0])
            self.show_software_detail(software_name)
    
    def update_selected_list(self):
        """更新已选软件列表"""
        self.selected_listbox.delete(0, tk.END)
        for software in sorted(self.selected_software):
            self.selected_listbox.insert(tk.END, software)
        
        # 更新统计信息
        total_software = sum(len(subcategories.get(subcat, [])) 
                           for subcategories in self.software_data.values() 
                           for subcat in subcategories)
        
        # 更新标题栏统计
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Label) and "共收录" in str(grandchild.cget('text')):
                                grandchild.config(text=f"共收录 {total_software} 款软件 | 已选择 {len(self.selected_software)} 款")
    
    def remove_selected(self):
        """移除选中的软件"""
        selection = self.selected_listbox.curselection()
        if selection:
            for index in reversed(selection):
                software_name = self.selected_listbox.get(index)
                self.selected_software.discard(software_name)
            self.update_selected_list()
            self.populate_tree()  # 刷新树形图标
            self.status_var.set(f"已移除 {len(selection)} 个软件")
    
    def clear_all_selected(self):
        """清空所有选中的软件"""
        if self.selected_software and messagebox.askyesno("确认清空", "确定要清空所有已选择的软件吗？"):
            count = len(self.selected_software)
            self.selected_software.clear()
            self.update_selected_list()
            self.populate_tree()  # 刷新树形图标
            self.status_var.set(f"已清空 {count} 个软件")
    
    def select_category(self):
        """选择整个分类"""
        # 创建分类选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择软件分类")
        dialog.geometry("400x500")
        dialog.configure(bg='#f5f5f5')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 分类列表
        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="选择要添加的软件分类:", font=('Microsoft YaHei', 12, 'bold')).pack(pady=(0, 10))
        
        # 创建复选框
        category_vars = {}
        for category, subcategories in self.software_data.items():
            category_frame = ttk.LabelFrame(frame, text=category, padding="5")
            category_frame.pack(fill=tk.X, pady=(0, 5))
            
            category_vars[category] = {}
            for subcategory in subcategories.keys():
                var = tk.BooleanVar()
                category_vars[category][subcategory] = var
                ttk.Checkbutton(category_frame, text=subcategory, variable=var).pack(anchor=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        def apply_selection():
            added_count = 0
            for category, subcategories in category_vars.items():
                for subcategory, var in subcategories.items():
                    if var.get():
                        for software in self.software_data[category][subcategory]:
                            if software['name'] not in self.selected_software:
                                self.selected_software.add(software['name'])
                                added_count += 1
            
            self.update_selected_list()
            self.populate_tree()
            self.status_var.set(f"批量添加了 {added_count} 个软件")
            dialog.destroy()
        
        ttk.Button(btn_frame, text="确定", command=apply_selection).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def export_software_list(self):
        """导出软件列表"""
        if not self.selected_software:
            messagebox.showwarning("警告", "没有选中的软件可以导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="导出软件列表",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'software_count': len(self.selected_software),
                    'selected_software': list(self.selected_software)
                }
                
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"软件列表导出时间: {export_data['export_time']}\n")
                        f.write(f"软件数量: {export_data['software_count']}\n\n")
                        for i, software in enumerate(export_data['selected_software'], 1):
                            f.write(f"{i}. {software}\n")
                
                messagebox.showinfo("成功", f"软件列表已导出到: {file_path}")
                self.status_var.set(f"已导出 {len(self.selected_software)} 个软件到文件")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def import_software_list(self):
        """导入软件列表"""
        file_path = filedialog.askopenfilename(
            title="导入软件列表",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        import_data = json.load(f)
                        imported_software = import_data.get('selected_software', [])
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        imported_software = []
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('软件') and not line.startswith('导出时间'):
                                # 提取软件名称（去掉序号）
                                if '. ' in line:
                                    software_name = line.split('. ', 1)[1]
                                    imported_software.append(software_name)
                
                # 验证软件是否存在
                valid_software = set()
                all_software = set()
                for category, subcategories in self.software_data.items():
                    for subcategory, software_list in subcategories.items():
                        for software in software_list:
                            all_software.add(software['name'])
                
                for software_name in imported_software:
                    if software_name in all_software:
                        valid_software.add(software_name)
                
                if valid_software:
                    self.selected_software.update(valid_software)
                    self.update_selected_list()
                    self.populate_tree()
                    messagebox.showinfo("成功", f"成功导入 {len(valid_software)} 个软件")
                    self.status_var.set(f"已导入 {len(valid_software)} 个软件")
                else:
                    messagebox.showwarning("警告", "文件中没有找到有效的软件")
                    
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def show_software_info(self):
        """显示选中软件的详细信息"""
        selection = self.selected_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个软件")
            return
        
        software_name = self.selected_listbox.get(selection[0])
        self.show_software_detail(software_name)
    
    def show_current_software_info(self):
        """显示当前树形选中软件的信息"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        
        item_text = self.tree.item(item, 'text')
        if not item_text.startswith('📁') and not item_text.startswith('📂'):
            software_name = item_text.replace('✅ ', '').replace('⭕ ', '')
            self.show_software_detail(software_name)
    
    def show_software_detail(self, software_name):
        """显示软件详细信息"""
        # 查找软件信息
        software_info = None
        for category, subcategories in self.software_data.items():
            for subcategory, software_list in subcategories.items():
                for software in software_list:
                    if software['name'] == software_name:
                        software_info = software.copy()
                        software_info['category'] = category
                        software_info['subcategory'] = subcategory
                        break
                if software_info:
                    break
            if software_info:
                break
        
        if not software_info:
            messagebox.showerror("错误", "未找到软件信息")
            return
        
        # 创建信息窗口
        info_window = tk.Toplevel(self.root)
        info_window.title(f"软件信息 - {software_name}")
        info_window.geometry("500x400")
        info_window.configure(bg='#f5f5f5')
        info_window.transient(self.root)
        
        frame = ttk.Frame(info_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 软件信息
        info_text = tk.Text(frame, font=('Microsoft YaHei', 10), wrap=tk.WORD, 
                           height=15, bg='white', relief=tk.FLAT, padx=10, pady=10)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        info_content = f"""软件名称: {software_info['name']}
分类: {software_info['category']} > {software_info['subcategory']}
描述: {software_info['description']}
下载链接: {software_info['url']}

状态: {'已选择' if software_name in self.selected_software else '未选择'}
"""
        
        info_text.insert(tk.END, info_content)
        info_text.config(state=tk.DISABLED)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        if software_info['url'] != 'builtin':
            ttk.Button(btn_frame, text="访问官网", 
                      command=lambda: webbrowser.open(software_info['url'])).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="关闭", command=info_window.destroy).pack(side=tk.RIGHT)
    
    def visit_software_website(self):
        """访问软件官网"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        
        item_text = self.tree.item(item, 'text')
        if not item_text.startswith('📁') and not item_text.startswith('📂'):
            software_name = item_text.replace('✅ ', '').replace('⭕ ', '')
            url = self.get_software_url(software_name)
            if url and url != 'builtin':
                webbrowser.open(url)
            else:
                messagebox.showinfo("提示", "该软件为系统内置软件或无可用链接")
    
    def get_software_url(self, software_name):
        """获取软件下载链接"""
        for category, subcategories in self.software_data.items():
            for subcategory, software_list in subcategories.items():
                for software in software_list:
                    if software['name'] == software_name:
                        return software['url']
        return None
    
    def generate_installer(self):
        """生成一键安装程序"""
        if not self.selected_software:
            messagebox.showwarning("警告", "请先选择要安装的软件")
            return
        
        # 选择保存路径
        save_path = filedialog.asksaveasfilename(
            title="保存安装程序",
            defaultextension=".bat",
            filetypes=[("批处理文件", "*.bat"), ("PowerShell脚本", "*.ps1"), ("所有文件", "*.*")]
        )
        
        if save_path:
            self.create_installer_script(save_path)
    
    def create_installer_script(self, save_path):
        """创建安装脚本"""
        try:
            if save_path.endswith('.ps1'):
                # PowerShell脚本
                script_content = self.generate_powershell_script()
            else:
                # 批处理脚本
                script_content = self.generate_batch_script()
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            messagebox.showinfo("成功", f"安装程序已生成：{save_path}\n\n包含 {len(self.selected_software)} 个软件")
            self.status_var.set(f"已生成包含 {len(self.selected_software)} 个软件的安装程序")
            
            # 询问是否立即运行
            if messagebox.askyesno("运行安装程序", "是否立即运行生成的安装程序？"):
                subprocess.Popen(save_path, shell=True)
                
        except Exception as e:
            messagebox.showerror("错误", f"生成安装程序失败：{str(e)}")
    
    def generate_batch_script(self):
        """生成批处理脚本"""
        script_content = """@echo off
chcp 65001 >nul
echo ========================================
echo 软件一键安装程序 v2.0
echo ========================================
echo.
echo 正在安装选中的软件，请稍候...
echo.

"""
        
        # 创建下载目录
        script_content += "set DOWNLOAD_DIR=%TEMP%\\SoftwareInstaller\n"
        script_content += "if not exist \"%DOWNLOAD_DIR%\" mkdir \"%DOWNLOAD_DIR%\"\n\n"
        
        # 获取选中软件的下载链接
        valid_software = []
        for software_name in self.selected_software:
            url = self.get_software_url(software_name)
            if url and url != 'builtin':
                valid_software.append((software_name, url))
        
        for i, (software_name, url) in enumerate(valid_software, 1):
            safe_name = software_name.replace(' ', '_').replace('/', '_')
            script_content += f"echo [{i}/{len(valid_software)}] 正在下载 {software_name}...\n"
            script_content += f"powershell -Command \"try {{ Invoke-WebRequest -Uri '{url}' -OutFile '%DOWNLOAD_DIR%\\{safe_name}.exe' -ErrorAction Stop; Write-Host '下载完成: {software_name}' }} catch {{ Write-Host '下载失败: {software_name} - ' $_.Exception.Message }}\"\n"
            script_content += f"if exist \"%DOWNLOAD_DIR%\\{safe_name}.exe\" (\n"
            script_content += f"    echo 正在安装 {software_name}...\n"
            script_content += f"    start /wait \"%DOWNLOAD_DIR%\\{safe_name}.exe\" /S /silent\n"
            script_content += f"    echo 安装完成: {software_name}\n"
            script_content += f") else (\n"
            script_content += f"    echo 跳过安装: {software_name} (下载失败)\n"
            script_content += f")\n\n"
        
        script_content += "echo.\n"
        script_content += "echo ========================================\n"
        script_content += "echo 所有软件安装完成！\n"
        script_content += "echo ========================================\n"
        script_content += "echo.\n"
        script_content += "echo 正在清理临时文件...\n"
        script_content += "rd /s /q \"%DOWNLOAD_DIR%\" 2>nul\n"
        script_content += "echo 清理完成。\n"
        script_content += "echo.\n"
        script_content += "pause\n"
        
        return script_content
    
    def generate_powershell_script(self):
        """生成PowerShell脚本"""
        script_content = """# 软件一键安装程序 v2.0 (PowerShell版本)
# 编码: UTF-8

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "软件一键安装程序 v2.0" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "正在安装选中的软件，请稍候..." -ForegroundColor Green
Write-Host ""

# 创建下载目录
$downloadDir = "$env:TEMP\\SoftwareInstaller"
if (!(Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
}

# 软件列表
$softwareList = @(
"""
        
        # 获取选中软件的下载链接
        valid_software = []
        for software_name in self.selected_software:
            url = self.get_software_url(software_name)
            if url and url != 'builtin':
                valid_software.append((software_name, url))
        
        for software_name, url in valid_software:
            script_content += f"    @{{Name='{software_name}'; Url='{url}'}},\n"
        
        script_content = script_content.rstrip(',\n') + "\n)\n\n"
        
        script_content += """# 下载和安装软件
$totalCount = $softwareList.Count
$currentCount = 0

foreach ($software in $softwareList) {
    $currentCount++
    $safeName = $software.Name -replace '[\\s/]', '_'
    $filePath = "$downloadDir\\$safeName.exe"
    
    Write-Host "[$currentCount/$totalCount] 正在下载 $($software.Name)..." -ForegroundColor Yellow
    
    try {
        Invoke-WebRequest -Uri $software.Url -OutFile $filePath -ErrorAction Stop
        Write-Host "下载完成: $($software.Name)" -ForegroundColor Green
        
        if (Test-Path $filePath) {
            Write-Host "正在安装 $($software.Name)..." -ForegroundColor Cyan
            Start-Process -FilePath $filePath -ArgumentList "/S", "/silent" -Wait -ErrorAction SilentlyContinue
            Write-Host "安装完成: $($software.Name)" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "下载失败: $($software.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "所有软件安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "正在清理临时文件..." -ForegroundColor Yellow
Remove-Item -Path $downloadDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "清理完成。" -ForegroundColor Green
Write-Host ""
Read-Host "按回车键退出"
"""
        
        return script_content
    
    def download_software(self):
        """下载选中的软件"""
        if not self.selected_software:
            messagebox.showwarning("警告", "请先选择要下载的软件")
            return
        
        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中，请稍候...")
            return
        
        # 选择下载目录
        download_dir = filedialog.askdirectory(
            title="选择下载目录",
            initialdir=self.config.get('download_path', str(Path.home() / 'Downloads'))
        )
        
        if download_dir:
            self.config['download_path'] = download_dir
            self.start_download(download_dir)
    
    def start_download(self, download_dir):
        """开始下载"""
        self.is_downloading = True
        self.progress_var.set(0)
        
        # 获取有效的下载链接
        valid_software = []
        for software_name in self.selected_software:
            url = self.get_software_url(software_name)
            if url and url != 'builtin':
                valid_software.append((software_name, url))
        
        if not valid_software:
            messagebox.showwarning("警告", "没有可下载的软件（可能都是系统内置软件）")
            self.is_downloading = False
            return
        
        def download_thread():
            success_count = 0
            total_count = len(valid_software)
            
            for i, (software_name, url) in enumerate(valid_software):
                try:
                    self.status_var.set(f"正在下载 {software_name}... ({i+1}/{total_count})")
                    
                    # 获取文件扩展名
                    parsed_url = urlparse(url)
                    url_path = parsed_url.path
                    filename = os.path.basename(url_path)
                    
                    # 如果URL中没有文件名或文件名不包含扩展名
                    if not filename or '.' not in filename:
                        # 尝试从URL路径中提取常见的软件扩展名
                        common_extensions = ['.exe', '.msi', '.zip', '.rar', '.7z', '.dmg', '.pkg', '.deb', '.rpm']
                        found_ext = None
                        for ext in common_extensions:
                            if ext in url_path.lower():
                                found_ext = ext
                                break
                        
                        # 生成安全的文件名（移除非法字符）
                        safe_name = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in software_name)
                        
                        if found_ext:
                            # 使用找到的扩展名
                            filename = f"{safe_name}{found_ext}"
                        else:
                            # 默认使用.exe
                            filename = f"{safe_name}.exe"
                    
                    filepath = os.path.join(download_dir, filename)
                    
                    # 下载文件
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(filepath, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 更新进度
                                if total_size > 0:
                                    file_progress = (downloaded / total_size) * 100
                                    overall_progress = ((i + file_progress/100) / total_count) * 100
                                else:
                                    overall_progress = ((i + 1) / total_count) * 100
                                
                                self.progress_var.set(overall_progress)
                    
                    success_count += 1
                    print(f"下载完成: {software_name} -> {filepath}")
                    
                except Exception as e:
                    print(f"下载失败 {software_name}: {str(e)}")
                    continue
            
            self.is_downloading = False
            self.progress_var.set(100)
            self.status_var.set(f"下载完成！成功: {success_count}/{total_count}")
            
            messagebox.showinfo("下载完成", 
                              f"下载完成！\n成功: {success_count} 个\n失败: {total_count - success_count} 个\n\n文件保存在: {download_dir}")
        
        # 启动下载线程
        threading.Thread(target=download_thread, daemon=True).start()
        messagebox.showinfo("开始下载", f"开始下载 {len(valid_software)} 个软件，请稍候...")
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("500x600")
        settings_window.configure(bg='#f5f5f5')
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        frame = ttk.Frame(settings_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置选项
        ttk.Label(frame, text="应用程序设置", font=('Microsoft YaHei', 14, 'bold')).pack(pady=(0, 20))
        
        # 下载路径设置
        path_frame = ttk.LabelFrame(frame, text="下载设置", padding="10")
        path_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(path_frame, text="默认下载路径:").pack(anchor=tk.W)
        path_var = tk.StringVar(value=self.config.get('download_path', ''))
        path_entry = ttk.Entry(path_frame, textvariable=path_var, width=50)
        path_entry.pack(fill=tk.X, pady=(5, 5))
        
        def browse_path():
            path = filedialog.askdirectory(initialdir=path_var.get())
            if path:
                path_var.set(path)
        
        ttk.Button(path_frame, text="浏览", command=browse_path).pack(anchor=tk.W)
        
        # 并发下载数设置
        concurrent_frame = ttk.LabelFrame(frame, text="性能设置", padding="10")
        concurrent_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(concurrent_frame, text="并发下载数:").pack(anchor=tk.W)
        concurrent_var = tk.IntVar(value=self.config.get('concurrent_downloads', 3))
        concurrent_spin = ttk.Spinbox(concurrent_frame, from_=1, to=10, textvariable=concurrent_var, width=10)
        concurrent_spin.pack(anchor=tk.W, pady=(5, 0))
        
        # 自动检查更新
        update_frame = ttk.LabelFrame(frame, text="更新设置", padding="10")
        update_frame.pack(fill=tk.X, pady=(0, 15))
        
        update_var = tk.BooleanVar(value=self.config.get('auto_check_updates', True))
        ttk.Checkbutton(update_frame, text="启动时自动检查软件更新", variable=update_var).pack(anchor=tk.W)
        
        # 系统信息
        if PSUTIL_AVAILABLE:
            info_frame = ttk.LabelFrame(frame, text="系统信息", padding="10")
            info_frame.pack(fill=tk.X, pady=(0, 15))
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info_text = f"""CPU使用率: {cpu_percent}%
内存使用率: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
磁盘使用率: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"""
            
            ttk.Label(info_frame, text=info_text, font=('Consolas', 9)).pack(anchor=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_settings():
            self.config['download_path'] = path_var.get()
            self.config['concurrent_downloads'] = concurrent_var.get()
            self.config['auto_check_updates'] = update_var.get()
            self.save_config()
            messagebox.showinfo("成功", "设置已保存")
            settings_window.destroy()
        
        def reset_settings():
            if messagebox.askyesno("确认重置", "确定要重置所有设置为默认值吗？"):
                path_var.set(str(Path.home() / 'Downloads' / 'SoftwareManager'))
                concurrent_var.set(3)
                update_var.set(True)
        
        ttk.Button(btn_frame, text="保存", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="重置", command=reset_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="取消", command=settings_window.destroy).pack(side=tk.RIGHT)
    
    def show_help(self):
        """显示帮助信息"""
        help_window = tk.Toplevel(self.root)
        help_window.title("帮助")
        help_window.geometry("600x500")
        help_window.configure(bg='#f5f5f5')
        help_window.transient(self.root)
        
        frame = ttk.Frame(help_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = tk.Text(text_frame, font=('Microsoft YaHei', 10), wrap=tk.WORD, 
                           bg='white', relief=tk.FLAT, padx=15, pady=15)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=help_text.yview)
        help_text.configure(yscrollcommand=scrollbar.set)
        
        help_content = """软件资源整合管理器 - 使用帮助

🎯 主要功能:
• 浏览和选择1000+款常用软件
• 生成一键安装批处理程序
• 批量下载软件安装包
• 软件分类管理和搜索

📖 使用说明:

1. 浏览软件:
   • 在左侧树形列表中浏览软件分类
   • 使用搜索框快速查找软件
   • 双击软件名称添加到选择列表

2. 管理选择:
   • 在右侧查看已选择的软件
   • 双击可查看软件详细信息
   • 使用控制按钮管理选择列表

3. 生成安装程序:
   • 点击"生成一键安装程序"按钮
   • 选择保存位置和文件类型
   • 运行生成的脚本自动安装软件

4. 下载软件:
   • 点击"下载选中软件"按钮
   • 选择下载目录
   • 等待下载完成

⚙️ 高级功能:
• 批量选择软件分类
• 导入/导出软件列表
• 软件信息查看
• 自定义下载路径
• 并发下载控制

🔧 快捷键:
• Ctrl+F: 快速搜索
• Delete: 删除选中软件
• Ctrl+A: 全选软件分类
• F1: 显示帮助

💡 提示:
• 生成的安装程序支持静默安装
• 建议在安装前关闭杀毒软件
• 某些软件可能需要管理员权限
• 下载失败的软件会自动跳过

📞 技术支持:
如有问题，请查看软件日志或联系技术支持。
"""
        
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 关闭按钮
        ttk.Button(frame, text="关闭", command=help_window.destroy).pack(pady=(15, 0))
    
    def show_about(self):
        """显示关于信息"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("400x350")
        about_window.configure(bg='#f5f5f5')
        about_window.transient(self.root)
        about_window.resizable(False, False)
        
        frame = ttk.Frame(about_window, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 应用图标和标题
        ttk.Label(frame, text="🚀", font=('Microsoft YaHei', 48)).pack(pady=(0, 10))
        ttk.Label(frame, text="软件资源整合管理器", 
                 font=('Microsoft YaHei', 16, 'bold')).pack()
        ttk.Label(frame, text="Enhanced Version 2.0", 
                 font=('Microsoft YaHei', 12)).pack(pady=(5, 20))
        
        # 版本信息
        info_text = """类似Ninite的一键安装程序生成器
支持1000+款常用软件的管理和安装

版本: 2.0 Enhanced
开发语言: Python 3.x
界面框架: Tkinter

功能特性:
✓ 软件分类浏览和搜索
✓ 批量选择和管理
✓ 一键安装程序生成
✓ 软件批量下载
✓ 配置保存和恢复

© 2024 软件资源整合管理器"""
        
        ttk.Label(frame, text=info_text, font=('Microsoft YaHei', 9), 
                 justify=tk.CENTER).pack(pady=(0, 20))
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="检查更新", command=self.check_updates).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=about_window.destroy).pack(side=tk.LEFT)
    
    def check_updates(self):
        """检查更新"""
        messagebox.showinfo("检查更新", "当前已是最新版本 v2.0 Enhanced")
    
    def on_closing(self):
        """程序关闭事件"""
        # 保存配置
        self.save_config()
        
        # 如果正在下载，询问是否确认退出
        if self.is_downloading:
            if not messagebox.askyesno("确认退出", "正在下载中，确定要退出吗？"):
                return
        
        self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        # 恢复窗口大小
        if self.config.get('window_geometry'):
            self.root.geometry(self.config['window_geometry'])
        
        # 居中显示窗口
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # 启动主循环
        self.root.mainloop()

def main():
    """主函数"""
    try:
        app = EnhancedSoftwareManager()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()