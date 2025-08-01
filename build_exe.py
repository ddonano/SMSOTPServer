#!/usr/bin/env python3
"""
SMS OTP Server - EXE打包脚本
将项目打包成可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print("✅ PyInstaller已安装")
        return True
    except ImportError:
        print("❌ PyInstaller未安装")
        print("请运行: pip install pyinstaller")
        return False

def create_spec_file():
    """创建PyInstaller规范文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 控制台版本
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('favicon.ico', '.'),
        ('SmsForwarder.json', '.'),
    ],
    hiddenimports=[
        'core',
        'core.server',
        'core.message_processor', 
        'core.config_manager',
        'tray_manager',
        'utils',
        'notification_manager',
        'pystray',
        'PIL',
        'winotify',
        'pyperclip'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SMSCodeServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico'
)

# 托盘版本
b = Analysis(
    ['main_tray.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('favicon.ico', '.'),
        ('SmsForwarder.json', '.'),
    ],
    hiddenimports=[
        'core',
        'core.server',
        'core.message_processor', 
        'core.config_manager',
        'tray_manager',
        'utils',
        'notification_manager',
        'pystray',
        'PIL',
        'winotify',
        'pyperclip'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz2 = PYZ(b.pure, b.zipped_data, cipher=block_cipher)

exe2 = EXE(
    pyz2,
    b.scripts,
    b.binaries,
    b.zipfiles,
    b.datas,
    [],
    name='SMSCodeServer_Tray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico'
)
'''
    
    with open('SMSCodeServer.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 规范文件创建成功: SMSCodeServer.spec")

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️  清理目录: {dir_name}")

def build_exe():
    """构建exe文件"""
    print("🔨 开始构建exe文件...")
    
    try:
        # 使用PyInstaller构建
        cmd = ['pyinstaller', '--clean', 'SMSCodeServer.spec']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ exe文件构建成功！")
            print("📁 输出目录: dist/")
            return True
        else:
            print("❌ 构建失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程中出错: {e}")
        return False

def show_build_info():
    """显示构建信息"""
    print("\n📋 构建信息:")
    print("=" * 50)
    
    # 检查输出文件
    dist_dir = Path('dist')
    if dist_dir.exists():
        exe_files = list(dist_dir.glob('*.exe'))
        for exe_file in exe_files:
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"📦 {exe_file.name} ({size_mb:.1f} MB)")
    
    print("\n🚀 使用说明:")
    print("1. 控制台版本: SMSCodeServer.exe")
    print("2. 托盘版本: SMSCodeServer_Tray.exe")
    print("3. 将exe文件复制到任意目录即可使用")

def main():
    """主函数"""
    print("🚀 SMS OTP Server - EXE打包工具")
    print("=" * 50)
    
    # 检查PyInstaller
    if not check_pyinstaller():
        return 1
    
    # 清理构建目录
    clean_build_dirs()
    
    # 创建规范文件
    create_spec_file()
    
    # 构建exe
    if build_exe():
        show_build_info()
        print("\n🎉 打包完成！")
        return 0
    else:
        print("\n💥 打包失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 