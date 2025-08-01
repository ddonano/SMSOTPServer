"""
配置管理模块
统一管理配置文件的读取和验证
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = self._get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as file:
                    self.config = json.load(file)
                logging.info(f"配置文件加载成功: {config_path}")
            else:
                logging.warning(f"配置文件不存在: {config_path}")
                self._create_default_config()
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _get_config_path(self) -> str:
        """获取配置文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe文件
            return os.path.join(sys._MEIPASS, self.config_file)
        else:
            # 开发环境
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config_file)
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            'port': 65432,
            'auto_hide': False,
            'log_level': 'INFO'
        }
        logging.info("使用默认配置")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            config_path = self._get_config_path()
            with open(config_path, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, indent=2, ensure_ascii=False)
            logging.info(f"配置文件保存成功: {config_path}")
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def get_port(self) -> int:
        """获取端口号"""
        port = self.get('port', 65432)
        if not isinstance(port, int) or port < 1 or port > 65535:
            logging.warning(f"无效的端口号: {port}，使用默认端口65432")
            return 65432
        return port
    
    def set_port(self, port: int):
        """设置端口号"""
        if isinstance(port, int) and 1 <= port <= 65535:
            self.set('port', port)
        else:
            raise ValueError(f"无效的端口号: {port}")
    
    def get_auto_hide(self) -> bool:
        """获取自动隐藏设置"""
        return self.get('auto_hide', False)
    
    def set_auto_hide(self, auto_hide: bool):
        """设置自动隐藏"""
        self.set('auto_hide', bool(auto_hide))
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            port = self.get_port()
            auto_hide = self.get_auto_hide()
            
            logging.info(f"配置验证通过 - 端口: {port}, 自动隐藏: {auto_hide}")
            return True
        except Exception as e:
            logging.error(f"配置验证失败: {e}")
            return False 