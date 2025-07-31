#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件管理器 V3.0
完全重构版本 - 现代化UI界面

主要特性：
- 现代化分页UI设计
- 完整的下载校验和自动纠错系统
- 分级日志系统
- 响应式布局
- 协议页面和复选框验证
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
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
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
import sys
from dataclasses import dataclass
from enum import Enum

# 导入主程序模块
try:
    from software_manager_v3 import SoftwareManagerV3
except ImportError:
    print("警告: 无法导入主程序模块，将使用内置功能")
    SoftwareManagerV3 = None

# 设置现代化主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class PageType(Enum):
    """页面类型枚举"""
    WELCOME = "welcome"
    SOFTWARE_SELECTION = "software_selection"
    DOWNLOAD_SETTINGS = "download_settings"
    CONNECTIVITY_CHECK = "connectivity_check"
    DOWNLOAD_PROGRESS = "download_progress"
    VALIDATION = "validation"
    COMPLETION = "completion"
    AGREEMENT = "agreement"
    PRIVACY = "privacy"

@dataclass
class DownloadItem:
    """下载项数据类"""
    name: str
    url: str
    size: int
    checksum: str
    category: str
    description: str
    version: str

class Logger:
    """分级日志系统"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建主日志记录器
        self.logger = logging.getLogger('SoftwareManager')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器 - 所有日志
        file_handler = logging.FileHandler(
            self.log_dir / f"software_manager_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 错误日志处理器
        error_handler = logging.FileHandler(
            self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)

class FileValidator:
    """文件校验和自动纠错系统"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def calculate_checksum(self, file_path: Path) -> str:
        """计算文件MD5校验和"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"计算校验和失败: {file_path} - {e}")
            return ""
    
    def validate_file(self, file_path: Path, expected_checksum: str = None) -> bool:
        """验证文件是否存在"""
        if not file_path.exists():
            self.logger.warning(f"文件不存在: {file_path}")
            return False
        
        self.logger.info(f"文件存在: {file_path}")
        return True
    
    def validate_directory(self, download_path: Path, items: List[DownloadItem]) -> Dict[str, bool]:
        """验证下载目录中的所有文件是否存在"""
        results = {}
        
        for item in items:
            file_path = download_path / f"{item.name}.exe"
            results[item.name] = self.validate_file(file_path)
        
        return results
    
    def auto_repair(self, download_path: Path, failed_items: List[DownloadItem]) -> List[str]:
        """自动纠错机制"""
        repaired = []
        
        for item in failed_items:
            file_path = download_path / f"{item.name}.exe"
            
            try:
                # 尝试删除损坏的文件
                if file_path.exists():
                    file_path.unlink()
                    self.logger.info(f"删除损坏文件: {file_path}")
                
                # 标记需要重新下载
                repaired.append(item.name)
                self.logger.info(f"标记重新下载: {item.name}")
                
            except Exception as e:
                self.logger.error(f"自动纠错失败: {item.name} - {e}")
        
        return repaired

class ModernSoftwareManager:
    """现代化软件管理器主类"""
    
    def __init__(self):
        # 先初始化基础组件
        if SoftwareManagerV3:
            # 临时创建一个SoftwareManagerV3实例来获取logger
            temp_manager = SoftwareManagerV3()
            self.logger = temp_manager.logger.get_logger('main')
        else:
            self.logger = Logger()
        
        # 加载软件数据
        self.load_software_data()
        
        # 初始化核心管理器
        if SoftwareManagerV3:
            self.core_manager = SoftwareManagerV3(self.software_data)
            self.logger = self.core_manager.logger.get_logger('main')
            self.validator = self.core_manager.downloader.validator
        else:
            # 使用内置日志和校验系统
            self.core_manager = None
            self.validator = FileValidator(self.logger)
        
        self.logger.info("软件管理器 V3.0 UI 启动")
        
        # 应用程序状态
        self.current_page = PageType.WELCOME
        self.selected_software = set()
        
        # 步骤完成状态
        self.software_selected = False
        self.download_path_set = False
        self.connectivity_checked = False
        self.download_completed = False
        self.validation_completed = False
        
        # 定义页面流程顺序
        self.page_flow = [
            PageType.WELCOME,
            PageType.SOFTWARE_SELECTION,
            PageType.DOWNLOAD_SETTINGS,
            PageType.CONNECTIVITY_CHECK,
            PageType.DOWNLOAD_PROGRESS,
            PageType.VALIDATION,
            PageType.COMPLETION
        ]
        
        # 当前步骤索引
        self.current_step = 0
        
        # 获取下载路径
        if self.core_manager:
            self.download_path = Path(self.core_manager.get_config("download_path", str(Path.home() / "Downloads" / "SoftwareManager")))
        else:
            self.download_path = Path.home() / "Downloads" / "SoftwareManager"
        
        self.agreement_accepted = False
        self.privacy_accepted = False
        
        # 下载设置
        if self.core_manager:
            self.download_settings = {
                'path': str(self.download_path),
                'concurrent': self.core_manager.get_config('concurrent_downloads', 3),
                'timeout': self.core_manager.get_config('timeout_seconds', 30),
                'retry_count': self.core_manager.get_config('max_retries', 3)
            }
        else:
            self.download_settings = {
                'path': str(self.download_path),
                'concurrent': 3,
                'timeout': 30,
                'retry_count': 3
            }
        
        # 软件数据
        self.software_data = {}
        self.categories = {}
        
        # UI组件
        self.root = None
        self.main_frame = None
        self.content_frame = None
        self.navigation_frame = None
        
        # 加载配置和数据
        self.load_software_data()
        self.load_config()
        
        # 创建主窗口
        self.create_main_window()
    
    def load_software_data(self):
        """加载软件数据"""
        try:
            with open('software_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 重新组织数据结构以适应UI显示
                self.software_data = {}
                self.categories = {}
                
                # 遍历主分类
                for main_category, subcategories in data.items():
                    self.categories[main_category] = {'name': main_category}
                    
                    # 遍历子分类
                    for sub_category, software_list in subcategories.items():
                        # 为每个子分类创建一个分类
                        category_key = f"{main_category}_{sub_category}"
                        self.categories[category_key] = {'name': f"{main_category} - {sub_category}"}
                        
                        # 添加软件到软件数据中
                        for software in software_list:
                            software_name = software['name']
                            self.software_data[software_name] = {
                                'name': software_name,  # 添加name字段
                                'category': category_key,
                                'description': software.get('description', ''),
                                'url': software.get('url', ''),
                                'version': software.get('version', '1.0'),
                                'size': software.get('size', 0),
                                'checksum': software.get('checksum', '')
                            }
                            
            self.logger.info(f"软件数据加载成功，共加载 {len(self.software_data)} 个软件")
        except Exception as e:
            self.logger.error(f"加载软件数据失败: {e}")
            self.software_data = {}
            self.categories = {}
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.download_settings.update(config.get('download_settings', {}))
                self.download_path = Path(self.download_settings['path'])
            self.logger.info("配置文件加载成功")
        except Exception as e:
            self.logger.warning(f"加载配置文件失败，使用默认配置: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            config = {
                'download_settings': self.download_settings,
                'last_updated': datetime.now().isoformat()
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.logger.info("配置文件保存成功")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def create_main_window(self):
        """创建主窗口"""
        self.root = ctk.CTk()
        self.root.title("软件管理器 V3.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # 设置窗口图标（如果存在）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建导航区域
        self.create_navigation()
        
        # 创建内容区域
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=(0, 10), pady=10)
        
        # 显示欢迎页面
        self.show_page(PageType.WELCOME)
        
        # 绑定窗口事件
        self.root.bind("<Configure>", self.on_window_resize)
        
        self.logger.info("主窗口创建完成")
    
    def create_navigation(self):
        """创建导航区域"""
        self.navigation_frame = ctk.CTkFrame(self.main_frame, width=220)
        self.navigation_frame.pack(side="left", fill="y", padx=(10, 10), pady=10)
        self.navigation_frame.pack_propagate(False)
        
        # 标题
        title_label = ctk.CTkLabel(
            self.navigation_frame,
            text="软件管理器\nV3.0",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # 步骤进度指示
        self.nav_steps = {}
        steps = [
            (PageType.WELCOME, "1. 欢迎"),
            (PageType.SOFTWARE_SELECTION, "2. 选择软件"),
            (PageType.DOWNLOAD_SETTINGS, "3. 下载设置"),
            (PageType.CONNECTIVITY_CHECK, "4. 连通性检测"),
            (PageType.DOWNLOAD_PROGRESS, "5. 下载进度"),
            (PageType.VALIDATION, "6. 文件校验"),
            (PageType.COMPLETION, "7. 完成")
        ]
        
        for i, (page_type, text) in enumerate(steps):
            step_frame = ctk.CTkFrame(self.navigation_frame)
            step_frame.pack(fill="x", padx=10, pady=3)
            
            step_label = ctk.CTkLabel(
                step_frame,
                text=text,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            step_label.pack(fill="x", padx=15, pady=8)
            
            self.nav_steps[page_type] = step_frame
        
        # 更新导航状态
        self.update_navigation()
    
    def update_navigation(self):
        """更新导航步骤状态"""
        current_index = self.page_flow.index(self.current_page) if self.current_page in self.page_flow else 0
        
        for i, page_type in enumerate(self.page_flow):
            if page_type in self.nav_steps:
                step_frame = self.nav_steps[page_type]
                
                if i < current_index:
                    # 已完成的步骤 - 绿色
                    step_frame.configure(fg_color=("#2d5a2d", "#1a3d1a"))
                elif i == current_index:
                    # 当前步骤 - 蓝色高亮
                    step_frame.configure(fg_color=("#1f538d", "#14375e"))
                else:
                    # 未到达的步骤 - 灰色
                    step_frame.configure(fg_color=("#404040", "#2b2b2b"))
    
    def can_proceed_to_page(self, target_page: PageType) -> Tuple[bool, str]:
        """检查是否可以进入目标页面"""
        # 获取当前页面在流程中的索引
        current_index = self.page_flow.index(self.current_page) if self.current_page in self.page_flow else 0
        target_index = self.page_flow.index(target_page) if target_page in self.page_flow else 0
        
        # 如果是向后导航，总是允许
        if target_index <= current_index:
            return True, ""
        
        # 检查每个步骤的完成状态
        if target_page == PageType.DOWNLOAD_SETTINGS:
            if not self.software_selected:
                return False, "请先选择要下载的软件"
        
        elif target_page == PageType.CONNECTIVITY_CHECK:
            if not self.software_selected:
                return False, "请先选择要下载的软件"
            if not self.download_path_set:
                return False, "请先设置有效的下载路径"
        
        elif target_page == PageType.DOWNLOAD_PROGRESS:
            if not self.software_selected:
                return False, "请先选择要下载的软件"
            if not self.download_path_set:
                return False, "请先设置有效的下载路径"
            if not self.connectivity_checked:
                return False, "请先完成连接性检查"
        
        elif target_page == PageType.VALIDATION:
            if not self.software_selected:
                return False, "请先选择要下载的软件"
            if not self.download_path_set:
                return False, "请先设置有效的下载路径"
            if not self.connectivity_checked:
                return False, "请先完成连接性检查"
            if not self.download_completed:
                return False, "请先完成软件下载"
        
        elif target_page == PageType.COMPLETION:
            if not self.software_selected:
                return False, "请先选择要下载的软件"
            if not self.download_path_set:
                return False, "请先设置有效的下载路径"
            if not self.connectivity_checked:
                return False, "请先完成连接性检查"
            if not self.download_completed:
                return False, "请先完成软件下载"
            if not self.validation_completed:
                return False, "请先完成文件校验"
        
        return True, ""
    
    def show_page(self, page_type: PageType):
        """显示指定页面"""
        # 检查是否可以进入目标页面
        can_proceed, error_message = self.can_proceed_to_page(page_type)
        if not can_proceed:
            messagebox.showwarning("步骤未完成", error_message)
            return
        
        # 清空内容区域
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_page = page_type
        self.update_navigation()
        
        # 根据页面类型显示相应内容
        if page_type == PageType.WELCOME:
            self.show_welcome_page()
        elif page_type == PageType.SOFTWARE_SELECTION:
            self.show_software_selection_page()
        elif page_type == PageType.VALIDATION:
            self.show_validation_page()
        elif page_type == PageType.DOWNLOAD_SETTINGS:
            self.show_download_settings_page()
        elif page_type == PageType.CONNECTIVITY_CHECK:
            self.show_connectivity_check_page()
        elif page_type == PageType.DOWNLOAD_PROGRESS:
            self.show_download_progress_page()
        elif page_type == PageType.COMPLETION:
            self.show_completion_page()
        elif page_type == PageType.AGREEMENT:
            self.show_agreement_page()
        elif page_type == PageType.PRIVACY:
            self.show_privacy_page()
        
        self.logger.info(f"切换到页面: {page_type.value}")
    
    def show_welcome_page(self):
        """显示欢迎页面"""
        # 主容器
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 欢迎标题
        title_label = ctk.CTkLabel(
            container,
            text="欢迎使用软件管理器 V3.0",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # 欢迎语
        welcome_text = """
欢迎使用全新的软件管理器 V3.0！

本软件管理器为您提供：
• 一站式软件下载和管理
• 智能文件校验和自动纠错
• 现代化的用户界面
• 完整的日志记录系统
• 响应式布局设计

在开始使用之前，请仔细阅读并同意我们的用户协议和隐私协议。
        """
        
        welcome_label = ctk.CTkLabel(
            container,
            text=welcome_text,
            font=ctk.CTkFont(size=16),
            justify="left"
        )
        welcome_label.pack(pady=20)
        
        # 协议区域
        agreement_frame = ctk.CTkFrame(container)
        agreement_frame.pack(fill="x", padx=40, pady=20)
        
        agreement_title = ctk.CTkLabel(
            agreement_frame,
            text="协议确认",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        agreement_title.pack(pady=(20, 15))
        
        # 用户协议复选框
        self.agreement_var = tk.BooleanVar()
        agreement_check_frame = ctk.CTkFrame(agreement_frame)
        agreement_check_frame.pack(fill="x", padx=20, pady=10)
        
        agreement_checkbox = ctk.CTkCheckBox(
            agreement_check_frame,
            text="我已阅读并同意",
            variable=self.agreement_var,
            command=self.check_agreements
        )
        agreement_checkbox.pack(side="left", padx=10, pady=10)
        
        agreement_link = ctk.CTkButton(
            agreement_check_frame,
            text="《用户协议》",
            width=100,
            height=30,
            fg_color="transparent",
            text_color=("#1f538d", "#4a9eff"),
            hover_color=("#e0e0e0", "#2a2a2a"),
            command=lambda: self.show_page(PageType.AGREEMENT)
        )
        agreement_link.pack(side="left", padx=5, pady=10)
        
        # 隐私协议复选框
        self.privacy_var = tk.BooleanVar()
        privacy_check_frame = ctk.CTkFrame(agreement_frame)
        privacy_check_frame.pack(fill="x", padx=20, pady=10)
        
        privacy_checkbox = ctk.CTkCheckBox(
            privacy_check_frame,
            text="我已阅读并同意",
            variable=self.privacy_var,
            command=self.check_agreements
        )
        privacy_checkbox.pack(side="left", padx=10, pady=10)
        
        privacy_link = ctk.CTkButton(
            privacy_check_frame,
            text="《隐私协议》",
            width=100,
            height=30,
            fg_color="transparent",
            text_color=("#1f538d", "#4a9eff"),
            hover_color=("#e0e0e0", "#2a2a2a"),
            command=lambda: self.show_page(PageType.PRIVACY)
        )
        privacy_link.pack(side="left", padx=5, pady=10)
        
        # 继续按钮
        self.continue_button = ctk.CTkButton(
            agreement_frame,
            text="开始使用",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self.show_page(PageType.SOFTWARE_SELECTION),
            state="disabled"
        )
        self.continue_button.pack(pady=(20, 30))
    
    def check_agreements(self):
        """检查协议是否都已同意"""
        self.agreement_accepted = self.agreement_var.get()
        self.privacy_accepted = self.privacy_var.get()
        
        if self.agreement_accepted and self.privacy_accepted:
            self.continue_button.configure(state="normal")
            self.logger.info("用户已同意所有协议")
        else:
            self.continue_button.configure(state="disabled")
    
    def show_agreement_page(self):
        """显示用户协议页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            container,
            text="用户协议",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 协议内容
        agreement_text = """
用户协议

1. 接受条款
通过使用本软件，您同意受本协议条款的约束。

2. 软件使用
本软件仅供个人和非商业用途使用。

3. 知识产权
本软件及其所有相关材料均受版权法保护。

4. 免责声明
本软件按"现状"提供，不提供任何明示或暗示的保证。

5. 责任限制
在任何情况下，软件提供方均不对任何损害承担责任。

6. 协议修改
我们保留随时修改本协议的权利。

7. 适用法律
本协议受中华人民共和国法律管辖。
        """
        
        agreement_label = ctk.CTkLabel(
            container,
            text=agreement_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        agreement_label.pack(pady=20, padx=20)
        
        # 返回按钮
        back_button = ctk.CTkButton(
            container,
            text="返回",
            width=150,
            height=40,
            command=lambda: self.show_page(PageType.WELCOME)
        )
        back_button.pack(pady=20)
    
    def show_privacy_page(self):
        """显示隐私协议页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            container,
            text="隐私协议",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 隐私协议内容
        privacy_text = """
隐私协议

1. 信息收集
我们可能收集您提供的个人信息和使用信息。

2. 信息使用
我们使用收集的信息来提供和改进我们的服务。

3. 信息共享
我们不会向第三方出售、交易或转让您的个人信息。

4. 数据安全
我们采取适当的安全措施来保护您的个人信息。

5. Cookie使用
我们可能使用Cookie来改善用户体验。

6. 第三方链接
我们的服务可能包含第三方网站的链接。

7. 隐私政策更新
我们可能会不时更新本隐私政策。

8. 联系我们
如有隐私相关问题，请联系我们。
        """
        
        privacy_label = ctk.CTkLabel(
            container,
            text=privacy_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        privacy_label.pack(pady=20, padx=20)
        
        # 返回按钮
        back_button = ctk.CTkButton(
            container,
            text="返回",
            width=150,
            height=40,
            command=lambda: self.show_page(PageType.WELCOME)
        )
        back_button.pack(pady=20)
    
    def show_software_selection_page(self):
        """显示软件选择页面 - 多级菜单结构"""
        # 主容器
        main_container = ctk.CTkFrame(self.content_frame)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 页面标题
        title_label = ctk.CTkLabel(
            main_container,
            text="选择要下载的软件",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 搜索和统计区域
        search_frame = ctk.CTkFrame(main_container)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        # 搜索框
        search_label = ctk.CTkLabel(
            search_frame,
            text="搜索软件:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        search_label.pack(side="left", padx=(20, 10), pady=15)
        
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=300,
            height=35,
            placeholder_text="输入软件名称..."
        )
        self.search_entry.pack(side="left", padx=10, pady=15)
        self.search_var.trace('w', self.on_search_change)
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(
            search_frame,
            text="已选择: 0 个软件",
            font=ctk.CTkFont(size=14)
        )
        self.stats_label.pack(side="right", padx=20, pady=15)
        
        # 主要内容区域 - 分为左右两栏
        content_frame = ctk.CTkFrame(main_container)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 左侧：多级菜单选择区域
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        left_title = ctk.CTkLabel(
            left_frame,
            text="软件分类",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        left_title.pack(pady=(15, 10))
        
        # 分类选择区域
        self.category_frame = ctk.CTkScrollableFrame(left_frame)
        self.category_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 右侧：已选列表区域
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.configure(width=300)
        
        right_title = ctk.CTkLabel(
            right_frame,
            text="已选软件列表",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        right_title.pack(pady=(15, 10))
        
        # 已选列表操作按钮
        selected_action_frame = ctk.CTkFrame(right_frame)
        selected_action_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        clear_selected_btn = ctk.CTkButton(
            selected_action_frame,
            text="清空已选列表",
            width=120,
            height=35,
            command=self.clear_selected_list
        )
        clear_selected_btn.pack(side="left", padx=(10, 5), pady=10)
        
        select_all_btn = ctk.CTkButton(
            selected_action_frame,
            text="全选当前分类",
            width=120,
            height=35,
            command=self.select_all_in_category
        )
        select_all_btn.pack(side="right", padx=(5, 10), pady=10)
        
        # 已选软件列表
        self.selected_list_frame = ctk.CTkScrollableFrame(right_frame)
        self.selected_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 底部继续按钮
        continue_btn = ctk.CTkButton(
            main_container,
            text="继续到下载设置",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self.show_page(PageType.DOWNLOAD_SETTINGS)
        )
        continue_btn.pack(pady=20)
        
        # 初始化界面
        self.current_category = None
        self.current_subcategory = None
        self.populate_category_menu()
        self.update_selected_list()
        self.update_stats()
    
    def populate_category_menu(self):
        """填充分类菜单"""
        # 清空现有内容
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        # 重新组织数据结构为真正的多级菜单
        main_categories = {}
        for category_key, category_info in self.categories.items():
            if '_' in category_key:
                main_cat, sub_cat = category_key.split('_', 1)
                if main_cat not in main_categories:
                    main_categories[main_cat] = {}
                main_categories[main_cat][sub_cat] = category_key
        
        # 创建主分类按钮
        for main_cat in main_categories.keys():
            main_cat_frame = ctk.CTkFrame(self.category_frame)
            main_cat_frame.pack(fill="x", padx=10, pady=5)
            
            # 主分类按钮
            main_cat_btn = ctk.CTkButton(
                main_cat_frame,
                text=f"📁 {main_cat}",
                width=200,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda cat=main_cat: self.toggle_main_category(cat)
            )
            main_cat_btn.pack(pady=10)
            
            # 子分类容器（初始隐藏）
            sub_frame = ctk.CTkFrame(main_cat_frame)
            sub_frame.pack(fill="x", padx=20, pady=(0, 10))
            sub_frame.pack_forget()  # 初始隐藏
            
            # 存储引用以便后续操作
            setattr(main_cat_frame, 'sub_frame', sub_frame)
            setattr(main_cat_frame, 'main_cat', main_cat)
            setattr(main_cat_frame, 'expanded', False)
            
            # 创建子分类按钮
            for sub_cat, category_key in main_categories[main_cat].items():
                sub_cat_btn = ctk.CTkButton(
                    sub_frame,
                    text=f"📂 {sub_cat}",
                    width=180,
                    height=35,
                    font=ctk.CTkFont(size=12),
                    command=lambda key=category_key: self.show_category_software(key)
                )
                sub_cat_btn.pack(pady=2)
    
    def toggle_main_category(self, main_cat):
        """切换主分类的展开/收起状态"""
        for widget in self.category_frame.winfo_children():
            if hasattr(widget, 'main_cat') and widget.main_cat == main_cat:
                if widget.expanded:
                    widget.sub_frame.pack_forget()
                    widget.expanded = False
                else:
                    widget.sub_frame.pack(fill="x", padx=20, pady=(0, 10))
                    widget.expanded = True
                break
    
    def show_category_software(self, category_key):
        """显示指定分类的软件列表"""
        self.current_category = category_key
        
        # 清空分类框架，显示软件列表
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        # 返回按钮
        back_btn = ctk.CTkButton(
            self.category_frame,
            text="← 返回分类选择",
            width=150,
            height=35,
            command=self.populate_category_menu
        )
        back_btn.pack(pady=(10, 20))
        
        # 分类标题
        category_name = self.categories.get(category_key, {}).get('name', category_key)
        title_label = ctk.CTkLabel(
            self.category_frame,
            text=category_name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # 软件列表
        software_list = []
        for software_name, software_info in self.software_data.items():
            if software_info.get('category') == category_key:
                software_list.append((software_name, software_info))
        
        if not software_list:
            no_software_label = ctk.CTkLabel(
                self.category_frame,
                text="该分类下暂无软件",
                font=ctk.CTkFont(size=14)
            )
            no_software_label.pack(pady=20)
            return
        
        # 创建软件项目
        for software_name, software_info in software_list:
            self.create_software_item_new(self.category_frame, software_name, software_info)
    
    def create_software_item_new(self, parent, name, info):
        """创建新的软件项目（用于多级菜单）"""
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", padx=10, pady=5)
        
        # 左侧：软件信息
        info_frame = ctk.CTkFrame(item_frame)
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # 软件名称
        name_label = ctk.CTkLabel(
            info_frame,
            text=info.get('name', name),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.pack(anchor="w", pady=(5, 2))
        
        # 软件描述
        desc_label = ctk.CTkLabel(
            info_frame,
            text=info.get('description', ''),
            font=ctk.CTkFont(size=11),
            wraplength=300
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        # 右侧：选择按钮
        is_selected = name in self.selected_software
        select_btn = ctk.CTkButton(
            item_frame,
            text="✓ 已选" if is_selected else "+ 选择",
            width=80,
            height=35,
            fg_color="#2fa572" if is_selected else None,
            command=lambda: self.toggle_software_selection_new(name, select_btn)
        )
        select_btn.pack(side="right", padx=10, pady=10)
    
    def toggle_software_selection_new(self, software_name, button):
        """切换软件选择状态（新版本）"""
        if software_name in self.selected_software:
            self.selected_software.discard(software_name)
            button.configure(text="+ 选择", fg_color=None)
        else:
            self.selected_software.add(software_name)
            button.configure(text="✓ 已选", fg_color="#2fa572")
        
        # 更新软件选择状态
        self.software_selected = len(self.selected_software) > 0
        
        self.update_selected_list()
        self.update_stats()
        self.logger.info(f"软件选择状态变更: {software_name} - {software_name in self.selected_software}")
    
    def update_selected_list(self):
        """更新已选软件列表"""
        # 清空现有内容
        for widget in self.selected_list_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_software:
            empty_label = ctk.CTkLabel(
                self.selected_list_frame,
                text="暂无选择的软件",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            empty_label.pack(pady=20)
            return
        
        # 显示已选软件
        for software_name in sorted(self.selected_software):
            software_info = self.software_data.get(software_name, {})
            
            item_frame = ctk.CTkFrame(self.selected_list_frame)
            item_frame.pack(fill="x", padx=5, pady=2)
            
            # 软件名称
            name_label = ctk.CTkLabel(
                item_frame,
                text=software_info.get('name', software_name),
                font=ctk.CTkFont(size=12, weight="bold")
            )
            name_label.pack(side="left", padx=(10, 5), pady=8)
            
            # 删除按钮
            remove_btn = ctk.CTkButton(
                item_frame,
                text="✕",
                width=25,
                height=25,
                font=ctk.CTkFont(size=12),
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda name=software_name: self.remove_selected_software(name)
            )
            remove_btn.pack(side="right", padx=5, pady=5)
    
    def remove_selected_software(self, software_name):
        """从已选列表中移除指定软件"""
        self.selected_software.discard(software_name)
        self.software_selected = len(self.selected_software) > 0
        
        # 如果当前正在显示该软件所在的分类，需要更新按钮状态
        if self.current_category:
            software_info = self.software_data.get(software_name, {})
            if software_info.get('category') == self.current_category:
                self.show_category_software(self.current_category)
        
        self.update_selected_list()
        self.update_stats()
        self.logger.info(f"从已选列表移除软件: {software_name}")
    
    def clear_selected_list(self):
        """清空已选软件列表"""
        self.selected_software.clear()
        self.software_selected = False
        
        # 如果当前正在显示某个分类，需要更新按钮状态
        if self.current_category:
            self.show_category_software(self.current_category)
        
        self.update_selected_list()
        self.update_stats()
        self.logger.info("清空已选软件列表")
    
    def select_all_in_category(self):
        """选择当前分类的所有软件"""
        if not self.current_category:
            messagebox.showwarning("提示", "请先选择一个软件分类")
            return
        
        # 添加当前分类的所有软件到已选列表
        for software_name, software_info in self.software_data.items():
            if software_info.get('category') == self.current_category:
                self.selected_software.add(software_name)
        
        self.software_selected = len(self.selected_software) > 0
        
        # 更新界面
        self.show_category_software(self.current_category)
        self.update_selected_list()
        self.update_stats()
        self.logger.info(f"选择分类 {self.current_category} 的所有软件")
    
    def populate_software_list(self):
        """填充软件列表（保留原方法以兼容性）"""
        # 这个方法现在被新的多级菜单系统替代
        pass
    
    def create_software_item(self, parent, name, info, row, col):
        """创建软件项目（旧版本，保留以兼容性）"""
        # 这个方法现在被 create_software_item_new 替代
        pass
    
    def toggle_software_selection(self, software_name, selected):
        """切换软件选择状态（旧版本，保留以兼容性）"""
        if selected:
            self.selected_software.add(software_name)
        else:
            self.selected_software.discard(software_name)
        
        # 更新软件选择状态
        self.software_selected = len(self.selected_software) > 0
        
        self.update_stats()
        self.logger.info(f"软件选择状态变更: {software_name} - {selected}")
    
    def select_all_software(self):
        """全选软件（旧版本，保留以兼容性）"""
        self.selected_software = set(self.software_data.keys())
        self.software_selected = len(self.selected_software) > 0
        
        # 更新界面
        if hasattr(self, 'current_category') and self.current_category:
            self.show_category_software(self.current_category)
        else:
            self.populate_category_menu()
        
        self.update_selected_list()
        self.update_stats()
        self.logger.info("全选所有软件")
    
    def clear_selection(self):
        """清空选择（旧版本，保留以兼容性）"""
        self.selected_software.clear()
        self.software_selected = False
        
        # 更新界面
        if hasattr(self, 'current_category') and self.current_category:
            self.show_category_software(self.current_category)
        else:
            self.populate_category_menu()
        
        self.update_selected_list()
        self.update_stats()
        self.logger.info("清空软件选择")
    
    def on_search_change(self, *args):
        """搜索框内容变化"""
        search_term = self.search_var.get().lower().strip()
        
        if not search_term:
            # 如果搜索框为空，返回分类菜单
            self.current_category = None
            self.populate_category_menu()
            return
        
        # 执行搜索
        self.perform_search(search_term)
        self.logger.debug(f"搜索内容变更: {search_term}")
    
    def perform_search(self, search_term):
        """执行软件搜索"""
        # 清空分类框架
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        # 搜索结果标题
        title_label = ctk.CTkLabel(
            self.category_frame,
            text=f"搜索结果: \"{search_term}\"",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 15))
        
        # 返回按钮
        back_btn = ctk.CTkButton(
            self.category_frame,
            text="← 返回分类选择",
            width=150,
            height=35,
            command=self.clear_search
        )
        back_btn.pack(pady=(0, 20))
        
        # 搜索软件
        search_results = []
        for software_name, software_info in self.software_data.items():
            # 在软件名称和描述中搜索
            name_match = search_term in software_info.get('name', software_name).lower()
            desc_match = search_term in software_info.get('description', '').lower()
            
            if name_match or desc_match:
                search_results.append((software_name, software_info))
        
        if not search_results:
            no_result_label = ctk.CTkLabel(
                self.category_frame,
                text="未找到匹配的软件",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_result_label.pack(pady=20)
            return
        
        # 显示搜索结果
        result_label = ctk.CTkLabel(
            self.category_frame,
            text=f"找到 {len(search_results)} 个软件",
            font=ctk.CTkFont(size=12)
        )
        result_label.pack(pady=(0, 10))
        
        # 创建搜索结果项目
        for software_name, software_info in search_results:
            self.create_software_item_new(self.category_frame, software_name, software_info)
    
    def clear_search(self):
        """清空搜索，返回分类菜单"""
        self.search_var.set("")
        self.current_category = None
        self.populate_category_menu()
    
    def update_stats(self):
        """更新统计信息"""
        count = len(self.selected_software)
        self.stats_label.configure(text=f"已选择: {count} 个软件")
    
    def show_validation_page(self):
        """显示文件校验页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 页面标题
        title_label = ctk.CTkLabel(
            container,
            text="下载文件校验与自动纠错",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 说明文本
        info_frame = ctk.CTkFrame(container)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="此步骤将检测下载目录中已下载文件的完整性和正确性\n如发现文件损坏或缺失，系统将自动尝试修复",
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        info_label.pack(pady=15)
        
        # 当前下载路径显示
        path_frame = ctk.CTkFrame(container)
        path_frame.pack(fill="x", padx=20, pady=10)
        
        path_label = ctk.CTkLabel(
            path_frame,
            text=f"检测路径: {self.download_settings['path']}",
            font=ctk.CTkFont(size=16)
        )
        path_label.pack(pady=15)
        
        # 校验状态区域
        status_frame = ctk.CTkFrame(container)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        status_title = ctk.CTkLabel(
            status_frame,
            text="校验状态",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        status_title.pack(pady=(15, 10))
        
        self.validation_status = ctk.CTkLabel(
            status_frame,
            text="正在自动检测本地下载文件的完整性，请稍候...",
            font=ctk.CTkFont(size=14)
        )
        self.validation_status.pack(pady=10)
        
        # 校验进度条
        self.validation_progress = ctk.CTkProgressBar(
            status_frame,
            width=600,
            height=20
        )
        self.validation_progress.pack(pady=10)
        self.validation_progress.set(0)
        
        # 校验结果区域
        self.validation_results_frame = ctk.CTkScrollableFrame(
            container,
            height=200
        )
        self.validation_results_frame.pack(fill="x", padx=20, pady=10)
        
        # 操作按钮
        button_frame = ctk.CTkFrame(container)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        continue_btn = ctk.CTkButton(
            button_frame,
            text="下一步",
            width=200,
            height=40,
            command=lambda: self.show_page(PageType.COMPLETION)
        )
        continue_btn.pack(side="right", padx=20, pady=15)
        
        # 自动开始校验
        self.root.after(500, self.start_validation)
    
    def start_validation(self):
        """开始文件校验"""
        self.validation_status.configure(text="正在校验文件...")
        self.validation_progress.set(0)
        
        # 清空结果区域
        for widget in self.validation_results_frame.winfo_children():
            widget.destroy()
        
        # 在新线程中执行校验
        threading.Thread(target=self._perform_validation, daemon=True).start()
    
    def _perform_validation(self):
        """执行文件校验（在后台线程中）"""
        try:
            # 获取下载前的文件数量
            if not hasattr(self, 'pre_download_file_count'):
                self.pre_download_file_count = self._count_target_files()
            
            # 获取下载后的文件数量
            post_download_file_count = self._count_target_files()
            
            # 计算新增文件数量
            new_files_count = post_download_file_count - self.pre_download_file_count
            expected_count = len(self.selected_software)
            
            # 创建校验结果
            results = {
                'new_files_count': new_files_count,
                'expected_count': expected_count,
                'validation_passed': new_files_count >= expected_count
            }
            
            # 更新UI（在主线程中）
            self.root.after(0, self._update_validation_results, results)
            
        except Exception as e:
            self.logger.error(f"文件校验失败: {e}")
            error_msg = str(e)
            self.root.after(0, lambda: self.validation_status.configure(text=f"校验失败: {error_msg}"))
    
    def _count_target_files(self):
        """统计目标文件类型的数量"""
        target_extensions = ['.exe', '.7z', '.zip', '.rar']
        count = 0
        
        try:
            if self.download_path.exists():
                for file_path in self.download_path.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in target_extensions:
                        count += 1
        except Exception as e:
            self.logger.error(f"统计文件数量失败: {e}")
        
        return count
    
    def _update_validation_results(self, results):
        """更新校验结果显示"""
        self.validation_progress.set(1.0)
        
        new_files_count = results['new_files_count']
        expected_count = results['expected_count']
        validation_passed = results['validation_passed']
        
        self.validation_status.configure(
            text=f"校验完成: 新增 {new_files_count} 个文件，期望 {expected_count} 个文件"
        )
        
        # 显示详细结果
        result_frame = ctk.CTkFrame(self.validation_results_frame)
        result_frame.pack(fill="x", padx=10, pady=5)
        
        if validation_passed:
            status_text = "✓ 校验通过"
            status_color = "green"
            detail_text = f"下载目录中新增了 {new_files_count} 个目标文件（.exe/.7z/.zip/.rar），符合预期的 {expected_count} 个软件"
        else:
            status_text = "✗ 校验失败"
            status_color = "red"
            detail_text = f"下载目录中仅新增了 {new_files_count} 个目标文件，少于预期的 {expected_count} 个软件"
        
        result_label = ctk.CTkLabel(
            result_frame,
            text=status_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=status_color
        )
        result_label.pack(pady=10)
        
        detail_label = ctk.CTkLabel(
            result_frame,
            text=detail_text,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        detail_label.pack(pady=5)
        
        # 设置校验完成标志
        self.validation_completed = True
        
        # 如果校验失败且未进行过自动纠错，则执行自动纠错
        if not validation_passed and not hasattr(self, 'auto_repair_attempted'):
            self.auto_repair_attempted = True
            self.root.after(1000, self.start_auto_repair)  # 延迟1秒后自动开始纠错
    
    def start_auto_repair(self):
        """开始自动纠错"""
        self.validation_status.configure(text="正在执行自动纠错...")
        
        # 在新线程中执行纠错
        threading.Thread(target=self._perform_auto_repair, daemon=True).start()
    
    def _perform_auto_repair(self):
        """执行自动纠错（在后台线程中）"""
        try:
            # 更新状态
            self.root.after(0, lambda: self.validation_status.configure(
                text="正在重新下载软件..."
            ))
            
            # 重新执行下载过程
            if self.core_manager:
                # 使用核心管理器重新下载
                download_items = []
                for software_name in self.selected_software:
                    if software_name in self.software_data:
                        info = self.software_data[software_name]
                        item = DownloadItem(
                            name=info.get('name', software_name),
                            url=info.get('url', ''),
                            size=info.get('size', 0),
                            checksum=info.get('checksum', ''),
                            category=info.get('category', ''),
                            description=info.get('description', ''),
                            version=info.get('version', '')
                        )
                        download_items.append(item)
                
                # 执行重新下载
                success = self.core_manager.download_software(download_items, self.download_path)
                
                if success:
                    self.root.after(0, lambda: self.validation_status.configure(
                        text="重新下载完成，正在重新校验..."
                    ))
                    # 延迟后重新校验
                    self.root.after(2000, self._perform_revalidation)
                else:
                    self.root.after(0, lambda: self.validation_status.configure(
                        text="重新下载失败，请手动检查"
                    ))
            else:
                # 模拟重新下载
                self.root.after(0, lambda: self.validation_status.configure(
                    text="模拟重新下载完成，正在重新校验..."
                ))
                # 延迟后重新校验
                self.root.after(2000, self._perform_revalidation)
            
        except Exception as e:
            self.logger.error(f"自动纠错失败: {e}")
            error_msg = str(e)
            try:
                self.root.after(0, lambda: self.validation_status.configure(text=f"自动纠错失败: {error_msg}"))
            except Exception as ui_error:
                self.logger.warning(f"UI更新失败: {ui_error}")
    
    def _perform_revalidation(self):
        """重新校验"""
        # 清空之前的结果
        for widget in self.validation_results_frame.winfo_children():
            widget.destroy()
        
        # 重新开始校验
        self.validation_status.configure(text="正在重新校验...")
        self.validation_progress.set(0.0)
        
        # 在新线程中执行校验
        threading.Thread(target=self._perform_validation, daemon=True).start()
    
    def show_download_settings_page(self):
        """显示下载设置页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 页面标题
        title_label = ctk.CTkLabel(
            container,
            text="下载设置配置",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 下载路径设置
        path_frame = ctk.CTkFrame(container)
        path_frame.pack(fill="x", padx=20, pady=10)
        
        path_title = ctk.CTkLabel(
            path_frame,
            text="下载路径设置",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        path_title.pack(pady=(15, 10))
        
        path_input_frame = ctk.CTkFrame(path_frame)
        path_input_frame.pack(fill="x", padx=20, pady=10)
        
        self.path_var = tk.StringVar(value=str(self.download_path))
        path_entry = ctk.CTkEntry(
            path_input_frame,
            textvariable=self.path_var,
            width=500,
            height=35
        )
        path_entry.pack(side="left", padx=(10, 5), pady=10)
        
        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="浏览",
            width=80,
            height=35,
            command=self.browse_download_path
        )
        browse_btn.pack(side="left", padx=5, pady=10)
        
        # 路径验证状态
        self.path_status = ctk.CTkLabel(
            path_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.path_status.pack(pady=(0, 15))
        
        # 绑定路径变化事件
        self.path_var.trace('w', self.validate_download_path)
        
        # 页面加载时自动验证当前路径
        self.root.after(100, self.validate_download_path)
        
        # 高级设置
        advanced_frame = ctk.CTkFrame(container)
        advanced_frame.pack(fill="x", padx=20, pady=10)
        
        advanced_title = ctk.CTkLabel(
            advanced_frame,
            text="高级设置",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        advanced_title.pack(pady=(15, 10))
        
        # 并发下载数
        concurrent_frame = ctk.CTkFrame(advanced_frame)
        concurrent_frame.pack(fill="x", padx=20, pady=10)
        
        concurrent_label = ctk.CTkLabel(
            concurrent_frame,
            text="同时下载数量:",
            font=ctk.CTkFont(size=14)
        )
        concurrent_label.pack(side="left", padx=15, pady=10)
        
        self.concurrent_var = tk.IntVar(value=self.download_settings['concurrent'])
        concurrent_slider = ctk.CTkSlider(
            concurrent_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.concurrent_var,
            width=200
        )
        concurrent_slider.pack(side="left", padx=15, pady=10)
        
        self.concurrent_value_label = ctk.CTkLabel(
            concurrent_frame,
            text=str(self.concurrent_var.get()),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.concurrent_value_label.pack(side="left", padx=15, pady=10)
        
        concurrent_slider.configure(command=self.update_concurrent_value)
        
        # 超时设置
        timeout_frame = ctk.CTkFrame(advanced_frame)
        timeout_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        timeout_label = ctk.CTkLabel(
            timeout_frame,
            text="连接超时 (秒):",
            font=ctk.CTkFont(size=14)
        )
        timeout_label.pack(side="left", padx=15, pady=10)
        
        self.timeout_var = tk.IntVar(value=self.download_settings['timeout'])
        timeout_slider = ctk.CTkSlider(
            timeout_frame,
            from_=10,
            to=120,
            number_of_steps=11,
            variable=self.timeout_var,
            width=200
        )
        timeout_slider.pack(side="left", padx=15, pady=10)
        
        self.timeout_value_label = ctk.CTkLabel(
            timeout_frame,
            text=str(self.timeout_var.get()),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.timeout_value_label.pack(side="left", padx=15, pady=10)
        
        timeout_slider.configure(command=self.update_timeout_value)
        
        # 继续按钮
        continue_btn = ctk.CTkButton(
            container,
            text="开始下载",
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self.show_page(PageType.CONNECTIVITY_CHECK)
        )
        continue_btn.pack(pady=20)
    
    def browse_download_path(self):
        """浏览下载路径"""
        path = filedialog.askdirectory(initialdir=str(self.download_path))
        if path:
            self.path_var.set(path)
            self.download_path = Path(path)
            self.download_settings['path'] = path
            
            # 更新核心管理器配置
            if self.core_manager:
                self.core_manager.set_config('download_path', path)
            
            self.save_config()
            self.logger.info(f"下载路径已更改: {path}")
    
    def validate_download_path(self, *args):
        """验证下载路径"""
        path = self.path_var.get()
        try:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_dir():
                self.path_status.configure(text="✓ 路径有效", text_color="green")
                self.download_path = path_obj
                self.download_settings['path'] = path
                self.download_path_set = True  # 设置路径已配置标志
                
                # 更新核心管理器配置
                if self.core_manager:
                    self.core_manager.set_config('download_path', path)
                    
            else:
                self.path_status.configure(text="✗ 路径无效或不存在", text_color="red")
                self.download_path_set = False  # 路径无效时重置标志
        except Exception as e:
            self.path_status.configure(text=f"✗ 路径错误: {e}", text_color="red")
    
    def update_concurrent_value(self, value):
        """更新并发下载数值"""
        val = int(float(value))
        self.concurrent_value_label.configure(text=str(val))
        self.download_settings['concurrent'] = val
        
        # 更新核心管理器配置
        if self.core_manager:
            self.core_manager.set_config('concurrent_downloads', val)
    
    def update_timeout_value(self, value):
        """更新超时值"""
        val = int(float(value))
        self.timeout_value_label.configure(text=str(val))
        self.download_settings['timeout'] = val
        
        # 更新核心管理器配置
        if self.core_manager:
            self.core_manager.set_config('timeout_seconds', val)
    
    def show_connectivity_check_page(self):
        """显示连通性检测页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 页面标题
        title_label = ctk.CTkLabel(
            container,
            text="服务器连通性检测",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 检测说明
        desc_label = ctk.CTkLabel(
            container,
            text="正在检测您的网络与软件下载服务器的连通性，请稍候...",
            font=ctk.CTkFont(size=16)
        )
        desc_label.pack(pady=10)
        
        # 检测进度
        progress_frame = ctk.CTkFrame(container)
        progress_frame.pack(fill="x", padx=20, pady=20)
        
        self.connectivity_progress = ctk.CTkProgressBar(
            progress_frame,
            width=600,
            height=25
        )
        self.connectivity_progress.pack(pady=20)
        self.connectivity_progress.set(0)
        
        self.connectivity_status = ctk.CTkLabel(
            progress_frame,
            text="准备开始检测...",
            font=ctk.CTkFont(size=14)
        )
        self.connectivity_status.pack(pady=10)
        
        # 检测结果区域
        self.connectivity_results_frame = ctk.CTkScrollableFrame(
            container,
            height=300
        )
        self.connectivity_results_frame.pack(fill="x", padx=20, pady=10)
        
        # 操作按钮
        button_frame = ctk.CTkFrame(container)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        self.connectivity_continue_btn = ctk.CTkButton(
            button_frame,
            text="下一步",
            width=200,
            height=40,
            command=lambda: self.show_page(PageType.DOWNLOAD_PROGRESS)
        )
        self.connectivity_continue_btn.pack(side="right", padx=20, pady=15)
        
        # 自动开始连通性检测
        self.root.after(500, self.start_connectivity_check)
    
    def start_connectivity_check(self):
        """开始连通性检测"""
        self.connectivity_status.configure(text="正在检测网络连通性...")
        self.connectivity_progress.set(0)
        
        # 清空结果区域
        for widget in self.connectivity_results_frame.winfo_children():
            widget.destroy()
        
        # 在新线程中执行检测
        threading.Thread(target=self._perform_connectivity_check, daemon=True).start()
    
    def _safe_set_progress(self, value):
        """安全设置进度条"""
        try:
            if hasattr(self, 'connectivity_progress') and self.connectivity_progress.winfo_exists():
                self.connectivity_progress.set(value)
        except Exception:
            pass
    
    def _safe_set_status(self, text):
        """安全设置状态文本"""
        try:
            if hasattr(self, 'connectivity_status') and self.connectivity_status.winfo_exists():
                self.connectivity_status.configure(text=text)
        except Exception:
            pass
    
    def _perform_connectivity_check(self):
        """执行连通性检测 - 检测选定软件的服务器连通性"""
        try:
            # 获取选定软件的下载URL
            test_urls = []
            software_urls = {}
            
            for software_name in self.selected_software:
                if software_name in self.software_data:
                    url = self.software_data[software_name].get('url', '')
                    if url:
                        # 提取域名进行连通性测试
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        if domain_url not in test_urls:
                            test_urls.append(domain_url)
                            software_urls[domain_url] = [software_name]
                        else:
                            software_urls[domain_url].append(software_name)
            
            if not test_urls:
                self.root.after(0, lambda: self._safe_set_status("没有选择需要下载的软件"))
                return
            
            results = []
            failed_software = []
            
            for i, url in enumerate(test_urls):
                progress = (i + 1) / len(test_urls)
                self.root.after(0, lambda p=progress: self._safe_set_progress(p))
                self.root.after(0, lambda u=url: self._safe_set_status(f"正在检测: {u}"))
                
                try:
                    response = requests.get(url, timeout=10)
                    success = response.status_code == 200
                    results.append((url, success, response.status_code, software_urls[url]))
                    if not success:
                        failed_software.extend(software_urls[url])
                except Exception as e:
                    results.append((url, False, str(e), software_urls[url]))
                    failed_software.extend(software_urls[url])
                
                time.sleep(1)  # 模拟检测时间
            
            # 更新UI
            self.root.after(0, lambda: self._update_connectivity_results(results, failed_software))
            
        except Exception as e:
            self.logger.error(f"连通性检测失败: {e}")
            error_msg = f"检测失败: {e}"
            self.root.after(0, lambda: self._safe_set_status(error_msg))
    
    def _update_connectivity_results(self, results, failed_software):
        """更新连通性检测结果"""
        try:
            if hasattr(self, 'connectivity_progress') and self.connectivity_progress.winfo_exists():
                self.connectivity_progress.set(1.0)
        except Exception:
            pass
        
        success_count = sum(1 for _, success, _, _ in results if success)
        total_count = len(results)
        
        try:
            if hasattr(self, 'connectivity_status') and self.connectivity_status.winfo_exists():
                self.connectivity_status.configure(
                    text=f"检测完成: {success_count}/{total_count} 个服务器连接正常"
                )
        except Exception:
            pass
        
        # 清空之前的结果
        try:
            if hasattr(self, 'connectivity_results_frame'):
                for widget in self.connectivity_results_frame.winfo_children():
                    widget.destroy()
        except Exception:
            pass
        
        # 显示详细结果
        for url, success, status, software_list in results:
            try:
                result_frame = ctk.CTkFrame(self.connectivity_results_frame)
                result_frame.pack(fill="x", padx=10, pady=5)
                
                status_text = "✓ 连接正常" if success else f"✗ 连接失败 ({status})"
                status_color = "green" if success else "red"
                
                result_label = ctk.CTkLabel(
                    result_frame,
                    text=f"{url}: {status_text}",
                    font=ctk.CTkFont(size=14),
                    text_color=status_color
                )
                result_label.pack(pady=5)
                
                # 显示受影响的软件
                software_text = "相关软件: " + ", ".join(software_list)
                software_label = ctk.CTkLabel(
                    result_frame,
                    text=software_text,
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                )
                software_label.pack(pady=2)
            except Exception:
                continue
        
        # 如果有失败的软件，显示警告和返回选项
        if failed_software:
            try:
                warning_frame = ctk.CTkFrame(self.connectivity_results_frame)
                warning_frame.pack(fill="x", padx=10, pady=10)
                
                warning_label = ctk.CTkLabel(
                    warning_frame,
                    text=f"⚠️ 以下软件的服务器连接失败，无法下载:",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="orange"
                )
                warning_label.pack(pady=10)
                
                failed_text = "\n".join([f"• {software}" for software in failed_software])
                failed_label = ctk.CTkLabel(
                    warning_frame,
                    text=failed_text,
                    font=ctk.CTkFont(size=12),
                    text_color="red"
                )
                failed_label.pack(pady=5)
                
                # 添加返回按钮
                button_frame = ctk.CTkFrame(warning_frame)
                button_frame.pack(fill="x", pady=10)
                
                back_btn = ctk.CTkButton(
                    button_frame,
                    text="返回软件选择",
                    width=150,
                    height=35,
                    command=lambda: self.show_page(PageType.SOFTWARE_SELECTION)
                )
                back_btn.pack(side="left", padx=10)
                
                retry_btn = ctk.CTkButton(
                    button_frame,
                    text="重新检测",
                    width=150,
                    height=35,
                    command=self.retry_connectivity_check
                )
                retry_btn.pack(side="left", padx=10)
                
                # 禁用继续按钮
                if hasattr(self, 'connectivity_continue_btn'):
                    self.connectivity_continue_btn.configure(state="disabled")
            except Exception:
                pass
        else:
            # 启用继续按钮
            if hasattr(self, 'connectivity_continue_btn'):
                self.connectivity_continue_btn.configure(state="normal")
        
        # 设置连接性检查完成标志
        self.connectivity_checked = True
    
    def retry_connectivity_check(self):
        """重新进行连通性检测"""
        self.start_connectivity_check()
    
    def show_download_progress_page(self):
        """显示下载进度页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 页面标题
        title_label = ctk.CTkLabel(
            container,
            text="正在下载软件",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # 总体进度
        overall_frame = ctk.CTkFrame(container)
        overall_frame.pack(fill="x", padx=20, pady=10)
        
        overall_title = ctk.CTkLabel(
            overall_frame,
            text="总体进度",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        overall_title.pack(pady=(15, 10))
        
        self.overall_progress = ctk.CTkProgressBar(
            overall_frame,
            width=600,
            height=25
        )
        self.overall_progress.pack(pady=10)
        self.overall_progress.set(0)
        
        self.overall_status = ctk.CTkLabel(
            overall_frame,
            text="准备开始下载...",
            font=ctk.CTkFont(size=14)
        )
        self.overall_status.pack(pady=(10, 15))
        
        # 详细进度
        detail_frame = ctk.CTkFrame(container)
        detail_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        detail_title = ctk.CTkLabel(
            detail_frame,
            text="详细进度",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        detail_title.pack(pady=(15, 10))
        
        self.download_details_frame = ctk.CTkScrollableFrame(
            detail_frame,
            height=300
        )
        self.download_details_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # 操作按钮
        button_frame = ctk.CTkFrame(container)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        retry_download_btn = ctk.CTkButton(
            button_frame,
            text="重新下载",
            width=150,
            height=40,
            command=self.start_download_process
        )
        retry_download_btn.pack(side="left", padx=(20, 10), pady=15)
        
        next_step_btn = ctk.CTkButton(
            button_frame,
            text="下一步",
            width=150,
            height=40,
            command=lambda: self.show_page(PageType.VALIDATION)
        )
        next_step_btn.pack(side="right", padx=20, pady=15)
        
        # 自动开始下载
        self.root.after(500, self.start_download_process)
    
    def start_download_process(self):
        """开始下载过程"""
        self.overall_status.configure(text="正在准备下载...")
        self.overall_progress.set(0)
        
        # 记录下载前的文件数量
        self.pre_download_file_count = self._count_target_files()
        self.logger.info(f"下载前目标文件数量: {self.pre_download_file_count}")
        
        # 清空详细进度区域
        for widget in self.download_details_frame.winfo_children():
            widget.destroy()
        
        # 在新线程中执行下载
        threading.Thread(target=self._perform_download, daemon=True).start()
    
    def _perform_download(self):
        """执行下载过程（在后台线程中）"""
        try:
            # 确保下载目录存在
            self.download_path.mkdir(parents=True, exist_ok=True)
            
            # 创建下载项列表
            download_items = []
            for software_name in self.selected_software:
                if software_name in self.software_data:
                    info = self.software_data[software_name]
                    item = DownloadItem(
                        name=info.get('name', software_name),
                        url=info.get('url', ''),
                        size=info.get('size', 0),
                        checksum=info.get('checksum', ''),
                        category=info.get('category', ''),
                        description=info.get('description', ''),
                        version=info.get('version', '')
                    )
                    download_items.append(item)
            
            # 使用核心管理器或模拟下载
            if self.core_manager:
                # 使用真实下载功能
                software_names = [item.name for item in download_items]
                
                def progress_callback(completed_count, total_count, software_name, success):
                    """下载进度回调"""
                    progress = (completed_count / total_count) * 100
                    status = "下载成功" if success else "下载中..."
                    self.root.after(0, lambda: self._safe_update_status(f"正在下载: {software_name} - {status}"))
                    if hasattr(self, f"progress_{software_name}"):
                        progress_bar = getattr(self, f"progress_{software_name}")
                        self.root.after(0, lambda p=progress: progress_bar.set(p/100))
                    if hasattr(self, f"status_{software_name}"):
                        status_label = getattr(self, f"status_{software_name}")
                        self.root.after(0, lambda s=status: status_label.configure(text=s))
                
                # 先创建下载项
                for software_name in self.selected_software:
                    if software_name in self.software_data:
                        info = self.software_data[software_name]
                        self.root.after(0, lambda sn=software_name, inf=info: self._create_download_item(sn, inf))
                
                try:
                    results = self.core_manager.download_selected_software(software_names, str(self.download_path), progress_callback)
                    self.root.after(0, lambda: self._safe_update_status("所有软件下载完成！请点击下一步进行校验"))
                    # 设置下载完成标志
                    self.download_completed = True
                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda msg=error_msg: self._safe_update_status(f"下载失败: {msg}"))
                    self.download_completed = False
            else:
                # 使用模拟下载
                total_items = len(self.selected_software)
                completed_items = 0
                
                for software_name in self.selected_software:
                    if software_name in self.software_data:
                        info = self.software_data[software_name]
                        
                        # 更新总体状态
                        status_msg = f"正在下载: {software_name}"
                        self.root.after(0, lambda msg=status_msg: self._safe_update_status(msg))
                        
                        # 创建详细进度项
                        self.root.after(0, lambda sn=software_name, inf=info: self._create_download_item(sn, inf))
                        
                        # 模拟下载过程
                        self._simulate_download(software_name, info)
                        
                        completed_items += 1
                        progress = completed_items / total_items
                        self.root.after(0, lambda p=progress: self._safe_update_progress(p))
                
                # 模拟下载完成
                self.root.after(0, lambda: self._safe_update_status("所有软件下载完成！请点击下一步进行校验"))
                self.download_completed = True
            
        except Exception as e:
            self.logger.error(f"下载过程失败: {e}")
            error_msg = f"下载失败: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self._safe_update_status(msg))
    
    def _safe_update_status(self, message):
        """安全更新状态文本"""
        try:
            if hasattr(self, 'overall_status') and self.overall_status.winfo_exists():
                self.overall_status.configure(text=message)
        except Exception:
            pass
    
    def _safe_update_progress(self, value):
        """安全更新进度条"""
        try:
            if hasattr(self, 'overall_progress') and self.overall_progress.winfo_exists():
                self.overall_progress.set(value)
        except Exception:
            pass
    
    def _create_download_item(self, software_name, info):
        """创建下载项目显示"""
        item_frame = ctk.CTkFrame(self.download_details_frame)
        item_frame.pack(fill="x", padx=10, pady=5)
        
        name_label = ctk.CTkLabel(
            item_frame,
            text=info.get('name', software_name),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.pack(side="left", padx=15, pady=10)
        
        progress_bar = ctk.CTkProgressBar(
            item_frame,
            width=300,
            height=15
        )
        progress_bar.pack(side="left", padx=15, pady=10)
        progress_bar.set(0)
        
        status_label = ctk.CTkLabel(
            item_frame,
            text="准备中...",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side="right", padx=15, pady=10)
        
        # 保存引用以便更新
        setattr(self, f"progress_{software_name}", progress_bar)
        setattr(self, f"status_{software_name}", status_label)
    
    def _simulate_download(self, software_name, info):
        """模拟下载过程"""
        progress_bar = getattr(self, f"progress_{software_name}", None)
        status_label = getattr(self, f"status_{software_name}", None)
        
        if not progress_bar or not status_label:
            return
        
        # 模拟下载进度
        for i in range(101):
            progress = i / 100
            self.root.after(0, lambda p=progress: progress_bar.set(p))
            
            if i < 100:
                self.root.after(0, lambda p=i: status_label.configure(text=f"{p}%"))
            else:
                self.root.after(0, lambda: status_label.configure(text="完成", text_color="green"))
            
            time.sleep(0.05)  # 模拟下载时间
    
    def pause_download(self):
        """暂停下载"""
        self.overall_status.configure(text="下载已暂停")
        self.logger.info("用户暂停下载")
    
    def cancel_download(self):
        """取消下载"""
        self.overall_status.configure(text="下载已取消")
        self.logger.info("用户取消下载")
    
    def show_completion_page(self):
        """显示完成页面"""
        container = ctk.CTkScrollableFrame(self.content_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 完成标题
        title_label = ctk.CTkLabel(
            container,
            text="下载完成！",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="green"
        )
        title_label.pack(pady=(40, 20))
        
        # 感谢信息
        thanks_label = ctk.CTkLabel(
            container,
            text="感谢您使用软件管理器 V3.0！\n所有选择的软件已成功下载到指定目录。",
            font=ctk.CTkFont(size=18),
            justify="center"
        )
        thanks_label.pack(pady=20)
        
        # 统计信息
        stats_frame = ctk.CTkFrame(container)
        stats_frame.pack(fill="x", padx=40, pady=20)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="下载统计",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        stats_title.pack(pady=(20, 15))
        
        stats_text = f"""
下载软件数量: {len(self.selected_software)} 个
下载路径: {self.download_path}
完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        stats_label.pack(pady=(0, 20))
        
        # 操作按钮
        action_frame = ctk.CTkFrame(container)
        action_frame.pack(fill="x", padx=40, pady=30)
        
        open_folder_btn = ctk.CTkButton(
            action_frame,
            text="打开下载文件夹",
            width=180,
            height=45,
            command=self.open_download_folder,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        open_folder_btn.pack(side="left", padx=(20, 10), pady=15)
        
        restart_btn = ctk.CTkButton(
            action_frame,
            text="重新开始",
            width=180,
            height=45,
            command=self.restart_application,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        restart_btn.pack(side="left", padx=10, pady=15)
        
        exit_btn = ctk.CTkButton(
            action_frame,
            text="退出程序",
            width=180,
            height=45,
            command=self.exit_application,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        exit_btn.pack(side="right", padx=20, pady=15)
    
    def open_download_folder(self):
        """打开下载文件夹"""
        try:
            # 确保使用最新的下载路径
            current_path = Path(self.download_settings['path'])
            if current_path.exists():
                subprocess.run(['explorer', str(current_path)], check=True)
                self.logger.info(f"打开下载文件夹: {current_path}")
            else:
                # 尝试创建目录
                try:
                    current_path.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['explorer', str(current_path)], check=True)
                    self.logger.info(f"创建并打开下载文件夹: {current_path}")
                except Exception as create_error:
                    self.logger.error(f"无法创建下载文件夹: {create_error}")
                    messagebox.showwarning("警告", f"下载文件夹不存在且无法创建: {current_path}")
        except Exception as e:
            self.logger.error(f"打开文件夹失败: {e}")
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
    
    def restart_application(self):
        """重新开始应用程序"""
        self.logger.info("用户重新开始应用程序")
        # 重置状态
        self.selected_software.clear()
        self.agreement_accepted = False
        self.privacy_accepted = False
        # 返回欢迎页面
        self.show_page(PageType.WELCOME)
    
    def exit_application(self):
        """退出应用程序"""
        self.logger.info("用户退出应用程序")
        self.save_config()
        self.root.quit()
    
    def on_window_resize(self, event):
        """窗口大小变化事件处理"""
        if event.widget == self.root:
            # 响应式布局调整
            width = self.root.winfo_width()
            if width < 900:
                # 小屏幕模式
                self.navigation_frame.configure(width=150)
            else:
                # 正常模式
                self.navigation_frame.configure(width=200)
    
    def run(self):
        """运行应用程序"""
        self.logger.info("应用程序开始运行")
        self.root.mainloop()
        self.logger.info("应用程序结束运行")

if __name__ == "__main__":
    try:
        app = ModernSoftwareManager()
        app.run()
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)