#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件资源整合桌面应用程序
类似Ninite的一键安装程序生成器
支持1000+款常用软件的管理和安装
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

class SoftwareManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("软件资源整合管理器 v1.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口图标和样式
        self.setup_styles()
        
        # 软件数据
        self.software_data = self.load_software_data()
        self.selected_software = set()
        
        # 创建界面
        self.create_widgets()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure('Title.TLabel', font=('Microsoft YaHei', 16, 'bold'), background='#f0f0f0')
        style.configure('Heading.TLabel', font=('Microsoft YaHei', 12, 'bold'), background='#f0f0f0')
        style.configure('Custom.TButton', font=('Microsoft YaHei', 10), padding=10)
        style.configure('Treeview', font=('Microsoft YaHei', 9))
        style.configure('Treeview.Heading', font=('Microsoft YaHei', 10, 'bold'))
        
    def load_software_data(self):
        """加载软件数据"""
        try:
            with open('software_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_software_data()
    
    def get_default_software_data(self):
        """获取默认软件数据"""
        return {
            "系统工具": {
                "系统优化": [
                    {"name": "CCleaner", "url": "https://download.ccleaner.com/ccsetup.exe", "description": "系统清理优化工具"},
                    {"name": "Advanced SystemCare", "url": "https://download.iobit.com/asc-setup.exe", "description": "系统优化加速工具"},
                    {"name": "Wise Care 365", "url": "https://downloads.wisecleaner.com/soft/WiseCare365.exe", "description": "系统维护优化套件"},
                    {"name": "Glary Utilities", "url": "https://download.glarysoft.com/gu5setup.exe", "description": "系统优化工具集"},
                    {"name": "Driver Booster", "url": "https://download.iobit.com/driver_booster_setup.exe", "description": "驱动程序更新工具"},
                    {"name": "IObit Uninstaller", "url": "https://download.iobit.com/iobituninstaller.exe", "description": "软件卸载工具"},
                    {"name": "Revo Uninstaller", "url": "https://download.revouninstaller.com/revosetup.exe", "description": "强力卸载工具"},
                    {"name": "Ashampoo WinOptimizer", "url": "https://www.ashampoo.com/downloads/winoptimizer.exe", "description": "Windows优化工具"},
                    {"name": "O&O Defrag", "url": "https://dl.oo-software.com/files/oosuite/oodefrag.exe", "description": "磁盘碎片整理工具"},
                    {"name": "Disk Drill", "url": "https://downloads.cleverfiles.com/DiskDrill.exe", "description": "数据恢复工具"}
                ],
                "压缩解压": [
                    {"name": "WinRAR", "url": "https://www.rarlab.com/rar/winrar-x64.exe", "description": "经典压缩解压工具"},
                    {"name": "7-Zip", "url": "https://www.7-zip.org/a/7z-x64.exe", "description": "免费开源压缩工具"},
                    {"name": "Bandizip", "url": "https://dl.bandisoft.com/bandizip.std/BANDIZIP-SETUP-STD-X64.EXE", "description": "轻量级压缩工具"},
                    {"name": "PeaZip", "url": "https://github.com/peazip/PeaZip/releases/latest/download/peazip-portable.exe", "description": "免费压缩归档工具"},
                    {"name": "WinZip", "url": "https://download.winzip.com/winzip.exe", "description": "专业压缩软件"},
                    {"name": "7-Zip Portable", "url": "https://portableapps.com/apps/utilities/7-zip_portable", "description": "7-Zip便携版"},
                    {"name": "IZArc", "url": "https://www.izarc.org/download/izarc.exe", "description": "多格式压缩工具"},
                    {"name": "Hamster Zip Archiver", "url": "https://hamstersoft.com/downloads/hamster-zip-archiver.exe", "description": "简单易用的压缩工具"},
                    {"name": "PowerArchiver", "url": "https://www.powerarchiver.com/download/powerarchiver.exe", "description": "专业压缩归档工具"},
                    {"name": "ZipGenius", "url": "https://www.zipgenius.com/downloads/zipgenius.exe", "description": "多功能压缩工具"}
                ]
            },
            "办公软件": {
                "文档处理": [
                    {"name": "Microsoft Office", "url": "https://www.microsoft.com/office", "description": "微软办公套件"},
                    {"name": "WPS Office", "url": "https://wps.com/download", "description": "金山办公套件"},
                    {"name": "LibreOffice", "url": "https://download.libreoffice.org/libreoffice/stable/", "description": "免费开源办公套件"},
                    {"name": "Apache OpenOffice", "url": "https://www.openoffice.org/download/", "description": "开源办公软件"},
                    {"name": "永中Office", "url": "https://www.yozosoft.com/download", "description": "国产办公软件"}
                ]
            }
        }
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="软件资源整合管理器", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左侧软件分类树
        self.create_software_tree(main_frame)
        
        # 右侧已选软件列表
        self.create_selected_list(main_frame)
        
        # 底部操作按钮
        self.create_action_buttons(main_frame)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def create_software_tree(self, parent):
        """创建软件分类树"""
        # 左侧框架
        left_frame = ttk.LabelFrame(parent, text="软件分类", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 创建树形控件
        self.tree = ttk.Treeview(left_frame, selectmode='extended')
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # 填充树形数据
        self.populate_tree()
        
        # 绑定事件
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
    
    def create_selected_list(self, parent):
        """创建已选软件列表"""
        # 右侧框架
        right_frame = ttk.LabelFrame(parent, text="已选择的软件", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建列表框
        self.selected_listbox = tk.Listbox(right_frame, font=('Microsoft YaHei', 9))
        self.selected_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        list_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.selected_listbox.yview)
        list_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.selected_listbox.configure(yscrollcommand=list_scroll.set)
        
        # 操作按钮框架
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # 移除选中按钮
        remove_btn = ttk.Button(button_frame, text="移除选中", command=self.remove_selected)
        remove_btn.grid(row=0, column=0, padx=(0, 10))
        
        # 清空全部按钮
        clear_btn = ttk.Button(button_frame, text="清空全部", command=self.clear_all_selected)
        clear_btn.grid(row=0, column=1)
        
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
    
    def create_action_buttons(self, parent):
        """创建操作按钮"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        # 生成安装程序按钮
        generate_btn = ttk.Button(button_frame, text="生成一键安装程序", 
                                style='Custom.TButton', command=self.generate_installer)
        generate_btn.grid(row=0, column=0, padx=(0, 20))
        
        # 下载软件按钮
        download_btn = ttk.Button(button_frame, text="下载选中软件", 
                                style='Custom.TButton', command=self.download_software)
        download_btn.grid(row=0, column=1, padx=(0, 20))
        
        # 设置按钮
        settings_btn = ttk.Button(button_frame, text="设置", 
                                style='Custom.TButton', command=self.open_settings)
        settings_btn.grid(row=0, column=2)
    
    def populate_tree(self):
        """填充树形数据"""
        for category, subcategories in self.software_data.items():
            category_id = self.tree.insert('', 'end', text=category, open=True)
            
            for subcategory, software_list in subcategories.items():
                subcategory_id = self.tree.insert(category_id, 'end', text=subcategory, open=True)
                
                for software in software_list:
                    self.tree.insert(subcategory_id, 'end', text=software['name'], 
                                   values=(software['url'], software['description']))
    
    def on_tree_double_click(self, event):
        """树形控件双击事件"""
        item = self.tree.selection()[0]
        item_text = self.tree.item(item, 'text')
        
        # 检查是否是软件项（有URL值）
        values = self.tree.item(item, 'values')
        if values and len(values) >= 2:
            software_info = {
                'name': item_text,
                'url': values[0],
                'description': values[1]
            }
            
            if software_info['name'] not in self.selected_software:
                self.selected_software.add(software_info['name'])
                self.update_selected_list()
                messagebox.showinfo("添加成功", f"已添加 {software_info['name']} 到选择列表")
            else:
                messagebox.showwarning("重复添加", f"{software_info['name']} 已在选择列表中")
    
    def update_selected_list(self):
        """更新已选软件列表"""
        self.selected_listbox.delete(0, tk.END)
        for software in sorted(self.selected_software):
            self.selected_listbox.insert(tk.END, software)
    
    def remove_selected(self):
        """移除选中的软件"""
        selection = self.selected_listbox.curselection()
        if selection:
            for index in reversed(selection):
                software_name = self.selected_listbox.get(index)
                self.selected_software.discard(software_name)
            self.update_selected_list()
    
    def clear_all_selected(self):
        """清空所有选中的软件"""
        if messagebox.askyesno("确认清空", "确定要清空所有已选择的软件吗？"):
            self.selected_software.clear()
            self.update_selected_list()
    
    def generate_installer(self):
        """生成一键安装程序"""
        if not self.selected_software:
            messagebox.showwarning("警告", "请先选择要安装的软件")
            return
        
        # 选择保存路径
        save_path = filedialog.asksaveasfilename(
            title="保存安装程序",
            defaultextension=".bat",
            filetypes=[("批处理文件", "*.bat"), ("所有文件", "*.*")]
        )
        
        if save_path:
            self.create_installer_script(save_path)
    
    def create_installer_script(self, save_path):
        """创建安装脚本"""
        script_content = "@echo off\n"
        script_content += "echo 软件一键安装程序\n"
        script_content += "echo 正在安装选中的软件...\n\n"
        
        # 获取选中软件的下载链接
        for software_name in self.selected_software:
            url = self.get_software_url(software_name)
            if url:
                script_content += f"echo 正在下载并安装 {software_name}...\n"
                # 尝试从URL中提取文件名和扩展名
                parsed_url = urlparse(url)
                url_path = parsed_url.path
                url_filename = os.path.basename(url_path)
                
                if url_filename and '.' in url_filename:
                    # 使用URL中的文件名
                    safe_filename = url_filename
                else:
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
                        safe_filename = f"{safe_name}{found_ext}"
                    else:
                        # 默认使用.exe
                        safe_filename = f"{safe_name}.exe"
                
                script_content += f"powershell -Command \"Invoke-WebRequest -Uri '{url}' -OutFile '{safe_filename}'\"\n"
                script_content += f"start /wait {safe_filename} /S\n"
                script_content += f"del {safe_filename}\n\n"
        
        script_content += "echo 所有软件安装完成！\n"
        script_content += "pause\n"
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            messagebox.showinfo("成功", f"安装程序已生成：{save_path}")
        except Exception as e:
            messagebox.showerror("错误", f"生成安装程序失败：{str(e)}")
    
    def get_software_url(self, software_name):
        """获取软件下载链接"""
        for category, subcategories in self.software_data.items():
            for subcategory, software_list in subcategories.items():
                for software in software_list:
                    if software['name'] == software_name:
                        return software['url']
        return None
    
    def download_software(self):
        """下载选中的软件"""
        if not self.selected_software:
            messagebox.showwarning("警告", "请先选择要下载的软件")
            return
        
        # 选择下载目录
        download_dir = filedialog.askdirectory(title="选择下载目录")
        if download_dir:
            self.start_download(download_dir)
    
    def start_download(self, download_dir):
        """开始下载"""
        def download_thread():
            for software_name in self.selected_software:
                url = self.get_software_url(software_name)
                if url:
                    try:
                        response = requests.get(url, stream=True)
                        # 尝试从URL中提取文件名和扩展名
                        parsed_url = urlparse(url)
                        url_path = parsed_url.path
                        url_filename = os.path.basename(url_path)
                        
                        if url_filename and '.' in url_filename:
                            # 使用URL中的文件名
                            filename = os.path.join(download_dir, url_filename)
                        else:
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
                                filename = os.path.join(download_dir, f"{safe_name}{found_ext}")
                            else:
                                # 默认使用.exe
                                filename = os.path.join(download_dir, f"{safe_name}.exe")
                        
                        with open(filename, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        print(f"下载完成: {software_name}")
                    except Exception as e:
                        print(f"下载失败 {software_name}: {str(e)}")
            
            messagebox.showinfo("完成", "所有软件下载完成！")
        
        threading.Thread(target=download_thread, daemon=True).start()
        messagebox.showinfo("开始下载", "下载已开始，请稍候...")
    
    def open_settings(self):
        """打开设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x300")
        settings_window.configure(bg='#f0f0f0')
        
        ttk.Label(settings_window, text="设置功能开发中...", 
                 font=('Microsoft YaHei', 12)).pack(pady=50)
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SoftwareManager()
    app.run()