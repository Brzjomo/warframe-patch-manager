#!/usr/bin/env python3
"""
WarframePatchManager - 主程序入口
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
# 处理PyInstaller打包环境
if getattr(sys, 'frozen', False):
    # 打包环境：使用exe所在目录作为项目根目录
    project_root = Path(sys.executable).parent
else:
    # 开发环境：使用src目录的父目录
    project_root = Path(__file__).parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "warframe_patch_manager.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    print("=" * 50)
    print("WarframePatchManager")
    print("=" * 50)
    print()

    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("启动 WarframePatchManager")

    try:
        # 尝试导入 PySide6
        from PySide6.QtWidgets import QApplication

        # 导入配置
        from src.config.settings import Settings

        # 加载配置
        settings = Settings()
        logger.info("配置加载完成")

        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("WarframePatchManager")
        app.setOrganizationName("OpenWF")
        app.setOrganizationDomain("openwf.example.com")

        logger.info("Qt 应用初始化完成")

        # 导入并创建主窗口
        try:
            from src.gui.main_window import MainWindow
            window = MainWindow(settings)
            window.show()

            logger.info("主窗口创建完成")

            # 运行应用
            logger.info("进入应用主循环")
            return_code = app.exec()
            logger.info(f"应用退出，返回码: {return_code}")

            return return_code

        except ImportError as e:
            logger.error(f"导入 GUI 模块失败: {e}")
            print(f"错误: GUI 模块未实现: {e}")
            print("请先实现 GUI 模块")
            return 1

    except ImportError as e:
        logger.error(f"导入 Qt 模块失败: {e}")
        print(f"错误: 缺少 PySide6 依赖")
        print("请运行: pip install PySide6")
        return 1
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())