#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VocabMaster 打包脚本
用于将 VocabMaster 项目打包成独立的 .exe 可执行文件
"""

import os
import subprocess
import shutil
import platform
from pathlib import Path

def clean_previous_build():
    """清理之前的构建文件"""
    print("清理之前的构建文件...")
    
    # 获取当前目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 切换到脚本所在目录
    original_dir = os.getcwd()
    os.chdir(base_dir)
    
    try:
        # 清理 build 目录
        if os.path.exists("build"):
            shutil.rmtree("build")
        
        # 清理 dist 目录
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        
        # 删除 .spec 文件
        if os.path.exists("VocabMaster.spec"):
            os.remove("VocabMaster.spec")
    finally:
        # 恢复原来的工作目录
        os.chdir(original_dir)

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 获取当前目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 项目相关路径
    icon_path = os.path.join(base_dir, "assets", "icon.ico")
    app_path = os.path.join(base_dir, "app.py")
    assets_path = os.path.join(base_dir, "assets")
    terms_path = os.path.join(base_dir, "terms_and_expressions")
    
    # 确保 assets 目录和图标文件存在
    if not os.path.exists(icon_path):
        print(f"警告: 图标文件不存在: {icon_path}")
        icon_path = ""  # 如果图标不存在，使用空字符串让 PyInstaller 使用默认图标
    
    # 确保主程序文件存在
    if not os.path.exists(app_path):
        print(f"错误: 主程序文件不存在: {app_path}")
        return False
    
    # 创建目录确保日志文件夹存在
    logs_dir = os.path.join(base_dir, "logs")
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--name=VocabMaster",
        f"--icon={icon_path}" if icon_path else "",
        "--noconfirm",
        "--windowed",  # 使用 GUI 模式，不显示控制台窗口
        "--onefile",   # 打包成单个可执行文件
        "--clean",     # 在构建之前清理 PyInstaller 缓存
        # 添加必要的数据文件
        "--add-data", f"{assets_path}{os.pathsep}assets",
        "--add-data", f"{terms_path}{os.pathsep}terms_and_expressions",
        "--add-data", f"{logs_dir}{os.pathsep}logs",
        "--add-data", f"{data_dir}{os.pathsep}data",
        # 排除不必要的模块以减小文件大小
        "--exclude-module=matplotlib",
        "--exclude-module=opencv-python",
        "--exclude-module=notebook",
        "--exclude-module=scipy",
        # 指定隐藏导入，确保所有依赖被正确打包
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=PyQt6",
        # 主程序文件 - 使用绝对路径
        app_path
    ]
    
    # 过滤掉空项
    cmd = [item for item in cmd if item]
    
    # 切换到脚本所在目录执行命令
    original_dir = os.getcwd()
    os.chdir(base_dir)
    
    print(f"切换工作目录到: {base_dir}")
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd)
        success = result.returncode == 0
    finally:
        # 恢复原来的工作目录
        os.chdir(original_dir)
    
    if not success:
        print("构建失败!")
        return False
    
    print("构建成功!")
    return True

def copy_additional_files():
    """复制额外所需文件到构建目录"""
    print("复制额外文件...")
    
    # 获取当前目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 如果使用 --onefile 选项，则不需要此步骤
    pass

def main():
    """主函数"""
    print("=" * 50)
    print("VocabMaster 打包脚本")
    print("=" * 50)
    
    # 获取当前目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 检查是否安装了 PyInstaller
    try:
        import PyInstaller
        print(f"找到 PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 未安装 PyInstaller! 请先运行: pip install pyinstaller")
        return
    
    # 清理之前的构建文件
    clean_previous_build()
    
    # 构建可执行文件
    if build_executable():
        # 复制额外文件
        copy_additional_files()
        
        # 获取打包后文件的路径
        exe_path = os.path.join(base_dir, "dist", "VocabMaster.exe")
        if os.path.exists(exe_path):
            exe_size = os.path.getsize(exe_path) / (1024 * 1024)  # 转换为 MB
            print(f"生成的可执行文件大小: {exe_size:.2f} MB")
            print(f"可执行文件位置: {os.path.abspath(exe_path)}")
        else:
            print("警告: 未找到生成的可执行文件!")
        
        print("\n构建完成! 可执行文件已生成在 dist 目录下。")
        print(f"运行方式: 双击 {os.path.join(base_dir, 'dist', 'VocabMaster.exe')} 即可启动程序。")
    else:
        print("\n构建失败! 请检查错误信息。")

if __name__ == "__main__":
    main()