"""
设置对话框模块
提供可视化编辑config.json的界面
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QSpinBox, QComboBox, QCheckBox,
    QPushButton, QFormLayout, QMessageBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from src.config.settings import Settings


class SettingsDialog(QDialog):
    """设置对话框类"""

    # 配置已保存信号
    settings_saved = Signal()

    def __init__(self, settings: Optional[Settings] = None, parent=None):
        """
        初始化设置对话框

        Args:
            settings: 配置对象
            parent: 父窗口
        """
        super().__init__(parent)
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("设置")
        self.resize(600, 500)

        # 主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # API设置选项卡
        self.setup_api_tab()

        # 搜索设置选项卡
        self.setup_search_tab()

        # 编辑器设置选项卡
        self.setup_editor_tab()

        # 窗口设置选项卡
        self.setup_window_tab()

        # 按钮布局
        button_layout = QHBoxLayout()

        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # 测试连接按钮
        self.test_button = QPushButton("测试API连接")
        self.test_button.clicked.connect(self.test_api_connection)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def setup_api_tab(self):
        """设置API选项卡"""
        api_tab = QWidget()
        layout = QVBoxLayout()
        api_tab.setLayout(layout)

        # API设置分组
        api_group = QGroupBox("API设置")
        api_form = QFormLayout()
        api_group.setLayout(api_form)
        layout.addWidget(api_group)

        # API基础URL
        self.api_base_url_edit = QLineEdit()
        self.api_base_url_edit.setPlaceholderText("http://localhost:8080")
        api_form.addRow("API基础URL:", self.api_base_url_edit)

        # 元数据基础URL（新增字段）
        self.metadata_base_url_edit = QLineEdit()
        self.metadata_base_url_edit.setPlaceholderText("http://localhost:6155")
        api_form.addRow("元数据服务器URL:", self.metadata_base_url_edit)

        # 超时设置
        self.api_timeout_spin = QSpinBox()
        self.api_timeout_spin.setRange(1, 300)
        self.api_timeout_spin.setSuffix(" 秒")
        api_form.addRow("请求超时:", self.api_timeout_spin)

        # 重试次数
        self.api_retry_spin = QSpinBox()
        self.api_retry_spin.setRange(1, 10)
        api_form.addRow("重试次数:", self.api_retry_spin)

        layout.addStretch()

        self.tab_widget.addTab(api_tab, "API")

    def setup_search_tab(self):
        """设置搜索选项卡"""
        search_tab = QWidget()
        layout = QVBoxLayout()
        search_tab.setLayout(layout)

        # 搜索设置分组
        search_group = QGroupBox("搜索设置")
        search_form = QFormLayout()
        search_group.setLayout(search_form)
        layout.addWidget(search_group)

        # 最小字符数
        self.search_min_chars_spin = QSpinBox()
        self.search_min_chars_spin.setRange(1, 10)
        search_form.addRow("最小搜索字符数:", self.search_min_chars_spin)

        # 最大结果数
        self.search_max_results_spin = QSpinBox()
        self.search_max_results_spin.setRange(10, 5000)
        self.search_max_results_spin.setSingleStep(100)
        search_form.addRow("最大搜索结果:", self.search_max_results_spin)

        # 支持的语言
        self.search_languages_edit = QLineEdit()
        self.search_languages_edit.setPlaceholderText("zh,en,de,fr,...")
        search_form.addRow("支持的语言:", self.search_languages_edit)

        layout.addStretch()

        self.tab_widget.addTab(search_tab, "搜索")

    def setup_editor_tab(self):
        """设置编辑器选项卡"""
        editor_tab = QWidget()
        layout = QVBoxLayout()
        editor_tab.setLayout(layout)

        # 编辑器设置分组
        editor_group = QGroupBox("编辑器设置")
        editor_form = QFormLayout()
        editor_group.setLayout(editor_form)
        layout.addWidget(editor_group)

        # 字体大小
        self.editor_font_size_spin = QSpinBox()
        self.editor_font_size_spin.setRange(8, 32)
        editor_form.addRow("字体大小:", self.editor_font_size_spin)

        # 主题
        self.editor_theme_combo = QComboBox()
        self.editor_theme_combo.addItems(["dark", "light"])
        editor_form.addRow("主题:", self.editor_theme_combo)

        # 自动保存
        self.editor_auto_save_check = QCheckBox()
        editor_form.addRow("自动保存:", self.editor_auto_save_check)

        # 保存路径
        self.editor_save_path_edit = QLineEdit()
        editor_form.addRow("默认保存路径:", self.editor_save_path_edit)

        layout.addStretch()

        self.tab_widget.addTab(editor_tab, "编辑器")

    def setup_window_tab(self):
        """设置窗口选项卡"""
        window_tab = QWidget()
        layout = QVBoxLayout()
        window_tab.setLayout(layout)

        # 窗口设置分组
        window_group = QGroupBox("窗口设置")
        window_form = QFormLayout()
        window_group.setLayout(window_form)
        layout.addWidget(window_group)

        # 窗口宽度
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(400, 3840)
        window_form.addRow("窗口宽度:", self.window_width_spin)

        # 窗口高度
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(300, 2160)
        window_form.addRow("窗口高度:", self.window_height_spin)

        layout.addStretch()

        self.tab_widget.addTab(window_tab, "窗口")

    def load_settings(self):
        """从配置加载设置到UI"""
        try:
            # API设置
            self.api_base_url_edit.setText(
                self.settings.get("api.base_url", "http://localhost:8080")
            )
            # 加载metadata_base_url，如果不存在则使用默认值
            self.metadata_base_url_edit.setText(
                self.settings.get("api.metadata_base_url", "http://localhost:6155")
            )
            self.api_timeout_spin.setValue(
                self.settings.get("api.timeout", 30)
            )
            self.api_retry_spin.setValue(
                self.settings.get("api.retry_count", 3)
            )

            # 搜索设置
            self.search_min_chars_spin.setValue(
                self.settings.get("search.min_chars", 2)
            )
            self.search_max_results_spin.setValue(
                self.settings.get("search.max_results", 1500)
            )

            # 语言列表转为逗号分隔的字符串
            languages = self.settings.get("search.languages", ["zh", "en"])
            self.search_languages_edit.setText(",".join(languages))

            # 编辑器设置
            self.editor_font_size_spin.setValue(
                self.settings.get("editor.font_size", 12)
            )
            self.editor_theme_combo.setCurrentText(
                self.settings.get("editor.theme", "dark")
            )
            self.editor_auto_save_check.setChecked(
                self.settings.get("editor.auto_save", False)
            )
            self.editor_save_path_edit.setText(
                self.settings.get("editor.save_path", "../Metadata Patches")
            )

            # 窗口设置
            self.window_width_spin.setValue(
                self.settings.get("window.width", 1200)
            )
            self.window_height_spin.setValue(
                self.settings.get("window.height", 800)
            )

        except Exception as e:
            self.logger.error(f"加载设置到UI失败: {e}")
            QMessageBox.critical(self, "错误", f"加载设置失败:\n{str(e)}")

    def save_settings(self):
        """保存UI设置到配置"""
        try:
            # API设置
            self.settings.set("api.base_url", self.api_base_url_edit.text().strip())
            # 保存metadata_base_url到配置
            metadata_url = self.metadata_base_url_edit.text().strip()
            if metadata_url:
                self.settings.set("api.metadata_base_url", metadata_url)
            else:
                self.settings.set("api.metadata_base_url", "http://localhost:6155")

            self.settings.set("api.timeout", self.api_timeout_spin.value())
            self.settings.set("api.retry_count", self.api_retry_spin.value())

            # 搜索设置
            self.settings.set("search.min_chars", self.search_min_chars_spin.value())
            self.settings.set("search.max_results", self.search_max_results_spin.value())

            # 语言列表处理
            languages_text = self.search_languages_edit.text().strip()
            if languages_text:
                languages = [lang.strip() for lang in languages_text.split(",") if lang.strip()]
                if languages:  # 确保不为空列表
                    self.settings.set("search.languages", languages)

            # 编辑器设置
            self.settings.set("editor.font_size", self.editor_font_size_spin.value())
            self.settings.set("editor.theme", self.editor_theme_combo.currentText())
            self.settings.set("editor.auto_save", self.editor_auto_save_check.isChecked())
            self.settings.set("editor.save_path", self.editor_save_path_edit.text().strip())

            # 窗口设置
            self.settings.set("window.width", self.window_width_spin.value())
            self.settings.set("window.height", self.window_height_spin.value())

            # 保存到文件
            if self.settings.save():
                self.logger.info("设置保存成功")
                self.settings_saved.emit()
                QMessageBox.information(self, "成功", "设置已保存")
                self.accept()
            else:
                self.logger.error("设置保存失败")
                QMessageBox.critical(self, "错误", "保存设置失败，请检查文件权限")

        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败:\n{str(e)}")

    def test_api_connection(self):
        """测试API连接"""
        from src.core.api_client import get_api_client

        try:
            base_url = self.api_base_url_edit.text().strip()
            if not base_url:
                QMessageBox.warning(self, "警告", "请输入API基础URL")
                return

            # 创建临时API客户端进行测试
            client = get_api_client()
            original_url = client.base_url

            # 临时设置URL
            client.set_base_url(base_url)

            # 测试连接
            if client.test_connection():
                QMessageBox.information(self, "成功", f"API连接测试成功\nURL: {base_url}")
            else:
                QMessageBox.warning(self, "警告", f"API连接测试失败\nURL: {base_url}")

            # 恢复原始URL
            client.set_base_url(original_url)

        except Exception as e:
            self.logger.error(f"API连接测试失败: {e}")
            QMessageBox.critical(self, "错误", f"API连接测试失败:\n{str(e)}")

    def get_metadata_base_url(self) -> str:
        """获取元数据服务器URL"""
        return self.metadata_base_url_edit.text().strip() or "http://localhost:6155"


if __name__ == "__main__":
    # 测试设置对话框
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())