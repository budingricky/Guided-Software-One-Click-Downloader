#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件管理器 V3.0 - 主程序
功能：软件下载、文件校验、自动纠错、日志系统
作者：AI Assistant
版本：3.0
"""

import os
import sys
import json
import hashlib
import requests
import threading
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import logging
from logging.handlers import RotatingFileHandler

class LogLevel:
    """日志级别常量"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class SoftwareManagerLogger:
    """分级日志系统"""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建不同级别的日志文件
        self.loggers = {}
        self._setup_loggers()
    
    def _setup_loggers(self):
        """设置不同级别的日志记录器"""
        log_configs = [
            ('main', 'software_manager.log', logging.INFO),
            ('error', 'errors.log', logging.ERROR),
            ('download', 'downloads.log', logging.INFO),
            ('validation', 'validation.log', logging.INFO)
        ]
        
        for name, filename, level in log_configs:
            logger = logging.getLogger(f'sm_{name}')
            logger.setLevel(logging.DEBUG)
            
            # 文件处理器
            file_handler = RotatingFileHandler(
                self.log_dir / filename,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            self.loggers[name] = logger
    
    def get_logger(self, name: str = 'main'):
        """获取指定的日志记录器"""
        return self.loggers.get(name, self.loggers['main'])
    
    def log(self, level: int, message: str, logger_name: str = 'main'):
        """记录日志"""
        logger = self.get_logger(logger_name)
        logger.log(level, message)
    
    def info(self, message: str, logger_name: str = 'main'):
        """记录信息日志"""
        self.log(LogLevel.INFO, message, logger_name)
    
    def warning(self, message: str, logger_name: str = 'main'):
        """记录警告日志"""
        self.log(LogLevel.WARNING, message, logger_name)
    
    def error(self, message: str, logger_name: str = 'error'):
        """记录错误日志"""
        self.log(LogLevel.ERROR, message, logger_name)
    
    def debug(self, message: str, logger_name: str = 'main'):
        """记录调试日志"""
        self.log(LogLevel.DEBUG, message, logger_name)

class FileValidator:
    """文件校验器"""
    
    def __init__(self, logger: SoftwareManagerLogger):
        self.logger = logger
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """计算文件哈希值"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败 {file_path}: {e}", 'validation')
            return ""
    
    def validate_file_integrity(self, file_path: Path, expected_hash: str = None, 
                              expected_size: int = None) -> Tuple[bool, str]:
        """验证文件完整性"""
        if not file_path.exists():
            return False, "文件不存在"
        
        try:
            # 检查文件大小
            if expected_size is not None:
                actual_size = file_path.stat().st_size
                if actual_size != expected_size:
                    return False, f"文件大小不匹配: 期望 {expected_size}, 实际 {actual_size}"
            
            # 检查文件哈希
            if expected_hash:
                actual_hash = self.calculate_file_hash(file_path)
                if actual_hash.lower() != expected_hash.lower():
                    return False, f"文件哈希不匹配: 期望 {expected_hash}, 实际 {actual_hash}"
            
            # 检查文件是否可读
            with open(file_path, 'rb') as f:
                f.read(1024)  # 尝试读取前1KB
            
            return True, "文件完整"
            
        except Exception as e:
            return False, f"文件验证失败: {e}"
    
    def validate_executable(self, file_path: Path) -> Tuple[bool, str]:
        """验证可执行文件"""
        if not file_path.exists():
            return False, "文件不存在"
        
        try:
            # 检查文件扩展名
            valid_extensions = {'.exe', '.msi', '.zip', '.rar', '.7z'}
            if file_path.suffix.lower() not in valid_extensions:
                return False, f"不支持的文件类型: {file_path.suffix}"
            
            # 检查文件大小（不能为0）
            if file_path.stat().st_size == 0:
                return False, "文件大小为0"
            
            # 对于exe文件，检查PE头
            if file_path.suffix.lower() == '.exe':
                with open(file_path, 'rb') as f:
                    header = f.read(2)
                    if header != b'MZ':
                        return False, "无效的PE文件头"
            
            return True, "可执行文件有效"
            
        except Exception as e:
            return False, f"可执行文件验证失败: {e}"

class AutoCorrector:
    """自动纠错器"""
    
    def __init__(self, logger: SoftwareManagerLogger, validator: FileValidator):
        self.logger = logger
        self.validator = validator
    
    def _generate_filename(self, software_info: Dict) -> str:
        """生成文件名：优先使用filename字段，否则根据软件名称和URL生成"""
        # 首先检查是否有指定的filename字段
        filename = software_info.get('filename')
        if not filename:
            software_name = software_info.get('name', 'unknown')
            url = software_info.get('url', '')
            
            if url and url != 'builtin':
                # 从URL中提取文件名
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                url_path = parsed_url.path
                basename = os.path.basename(url_path)
                
                # 如果URL中有文件名且包含扩展名
                if basename and '.' in basename:
                    # 使用URL中的文件名
                    filename = basename
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
                        filename = f"{safe_name}{found_ext}"
                    else:
                        # 默认使用.exe
                        filename = f"{safe_name}.exe"
            else:
                # 没有URL，使用软件名称和默认扩展名
                safe_name = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in software_name)
                filename = f"{safe_name}.exe"
        return filename
    
    def auto_correct_download(self, software_info: Dict, download_path: Path, 
                            max_retries: int = 3) -> Tuple[bool, str]:
        """自动纠错下载"""
        filename = self._generate_filename(software_info)
        file_path = download_path / filename
        
        for attempt in range(max_retries):
            self.logger.info(f"开始第 {attempt + 1} 次纠错尝试: {software_info['name']}", 'validation')
            
            try:
                # 检查现有文件
                if file_path.exists():
                    is_valid, message = self.validator.validate_file_integrity(
                        file_path,
                        software_info.get('hash'),
                        software_info.get('size')
                    )
                    
                    if is_valid:
                        self.logger.info(f"文件验证通过: {software_info['name']}", 'validation')
                        return True, "文件完整"
                    else:
                        self.logger.warning(f"文件验证失败: {message}, 尝试重新下载", 'validation')
                        # 删除损坏的文件
                        file_path.unlink(missing_ok=True)
                
                # 重新下载
                success, error_msg = self._download_file(
                    software_info.get('url', ''),
                    file_path,
                    software_info.get('size', 0)
                )
                
                if success:
                    # 验证下载的文件
                    is_valid, message = self.validator.validate_file_integrity(
                        file_path,
                        software_info.get('hash'),
                        software_info.get('size')
                    )
                    
                    if is_valid:
                        self.logger.info(f"纠错成功: {software_info['name']}", 'validation')
                        return True, "纠错成功"
                    else:
                        self.logger.warning(f"下载文件仍然无效: {message}", 'validation')
                else:
                    self.logger.error(f"下载失败: {error_msg}", 'validation')
                
            except Exception as e:
                self.logger.error(f"纠错过程出错: {e}", 'validation')
            
            # 等待后重试
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
        
        return False, f"经过 {max_retries} 次尝试后仍然失败"
    
    def _download_file(self, url: str, file_path: Path, expected_size: int = 0) -> Tuple[bool, str]:
        """下载文件"""
        try:
            self.logger.info(f"开始下载: {url} -> {file_path}", 'download')
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloaded_size = 0
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
            
            # 检查下载大小
            if expected_size > 0 and downloaded_size != expected_size:
                self.logger.warning(
                    f"下载大小不匹配: 期望 {expected_size}, 实际 {downloaded_size}",
                    'download'
                )
            
            self.logger.info(f"下载完成: {file_path} ({downloaded_size} bytes)", 'download')
            return True, "下载成功"
            
        except Exception as e:
            self.logger.error(f"下载失败: {e}", 'download')
            return False, str(e)
    
    def correct_path_issues(self, download_path: Path) -> Tuple[bool, str]:
        """纠正路径问题"""
        try:
            # 检查路径是否存在
            if not download_path.exists():
                self.logger.info(f"创建下载目录: {download_path}", 'validation')
                download_path.mkdir(parents=True, exist_ok=True)
            
            # 检查路径权限
            test_file = download_path / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                return True, "路径可写"
            except PermissionError:
                return False, "路径无写入权限"
            
        except Exception as e:
            self.logger.error(f"路径纠正失败: {e}", 'validation')
            return False, str(e)

class SoftwareDownloader:
    """软件下载器"""
    
    def __init__(self, logger: SoftwareManagerLogger):
        self.logger = logger
        self.validator = FileValidator(logger)
        self.corrector = AutoCorrector(logger, self.validator)
        self.download_sessions = {}
    
    def _generate_filename(self, software_info: Dict) -> str:
        """生成文件名：优先使用filename字段，否则根据软件名称和URL生成"""
        return self.corrector._generate_filename(software_info)
    
    def download_software(self, software_list: List[str], download_path: Path, 
                         software_data: Dict, progress_callback=None) -> Dict[str, Tuple[bool, str]]:
        """下载软件列表"""
        results = {}
        
        # 验证下载路径
        path_valid, path_message = self.corrector.correct_path_issues(download_path)
        if not path_valid:
            self.logger.error(f"下载路径问题: {path_message}")
            return {software: (False, path_message) for software in software_list}
        
        total_count = len(software_list)
        completed_count = 0
        
        for software_name in software_list:
            if software_name not in software_data:
                results[software_name] = (False, "软件信息不存在")
                continue
            
            software_info = software_data[software_name]
            self.logger.info(f"开始下载: {software_name}", 'download')
            
            # 尝试下载和纠错
            success, message = self.corrector.auto_correct_download(
                software_info, download_path
            )
            
            results[software_name] = (success, message)
            completed_count += 1
            
            # 更新进度
            if progress_callback:
                progress_callback(completed_count, total_count, software_name, success)
            
            self.logger.info(
                f"下载结果: {software_name} - {'成功' if success else '失败'} ({message})",
                'download'
            )
        
        return results
    
    def validate_existing_downloads(self, download_path: Path, 
                                  software_data: Dict) -> Dict[str, Tuple[bool, str]]:
        """验证现有下载"""
        results = {}
        
        if not download_path.exists():
            self.logger.warning(f"下载路径不存在: {download_path}", 'validation')
            return results
        
        for software_name, software_info in software_data.items():
            filename = self._generate_filename(software_info)
            file_path = download_path / filename
            
            if file_path.exists():
                # 验证文件完整性
                is_valid, message = self.validator.validate_file_integrity(
                    file_path,
                    software_info.get('hash'),
                    software_info.get('size')
                )
                
                # 验证可执行文件
                if is_valid:
                    is_executable, exec_message = self.validator.validate_executable(file_path)
                    if not is_executable:
                        is_valid = False
                        message = exec_message
                
                results[software_name] = (is_valid, message)
                self.logger.info(
                    f"验证结果: {software_name} - {'有效' if is_valid else '无效'} ({message})",
                    'validation'
                )
            else:
                results[software_name] = (False, "文件不存在")
        
        return results

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Path = None):
        self.config_file = config_file or Path("config_v3.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置"""
        default_config = {
            "download_path": str(Path.home() / "Downloads" / "SoftwareManager"),
            "concurrent_downloads": 3,
            "timeout_seconds": 30,
            "max_retries": 3,
            "auto_validation": True,
            "log_level": "INFO",
            "theme": "dark"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"加载配置失败，使用默认配置: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()

class SoftwareManagerV3:
    """软件管理器 V3.0 - 主要管理类"""
    
    def __init__(self, software_data: Dict = None):
        self.config_manager = ConfigManager()
        self.logger = SoftwareManagerLogger()
        self.downloader = SoftwareDownloader(self.logger)
        self.software_data = software_data if software_data else self._load_software_data()
        
        self.logger.info("软件管理器 V3.0 初始化完成")
    
    def _generate_filename(self, software_info: Dict) -> str:
        """生成文件名：优先使用filename字段，否则根据软件名称和URL生成"""
        return self.downloader.corrector._generate_filename(software_info)
    
    def _load_software_data(self) -> Dict:
        """加载软件数据"""
        # 这里应该从配置文件或数据库加载真实的软件信息
        # 为演示目的，使用模拟数据
        return {
            "Chrome": {
                "name": "Google Chrome",
                "filename": "chrome_installer.exe",
                "url": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
                "size": 1024000,
                "hash": "abc123def456",
                "category": "浏览器",
                "description": "Google Chrome 浏览器"
            },
            "Firefox": {
                "name": "Mozilla Firefox",
                "filename": "firefox_installer.exe",
                "url": "https://download.mozilla.org/firefox/releases/latest/win64/en-US/Firefox%20Setup.exe",
                "size": 2048000,
                "hash": "def456ghi789",
                "category": "浏览器",
                "description": "Mozilla Firefox 浏览器"
            },
            "VSCode": {
                "name": "Visual Studio Code",
                "filename": "vscode_installer.exe",
                "url": "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user",
                "size": 3072000,
                "hash": "ghi789jkl012",
                "category": "开发工具",
                "description": "Visual Studio Code 编辑器"
            }
        }
    
    def get_software_list(self) -> List[str]:
        """获取软件列表"""
        return list(self.software_data.keys())
    
    def get_software_info(self, software_name: str) -> Optional[Dict]:
        """获取软件信息"""
        return self.software_data.get(software_name)
    
    def validate_download_path(self, path: str) -> Tuple[bool, str]:
        """验证下载路径"""
        try:
            download_path = Path(path)
            return self.downloader.corrector.correct_path_issues(download_path)
        except Exception as e:
            return False, str(e)
    
    def validate_existing_files(self, download_path: str) -> Dict[str, Tuple[bool, str]]:
        """验证现有文件"""
        path = Path(download_path)
        return self.downloader.validate_existing_downloads(path, self.software_data)
    
    def download_selected_software(self, software_list: List[str], download_path: str, 
                                 progress_callback=None) -> Dict[str, Tuple[bool, str]]:
        """下载选定的软件"""
        path = Path(download_path)
        
        # 更新配置中的下载路径
        self.config_manager.set("download_path", download_path)
        
        return self.downloader.download_software(
            software_list, path, self.software_data, progress_callback
        )
    
    def get_config(self, key: str, default=None):
        """获取配置"""
        return self.config_manager.get(key, default)
    
    def set_config(self, key: str, value):
        """设置配置"""
        self.config_manager.set(key, value)
    
    def get_download_statistics(self, download_path: str) -> Dict:
        """获取下载统计信息"""
        path = Path(download_path)
        stats = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "total_size": 0,
            "files": []
        }
        
        if not path.exists():
            return stats
        
        validation_results = self.validate_existing_files(download_path)
        
        for software_name, (is_valid, message) in validation_results.items():
            software_info = self.get_software_info(software_name)
            if software_info:
                filename = self._generate_filename(software_info)
                file_path = path / filename
                
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    if is_valid:
                        stats["valid_files"] += 1
                    else:
                        stats["invalid_files"] += 1
                    
                    stats["files"].append({
                        "name": software_name,
                        "filename": filename,
                        "size": file_size,
                        "valid": is_valid,
                        "message": message
                    })
        
        return stats

if __name__ == "__main__":
    # 测试代码
    manager = SoftwareManagerV3()
    print("软件管理器 V3.0 启动成功")
    print(f"可用软件: {manager.get_software_list()}")