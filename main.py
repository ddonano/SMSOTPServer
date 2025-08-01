#!/usr/bin/env python3
"""
SMS OTP Server - 控制台版
短信验证码转发服务器（简化版）
"""

import sys
import logging
import argparse
from core import SMSServer, ConfigManager

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    SMS OTP Server                            ║
║              短信验证码转发服务器 - 控制台版                  ║
║                                                              ║
║  功能: 自动提取短信验证码并复制到剪贴板                      ║
║  特色: 控制台显示、实时日志、简单易用                        ║
║  注意: 按 Ctrl+C 停止服务器                                  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="SMS OTP Server - 短信验证码转发服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py              # 使用默认配置启动
  python main.py -p 65432     # 指定端口启动
        """
    )
    parser.add_argument('-p', '--port', type=int, help="监听端口号", default=None)
    return parser.parse_args()

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 打印横幅
    print_banner()
    
    # 解析命令行参数
    args = parse_args()
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 确定端口号
    if args.port:
        port = args.port
        logging.info(f"使用命令行参数指定的端口: {port}")
    else:
        port = config_manager.get_port()
        logging.info(f"使用配置文件中的端口: {port}")
    
    # 验证端口号
    if port < 1 or port > 65535:
        logging.error("端口号必须在1-65535之间")
        return 1
    
    # 创建并启动服务器
    server = SMSServer(port, config_manager)
    
    try:
        print(f"📱 请确保手机端SmsForwarder已正确配置")
        print("⏹️  按 Ctrl+C 停止服务器\n")
        server.start()
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断，正在关闭服务器...")
        logging.info("用户中断程序")
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
