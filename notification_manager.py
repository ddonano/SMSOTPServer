"""
改进的通知管理器
解决Windows通知不显示的问题
"""

import os
import sys
import logging
import time
import threading
from typing import Optional, Dict, Any
from winotify import Notification, audio

class NotificationManager:
    """改进的通知管理器"""
    
    def __init__(self):
        self.last_notification_time = 0
        self.notification_queue = []
        self.is_processing = False
        self.min_interval = 1.0  # 最小通知间隔（秒）
        
    def get_icon_path(self) -> str:
        """获取图标路径"""
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'favicon.ico')
        else:
            icon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
        
        return icon_path if os.path.exists(icon_path) else ""
    
    def show_notification(self, title: str, message: str, notification_type: str = "info", 
                         duration: str = "long", sound: bool = True) -> bool:
        """
        显示通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型 (info, success, error, warning)
            duration: 显示时长 (short, long)
            sound: 是否播放声音
            
        Returns:
            bool: 是否成功显示
        """
        try:
            # 检查通知间隔
            current_time = time.time()
            if current_time - self.last_notification_time < self.min_interval:
                # 如果间隔太短，将通知加入队列
                self.notification_queue.append({
                    'title': title,
                    'message': message,
                    'type': notification_type,
                    'duration': duration,
                    'sound': sound,
                    'timestamp': current_time
                })
                
                # 启动队列处理线程
                if not self.is_processing:
                    threading.Thread(target=self._process_queue, daemon=True).start()
                return True
            
            # 更新最后通知时间
            self.last_notification_time = current_time
            
            # 获取图标路径
            icon_path = self.get_icon_path()
            
            # 根据通知类型设置不同的应用ID
            app_id_map = {
                "info": "SmsCodeServer",
                "success": "SmsCodeServer.Success",
                "error": "SmsCodeServer.Error",
                "warning": "SmsCodeServer.Warning"
            }
            app_id = app_id_map.get(notification_type, "SmsCodeServer")
            
            # 创建通知
            toast = Notification(
                app_id=app_id,
                title=title,
                msg=message,
                icon=icon_path,
                duration=duration
            )
            
            # 设置通知声音
            if sound:
                try:
                    toast.set_audio(audio.Default, loop=False)
                except Exception as e:
                    logging.warning(f"设置通知声音失败: {e}")
            
            # 显示通知
            toast.show()
            
            logging.info(f"通知已显示: {title} - {message}")
            return True
            
        except Exception as e:
            logging.error(f"通知显示失败: {str(e)}")
            return False
    
    def _process_queue(self):
        """处理通知队列"""
        self.is_processing = True
        
        while self.notification_queue:
            current_time = time.time()
            
            # 检查是否可以显示下一个通知
            if current_time - self.last_notification_time >= self.min_interval:
                notification = self.notification_queue.pop(0)
                
                # 显示通知
                self.show_notification(
                    notification['title'],
                    notification['message'],
                    notification['type'],
                    notification['duration'],
                    notification['sound']
                )
                
                # 等待一小段时间
                time.sleep(0.5)
            else:
                # 等待到可以显示下一个通知
                time.sleep(0.1)
        
        self.is_processing = False
    
    def show_success_notification(self, title: str, message: str) -> bool:
        """显示成功通知"""
        return self.show_notification(title, message, "success", "long", True)
    
    def show_error_notification(self, title: str, message: str) -> bool:
        """显示错误通知"""
        return self.show_notification(title, message, "error", "long", True)
    
    def show_warning_notification(self, title: str, message: str) -> bool:
        """显示警告通知"""
        return self.show_notification(title, message, "warning", "long", True)
    
    def show_info_notification(self, title: str, message: str) -> bool:
        """显示信息通知"""
        return self.show_notification(title, message, "info", "long", True)
    
    def test_notification(self) -> bool:
        """测试通知功能"""
        return self.show_notification(
            "通知测试",
            "如果您看到这条通知，说明通知功能正常工作！",
            "info",
            "short",
            True
        )

# 全局通知管理器实例
_notification_manager = NotificationManager()

# 便捷函数
def show_toast_notification(title: str, message: str, notification_type: str = "info") -> bool:
    """显示通知的便捷函数"""
    return _notification_manager.show_notification(title, message, notification_type)

def show_success_notification(title: str, message: str) -> bool:
    """显示成功通知"""
    return _notification_manager.show_success_notification(title, message)

def show_error_notification(title: str, message: str) -> bool:
    """显示错误通知"""
    return _notification_manager.show_error_notification(title, message)

def show_warning_notification(title: str, message: str) -> bool:
    """显示警告通知"""
    return _notification_manager.show_warning_notification(title, message)

def test_notification() -> bool:
    """测试通知功能"""
    return _notification_manager.test_notification()

if __name__ == "__main__":
    # 测试通知功能
    print("测试通知功能...")
    
    # 测试不同类型的通知
    test_notification()
    time.sleep(2)
    
    show_success_notification("成功", "操作成功完成！")
    time.sleep(2)
    
    show_error_notification("错误", "发生了一个错误！")
    time.sleep(2)
    
    show_warning_notification("警告", "请注意这个警告！")
    
    print("通知测试完成！") 