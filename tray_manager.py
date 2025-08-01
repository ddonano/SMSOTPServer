"""
系统托盘管理器
提供简化的托盘功能和用户界面
"""

import threading
import time
import logging
from typing import Optional, Callable, List, Dict, Any
import utils

# 尝试导入系统托盘相关库
try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("警告: pystray 或 PIL 未安装，系统托盘功能不可用")
    print("请运行: pip install pystray pillow")

class TrayManager:
    """系统托盘管理器"""
    
    def __init__(self, server_instance=None):
        self.server = server_instance
        self.icon = None
        self.is_running = False
        self.menu_items = []
        self.status_callback = None
        
    def set_status_callback(self, callback: Callable[[], str]):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def create_icon_image(self, size=(64, 64), color=(0, 120, 212), status="running"):
        """创建托盘图标"""
        # 创建基础图像
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 根据状态选择颜色
        if status == "running":
            fill_color = (0, 120, 212)  # 蓝色
        elif status == "stopped":
            fill_color = (200, 0, 0)    # 红色
        elif status == "error":
            fill_color = (255, 165, 0)  # 橙色
        else:
            fill_color = color
        
        # 绘制圆形背景
        margin = 4
        draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], 
                    fill=fill_color, outline=(255, 255, 255, 255), width=2)
        
        # 添加文字 "SMS"
        try:
            # 尝试使用系统字体
            font_size = size[0] // 4
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            text = "SMS"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        except Exception as e:
            logging.warning(f"绘制图标文字失败: {e}")
            
        return image
    
    def create_menu(self):
        """创建托盘菜单"""
        menu_items = []
        
        # 状态信息
        status_text = "状态: 运行中" if self.server and self.server.running else "状态: 已停止"
        menu_items.append(pystray.MenuItem(status_text, self.show_status, enabled=False))
        
        # 端口信息
        if self.server:
            port_text = f"端口: {self.server.port}"
            menu_items.append(pystray.MenuItem(port_text, self.show_port, enabled=False))
        
        # 使用分隔符（兼容不同版本的pystray）
        try:
            menu_items.append(pystray.MenuSeparator())
        except AttributeError:
            # 如果MenuSeparator不存在，使用空字符串作为分隔符
            menu_items.append(pystray.MenuItem("─" * 20, lambda: None, enabled=False))
        
        # 功能菜单
        menu_items.extend([
            pystray.MenuItem("重启服务器", self.restart_server),
            pystray.MenuItem("停止服务器", self.stop_server),
        ])
        
        # 第二个分隔符
        try:
            menu_items.append(pystray.MenuSeparator())
        except AttributeError:
            menu_items.append(pystray.MenuItem("─" * 20, lambda: None, enabled=False))
        
        menu_items.extend([
            pystray.MenuItem("关于", self.show_about),
            pystray.MenuItem("退出程序", self.quit_application)
        ])
        
        return pystray.Menu(*menu_items)
    
    def show_status(self, icon, item):
        """显示状态信息"""
        pass  # 只读菜单项
    
    def show_port(self, icon, item):
        """显示端口信息"""
        pass  # 只读菜单项
    
    def restart_server(self, icon, item):
        """重启服务器"""
        if not self.server:
            utils.show_toast_notification("错误", "服务器实例不可用")
            return
        
        try:
            utils.show_toast_notification("服务器重启", "正在重启服务器...")
            self.server.restart()
        except Exception as e:
            logging.error(f"重启服务器失败: {e}")
            utils.show_toast_notification("重启失败", f"错误: {str(e)}")
    
    def stop_server(self, icon, item):
        """停止服务器"""
        if not self.server:
            utils.show_toast_notification("错误", "服务器实例不可用")
            return
        
        try:
            utils.show_toast_notification("服务器停止", "正在停止服务器...")
            self.server.stop()
        except Exception as e:
            logging.error(f"停止服务器失败: {e}")
            utils.show_toast_notification("停止失败", f"错误: {str(e)}")
    
    def show_about(self, icon, item):
        """显示关于信息"""
        try:
            # 使用多个通知来显示完整的关于信息
            utils.show_toast_notification(
                "SMS OTP Server", 
                "短信验证码转发服务器\n版本: 1.0.0"
            )
            
            # 延迟显示功能说明
            import threading
            def show_features():
                time.sleep(1)
                utils.show_toast_notification(
                    "功能特性",
                    "• 自动提取短信验证码\n• 复制到剪贴板\n• 来电提醒\n• 系统托盘支持"
                )
            
            threading.Thread(target=show_features, daemon=True).start()
            
            # 延迟显示使用说明
            def show_usage():
                time.sleep(2)
                utils.show_toast_notification(
                    "使用说明",
                    "• 关闭控制台窗口程序将继续在后台运行\n• 只有通过托盘菜单的'退出程序'才能完全退出"
                )
            
            threading.Thread(target=show_usage, daemon=True).start()
            
        except Exception as e:
            logging.error(f"显示关于信息失败: {e}")
            # 备用方案：显示简单的关于信息
            utils.show_toast_notification("关于", "SMS OTP Server v1.0.0")
    
    def quit_application(self, icon, item):
        """退出应用程序"""
        utils.show_toast_notification("退出", "正在关闭服务器...")
        self.stop()
        if self.server:
            # 调用服务器的强制退出方法
            self.server.force_quit()
        if self.icon:
            self.icon.stop()
    
    def update_menu(self):
        """更新菜单"""
        if self.icon:
            try:
                self.icon.menu = self.create_menu()
            except Exception as e:
                logging.error(f"更新菜单失败: {e}")
    
    def update_icon(self, status="running"):
        """更新图标"""
        if self.icon:
            try:
                new_image = self.create_icon_image(status=status)
                self.icon.icon = new_image
            except Exception as e:
                logging.error(f"更新图标失败: {e}")
    
    def start(self):
        """启动托盘图标"""
        if not TRAY_AVAILABLE:
            logging.warning("系统托盘功能不可用")
            return False
        
        # 如果已经运行，先停止
        if self.is_running and self.icon:
            self.stop()
        
        try:
            # 创建图标
            icon_image = self.create_icon_image()
            menu = self.create_menu()
            
            # 创建托盘图标
            self.icon = pystray.Icon("sms_server", icon_image, "SMS OTP Server", menu)
            self.is_running = True
            
            # 在新线程中运行托盘图标，设置为非守护线程
            tray_thread = threading.Thread(target=self.icon.run, daemon=False)
            tray_thread.start()
            
            logging.info("系统托盘图标已启动")
            return True
            
        except Exception as e:
            logging.error(f"启动系统托盘失败: {e}")
            return False
    
    def stop(self):
        """停止托盘图标"""
        self.is_running = False
        if self.icon:
            try:
                self.icon.stop()
                # 等待图标完全停止
                time.sleep(0.2)
            except:
                pass
            finally:
                # 清空图标引用
                self.icon = None
    
    def is_available(self):
        """检查系统托盘是否可用"""
        return TRAY_AVAILABLE


# 便捷函数
def create_tray_manager(server_instance=None) -> Optional[TrayManager]:
    """创建托盘管理器"""
    if not TRAY_AVAILABLE:
        return None
    
    return TrayManager(server_instance)


def show_tray_notification(title: str, message: str, duration: str = "long"):
    """显示托盘通知"""
    try:
        utils.show_toast_notification(title, message)
    except Exception as e:
        logging.error(f"显示托盘通知失败: {e}")


if __name__ == "__main__":
    # 测试托盘功能
    if TRAY_AVAILABLE:
        tray = create_tray_manager()
        if tray:
            tray.start()
            print("托盘图标已启动，按 Ctrl+C 退出")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                tray.stop()
                print("托盘图标已停止")
    else:
        print("系统托盘功能不可用") 