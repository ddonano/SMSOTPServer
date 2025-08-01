"""
消息处理模块
处理SMS和CALL消息的核心逻辑
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from utils import copy_verification_code, caller_handler

class MessageProcessor:
    """消息处理器"""
    
    def __init__(self):
        pass
    
    def process_message(self, text: str, stats: Dict[str, Any]) -> bool:
        """
        处理接收到的消息
        
        Args:
            text: 消息文本
            stats: 统计信息字典
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 清理消息格式
            text = text.strip()
            if text.startswith('{') and text.endswith('}'):
                text = text[1:-1]
            
            # 解析消息类型
            match = self._split_string_at_first_dot(text)
            if not match:
                logging.error("❌ 消息格式错误")
                return False
            
            prefix, suffix = match
            return self._handle_message_type(prefix, suffix, stats)
            
        except Exception as e:
            logging.error(f"处理消息时出错: {e}")
            return False
    
    def _split_string_at_first_dot(self, text: str) -> Optional[Tuple[str, str]]:
        """
        分割字符串，以第一个"."为界限
        
        Args:
            text: 输入字符串
            
        Returns:
            Tuple[str, str]: (前缀, 后缀) 或 None
        """
        if "." not in text:
            return None
        
        index = text.find(".")
        before_dot = text[:index]
        after_dot = text[index + 1:]
        return before_dot, after_dot
    
    def _handle_message_type(self, prefix: str, suffix: str, stats: Dict[str, Any]) -> bool:
        """
        根据消息类型处理消息
        
        Args:
            prefix: 消息类型前缀
            suffix: 消息内容
            stats: 统计信息
            
        Returns:
            bool: 处理是否成功
        """
        if prefix == 'CALL':
            # 处理来电
            stats['call_count'] += 1
            logging.info(f"📞 处理来电: {suffix}")
            caller_handler(suffix)
            logging.info(f"处理来电消息，总计: {stats['call_count']}")
            return True
            
        elif prefix == 'SMS':
            # 处理短信
            stats['sms_count'] += 1
            logging.info(f"📱 处理短信: {suffix}")
            result = copy_verification_code(suffix)
            if result:
                logging.info(f"✅ 验证码已复制: {result}")
                logging.info(f"处理短信消息成功，总计: {stats['sms_count']}")
                return True
            else:
                logging.warning("❌ 验证码提取失败")
                logging.warning(f"处理短信消息失败，总计: {stats['sms_count']}")
                return False
                
        else:
            logging.warning(f"⚠️  未知消息类型: {prefix}")
            return False 