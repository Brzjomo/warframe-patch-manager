"""
配置管理模块
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class Settings:
    """配置管理类"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置

        Args:
            config_file: 配置文件路径，如果为 None 则使用默认路径
        """
        if config_file is None:
            config_file = self._get_default_config_path()

        self.config_file = Path(config_file)
        self.settings = self._load_default_settings()

        if self.config_file.exists():
            self.load()
        else:
            self.save()  # 创建默认配置文件

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径

        处理PyInstaller打包环境，确保配置文件保存在exe所在目录
        而不是临时解压目录
        """
        # 检查是否在PyInstaller打包环境中运行
        if getattr(sys, 'frozen', False):
            # PyInstaller打包环境
            # sys.executable 是exe文件的路径
            exe_dir = Path(sys.executable).parent
            # 配置文件保存在exe同目录
            return str(exe_dir / "config.json")
        else:
            # 开发环境：使用项目根目录
            base_dir = Path(__file__).parent.parent.parent
            return str(base_dir / "config.json")

    def _load_default_settings(self) -> Dict[str, Any]:
        """加载默认设置"""
        return {
            "api": {
                "metadata_base_url": "http://localhost:6155",
                "timeout": 30,
                "retry_count": 3
            },
            "search": {
                "min_chars": 2,
                "max_results": 1500
            },
            "editor": {
                "font_size": 12,
                "theme": "dark",
                "auto_save": False,
                "save_path": "../Metadata Patches"
            },
            "window": {
                "width": 1500,
                "height": 800,
                "maximized": False,
                "pos_x": None,
                "pos_y": None
            },
            "recent_files": [],
            "user": {
                "language": "auto"
            }
        }

    def load(self) -> bool:
        """从文件加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            # 合并配置（保持默认值，只更新存在的键）
            self._merge_settings(self.settings, loaded_settings)
            return True

        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置失败: {e}")
            return False

    def save(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            return True

        except IOError as e:
            print(f"保存配置失败: {e}")
            return False

    def _merge_settings(self, target: Dict, source: Dict):
        """递归合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_settings(target[key], value)
            else:
                target[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.settings

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, save: bool = True):
        """设置配置值"""
        keys = key.split('.')
        settings = self.settings

        # 导航到最后一个字典
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]

        # 设置值
        settings[keys[-1]] = value

        # 自动保存
        if save:
            self.save()

    def add_recent_file(self, file_path: str):
        """添加最近文件"""
        recent_files = self.get("recent_files", [])

        # 移除重复项
        if file_path in recent_files:
            recent_files.remove(file_path)

        # 添加到开头
        recent_files.insert(0, file_path)

        # 限制数量
        recent_files = recent_files[:10]

        self.set("recent_files", recent_files)

    def clear_recent_files(self):
        """清空最近文件列表"""
        self.set("recent_files", [])

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        try:
            self.get(key)
            return True
        except (KeyError, TypeError):
            return False


# 全局配置实例
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


if __name__ == "__main__":
    # 测试配置模块
    settings = Settings()
    print("当前配置:")
    print(json.dumps(settings.settings, indent=2, ensure_ascii=False))

    # 测试获取设置
    print(f"搜索最小字符数: {settings.get('search.min_chars')}")

    # 测试设置
    settings.set('user.language', 'zh-CN')
    print(f"用户语言: {settings.get('user.language')}")