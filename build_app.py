#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VocabMaster 打包脚本
用于将 VocabMaster 项目打包成独立的可执行文件，支持Windows、macOS和Linux平台
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
    """构建可执行文件，支持跨平台"""
    print("开始构建可执行文件...")
    
    # 获取当前目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 项目相关路径
    app_path = os.path.join(base_dir, "app.py")
    assets_path = os.path.join(base_dir, "assets")
    terms_path = os.path.join(base_dir, "terms_and_expressions")
    
    # 根据操作系统选择合适的图标文件
    current_os = platform.system().lower()
    if current_os == "windows":
        icon_path = os.path.join(base_dir, "assets", "icon.ico")
    elif current_os == "darwin":  # macOS
        icon_path = os.path.join(base_dir, "assets", "icon.icns")
    else:  # Linux
        icon_path = os.path.join(base_dir, "assets", "icon.png")
    
    # 确保图标文件存在
    if not os.path.exists(icon_path):
        print(f"警告: 图标文件不存在: {icon_path}")
        # 如果特定平台的图标不存在，尝试使用PNG图标作为备选
        fallback_icon = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(fallback_icon):
            icon_path = fallback_icon
            print(f"使用备选图标: {icon_path}")
        else:
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
        # 添加资源文件目录
        "--add-data", f"{assets_path}{os.pathsep}assets",
        # 添加日志目录 (确保logs目录存在)
        "--add-data", f"{logs_dir}{os.pathsep}logs",
        # 添加根目录下的数据文件 (目标是根目录 '.')
        "--add-data", f"bec_higher_cufe.json{os.pathsep}.",
        # 添加 terms_and_expressions 子目录下的数据文件 (目标是根目录 '.')
        "--add-data", f"terms_and_expressions{os.path.sep}terms_and_expressions_1.json{os.pathsep}.",
        "--add-data", f"terms_and_expressions{os.path.sep}terms_and_expressions_2.json{os.pathsep}.",
        # 如果还有其他数据文件，也像上面一样添加
        
        # 排除不必要的模块以减小文件大小
        "--exclude-module=matplotlib",
        "--exclude-module=opencv-python",
        "--exclude-module=notebook",
        "--exclude-module=scipy",
        # 指定隐藏导入，确保所有依赖被正确打包
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=PyQt6",
    ]
    
    # 根据操作系统添加特定配置
    system = platform.system().lower()
    if system == "darwin":  # macOS
        cmd.extend([
            "--target-architecture=x86_64",  # 支持Intel芯片
            "--target-architecture=arm64",   # 支持Apple Silicon
            "--osx-bundle-identifier=com.vocabmaster.app",
        ])
    elif system == "linux":
        # Linux特定配置
        cmd.extend([
            "--runtime-tmpdir=/tmp",
        ])
    
    # 添加主程序文件路径
    cmd.append(app_path)
    
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

def get_executable_name():
    """根据操作系统返回可执行文件名称"""
    system = platform.system().lower()
    if system == "windows":
        return "VocabMaster.exe"
    elif system == "darwin":  # macOS
        return "VocabMaster"
    else:  # Linux
        return "VocabMaster"

def main():
    """主函数"""
    print("=" * 50)
    print("VocabMaster 跨平台打包脚本")
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
    
    # 显示当前操作系统信息
    system = platform.system()
    release = platform.release()
    print(f"当前操作系统: {system} {release}")
    
    # 清理之前的构建文件
    clean_previous_build()
    
    # 构建可执行文件
    if build_executable():
        # 复制额外文件
        copy_additional_files()
        
        # 获取打包后文件的路径
        exe_name = get_executable_name()
        exe_path = os.path.join(base_dir, "dist", exe_name)
        if os.path.exists(exe_path):
            exe_size = os.path.getsize(exe_path) / (1024 * 1024)  # 转换为 MB
            print(f"生成的可执行文件大小: {exe_size:.2f} MB")
            print(f"可执行文件位置: {os.path.abspath(exe_path)}")
        else:
            print("警告: 未找到生成的可执行文件!")
        
        print("\n构建完成! 可执行文件已生成在 dist 目录下。")
        
        # 根据操作系统显示不同的运行提示
        system = platform.system().lower()
        if system == "windows":
            print(f"运行方式: 双击 {os.path.join('dist', exe_name)} 即可启动程序。")
        elif system == "darwin":  # macOS
            print(f"运行方式: 在终端中执行 chmod +x {os.path.join('dist', exe_name)} 赋予执行权限后，双击或执行 ./{os.path.join('dist', exe_name)} 启动程序。")
        else:  # Linux
            print(f"运行方式: 在终端中执行 chmod +x {os.path.join('dist', exe_name)} 赋予执行权限后，执行 ./{os.path.join('dist', exe_name)} 启动程序。")
    else:
        print("\n构建失败! 请检查错误信息。")

if __name__ == "__main__":
    main()