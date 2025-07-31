#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试现代化UI组件
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os

def test_ui():
    """测试UI组件"""
    print("🎨 测试CustomTkinter UI组件...")
    
    # 检查CustomTkinter版本
    print(f"CustomTkinter版本: {ctk.__version__}")
    
    # 检查软件数据文件
    if os.path.exists('software_data.json'):
        with open('software_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 软件数据文件加载成功，包含 {len(data)} 个分类")
    else:
        print("❌ 软件数据文件不存在")
        return False
    
    # 创建测试窗口
    try:
        root = ctk.CTk()
        root.title("🧪 UI测试")
        root.geometry("400x300")
        
        # 测试标签
        label = ctk.CTkLabel(
            root, 
            text="✅ CustomTkinter UI 测试成功！",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(pady=20)
        
        # 测试按钮
        def on_test_click():
            messagebox.showinfo("测试", "现代化UI组件工作正常！")
            root.destroy()
        
        test_btn = ctk.CTkButton(
            root,
            text="🎯 测试按钮",
            command=on_test_click,
            font=ctk.CTkFont(size=14)
        )
        test_btn.pack(pady=10)
        
        # 测试进度条
        progress = ctk.CTkProgressBar(root)
        progress.pack(pady=10)
        progress.set(0.7)
        
        # 自动关闭测试窗口
        root.after(3000, root.destroy)
        
        print("🎨 UI测试窗口已创建，3秒后自动关闭")
        root.mainloop()
        
        print("✅ CustomTkinter UI测试完成")
        return True
        
    except Exception as e:
        print(f"❌ UI测试失败: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🧪 现代化UI组件测试")
    print("="*50)
    
    success = test_ui()
    
    if success:
        print("\n🎉 所有测试通过！现代化UI可以正常使用")
    else:
        print("\n❌ 测试失败，请检查依赖安装")
    
    print("\n测试完成。")