import re
import sys
import os
import pyperclip
import logging
import time
from typing import List, Dict, Any, Optional

# 导入改进的通知管理器
try:
    from notification_manager import show_toast_notification, show_success_notification, show_error_notification

    NOTIFICATION_AVAILABLE = True
except ImportError:
    # 如果导入失败，使用原始的通知函数
    from winotify import Notification, audio

    NOTIFICATION_AVAILABLE = False

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局变量存储最后复制的验证码
_last_copied = None


def extract_first_long_number(text):
    # 匹配长度大于等于4的数字字符串
    pattern = r'\d{4,}'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None


def get_icon_path():
    # When running from a packaged .exe
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'favicon.ico')
    else:
        return os.path.join(os.path.dirname(__file__), 'favicon.ico')


def show_toast_notification(title, message):
    """显示通知（兼容性函数）"""
    if NOTIFICATION_AVAILABLE:
        # 使用改进的通知管理器
        from notification_manager import show_toast_notification as show_notification
        return show_notification(title, message, "info")
    else:
        # 使用原始的通知函数
        try:
            # 获取图标路径
            icon_path = get_icon_path()
            if not os.path.exists(icon_path):
                icon_path = ""  # 如果图标不存在则使用默认图标

            # 创建通知
            toast = Notification(
                app_id="SmsCodeServer",  # 应用标识名称
                title=title,
                msg=message,
                icon=icon_path,
                duration="long"  # short约为4.5秒，long约为9秒
            )

            # 设置通知声音
            toast.set_audio(audio.Default, loop=False)

            # 显示通知
            toast.show()
            return True

        except Exception as e:
            logging.error(f"通知显示失败: {str(e)}")
            return False


def caller_handler(text):
    # 显示通知
    show_toast_notification(
        f"联系电话: {text} 来了",
        f"原文: {text}"
    )


def show_handler(text):
    # 显示通知
    show_toast_notification(
        f"其他消息",
        f"原文: {text}"
    )


def copy_verification_code(text):
    global _last_copied

    number = extract_first_long_number(text)
    if number:
        # 复制到剪贴板
        try:
            pyperclip.copy(number)
            _last_copied = number

            logging.info(f"已复制到剪贴板: {number}")
        except Exception as e:
            logging.error(f"复制到剪贴板失败: {str(e)}")
            if NOTIFICATION_AVAILABLE:
                show_error_notification("复制失败", f"错误: {str(e)}")
            else:
                show_toast_notification("复制失败", f"错误: {str(e)}")
            return None

        # 处理文本，确保索引访问安全
        display_text = text
        if text.startswith('{') and text.endswith('}'):
            display_text = text[1:-1]

        # 显示通知
        if NOTIFICATION_AVAILABLE:
            show_success_notification(
                f"验证码: {number} 复制成功",
                f"短信原文: {display_text}"
            )
        else:
            show_toast_notification(
                f"验证码: {number} 复制成功",
                f"短信原文: {display_text}"
            )
        return number
    else:
        logging.warning("未找到符合条件的数字字符串")
        if NOTIFICATION_AVAILABLE:
            show_error_notification("复制失败", "请检查短信验证码")
        else:
            show_toast_notification("复制失败", "请检查短信验证码")
        return None


def get_last_copied_code() -> Optional[str]:
    """获取最后复制的验证码"""
    return _last_copied


if __name__ == "__main__":
    test_text = "{这是一段包含验证码737363的测试文本}"
    copy_verification_code(test_text)
