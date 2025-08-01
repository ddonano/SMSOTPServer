"""
SMS服务器核心模块
提供基础的socket服务器功能
"""

import socket
import threading
import time
import logging
from typing import Optional, Dict, Any
from .message_processor import MessageProcessor
from .config_manager import ConfigManager

class SMSServer:
    """SMS服务器核心类"""
    
    def __init__(self, port: int, config_manager: Optional[ConfigManager] = None):
        self.port = port
        self.server_socket = None
        self.running = False
        self.force_exit = False
        self.stats = {
            'start_time': 0,
            'last_activity': 0,
            'sms_count': 0,
            'call_count': 0
        }
        
        # 初始化组件
        self.config_manager = config_manager or ConfigManager()
        self.message_processor = MessageProcessor()
        
    def start(self):
        """启动服务器"""
        self.running = True
        self.stats['start_time'] = time.time()
        
        # 创建socket对象
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            logging.info(f"服务器启动成功，监听端口 {self.port}")
            
            # 主服务器循环
            while self.running and not self.force_exit:
                try:
                    # 设置socket超时，以便能够响应退出信号
                    self.server_socket.settimeout(1.0)
                    client_socket, client_address = self.server_socket.accept()
                    logging.info(f"客户端连接: {client_address}")
                    
                    # 在新线程中处理客户端连接
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    # 超时是正常的，继续循环
                    continue
                except Exception as e:
                    if self.running and not self.force_exit:
                        logging.error(f"处理客户端连接时出错: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"服务器启动失败: {e}")
        finally:
            self.stop()
    
    def _handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        try:
            data = client_socket.recv(1024)
            if not data:
                logging.warning(f"客户端 {client_address} 未发送数据")
                client_socket.close()
                return
            
            text = data.decode('utf-8')
            logging.info(f"收到数据: {text}")
            
            # 更新最后活动时间
            self.stats['last_activity'] = time.time()
            
            # 处理消息
            self.message_processor.process_message(text, self.stats)
            
        except Exception as e:
            logging.error(f"处理客户端 {client_address} 时出错: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def stop(self):
        """停止服务器"""
        self.running = False
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.server_socket = None
            except:
                pass
        
        logging.info("服务器已停止")
    
    def restart(self):
        """重启服务器"""
        logging.info("正在重启服务器...")
        self.stop()
        time.sleep(1)  # 等待资源释放
        self.start()
    
    def force_quit(self):
        """强制退出程序"""
        logging.info("收到强制退出信号")
        self.force_exit = True
        self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        return self.stats.copy() 