#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON文件加载
"""

import json

def test_json_loading():
    try:
        with open('software_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("JSON文件加载成功！")
        print(f"总分类数: {len(data)}")
        
        total_software = 0
        for category, subcategories in data.items():
            print(f"\n分类: {category}")
            for subcategory, software_list in subcategories.items():
                print(f"  子分类: {subcategory} ({len(software_list)} 个软件)")
                total_software += len(software_list)
        
        print(f"\n总软件数量: {total_software}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")
        print(f"错误字符位置: {e.pos}")
        return False
    except Exception as e:
        print(f"其他错误: {e}")
        return False

if __name__ == "__main__":
    test_json_loading()