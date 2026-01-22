"""
路径工具模块
处理PyInstaller打包环境下的路径问题
"""

import sys
import os
from pathlib import Path
from typing import Optional


def get_base_dir() -> Path:
    """获取应用程序基础目录

    在PyInstaller打包环境中返回exe所在目录
    在开发环境中返回项目根目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller打包环境
        # sys.executable 是exe文件的路径
        return Path(sys.executable).parent
    else:
        # 开发环境：返回项目根目录（src目录的父目录）
        # 假设这个文件在 src/utils/path_utils.py
        return Path(__file__).parent.parent.parent


def get_project_root() -> Path:
    """获取项目根目录（兼容性函数，与get_base_dir相同）"""
    return get_base_dir()


def get_data_dir() -> Path:
    """获取数据目录路径"""
    base_dir = get_base_dir()
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path(filename: str = "config.json") -> Path:
    """获取配置文件路径"""
    base_dir = get_base_dir()
    return base_dir / filename


def get_patches_dir() -> Path:
    """获取补丁目录路径"""
    from src.config.settings import get_settings

    try:
        settings = get_settings()
        save_path_str = settings.get("editor.save_path", "../Metadata Patches")
        save_path = Path(save_path_str)

        if save_path.is_absolute():
            return save_path
        else:
            # 相对路径：相对于应用程序基础目录
            base_dir = get_base_dir()
            return (base_dir / save_path_str).resolve()

    except Exception:
        # 如果无法获取设置，使用默认路径
        base_dir = get_base_dir()
        return (base_dir / "../Metadata Patches").resolve()


def ensure_directory(path: Path) -> Path:
    """确保目录存在，如果不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    # 测试代码
    print("测试路径工具模块")
    print(f"基础目录: {get_base_dir()}")
    print(f"数据目录: {get_data_dir()}")
    print(f"配置文件路径: {get_config_path()}")
    print(f"补丁目录: {get_patches_dir()}")

    # 测试目录创建
    test_dir = get_base_dir() / "test_dir"
    ensure_directory(test_dir)
    print(f"测试目录已创建: {test_dir}")

    # 清理
    if test_dir.exists():
        test_dir.rmdir()
        print("测试目录已清理")