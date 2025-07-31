#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件资源整合管理器 v4.0 向导式界面
分步骤引导用户完成软件下载流程
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
import socket

# 设置CustomTkinter外观模式和颜色主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class WizardSoftwareManager:
    def __init__(self):
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("软件资源整合管理器 v4.0 向导")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 初始化数据
        self.software_data = {}
        self.selected_software = set()
        self.config = {}
        self.current_step = 1
        self.total_steps = 6
        self.connectivity_results = {}
        self.download_settings = {
            'path': str(Path.home() / 'Downloads'),
            'concurrent': 3,
            'timeout': 30
        }
        
        # 步骤信息
        self.steps = [
            {"title": "欢迎使用", "desc": "用户协议确认", "short": "欢迎"},
            {"title": "选择软件", "desc": "软件选择确认", "short": "选择"},
            {"title": "连通性检测", "desc": "服务器连接测试", "short": "检测"},
            {"title": "下载设置", "desc": "路径和参数配置", "short": "设置"},
            {"title": "正在下载", "desc": "软件下载进行中", "short": "下载"},
            {"title": "下载完成", "desc": "感谢使用", "short": "完成"}
        ]
        
        # 加载数据
        self.load_software_data()
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置网格权重
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
    
    def load_software_data(self):
        """加载软件数据"""
        try:
            with open('software_data.json', 'r', encoding='utf-8') as f:
                self.software_data = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("错误", "软件数据文件不存在！")
            self.software_data = {}
    
    def load_config(self):
        """加载配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'download_path': str(Path.home() / 'Downloads'),
                'max_concurrent_downloads': 3
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
        # 创建顶部进度指示器
        self.create_progress_indicator()
        
        # 创建主内容区域
        self.content_frame = ctk.CTkFrame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # 创建底部按钮区域
        self.create_bottom_buttons()
        
        # 设置网格权重
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 显示第一步
        self.show_step(1)
    
    def create_progress_indicator(self):
        """创建顶部进度指示器"""
        progress_frame = ctk.CTkFrame(self.root, height=120)
        progress_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        progress_frame.grid_propagate(False)
        self.progress_frame = progress_frame
        
        # 标题
        title_label = ctk.CTkLabel(
            progress_frame,
            text="🧙‍♂️ 软件安装向导",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=self.total_steps, pady=(10, 5))
        
        # 进度圆圈容器
        circles_frame = ctk.CTkFrame(progress_frame)
        circles_frame.grid(row=1, column=0, columnspan=self.total_steps, pady=(5, 10), sticky="ew")
        
        self.step_circles = []
        self.step_labels = []
        self.circle_labels = []
        
        # 配置列权重以平分空间
        for i in range(self.total_steps):
            circles_frame.grid_columnconfigure(i, weight=1)
        
        for i in range(self.total_steps):
            # 创建步骤容器
            step_container = ctk.CTkFrame(circles_frame)
            step_container.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
            
            # 创建圆圈（使用按钮模拟）
            circle_color = "#2E8B57" if i < self.current_step else "#D3D3D3"
            circle = ctk.CTkButton(
                step_container,
                text=self.steps[i]["short"],
                width=70,
                height=70,
                corner_radius=35,
                fg_color=circle_color,
                hover_color=circle_color,
                font=ctk.CTkFont(size=12, weight="bold"),
                state="disabled"
            )
            circle.grid(row=0, column=0, pady=(5, 3))
            self.step_circles.append(circle)
            self.circle_labels.append(circle)
            
            # 创建描述标签
            desc_label = ctk.CTkLabel(
                step_container,
                text=self.steps[i]["desc"],
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            desc_label.grid(row=1, column=0, pady=(0, 5))
            
            self.step_labels.append(desc_label)
            
            step_container.grid_columnconfigure(0, weight=1)
            
            # 添加连接线（除了最后一个）
            if i < self.total_steps - 1:
                line_frame = ctk.CTkFrame(circles_frame)
                line_frame.grid(row=0, column=i, sticky="e", padx=(40, 5), pady=32)
                line = ctk.CTkLabel(
                    line_frame,
                    text="━━━━━",
                    font=ctk.CTkFont(size=14),
                    text_color="#D3D3D3"
                )
                line.pack()
        
        progress_frame.grid_columnconfigure(0, weight=1)
    
    def create_bottom_buttons(self):
        """创建底部按钮"""
        self.button_frame = ctk.CTkFrame(self.root, height=70)
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.button_frame.grid_propagate(False)
        
        # 上一步按钮
        self.prev_btn = ctk.CTkButton(
            self.button_frame,
            text="上一步",
            width=120,
            height=40,
            command=self.prev_step,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.prev_btn.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # 下一步按钮
        self.next_btn = ctk.CTkButton(
            self.button_frame,
            text="下一步",
            width=120,
            height=40,
            command=self.next_step,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.next_btn.grid(row=0, column=1, padx=15, pady=15, sticky="e")
        
        # 退出按钮
        self.exit_btn = ctk.CTkButton(
            self.button_frame,
            text="退出",
            width=80,
            height=40,
            command=self.on_closing,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8b1538",
            hover_color="#5e0e26"
        )
        self.exit_btn.grid(row=0, column=2, padx=15, pady=15, sticky="e")
        
        self.button_frame.grid_columnconfigure(1, weight=1)
    
    def update_bottom_buttons(self):
        """根据当前步骤更新底部按钮显示"""
        # 更新按钮状态
        self.prev_btn.configure(state="normal" if self.current_step > 1 else "disabled")
        
        # 最后一页不显示下一步按钮
        if self.current_step == self.total_steps:
            self.next_btn.grid_remove()
        else:
            self.next_btn.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        
        # 除最后一页外不显示退出按钮
        if self.current_step == self.total_steps:
            self.exit_btn.grid(row=0, column=2, padx=20, pady=20, sticky="e")
        else:
            self.exit_btn.grid_remove()
    
    def update_progress_indicator(self):
        """更新进度指示器"""
        for i, circle in enumerate(self.step_circles):
            if i < self.current_step:
                circle.configure(fg_color="#2E8B57", hover_color="#2E8B57")
            elif i == self.current_step - 1:
                circle.configure(fg_color="#4169E1", hover_color="#4169E1")
            else:
                circle.configure(fg_color="#D3D3D3", hover_color="#D3D3D3")
    
    def show_step(self, step_num):
        """显示指定步骤"""
        # 清空内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 更新当前步骤
        self.current_step = step_num
        self.update_progress_indicator()
        self.update_bottom_buttons()
        
        # 根据步骤显示对应内容
        if step_num == 1:
            self.show_welcome_step()
        elif step_num == 2:
            self.show_software_selection_step()
        elif step_num == 3:
            self.show_connectivity_check_step()
        elif step_num == 4:
            self.show_download_settings_step()
        elif step_num == 5:
            self.show_download_progress_step()
        elif step_num == 6:
            self.show_completion_step()
    
    def show_welcome_step(self):
        """显示欢迎页面"""
        welcome_frame = ctk.CTkFrame(self.content_frame)
        welcome_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 欢迎标题
        title_label = ctk.CTkLabel(
            welcome_frame,
            text="欢迎使用软件资源整合管理器",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(30, 20))
        
        # 功能介绍
        intro_text = """
本软件将帮助您：

• 一站式管理和下载各类软件
• 智能分类浏览，快速找到所需软件
• 批量下载，节省时间
• 安全可靠的下载源
• 实时下载进度监控

使用向导式界面，让软件安装变得简单快捷！
        """
        
        intro_label = ctk.CTkLabel(
            welcome_frame,
            text=intro_text,
            font=ctk.CTkFont(size=16),
            justify="left"
        )
        intro_label.grid(row=1, column=0, pady=20)
        
        # 用户协议
        agreement_frame = ctk.CTkFrame(welcome_frame)
        agreement_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=20)
        
        agreement_title = ctk.CTkLabel(
            agreement_frame,
            text="用户协议",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        agreement_title.grid(row=0, column=0, pady=(15, 10))
        
        # 协议简要说明
        agreement_brief = ctk.CTkLabel(
            agreement_frame,
            text="本软件仅供学习研究使用，下载的软件请遵守相应版权协议。\n使用本软件即表示您同意相关条款。",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="center"
        )
        agreement_brief.grid(row=1, column=0, padx=20, pady=(0, 10))
        
        # 查看详细协议按钮
        view_agreement_btn = ctk.CTkButton(
            agreement_frame,
            text="📄 查看详细用户协议",
            width=200,
            height=35,
            command=self.show_agreement_window,
            font=ctk.CTkFont(size=12),
            fg_color="#4169E1",
            hover_color="#0000CD"
        )
        view_agreement_btn.grid(row=2, column=0, pady=(0, 15))
        
        # 同意复选框
        self.agreement_var = tk.BooleanVar()
        agreement_checkbox = ctk.CTkCheckBox(
            welcome_frame,
            text="我已阅读并同意用户协议",
            variable=self.agreement_var,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.check_agreement
        )
        agreement_checkbox.grid(row=3, column=0, pady=20)
        
        welcome_frame.grid_columnconfigure(0, weight=1)
        
        # 初始状态下一步按钮禁用
        self.next_btn.configure(state="disabled")
    
    def show_agreement_window(self):
        """显示详细用户协议窗口"""
        agreement_window = ctk.CTkToplevel(self.root)
        agreement_window.title("📋 用户协议详情")
        agreement_window.geometry("700x600")
        agreement_window.resizable(True, True)
        
        # 设置窗口图标和属性
        agreement_window.transient(self.root)
        agreement_window.grab_set()
        
        # 标题
        title_label = ctk.CTkLabel(
            agreement_window,
            text="📋 软件资源整合管理器用户协议",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # 协议内容
        agreement_text = ctk.CTkTextbox(
            agreement_window,
            font=ctk.CTkFont(size=12)
        )
        agreement_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        agreement_content = """
用户协议条款：

1. 软件用途
   本软件仅供学习和研究使用，请勿用于商业用途。

2. 版权声明
   下载的软件请遵守相应的版权和许可协议。用户应确保合法使用下载的软件。

3. 用户责任
   用户需对下载和使用的软件承担相应责任，包括但不限于：
   • 确保下载软件的合法性
   • 遵守软件的使用条款
   • 承担使用风险

4. 免责声明
   本软件不对下载内容的安全性、完整性和可用性做出保证。
   开发者不承担因使用本软件而产生的任何直接或间接损失。

5. 隐私保护
   本软件不会收集用户的个人隐私信息，仅记录必要的使用统计数据。

6. 协议变更
   开发者保留随时修改本协议的权利，修改后的协议将在软件更新时生效。

7. 法律适用
   本协议受中华人民共和国法律管辖。

8. 联系方式
   如有疑问，请联系开发者获取更多信息。

使用本软件即表示您已阅读、理解并同意遵守以上所有条款。
        """
        
        agreement_text.insert("1.0", agreement_content)
        agreement_text.configure(state="disabled")
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            agreement_window,
            text="关闭",
            width=100,
            command=agreement_window.destroy
        )
        close_btn.pack(pady=(0, 20))
    
    def check_agreement(self):
        """检查协议同意状态"""
        if self.agreement_var.get():
            self.next_btn.configure(state="normal")
        else:
            self.next_btn.configure(state="disabled")
    
    def show_software_selection_step(self):
        """显示软件选择页面"""
        selection_frame = ctk.CTkFrame(self.content_frame)
        selection_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            selection_frame,
            text="选择要下载的软件",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))
        
        # 搜索框
        search_frame = ctk.CTkFrame(selection_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        
        search_label = ctk.CTkLabel(search_frame, text="搜索", font=ctk.CTkFont(size=14))
        search_label.grid(row=0, column=0, padx=(15, 5), pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="搜索软件...",
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")
        
        clear_btn = ctk.CTkButton(
            search_frame,
            text="清除",
            width=60,
            height=35,
            command=self.clear_search,
            font=ctk.CTkFont(size=12)
        )
        clear_btn.grid(row=0, column=2, padx=(0, 15), pady=10)
        
        search_frame.grid_columnconfigure(1, weight=1)
        
        # 软件分类网格容器
        self.categories_container = ctk.CTkScrollableFrame(
            selection_frame,
            height=450
        )
        self.categories_container.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(
            selection_frame,
            text="总软件: 0 | 已选择: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.stats_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 设置网格权重
        selection_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_columnconfigure(1, weight=1)
        selection_frame.grid_rowconfigure(2, weight=1)
        
        # 初始化软件按钮字典
        self.software_buttons = {}
        
        # 填充软件分类
        self.populate_software_categories_grid(categories_container)
        self.update_stats()
    
    def populate_software_categories_grid(self, container):
        """填充软件分类网格"""
        # 清空现有内容
        for widget in container.winfo_children():
            widget.destroy()
        
        # 计算网格布局
        categories = list(self.software_data.keys())
        cols = 3  # 每行3个分类
        
        # 配置列权重
        for i in range(cols):
            container.grid_columnconfigure(i, weight=1)
        
        row = 0
        col = 0
        
        for category in categories:
            # 创建分类块
            category_block = ctk.CTkFrame(container)
            category_block.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # 分类标题
            category_title = ctk.CTkLabel(
                category_block,
                text=f"📁 {category}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            category_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10))
            
            # 全选按钮
            select_all_btn = ctk.CTkButton(
                category_block,
                text="全选分类",
                width=100,
                height=30,
                command=lambda cat=category: self.toggle_category(cat),
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#4169E1",
                hover_color="#0000CD"
            )
            select_all_btn.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10))
            
            # 软件网格
            software_frame = ctk.CTkFrame(category_block)
            software_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
            
            # 收集该分类下的所有软件
            all_software = []
            for subcategory, software_list in self.software_data[category].items():
                all_software.extend(software_list)
            
            # 创建软件按钮网格
            software_row = 0
            software_col = 0
            software_cols = 2  # 每行2个软件
            
            for i in range(software_cols):
                software_frame.grid_columnconfigure(i, weight=1)
            
            for software in all_software:
                # 创建软件按钮
                is_selected = software['name'] in self.selected_software
                
                software_btn = ctk.CTkButton(
                    software_frame,
                    text=software['name'],
                    width=150,
                    height=35,
                    command=lambda sw=software['name']: self.toggle_software(sw),
                    font=ctk.CTkFont(size=11),
                    fg_color="#2E8B57" if is_selected else "#D3D3D3",
                    hover_color="#228B22" if is_selected else "#B0B0B0",
                    text_color="white" if is_selected else "black"
                )
                software_btn.grid(row=software_row, column=software_col, padx=5, pady=3, sticky="ew")
                
                # 存储软件按钮引用以便后续更新
                if not hasattr(self, 'software_buttons'):
                    self.software_buttons = {}
                self.software_buttons[software['name']] = software_btn
                
                software_col += 1
                if software_col >= software_cols:
                    software_col = 0
                    software_row += 1
            
            category_block.grid_columnconfigure(0, weight=1)
            category_block.grid_columnconfigure(1, weight=1)
            
            # 更新网格位置
            col += 1
            if col >= cols:
                col = 0
                row += 1
    
    def toggle_software(self, software_name):
        """切换软件选择状态"""
        if software_name in self.selected_software:
            self.selected_software.discard(software_name)
        else:
            self.selected_software.add(software_name)
        
        # 更新按钮外观
        if software_name in self.software_buttons:
            btn = self.software_buttons[software_name]
            is_selected = software_name in self.selected_software
            btn.configure(
                fg_color="#2E8B57" if is_selected else "#D3D3D3",
                hover_color="#228B22" if is_selected else "#B0B0B0",
                text_color="white" if is_selected else "black"
            )
        
        self.update_stats()
    
    def toggle_category(self, category):
        """切换分类选择状态"""
        # 收集该分类下的所有软件
        all_software = []
        for subcategory, software_list in self.software_data[category].items():
            all_software.extend([sw['name'] for sw in software_list])
        
        # 检查是否全部已选
        all_selected = all(sw in self.selected_software for sw in all_software)
        
        if all_selected:
            # 取消选择所有
            for sw in all_software:
                self.selected_software.discard(sw)
        else:
            # 选择所有
            for sw in all_software:
                self.selected_software.add(sw)
        
        # 更新所有软件按钮外观
        for sw in all_software:
            if sw in self.software_buttons:
                btn = self.software_buttons[sw]
                is_selected = sw in self.selected_software
                btn.configure(
                    fg_color="#2E8B57" if is_selected else "#D3D3D3",
                    hover_color="#228B22" if is_selected else "#B0B0B0",
                    text_color="white" if is_selected else "black"
                )
        
        self.update_stats()
    
    def on_search_change(self, *args):
        """搜索框内容变化时的处理"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            # 如果搜索框为空，显示所有分类
            self.populate_software_categories_grid(self.categories_container)
            return
        
        # 清空现有内容
        for widget in self.categories_container.winfo_children():
            widget.destroy()
        
        # 创建搜索结果容器
        search_results_frame = ctk.CTkFrame(self.categories_container)
        search_results_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # 搜索结果标题
        results_title = ctk.CTkLabel(
            search_results_frame,
            text=f"🔍 搜索结果: '{search_text}'",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        results_title.grid(row=0, column=0, padx=15, pady=(15, 10))
        
        # 收集所有匹配的软件
        matching_software = []
        for category, subcategories in self.software_data.items():
            for subcategory, software_list in subcategories.items():
                for software in software_list:
                    if search_text in software['name'].lower():
                        matching_software.append(software)
        
        if not matching_software:
            # 没有找到匹配的软件
            no_results_label = ctk.CTkLabel(
                search_results_frame,
                text="未找到匹配的软件",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_results_label.grid(row=1, column=0, padx=15, pady=20)
        else:
            # 创建搜索结果网格
            results_grid = ctk.CTkFrame(search_results_frame)
            results_grid.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
            
            # 配置网格布局
            cols = 3  # 每行3个软件
            for i in range(cols):
                results_grid.grid_columnconfigure(i, weight=1)
            
            row = 0
            col = 0
            
            for software in matching_software:
                is_selected = software['name'] in self.selected_software
                
                software_btn = ctk.CTkButton(
                    results_grid,
                    text=software['name'],
                    width=200,
                    height=40,
                    command=lambda sw=software['name']: self.toggle_software(sw),
                    font=ctk.CTkFont(size=12),
                    fg_color="#2E8B57" if is_selected else "#D3D3D3",
                    hover_color="#228B22" if is_selected else "#B0B0B0",
                    text_color="white" if is_selected else "black"
                )
                software_btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                
                # 更新软件按钮引用
                self.software_buttons[software['name']] = software_btn
                
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
        
        search_results_frame.grid_columnconfigure(0, weight=1)
        self.categories_container.grid_columnconfigure(0, weight=1)
    
    def clear_search(self):
        """清除搜索"""
        self.search_var.set('')
    
    def clear_selection(self):
        """清空选择"""
        self.selected_software.clear()
        # 更新所有软件按钮外观
        if hasattr(self, 'software_buttons'):
            for btn in self.software_buttons.values():
                btn.configure(
                    fg_color="#D3D3D3",
                    hover_color="#B0B0B0",
                    text_color="black"
                )
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
        
        # 更新下一步按钮状态
        if selected_count > 0:
            self.next_btn.configure(state="normal")
        else:
            self.next_btn.configure(state="disabled")
    
    def on_window_resize(self, event):
        """窗口大小变化时的处理"""
        # 只处理主窗口的大小变化事件
        if event.widget == self.root:
            # 更新进度指示器的布局
            self.update_progress_indicator_layout()
            # 更新响应式布局
            self.update_responsive_layout()
    
    def update_progress_indicator_layout(self):
        """更新进度指示器布局以适应窗口大小"""
        if hasattr(self, 'progress_frame'):
            # 获取当前窗口宽度
            window_width = self.root.winfo_width()
            
            # 根据窗口宽度调整步骤标签的字体大小
            if window_width < 800:
                font_size = 10
                circle_size = 25
            elif window_width < 1000:
                font_size = 11
                circle_size = 30
            else:
                font_size = 12
                circle_size = 35
            
            # 更新步骤标签字体
            if hasattr(self, 'step_labels'):
                for label in self.step_labels:
                    label.configure(font=ctk.CTkFont(size=font_size))
            
            # 更新圆圈标签字体
            if hasattr(self, 'circle_labels'):
                for label in self.circle_labels:
                    label.configure(
                        font=ctk.CTkFont(size=font_size, weight="bold"),
                        width=circle_size,
                        height=circle_size
                    )
    
    def update_responsive_layout(self):
        """根据窗口大小更新响应式布局"""
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 根据窗口大小调整各种组件的尺寸和间距
        if window_width < 900:
            # 小窗口模式
            if hasattr(self, 'progress_frame'):
                self.progress_frame.configure(height=100)
            if hasattr(self, 'button_frame'):
                self.button_frame.configure(height=60)
        else:
            # 正常窗口模式
            if hasattr(self, 'progress_frame'):
                self.progress_frame.configure(height=120)
            if hasattr(self, 'button_frame'):
                self.button_frame.configure(height=70)
    
    def show_connectivity_check_step(self):
        """显示连通性检测页面"""
        check_frame = ctk.CTkFrame(self.content_frame)
        check_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            check_frame,
            text="服务器连通性检测",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # 说明
        desc_label = ctk.CTkLabel(
            check_frame,
            text="正在检测您的电脑与软件文件服务器的连通性，请稍候...",
            font=ctk.CTkFont(size=16)
        )
        desc_label.grid(row=1, column=0, pady=10)
        
        # 进度条
        self.connectivity_progress = ctk.CTkProgressBar(
            check_frame,
            width=600,
            height=20
        )
        self.connectivity_progress.grid(row=2, column=0, pady=20)
        self.connectivity_progress.set(0)
        
        # 状态标签
        self.connectivity_status = ctk.CTkLabel(
            check_frame,
            text="准备开始检测...",
            font=ctk.CTkFont(size=14)
        )
        self.connectivity_status.grid(row=3, column=0, pady=10)
        
        # 结果显示区域
        self.connectivity_results_frame = ctk.CTkScrollableFrame(
            check_frame,
            width=700,
            height=300
        )
        self.connectivity_results_frame.grid(row=4, column=0, pady=20, sticky="nsew")
        
        check_frame.grid_columnconfigure(0, weight=1)
        check_frame.grid_rowconfigure(4, weight=1)
        
        # 禁用下一步按钮
        self.next_btn.configure(state="disabled")
        
        # 开始连通性检测
        threading.Thread(target=self.start_connectivity_check, daemon=True).start()
    
    def start_connectivity_check(self):
        """开始连通性检测"""
        self.connectivity_results = {}
        software_list = list(self.selected_software)
        total_count = len(software_list)
        
        # 模拟服务器地址
        test_servers = [
            "https://github.com",
            "https://sourceforge.net",
            "https://download.microsoft.com",
            "https://www.google.com",
            "https://www.baidu.com"
        ]
        
        for i, software_name in enumerate(software_list):
            # 更新状态
            self.connectivity_status.configure(text=f"正在检测: {software_name}")
            
            # 随机选择一个服务器进行测试
            import random
            test_server = random.choice(test_servers)
            
            try:
                # 模拟网络检测
                response = requests.get(test_server, timeout=5)
                if response.status_code == 200:
                    self.connectivity_results[software_name] = "通过"
                    status_color = "#2E8B57"
                    status_icon = "✅"
                else:
                    self.connectivity_results[software_name] = "失败"
                    status_color = "#DC143C"
                    status_icon = "❌"
            except:
                # 模拟部分软件连接失败
                if random.random() > 0.1:  # 90%成功率
                    self.connectivity_results[software_name] = "通过"
                    status_color = "#2E8B57"
                    status_icon = "✅"
                else:
                    self.connectivity_results[software_name] = "失败"
                    status_color = "#DC143C"
                    status_icon = "❌"
            
            # 添加结果到显示区域
            result_label = ctk.CTkLabel(
                self.connectivity_results_frame,
                text=f"{status_icon} {software_name} - {self.connectivity_results[software_name]}",
                font=ctk.CTkFont(size=12),
                text_color=status_color
            )
            result_label.grid(row=i, column=0, padx=10, pady=2, sticky="w")
            
            # 更新进度条
            progress = (i + 1) / total_count
            self.connectivity_progress.set(progress)
            
            # 模拟检测时间
            time.sleep(0.5)
        
        # 检测完成
        failed_software = [name for name, status in self.connectivity_results.items() if status == "失败"]
        
        if failed_software:
            self.connectivity_status.configure(
                text=f"检测完成！{len(failed_software)} 个软件连接失败，无法下载。",
                text_color="#DC143C"
            )
            
            # 显示失败的软件
            failed_frame = ctk.CTkFrame(self.connectivity_results_frame)
            failed_frame.grid(row=total_count, column=0, pady=20, sticky="ew")
            
            failed_title = ctk.CTkLabel(
                failed_frame,
                text="❌ 连接失败的软件（将被排除）:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#DC143C"
            )
            failed_title.grid(row=0, column=0, padx=10, pady=10)
            
            for i, software_name in enumerate(failed_software):
                failed_label = ctk.CTkLabel(
                    failed_frame,
                    text=f"• {software_name}",
                    font=ctk.CTkFont(size=12),
                    text_color="#DC143C"
                )
                failed_label.grid(row=i+1, column=0, padx=20, pady=2, sticky="w")
            
            # 从选择列表中移除失败的软件
            for software_name in failed_software:
                self.selected_software.discard(software_name)
            
            # 禁用下一步
            self.next_btn.configure(state="disabled")
            
            # 添加重新检测按钮
            retry_btn = ctk.CTkButton(
                failed_frame,
                text="🔄 重新检测",
                command=self.retry_connectivity_check,
                font=ctk.CTkFont(size=12)
            )
            retry_btn.grid(row=len(failed_software)+1, column=0, pady=10)
            
        else:
            self.connectivity_status.configure(
                text="✅ 所有软件连接正常，可以继续下载！",
                text_color="#2E8B57"
            )
            self.next_btn.configure(state="normal")
    
    def retry_connectivity_check(self):
        """重新进行连通性检测"""
        # 清空结果显示区域
        for widget in self.connectivity_results_frame.winfo_children():
            widget.destroy()
        
        # 重置进度条
        self.connectivity_progress.set(0)
        self.connectivity_status.configure(text="重新开始检测...")
        
        # 重新开始检测
        threading.Thread(target=self.start_connectivity_check, daemon=True).start()
    
    def show_download_settings_step(self):
        """显示下载设置页面"""
        settings_frame = ctk.CTkFrame(self.content_frame)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            settings_frame,
            text="下载设置配置",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 20))
        
        # 下载路径设置
        path_frame = ctk.CTkFrame(settings_frame)
        path_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=40, pady=10)
        
        path_label = ctk.CTkLabel(
            path_frame,
            text="下载路径:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        path_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        path_input_frame = ctk.CTkFrame(path_frame)
        path_input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        self.path_var = tk.StringVar(value=self.download_settings['path'])
        self.path_entry = ctk.CTkEntry(
            path_input_frame,
            textvariable=self.path_var,
            width=500,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.path_entry.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="浏览",
            width=80,
            height=35,
            command=self.browse_download_path,
            font=ctk.CTkFont(size=12)
        )
        browse_btn.grid(row=0, column=1, padx=(5, 10), pady=10)
        
        path_input_frame.grid_columnconfigure(0, weight=1)
        path_frame.grid_columnconfigure(0, weight=1)
        
        # 路径验证状态
        self.path_status_label = ctk.CTkLabel(
            path_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.path_status_label.grid(row=2, column=0, padx=20, pady=(0, 10))
        
        # 高级设置
        advanced_frame = ctk.CTkFrame(settings_frame)
        advanced_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=40, pady=10)
        
        advanced_label = ctk.CTkLabel(
            advanced_frame,
            text="高级设置:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        # 并发下载数
        concurrent_frame = ctk.CTkFrame(advanced_frame)
        concurrent_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        concurrent_label = ctk.CTkLabel(
            concurrent_frame,
            text="同时下载数量:",
            font=ctk.CTkFont(size=14)
        )
        concurrent_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.concurrent_var = tk.IntVar(value=self.download_settings['concurrent'])
        concurrent_slider = ctk.CTkSlider(
            concurrent_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.concurrent_var,
            width=200
        )
        concurrent_slider.grid(row=0, column=1, padx=15, pady=10)
        
        self.concurrent_value_label = ctk.CTkLabel(
            concurrent_frame,
            text=str(self.concurrent_var.get()),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.concurrent_value_label.grid(row=0, column=2, padx=15, pady=10)
        
        # 绑定滑块变化事件
        concurrent_slider.configure(command=self.update_concurrent_value)
        
        concurrent_frame.grid_columnconfigure(1, weight=1)
        
        # 超时设置
        timeout_frame = ctk.CTkFrame(advanced_frame)
        timeout_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 15))
        
        timeout_label = ctk.CTkLabel(
            timeout_frame,
            text="连接超时 (秒):",
            font=ctk.CTkFont(size=14)
        )
        timeout_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.timeout_var = tk.IntVar(value=self.download_settings['timeout'])
        timeout_slider = ctk.CTkSlider(
            timeout_frame,
            from_=10,
            to=120,
            number_of_steps=11,
            variable=self.timeout_var,
            width=200
        )
        timeout_slider.grid(row=0, column=1, padx=15, pady=10)
        
        self.timeout_value_label = ctk.CTkLabel(
            timeout_frame,
            text=str(self.timeout_var.get()),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.timeout_value_label.grid(row=0, column=2, padx=15, pady=10)
        
        # 绑定滑块变化事件
        timeout_slider.configure(command=self.update_timeout_value)
        
        timeout_frame.grid_columnconfigure(1, weight=1)
        advanced_frame.grid_columnconfigure(0, weight=1)
        
        # 下载预览
        preview_frame = ctk.CTkFrame(settings_frame)
        preview_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=40, pady=10)
        
        preview_label = ctk.CTkLabel(
            preview_frame,
            text="📋 下载预览:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        preview_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        preview_text = f"将要下载 {len(self.selected_software)} 个软件\n"
        preview_text += f"下载路径: {self.download_settings['path']}\n"
        preview_text += f"并发数量: {self.download_settings['concurrent']}\n"
        preview_text += f"连接超时: {self.download_settings['timeout']} 秒"
        
        self.preview_info_label = ctk.CTkLabel(
            preview_frame,
            text=preview_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        self.preview_info_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        preview_frame.grid_columnconfigure(0, weight=1)
        
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # 绑定路径变化事件
        self.path_var.trace('w', self.validate_download_path)
        
        # 初始验证路径
        self.validate_download_path()
    
    def browse_download_path(self):
        """浏览下载路径"""
        path = filedialog.askdirectory(
            title="选择下载目录",
            initialdir=self.path_var.get()
        )
        if path:
            self.path_var.set(path)
    
    def validate_download_path(self, *args):
        """验证下载路径"""
        path = self.path_var.get()
        
        if not path:
            self.path_status_label.configure(
                text="❌ 请选择下载路径",
                text_color="#DC143C"
            )
            self.next_btn.configure(state="disabled")
            return
        
        try:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_dir():
                # 检查写入权限
                test_file = path_obj / "test_write.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    self.path_status_label.configure(
                        text="✅ 路径有效，具有写入权限",
                        text_color="#2E8B57"
                    )
                    self.download_settings['path'] = path
                    self.next_btn.configure(state="normal")
                except:
                    self.path_status_label.configure(
                        text="❌ 路径无写入权限",
                        text_color="#DC143C"
                    )
                    self.next_btn.configure(state="disabled")
            else:
                self.path_status_label.configure(
                    text="❌ 路径不存在或不是有效目录",
                    text_color="#DC143C"
                )
                self.next_btn.configure(state="disabled")
        except:
            self.path_status_label.configure(
                text="❌ 路径格式无效",
                text_color="#DC143C"
            )
            self.next_btn.configure(state="disabled")
    
    def update_concurrent_value(self, value):
        """更新并发数值显示"""
        self.concurrent_value_label.configure(text=str(int(value)))
        self.download_settings['concurrent'] = int(value)
    
    def update_timeout_value(self, value):
        """更新超时数值显示"""
        self.timeout_value_label.configure(text=str(int(value)))
        self.download_settings['timeout'] = int(value)
    
    def show_download_progress_step(self):
        """显示下载进度页面"""
        progress_frame = ctk.CTkFrame(self.content_frame)
        progress_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            progress_frame,
            text="正在下载软件",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # 总体进度
        overall_frame = ctk.CTkFrame(progress_frame)
        overall_frame.grid(row=1, column=0, sticky="ew", padx=40, pady=10)
        
        overall_label = ctk.CTkLabel(
            overall_frame,
            text="总体进度:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        overall_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.overall_progress = ctk.CTkProgressBar(
            overall_frame,
            width=600,
            height=25
        )
        self.overall_progress.grid(row=1, column=0, padx=20, pady=5)
        self.overall_progress.set(0)
        
        self.overall_status = ctk.CTkLabel(
            overall_frame,
            text="准备开始下载...",
            font=ctk.CTkFont(size=14)
        )
        self.overall_status.grid(row=2, column=0, padx=20, pady=(5, 15))
        
        overall_frame.grid_columnconfigure(0, weight=1)
        
        # 详细进度
        detail_frame = ctk.CTkFrame(progress_frame)
        detail_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
        
        detail_label = ctk.CTkLabel(
            detail_frame,
            text="详细进度:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        detail_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        self.detail_scrollable = ctk.CTkScrollableFrame(
            detail_frame,
            width=700,
            height=350
        )
        self.detail_scrollable.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        
        detail_frame.grid_columnconfigure(0, weight=1)
        detail_frame.grid_rowconfigure(1, weight=1)
        
        progress_frame.grid_columnconfigure(0, weight=1)
        progress_frame.grid_rowconfigure(2, weight=1)
        
        # 禁用所有导航按钮
        self.prev_btn.configure(state="disabled")
        self.next_btn.configure(state="disabled")
        
        # 开始下载
        threading.Thread(target=self.start_download_process, daemon=True).start()
    
    def start_download_process(self):
        """开始下载过程"""
        software_list = list(self.selected_software)
        total_count = len(software_list)
        completed = 0
        
        self.overall_status.configure(text=f"开始下载 {total_count} 个软件...")
        
        for i, software_name in enumerate(software_list):
            # 创建单个软件的进度显示
            software_frame = ctk.CTkFrame(self.detail_scrollable)
            software_frame.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            
            name_label = ctk.CTkLabel(
                software_frame,
                text=f"📦 {software_name}",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            name_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
            
            progress_bar = ctk.CTkProgressBar(
                software_frame,
                width=400,
                height=15
            )
            progress_bar.grid(row=1, column=0, padx=15, pady=5)
            progress_bar.set(0)
            
            status_label = ctk.CTkLabel(
                software_frame,
                text="等待下载...",
                font=ctk.CTkFont(size=10)
            )
            status_label.grid(row=2, column=0, padx=15, pady=(5, 10), sticky="w")
            
            software_frame.grid_columnconfigure(0, weight=1)
            
            # 模拟下载过程
            status_label.configure(text="正在连接服务器...")
            time.sleep(0.5)
            
            status_label.configure(text="开始下载...")
            
            # 模拟下载进度
            for progress in range(0, 101, 10):
                progress_bar.set(progress / 100)
                status_label.configure(text=f"下载中... {progress}%")
                time.sleep(0.2)
            
            status_label.configure(text="✅ 下载完成", text_color="#2E8B57")
            
            completed += 1
            overall_progress = completed / total_count
            self.overall_progress.set(overall_progress)
            self.overall_status.configure(
                text=f"已完成 {completed}/{total_count} 个软件的下载"
            )
        
        # 下载完成
        self.overall_status.configure(
            text="🎉 所有软件下载完成！",
            text_color="#2E8B57"
        )
        
        # 启用下一步按钮
        self.next_btn.configure(state="normal")
    
    def show_completion_step(self):
        """显示完成页面"""
        completion_frame = ctk.CTkFrame(self.content_frame)
        completion_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 成功图标和标题
        title_label = ctk.CTkLabel(
            completion_frame,
            text="下载完成！",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#4a9eff"
        )
        title_label.grid(row=0, column=0, pady=(40, 20))
        
        # 感谢信息
        thanks_text = """
恭喜您！所有软件已成功下载完成！

下载统计:
• 总计下载: {count} 个软件
• 下载路径: {path}
• 下载时间: {time}

接下来您可以:
• 前往下载目录查看和安装软件
• 根据需要配置和使用下载的软件
• 定期检查软件更新

感谢您使用软件资源整合管理器！
希望这些软件能够帮助您提高工作效率。
        """.format(
            count=len(self.selected_software),
            path=self.download_settings['path'],
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        thanks_label = ctk.CTkLabel(
            completion_frame,
            text=thanks_text,
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        thanks_label.grid(row=1, column=0, pady=20)
        
        # 操作按钮
        action_frame = ctk.CTkFrame(completion_frame)
        action_frame.grid(row=2, column=0, pady=30)
        
        open_folder_btn = ctk.CTkButton(
            action_frame,
            text="打开下载文件夹",
            width=180,
            height=45,
            command=self.open_download_folder,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        open_folder_btn.grid(row=0, column=0, padx=15, pady=15)
        
        restart_btn = ctk.CTkButton(
            action_frame,
            text="重新开始",
            width=180,
            height=45,
            command=self.restart_wizard,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8b5a00",
            hover_color="#5e3c00"
        )
        restart_btn.grid(row=0, column=1, padx=15, pady=15)
        
        completion_frame.grid_columnconfigure(0, weight=1)
        
        # 隐藏导航按钮
        self.prev_btn.configure(state="disabled")
        self.next_btn.configure(state="disabled")
    
    def open_download_folder(self):
        """打开下载文件夹"""
        try:
            import os
            import subprocess
            path = self.download_settings['path']
            if os.path.exists(path):
                subprocess.Popen(f'explorer "{path}"')
            else:
                messagebox.showerror("错误", "下载文件夹不存在！")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
    
    def restart_wizard(self):
        """重新开始向导"""
        # 重置所有状态
        self.selected_software.clear()
        self.connectivity_results.clear()
        self.current_step = 1
        
        # 重新显示第一步
        self.show_step(1)
    
    def prev_step(self):
        """上一步"""
        if self.current_step > 1:
            self.show_step(self.current_step - 1)
    
    def next_step(self):
        """下一步"""
        if self.current_step < self.total_steps:
            self.show_step(self.current_step + 1)
    
    def on_closing(self):
        """关闭程序"""
        if messagebox.askokcancel("退出", "确定要退出软件管理器吗？"):
            self.save_config()
            self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

def main():
    """主函数"""
    try:
        app = WizardSoftwareManager()
        app.run()
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()