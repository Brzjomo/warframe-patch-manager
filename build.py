#!/usr/bin/env python3
"""
打包脚本 - 将WarframePatchManager打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """主打包函数"""
    print("=" * 50)
    print("WarframePatchManager 打包工具")
    print("=" * 50)

    # 项目根目录
    project_root = Path(__file__).parent
    print(f"项目根目录: {project_root}")

    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return 1

    # 定义数据文件
    datas = []

    # 1. 数据文件：InternalName.csv
    data_csv = project_root / 'data' / 'InternalName.csv'
    if data_csv.exists():
        datas.append((str(data_csv), 'data'))
        print(f"[OK] 添加数据文件: {data_csv.name}")
    else:
        print(f"[ERROR] 数据文件不存在: {data_csv}")
        return 1

    # 2. i18n.json文件（多语言数据）- 保持原始目录结构
    i18n_path = project_root / 'node_modules' / '@wfcd' / 'items' / 'data' / 'json' / 'i18n.json'
    if i18n_path.exists():
        # 保持原始目录结构：node_modules/@wfcd/items/data/json/i18n.json
        datas.append((str(i18n_path), 'node_modules/@wfcd/items/data/json'))
        print(f"[OK] 添加i18n文件: {i18n_path.name} (保持原始目录结构)")
    else:
        print(f"[WARN] i18n文件不存在: {i18n_path}")
        # 尝试查找其他位置
        print("正在搜索i18n.json文件...")
        i18n_files = list(project_root.glob('**/i18n.json'))
        if i18n_files:
            i18n_path = i18n_files[0]
            datas.append((str(i18n_path), 'data'))
            print(f"[OK] 找到并添加i18n文件: {i18n_path}")
        else:
            print("[WARN] 未找到i18n.json文件，多语言功能可能受限")

    # 3. 配置文件（可选，应用可以生成默认配置）
    config_path = project_root / 'config.json'
    if config_path.exists():
        datas.append((str(config_path), '.'))
        print(f"[OK] 添加配置文件: {config_path.name}")
    else:
        print("[INFO] 未找到config.json，应用将生成默认配置")

    # 构建PyInstaller命令
    pyinstaller_cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--name=WarframePatchManager',
        '--onefile',  # 打包为单个可执行文件
        '--windowed',  # 不显示控制台窗口（GUI应用）
        '--clean',
        '--noconfirm',
        # 添加项目路径
        '--paths', str(project_root),
        '--paths', str(project_root / 'src'),
        # 添加隐藏导入
        '--hidden-import=PySide6',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=requests',
        '--hidden-import=pandas',
        '--hidden-import=pandas._libs.tslibs.timedeltas',
        '--hidden-import=pandas._libs.tslibs.np_datetime',
        '--hidden-import=pandas._libs.tslibs.base',
        '--hidden-import=pandas._libs.skiplist',
        '--hidden-import=python_dotenv',
        '--hidden-import=src',
        '--hidden-import=src.config',
        '--hidden-import=src.core',
        '--hidden-import=src.gui',
        '--hidden-import=src.utils',
        # 排除不需要的模块
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=tkinter',
        # 添加数据文件
    ]

    # 添加所有数据文件
    for src, dest in datas:
        pyinstaller_cmd.extend(['--add-data', f'{src}{os.pathsep}{dest}'])

    # 添加主程序文件
    pyinstaller_cmd.append(str(project_root / 'src' / 'main.py'))

    print("\n" + "=" * 50)
    print("开始打包...")
    print("命令:", ' '.join(pyinstaller_cmd[:10]), "...")  # 只显示前10个参数

    # 执行打包命令
    try:
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("打包输出:")
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"打包失败，返回码: {e.returncode}")
        print(f"标准输出: {e.stdout}")
        print(f"错误输出: {e.stderr}")
        return 1

    print("\n" + "=" * 50)
    print("打包完成!")

    # 显示结果
    dist_dir = project_root / 'dist'
    if dist_dir.exists():
        exe_files = list(dist_dir.glob('WarframePatchManager*'))
        if exe_files:
            print(f"可执行文件位置: {exe_files[0]}")
            print(f"文件大小: {exe_files[0].stat().st_size / (1024*1024):.2f} MB")

    print("\n部署说明:")
    print("1. 将dist/WarframePatchManager.exe复制到目标电脑")
    print("2. 确保目标电脑已安装Microsoft Visual C++ Redistributable")
    print("3. 首次运行会在同目录下生成config.json配置文件")
    print("4. 补丁文件默认保存在程序目录的'../Metadata Patches'文件夹中")

    return 0

if __name__ == '__main__':
    sys.exit(main())