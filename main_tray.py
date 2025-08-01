#!/usr/bin/env python3
"""
SMS OTP Server with System Tray
带系统托盘功能的短信验证码转发服务器
"""

import re
import socket
import json
import os
import sys
import logging
import argparse
import threading
import time
import utils
from typing import Optional

# 导入托盘管理器
try:
    from tray_manager import create_tray_manager
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("警告: 托盘管理器不可用，请安装依赖: pip install pystray pillow")

# 配置日志记录
class SafeStreamHandler(logging.StreamHandler):
    """安全的流处理器，处理控制台窗口隐藏的情况"""
    
    def emit(self, record):
        try:
            # 检查流是否可用
            if self.stream is None or self.stream.closed:
                return
            super().emit(record)
        except (AttributeError, OSError, ValueError):
            # 如果流不可用，静默忽略
            pass

# 创建自定义的日志配置
def setup_logging():
    """设置安全的日志配置"""
    # 清除现有的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 文件处理器
    file_handler = logging.FileHandler('sms_server.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 安全的流处理器
    stream_handler = SafeStreamHandler()
    stream_handler.setFormatter(formatter)
    
    # 设置根日志记录器
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

# 初始化日志配置
setup_logging()

def safe_logging(level, message, *args):
    """安全的日志记录函数，处理控制台窗口隐藏的情况"""
    try:
        if level == 'info':
            logging.info(message, *args)
        elif level == 'error':
            logging.error(message, *args)
        elif level == 'warning':
            logging.warning(message, *args)
        elif level == 'debug':
            logging.debug(message, *args)
    except (AttributeError, OSError, ValueError):
        # 如果日志记录失败，静默忽略
        pass

def hide_console_window():
    """隐藏控制台窗口"""
    try:
        import ctypes
        # 获取控制台窗口句柄
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            # 隐藏控制台窗口
            ctypes.windll.user32.ShowWindow(console_window, 0)  # SW_HIDE = 0
            
            # 更新日志处理器，移除可能失效的流处理器
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    # 检查流是否仍然有效
                    try:
                        if handler.stream is None or handler.stream.closed:
                            root_logger.removeHandler(handler)
                    except (AttributeError, OSError):
                        root_logger.removeHandler(handler)
            
            logging.info("控制台窗口已隐藏")
            return True
    except Exception as e:
        # 使用文件日志记录错误，避免控制台输出
        try:
            logging.error(f"隐藏控制台窗口失败: {e}")
        except:
            pass
        return False

def show_console_window():
    """显示控制台窗口"""
    try:
        import ctypes
        # 获取控制台窗口句柄
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            # 显示控制台窗口
            ctypes.windll.user32.ShowWindow(console_window, 1)  # SW_SHOW = 1
            ctypes.windll.user32.SetForegroundWindow(console_window)
            
            # 恢复流处理器
            root_logger = logging.getLogger()
            has_stream_handler = any(
                isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
                for handler in root_logger.handlers
            )
            
            if not has_stream_handler:
                # 重新添加安全的流处理器
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                stream_handler = SafeStreamHandler()
                stream_handler.setFormatter(formatter)
                root_logger.addHandler(stream_handler)
            
            logging.info("控制台窗口已显示")
            return True
    except Exception as e:
        # 使用文件日志记录错误，避免控制台输出
        try:
            logging.error(f"显示控制台窗口失败: {e}")
        except:
            pass
        return False

def setup_console_close_handler():
    """设置控制台关闭事件处理"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # 保存全局引用，防止被垃圾回收
        global _console_handler
        
        # 定义控制台关闭事件处理函数
        def console_ctrl_handler(ctrl_type):
            if ctrl_type in [0, 2]:  # CTRL_C_EVENT or CTRL_CLOSE_EVENT
                # 安全地记录日志，避免控制台输出错误
                try:
                    logging.info("检测到控制台关闭事件，程序将继续在后台运行")
                except:
                    pass
                # 隐藏控制台窗口而不是退出程序
                hide_console_window()
                return True  # 返回True表示已处理事件
            return False
        
        # 设置控制台事件处理
        handler_func = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
        _console_handler = handler_func(console_ctrl_handler)
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_handler, True)
        
        # 安全地记录日志
        try:
            logging.info("已设置控制台关闭事件处理")
        except:
            pass
        return True
    except Exception as e:
        # 安全地记录错误
        try:
            logging.error(f"设置控制台关闭事件处理失败: {e}")
        except:
            pass
        return False

def prevent_console_close():
    """防止控制台窗口被关闭"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # 获取控制台窗口句柄
        console_window = ctypes.windll.kernel32.GetConsoleWindow()
        if console_window:
            # 禁用关闭按钮
            ctypes.windll.user32.EnableMenuItem(
                ctypes.windll.user32.GetSystemMenu(console_window, False),
                0xF060,  # SC_CLOSE
                0x00000001  # MF_GRAYED
            )
            # 安全地记录日志
            try:
                logging.info("已禁用控制台关闭按钮")
            except:
                pass
            return True
    except Exception as e:
        # 安全地记录错误
        try:
            logging.error(f"禁用控制台关闭按钮失败: {e}")
        except:
            pass
        return False

class SMSServer:
    """SMS服务器类"""
    
    def __init__(self, port: int, enable_tray: bool = True, auto_hide: bool = False):
        self.port = port
        self.server_socket = None
        self.running = False
        self.tray_manager = None
        self.enable_tray = enable_tray and TRAY_AVAILABLE
        self.auto_hide = auto_hide
        self.force_exit = False  # 强制退出标志
        
        # 统计信息
        self.stats = {
            'sms_count': 0,
            'call_count': 0,
            'start_time': None,
            'last_activity': None
        }
        
    def start(self):
        """启动服务器"""
        self.running = True
        self.stats['start_time'] = time.time()
        
        # 设置控制台关闭事件处理
        if self.enable_tray:
            setup_console_close_handler()
            # 可选：禁用控制台关闭按钮，强制用户通过托盘退出
            # prevent_console_close()
        
        # 创建socket对象
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            safe_logging('info', f"服务器启动成功，监听端口 {self.port}")
            
            # 启动系统托盘
            if self.enable_tray:
                self.tray_manager = create_tray_manager(self)
                if self.tray_manager:
                    self.tray_manager.start()
                    safe_logging('info', "系统托盘已启动")
                    
                    # 如果启用自动隐藏，延迟隐藏控制台窗口
                    if self.auto_hide:
                        # 等待托盘图标完全启动后再隐藏窗口
                        time.sleep(2)
                        hide_console_window()
                    
                    # 显示托盘启动通知
                    utils.show_toast_notification(
                        "托盘已启动", 
                        "系统托盘图标已启动\n关闭控制台窗口程序将继续在后台运行"
                    )
            
            # 显示启动通知
            utils.show_toast_notification(
                "服务器启动", 
                f"SMS OTP Server 已启动\n监听端口: {self.port}\n程序将继续在后台运行"
            )
            
            # 主服务器循环
            while self.running and not self.force_exit:
                try:
                    # 设置socket超时，以便能够响应退出信号
                    self.server_socket.settimeout(1.0)
                    client_socket, client_address = self.server_socket.accept()
                    safe_logging('info', f"客户端连接: {client_address}")
                    
                    # 在新线程中处理客户端连接
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    # 超时是正常的，继续循环
                    continue
                except Exception as e:
                    if self.running and not self.force_exit:
                        safe_logging('error', f"处理客户端连接时出错: {e}")
                    continue
            
            # 如果程序正常退出（非强制退出），等待托盘线程结束
            if not self.force_exit and self.tray_manager and self.tray_manager.is_running:
                safe_logging('info', "等待托盘线程结束...")
                # 给托盘线程一些时间来完成
                time.sleep(1)
                    
        except Exception as e:
            safe_logging('error', f"服务器启动失败: {e}")
            if self.enable_tray and self.tray_manager:
                self.tray_manager.update_icon("error")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        try:
            data = client_socket.recv(1024)
            if not data:
                safe_logging('warning', f"客户端 {client_address} 未发送数据")
                client_socket.close()
                return
            
            text = data.decode('utf-8')
            safe_logging('info', f"收到数据: {text}")
            
            # 更新最后活动时间
            self.stats['last_activity'] = time.time()
            
            # 处理消息
            self.process_message(text)
            
        except Exception as e:
            logging.error(f"处理客户端 {client_address} 时出错: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def process_message(self, text):
        """处理消息"""
        # 清理消息格式
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            text = text[1:-1]
        
        # 解析消息类型
        match = split_string_at_first_dot(text)
        
        if match:
            prefix, suffix = match
            if prefix == 'CALL':
                # 处理来电
                self.stats['call_count'] += 1
                utils.caller_handler(suffix)
                logging.info(f"处理来电消息，总计: {self.stats['call_count']}")
                
            elif prefix == 'SMS':
                # 处理短信
                self.stats['sms_count'] += 1
                result = utils.copy_verification_code(suffix)
                if result:
                    logging.info(f"处理短信消息成功，总计: {self.stats['sms_count']}")
                else:
                    logging.warning(f"处理短信消息失败，总计: {self.stats['sms_count']}")
            else:
                logging.warning(f"未知消息类型: {prefix}")
        else:
            logging.error("无法匹配到预期格式")
    
    def restart(self):
        """重启服务器"""
        safe_logging('info', "正在重启服务器...")
        
        # 先停止托盘图标
        if self.tray_manager:
            self.tray_manager.stop()
            # 等待托盘图标完全停止
            time.sleep(0.5)
        
        # 停止服务器
        self.stop()
        
        # 等待资源释放
        time.sleep(1)
        
        # 重新创建托盘管理器
        if self.enable_tray:
            self.tray_manager = create_tray_manager(self)
        
        # 重新启动服务器
        self.start()
    
    def force_quit(self):
        """强制退出程序"""
        logging.info("收到强制退出信号")
        self.force_exit = True
        self.stop()
        # 强制退出程序
        os._exit(0)
    
    def stop(self):
        """停止服务器"""
        self.running = False
        
        # 停止托盘图标
        if self.tray_manager:
            self.tray_manager.stop()
            # 清空托盘管理器引用
            self.tray_manager = None
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.server_socket = None
            except:
                pass
        
        safe_logging('info', "服务器已停止")

def split_string_at_first_dot(text):
    """分割字符串，以第一个"."为界限"""
    if "." not in text:
        return None
    
    index = text.find(".")
    before_dot = text[:index]
    after_dot = text[index + 1:]
    return before_dot, after_dot

def get_config_path():
    """获取配置文件路径"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'config.json')
    else:
        return os.path.join(os.path.dirname(__file__), 'config.json')

def parse_args():
    """解析命令行参数"""
    # 检查stdout是否可用，如果不可用则重定向到文件
    if sys.stdout is None:
        # 重定向到日志文件
        sys.stdout = open('sms_server.log', 'a', encoding='utf-8')
        sys.stderr = sys.stdout
    
    parser = argparse.ArgumentParser(
        description="SMS OTP Server - 短信验证码转发服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main_tray.py              # 使用默认配置启动
  python main_tray.py -p 65432     # 指定端口启动
  python main_tray.py --no-tray    # 禁用系统托盘
  python main_tray.py --auto-hide  # 自动隐藏控制台窗口
        """
    )
    parser.add_argument('-p', '--port', type=int, help="监听端口号", default=None)
    parser.add_argument('--no-tray', action='store_true', help="禁用系统托盘")
    parser.add_argument('--auto-hide', action='store_true', help="自动隐藏控制台窗口")
    
    try:
        return parser.parse_args()
    except Exception as e:
        # 如果解析失败，返回默认参数
        logging.error(f"参数解析失败: {e}")
        return argparse.Namespace(port=None, no_tray=False, auto_hide=False)

def print_banner():
    """打印启动横幅"""
    try:
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    SMS OTP Server                            ║
║              短信验证码转发服务器                              ║
║                                                              ║
║  功能: 自动提取短信验证码并复制到剪贴板                      ║
║  特色: 系统托盘支持、复制历史、状态监控                        ║
║  注意: 关闭控制台窗口程序将继续在后台运行                    ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    except Exception as e:
        # 如果打印失败，记录到日志
        logging.info("SMS OTP Server 启动")
        logging.info("功能: 自动提取短信验证码并复制到剪贴板")
        logging.info("特色: 系统托盘支持、复制历史、状态监控")

def main():
    """主函数"""
    print_banner()
    
    # 解析命令行参数
    args = parse_args()
    
    # 确定端口号
    if args.port:
        port = args.port
        logging.info(f"使用命令行参数指定的端口: {port}")
    else:
        try:
            config_path = get_config_path()
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            port = config['port']
            logging.info(f"使用配置文件中的端口: {port}")
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            port = 65432
            logging.info(f"使用默认端口: {port}")
    
    # 验证端口号
    if port < 1 or port > 65535:
        logging.error("端口号必须在1-65535之间")
        return 1
    
    # 检查系统托盘可用性
    enable_tray = not args.no_tray and TRAY_AVAILABLE
    if not enable_tray and not args.no_tray:
        try:
            print("警告: 系统托盘功能不可用，请安装依赖: pip install pystray pillow")
        except:
            logging.warning("系统托盘功能不可用，请安装依赖: pip install pystray pillow")
    
    # 检查自动隐藏设置
    auto_hide = args.auto_hide
    if not auto_hide:
        # 如果没有命令行参数，尝试从配置文件读取
        try:
            config_path = get_config_path()
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
                auto_hide = config.get('auto_hide', False)
        except:
            auto_hide = False
    
    # 自动隐藏需要托盘功能支持
    auto_hide = auto_hide and enable_tray
    if auto_hide:
        try:
            print("🔔 已启用自动隐藏模式，程序将最小化到系统托盘")
        except:
            logging.info("已启用自动隐藏模式，程序将最小化到系统托盘")
    
    # 创建并启动服务器
    server = SMSServer(port, enable_tray, auto_hide)
    
    try:
        try:
            print(f"\n✅ 服务器启动中，监听端口: {port}")
            if enable_tray:
                print("🔔 系统托盘功能已启用")
                print("💡 关闭控制台窗口程序将继续在后台运行")
                print("💡 只有通过托盘菜单的'退出'选项才能完全退出程序")
            if auto_hide:
                print("🪟 控制台窗口将在2秒后自动隐藏")
            print("📱 请确保手机端SmsForwarder已正确配置")
            print("⏹️  按 Ctrl+C 停止服务器\n")
        except:
            logging.info(f"服务器启动中，监听端口: {port}")
            if enable_tray:
                logging.info("系统托盘功能已启用")
            if auto_hide:
                logging.info("控制台窗口将在2秒后自动隐藏")
        
        server.start()
        
    except KeyboardInterrupt:
        try:
            print("\n\n🛑 用户中断，正在关闭服务器...")
        except:
            safe_logging('info', "用户中断，正在关闭服务器...")
        safe_logging('info', "用户中断程序")
    except Exception as e:
        safe_logging('error', f"程序运行出错: {e}")
        try:
            print(f"\n❌ 程序运行出错: {e}")
        except:
            pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 