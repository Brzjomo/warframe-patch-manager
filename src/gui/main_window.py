"""
主窗口模块
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QMenuBar,
    QMenu, QToolBar, QMessageBox, QComboBox, QApplication, QFrame,
    QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence, QFont, QTextDocument, QTextCursor, QTextCharFormat

from src.config.settings import Settings
from src.core.search_engine import get_search_engine
from src.core.api_client import get_api_client
from src.core.wf_items_loader import get_wf_items_loader
from src.gui.syntax_highlighter import WarframeSyntaxHighlighter


class MainWindow(QMainWindow):
    """主窗口类"""

    # 自定义信号
    search_requested = Signal(str)
    item_selected = Signal(str)

    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化主窗口

        Args:
            settings: 配置对象
        """
        super().__init__()

        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

        # 初始化搜索引擎
        self.search_engine = get_search_engine()

        # 初始化 API 客户端
        self.api_client = get_api_client()

        # 当前语言
        self.current_language = "zh"

        # 当前编辑器内容的文件路径（None表示从API生成的内容）
        self.current_file_path = None

        # 初始化标志 - 用于防止初始化期间保存语言设置
        self.initializing_language_combo = True

        # 初始化搜索延迟定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._on_search_timer_timeout)

        # 初始化编辑器文本搜索延迟定时器
        self.editor_search_timer = QTimer()
        self.editor_search_timer.setSingleShot(True)
        self.editor_search_timer.timeout.connect(self._on_editor_search_timer_timeout)

        self.setup_ui()
        self.setup_connections()
        self.setup_language_combo()
        self.load_settings()

        # 更新初始状态
        item_count = self.search_engine.get_item_count()
        self.count_label.setText(f"项目: {item_count}")

        # 确保初始化标志为False（防止异常情况）
        self.initializing_language_combo = False

        # 加载本地补丁列表
        self.refresh_local_patches_list()

        self.logger.info("主窗口初始化完成")
        self.logger.info(f"已加载 {item_count} 个物品")

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("WarframePatchManager")
        self.resize(
            self.settings.get("window.width", 1500),
            self.settings.get("window.height", 800)
        )

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 创建工具栏
        self.setup_toolbar()

        # 创建搜索栏
        self.setup_search_bar()

        # 创建分割器（左侧搜索列表，右侧编辑器）
        self.setup_splitter()
        main_layout.addWidget(self.splitter)

        # 创建状态栏
        self.setup_statusbar()

        # 创建菜单栏
        self.setup_menubar()

    def setup_toolbar(self):
        """创建工具栏action（供编辑器和菜单栏使用）"""
        # 文件操作
        self.new_action = QAction("新建", self)
        self.new_action.setShortcut(QKeySequence.New)

        self.open_action = QAction("打开", self)
        self.open_action.setShortcut(QKeySequence.Open)

        self.save_action = QAction("保存", self)
        self.save_action.setShortcut(QKeySequence.Save)

        # 编辑操作
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut(QKeySequence.Undo)

        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut(QKeySequence.Redo)

        # 搜索操作
        self.search_action = QAction("搜索", self)
        self.search_action.setShortcut(QKeySequence.Find)

    def setup_search_bar(self):
        """设置搜索栏"""
        self.search_widget = QWidget()
        search_layout = QHBoxLayout()
        self.search_widget.setLayout(search_layout)

        # 搜索标签
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)

        # 语言选择下拉框
        self.language_combo = QComboBox()
        self.language_combo.setToolTip("选择搜索语言")
        self.language_combo.setMinimumWidth(80)
        search_layout.addWidget(self.language_combo)

        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入物品名称（支持多语言）...")
        search_layout.addWidget(self.search_input, 1)  # 拉伸因子为1

        # 搜索按钮
        self.search_button = QPushButton("搜索")
        search_layout.addWidget(self.search_button)

        # 清除按钮
        self.clear_button = QPushButton("清除")
        search_layout.addWidget(self.clear_button)

    def setup_editor_menubar(self):
        """设置编辑器菜单栏（传统菜单栏样式）"""
        self.editor_menubar = QMenuBar()

        # 文件菜单
        file_menu = self.editor_menubar.addMenu("文件")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)

        # 编辑菜单
        edit_menu = self.editor_menubar.addMenu("编辑")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)

        # 搜索菜单已移除，改为右侧搜索栏
        return self.editor_menubar

    def setup_editor_search_bar(self):
        """设置编辑器文本搜索栏"""
        self.editor_search_widget = QWidget()
        editor_search_layout = QHBoxLayout()
        self.editor_search_widget.setLayout(editor_search_layout)

        # 搜索标签
        editor_search_label = QLabel("搜索编辑器内容:")
        editor_search_layout.addWidget(editor_search_label)

        # 搜索输入框
        self.editor_search_input = QLineEdit()
        self.editor_search_input.setPlaceholderText("搜索编辑器文本...")
        editor_search_layout.addWidget(self.editor_search_input, 1)  # 拉伸因子为1

        # 搜索按钮
        self.editor_search_button = QPushButton("搜索")
        editor_search_layout.addWidget(self.editor_search_button)

        # 清除按钮
        self.editor_clear_button = QPushButton("清除")
        editor_search_layout.addWidget(self.editor_clear_button)

        return self.editor_search_widget

    def setup_language_combo(self):
        """设置语言下拉框"""
        # 清空现有项
        self.language_combo.clear()

        # 获取支持的语言
        try:
            supported_languages = self.search_engine.get_supported_languages()
            languages = sorted(supported_languages)

            self.logger.debug(f"支持的语言列表: {languages}")
            self.logger.debug(f"支持的语言数量: {len(languages)}")

            # 语言显示名称映射
            language_names = {
                "en": "English",
                "zh": "中文",
                "de": "Deutsch",
                "es": "Español",
                "fr": "Français",
                "it": "Italiano",
                "ja": "日本語",
                "ko": "한국어",
                "pl": "Polski",
                "pt": "Português",
                "ru": "Русский",
                "th": "ไทย",
                "tr": "Türkçe",
                "uk": "Українська",
                "tc": "繁體中文",
            }

            # 添加语言项
            for lang_code in languages:
                display_name = language_names.get(lang_code, lang_code.upper())
                self.language_combo.addItem(display_name, lang_code)
                self.logger.debug(f"添加语言项: {display_name} ({lang_code})")

            # 设置当前语言
            saved_language = self.settings.get("user.language", "auto")
            self.logger.debug(f"从配置读取的语言: {saved_language}")

            if saved_language == "auto":
                # 自动检测（默认为中文）
                self.current_language = "zh"
                self.logger.debug(f"自动检测模式，设置当前语言为: {self.current_language}")
            elif saved_language in languages:
                self.current_language = saved_language
                self.logger.debug(f"使用配置中的语言: {self.current_language}")
            else:
                self.current_language = "zh"
                self.logger.debug(f"配置语言不在支持列表中，默认设置为: {self.current_language}")

            # 选择当前语言
            index = self.language_combo.findData(self.current_language)
            self.logger.debug(f"查找语言 '{self.current_language}' 的索引: {index}")

            if index >= 0:
                self.language_combo.setCurrentIndex(index)
                self.logger.debug(f"设置下拉框索引为: {index}")
            else:
                self.logger.warning(f"语言 '{self.current_language}' 不在下拉框中，当前索引保持为: {self.language_combo.currentIndex()}")

            # 更新状态栏语言标签
            current_text = self.language_combo.currentText()
            self.language_label.setText(f"语言: {current_text}")

            self.logger.info(f"语言下拉框初始化完成，当前语言: {self.current_language}, 显示文本: {current_text}")

        except Exception as e:
            self.logger.error(f"初始化语言下拉框失败: {e}", exc_info=True)
            # 默认添加英文
            self.language_combo.addItem("English", "en")
            self.language_combo.setCurrentIndex(0)
            self.language_label.setText("语言: English")
            self.logger.warning("语言下拉框初始化失败，使用默认英文")
        finally:
            # 初始化完成，允许保存语言设置
            self.initializing_language_combo = False

    def setup_splitter(self):
        """设置分割器"""
        self.splitter = QSplitter(Qt.Horizontal)

        # ===== 左侧：分为两部分（左侧本地补丁管理，右侧搜索结果列表）=====
        self.left_container = QWidget()
        left_container_layout = QHBoxLayout()
        left_container_layout.setContentsMargins(0, 0, 0, 0)
        self.left_container.setLayout(left_container_layout)

        # 左侧分割器（本地补丁管理区域和搜索结果列表）
        self.left_splitter = QSplitter(Qt.Horizontal)
        left_container_layout.addWidget(self.left_splitter)

        # === 左侧：本地补丁管理区域 ===
        self.local_patches_widget = QWidget()
        local_patches_layout = QVBoxLayout()
        self.local_patches_widget.setLayout(local_patches_layout)

        # 本地补丁管理标签
        patches_label = QLabel("本地补丁管理:")
        local_patches_layout.addWidget(patches_label)

        # 补丁文件列表
        self.local_patches_list = QListWidget()
        local_patches_layout.addWidget(self.local_patches_list)

        # 补丁管理按钮区域
        patch_buttons_layout = QHBoxLayout()

        self.refresh_patches_button = QPushButton("刷新列表")
        self.enable_patch_button = QPushButton("启用补丁")
        self.disable_patch_button = QPushButton("禁用补丁")
        self.delete_patch_button = QPushButton("删除补丁")  # 从编辑器区域移过来的按钮

        patch_buttons_layout.addWidget(self.refresh_patches_button)
        patch_buttons_layout.addWidget(self.enable_patch_button)
        patch_buttons_layout.addWidget(self.disable_patch_button)
        patch_buttons_layout.addWidget(self.delete_patch_button)
        patch_buttons_layout.addStretch()

        local_patches_layout.addLayout(patch_buttons_layout)

        self.left_splitter.addWidget(self.local_patches_widget)

        # === 右侧：搜索结果列表 ===
        self.search_results_widget = QWidget()
        search_results_layout = QVBoxLayout()
        self.search_results_widget.setLayout(search_results_layout)

        # 结果列表标签
        results_label = QLabel("搜索结果:")
        search_results_layout.addWidget(results_label)

        # 结果列表
        self.results_list = QListWidget()
        search_results_layout.addWidget(self.results_list)

        self.left_splitter.addWidget(self.search_results_widget)

        # 设置左侧分割器的初始比例（本地补丁管理:搜索结果 = 4:6）
        self.left_splitter.setSizes([300, 500])

        self.splitter.addWidget(self.left_container)

        # ===== 右侧：编辑器区域 =====
        self.right_widget = QWidget()
        right_layout = QVBoxLayout()
        self.right_widget.setLayout(right_layout)

        # === 上方：搜索栏区域 ===
        search_area_label = QLabel("搜索设置:")
        right_layout.addWidget(search_area_label)

        # 将搜索栏widget添加到右侧上方
        right_layout.addWidget(self.search_widget)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(separator)

        # === 下方：编辑器区域 ===
        editor_area_label = QLabel("编辑器:")
        right_layout.addWidget(editor_area_label)

        # 编辑器菜单栏
        self.setup_editor_menubar()
        right_layout.addWidget(self.editor_menubar)

        # 文本编辑器
        self.text_editor = QTextEdit()
        right_layout.addWidget(self.text_editor, 3)  # 拉伸因子3，占据更多空间

        # 创建语法高亮器
        self.syntax_highlighter = WarframeSyntaxHighlighter(self.text_editor.document())

        # 编辑器文本搜索栏
        self.setup_editor_search_bar()
        right_layout.addWidget(self.editor_search_widget)

        # 编辑器按钮（删除补丁按钮已移除）
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("重新加载数据")
        self.save_button = QPushButton("快速保存")
        self.clear_editor_button = QPushButton("清空编辑器")

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_editor_button)
        button_layout.addStretch()

        right_layout.addLayout(button_layout)

        self.splitter.addWidget(self.right_widget)

        # 设置最外层分割器的初始分割比例（左侧:右侧 = 4:6）
        self.splitter.setSizes([400, 600])

    def setup_statusbar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label, 1)  # 拉伸

        # 项目计数标签
        self.count_label = QLabel("项目: 0")
        self.status_bar.addPermanentWidget(self.count_label)

        # 语言标签
        self.language_label = QLabel("语言: 自动")
        self.status_bar.addPermanentWidget(self.language_label)

    def setup_menubar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单（仅保留应用程序级别操作）
        # file_menu = menubar.addMenu("文件")
        # 新建、打开、保存操作已移动到编辑器菜单栏
        # file_menu.addAction(self.new_action)
        # file_menu.addAction(self.open_action)
        # file_menu.addAction(self.save_action)
        # file_menu.addSeparator()

        # exit_action = QAction("退出", self)
        # exit_action.setShortcut(QKeySequence.Quit)
        # exit_action.triggered.connect(self.close)
        # file_menu.addAction(exit_action)

        # 编辑菜单已移动到编辑器菜单栏

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        editor_menubar_action = QAction("编辑器菜单栏", self, checkable=True, checked=True)
        editor_menubar_action.toggled.connect(self.toggle_editor_menubar)
        view_menu.addAction(editor_menubar_action)

        statusbar_action = QAction("状态栏", self, checkable=True, checked=True)
        statusbar_action.toggled.connect(self.toggle_statusbar)
        view_menu.addAction(statusbar_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_connections(self):
        """设置信号连接"""
        # 搜索相关
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)

        # 列表选择
        self.results_list.itemSelectionChanged.connect(self._on_item_selected)
        self.local_patches_list.itemSelectionChanged.connect(self._on_local_patch_selected)

        # 编辑器按钮
        self.load_button.clicked.connect(self._on_load_clicked)
        self.save_button.clicked.connect(self._on_quick_save_clicked)
        self.clear_editor_button.clicked.connect(self._on_clear_editor_clicked)

        # 本地补丁管理按钮
        self.refresh_patches_button.clicked.connect(self._on_refresh_patches_clicked)
        self.enable_patch_button.clicked.connect(self._on_enable_patch_clicked)
        self.disable_patch_button.clicked.connect(self._on_disable_patch_clicked)
        self.delete_patch_button.clicked.connect(self._on_delete_patch_clicked)

        # 工具栏按钮
        self.open_action.triggered.connect(self._on_open_clicked)
        self.save_action.triggered.connect(self._on_save_clicked)
        self.undo_action.triggered.connect(self._on_undo_clicked)
        self.redo_action.triggered.connect(self._on_redo_clicked)

        # 编辑器文本搜索
        self.editor_search_input.textChanged.connect(self._on_editor_search_text_changed)
        self.editor_search_button.clicked.connect(self._on_editor_search_clicked)
        self.editor_clear_button.clicked.connect(self._on_editor_clear_clicked)

    def load_settings(self):
        """加载窗口设置"""
        # 窗口大小和位置
        if self.settings.get("window.maximized"):
            self.showMaximized()
        else:
            width = self.settings.get("window.width", 1500)
            height = self.settings.get("window.height", 800)
            self.resize(width, height)

            pos_x = self.settings.get("window.pos_x")
            pos_y = self.settings.get("window.pos_y")
            if pos_x is not None and pos_y is not None:
                self.move(pos_x, pos_y)

        # 编辑器字体大小
        font_size = self.settings.get("editor.font_size", 12)
        font = QFont()
        font.setPointSize(font_size)
        self.text_editor.setFont(font)

    def save_window_state(self):
        """保存窗口状态"""
        if not self.isMaximized():
            self.settings.set("window.width", self.width())
            self.settings.set("window.height", self.height())
            self.settings.set("window.pos_x", self.x())
            self.settings.set("window.pos_y", self.y())

        self.settings.set("window.maximized", self.isMaximized())
        self.settings.save()

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.save_window_state()
        self.logger.info("窗口关闭，状态已保存")
        event.accept()

    def _on_language_changed(self, index: int):
        """语言选择变化事件"""
        # 检查是否在初始化期间，避免初始化时保存错误的语言设置
        if self.initializing_language_combo:
            self.logger.debug(f"忽略初始化期间的语言选择变化事件，索引: {index}")
            return

        if index >= 0:
            lang_code = self.language_combo.itemData(index)
            current_text = self.language_combo.currentText()

            self.logger.debug(f"语言选择变化事件 - 索引: {index}, 语言代码: {lang_code}, 显示文本: {current_text}")

            if lang_code:
                self.current_language = lang_code
                # 更新状态栏显示
                self.language_label.setText(f"语言: {current_text}")

                # 保存语言设置
                self.logger.debug(f"保存语言设置到配置文件: {lang_code}")
                self.settings.set("user.language", lang_code)
                save_result = self.settings.save()
                if save_result:
                    self.logger.info(f"语言设置已保存: {lang_code}")
                else:
                    self.logger.error("保存语言设置失败")

                self.logger.info(f"语言已切换为: {lang_code}")

                # 如果当前有搜索文本，重新搜索
                search_text = self.search_input.text().strip()
                if search_text and len(search_text) >= self.settings.get("search.min_chars", 2):
                    self.logger.debug(f"语言切换，重新执行搜索: {search_text}")
                    self._perform_search(search_text)
            else:
                self.logger.warning(f"语言选择变化事件中获取到空的语言代码，索引: {index}")
        else:
            self.logger.warning(f"语言选择变化事件中索引无效: {index}")

    def _on_search_text_changed(self, text: str):
        """搜索文本变化事件"""
        # 重置定时器
        self.search_timer.stop()

        min_chars = self.settings.get("search.min_chars", 2)

        if len(text) >= min_chars:
            # 延迟搜索（避免频繁搜索）
            delay = 300  # 300毫秒
            self.search_timer.start(delay)
        elif len(text) == 0:
            # 清空搜索框，清除结果
            self.results_list.clear()
            self.count_label.setText("项目: 0")
            self.status_label.setText("就绪")
        else:
            # 字符数不足，显示提示
            self.status_label.setText(f"请输入至少 {min_chars} 个字符进行搜索")

    def _on_search_timer_timeout(self):
        """搜索定时器超时"""
        search_text = self.search_input.text().strip()
        if search_text:
            self._perform_search(search_text)

    def _on_search_clicked(self):
        """搜索按钮点击事件"""
        search_text = self.search_input.text().strip()
        if search_text:
            self._perform_search(search_text)

    def _on_clear_clicked(self):
        """清除按钮点击事件"""
        self.search_input.clear()
        self.results_list.clear()
        self.count_label.setText("项目: 0")
        self.status_label.setText("已清除搜索")

    def _load_metadata(self, internal_name: str, localized_name: Optional[str] = None):
        """
        加载指定内部名称的元数据到编辑器

        Args:
            internal_name: 物品内部名称
            localized_name: 本地化名称（如果为None则自动获取）
        """
        if localized_name is None:
            # 获取物品名称（根据当前语言）
            try:
                loader = get_wf_items_loader()
                localized_name = loader.get_item_name(internal_name, self.current_language)
                # 如果未找到多语言名称，使用英文名称
                if not localized_name:
                    localized_name = self.search_engine.get_by_internal_name(internal_name)
            except Exception as e:
                self.logger.warning(f"获取物品名称失败: {e}")
                localized_name = self.search_engine.get_by_internal_name(internal_name)

        # 获取元数据文本
        self.status_label.setText(f"正在获取元数据: {localized_name}...")

        try:
            metadata_text = self.api_client.get_effective_metadata(internal_name)
            # 内容来自API，清除文件路径标记
            self.current_file_path = None

            if metadata_text:
                # 在文本前添加两行注释（根据用户修改的格式）
                header = f"# {localized_name}\n{internal_name}\n\n"
                full_text = header + metadata_text

                # 清除之前的搜索高亮
                self._clear_editor_search_highlights()
                # 重置编辑器当前字符格式
                self._reset_editor_char_format()
                # 将文本放入编辑器
                self.text_editor.setPlainText(full_text)
                self.status_label.setText(f"元数据已加载: {localized_name}")
            else:
                # 清除之前的搜索高亮
                self._clear_editor_search_highlights()
                # 重置编辑器当前字符格式
                self._reset_editor_char_format()
                self.text_editor.clear()
                self.text_editor.setPlainText(f"# 获取元数据失败: {internal_name}\n# 请检查API服务器是否运行在 http://localhost:6155")
                self.status_label.setText(f"获取元数据失败: {localized_name}")

        except Exception as e:
            self.logger.error(f"获取元数据失败: {e}")
            # 清除之前的搜索高亮
            self._clear_editor_search_highlights()
            # 重置编辑器当前字符格式
            self._reset_editor_char_format()
            self.text_editor.clear()
            self.text_editor.setPlainText(f"# 获取元数据时发生错误: {internal_name}\n# 错误: {str(e)}")
            self.status_label.setText(f"获取元数据失败: {str(e)}")

    def _on_item_selected(self):
        """列表项选择事件"""
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            return

        selected_item = selected_items[0]
        item_data = selected_item.data(Qt.UserRole)

        if item_data:
            self.item_selected.emit(item_data)

            # 获取物品显示文本并复制到剪切板
            item_text = selected_item.text()
            # 截断过长的文本用于状态显示
            if len(item_text) > 60:
                display_text = item_text[:57] + "..."
            else:
                display_text = item_text

            # 复制显示文本到剪切板
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(item_text)

            self.status_label.setText(f"已选择: {display_text} (已复制到剪切板)")

            # 获取物品名称（根据当前语言）
            internal_name = item_data
            try:
                loader = get_wf_items_loader()
                localized_name = loader.get_item_name(internal_name, self.current_language)
                # 如果未找到多语言名称，使用英文名称
                if not localized_name:
                    localized_name = self.search_engine.get_by_internal_name(internal_name)
            except Exception as e:
                self.logger.warning(f"获取物品名称失败: {e}")
                localized_name = self.search_engine.get_by_internal_name(internal_name)

            # 加载元数据
            self._load_metadata(internal_name, localized_name)
        else:
            # 没有数据（如"未找到匹配的结果"项）
            self.status_label.setText("请选择有效的物品")

    def _on_load_clicked(self):
        """重新加载数据按钮点击事件"""
        # 检查是否有选中的项目
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个物品")
            return

        selected_item = selected_items[0]
        internal_name = selected_item.data(Qt.UserRole)

        if not internal_name:
            QMessageBox.warning(self, "警告", "选中的项目无效")
            return

        # 获取本地化名称用于显示
        try:
            loader = get_wf_items_loader()
            localized_name = loader.get_item_name(internal_name, self.current_language)
            if not localized_name:
                localized_name = self.search_engine.get_by_internal_name(internal_name)
        except Exception as e:
            self.logger.warning(f"获取物品名称失败: {e}")
            localized_name = self.search_engine.get_by_internal_name(internal_name)

        # 确认是否重新加载（丢弃当前编辑器内容）
        reply = QMessageBox.question(
            self,
            "确认重新加载",
            f"确定要重新加载 '{localized_name}' 的元数据吗？\n编辑器当前内容将被丢弃。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._load_metadata(internal_name, localized_name)

    def _on_save_clicked(self):
        """保存按钮点击事件（使用文件对话框）"""
        content = self.text_editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "警告", "编辑器内容为空")
            return

        # 获取默认保存路径
        default_path_str = self.settings.get("editor.save_path", "../Metadata Patches")
        default_path = Path(default_path_str)

        # 判断是否为绝对路径
        if not default_path.is_absolute():
            # 相对路径：相对于项目根目录
            base_dir = Path(__file__).parent.parent.parent
            default_path = (base_dir / default_path_str).resolve()

        # 确保目录存在
        try:
            default_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            default_path = Path.home()  # 失败时使用用户主目录

        # 提取第一行作为默认文件名
        first_line = content.split('\n')[0].strip()
        if first_line.startswith("# "):
            filename_base = first_line[2:]  # 去掉 "# "
        else:
            filename_base = first_line  # 如果没有#，直接使用

        # 替换非法字符
        import re
        # Windows文件名非法字符: \ / : * ? " < > |
        illegal_chars = r'[\\/*?:"<>|]'
        safe_filename = re.sub(illegal_chars, '_', filename_base)
        # 替换空格为下划线（可选）
        safe_filename = safe_filename.replace(' ', '_')
        # 限制文件名长度
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]

        # 添加.txt扩展名
        if not safe_filename.endswith('.txt'):
            safe_filename += '.txt'

        # 打开保存文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            str(default_path / safe_filename),
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if not file_path:
            return  # 用户取消

        file_path = Path(file_path)

        # 检查文件是否存在（Qt对话框可能已经处理了，但为了安全再次检查）
        # if file_path.exists():
        #     reply = QMessageBox.question(
        #         self,
        #         "文件已存在",
        #         f"文件 '{file_path.name}' 已存在，是否覆盖？",
        #         QMessageBox.Yes | QMessageBox.No,
        #         QMessageBox.No
        #     )
        #     if reply != QMessageBox.Yes:
        #         self.status_label.setText("保存已取消")
        #         return

        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"文件保存成功: {file_path}")
            self.status_label.setText(f"文件已保存: {file_path.name}")
            # 更新当前文件路径
            self.current_file_path = file_path
            QMessageBox.information(self, "保存成功", f"文件已保存到:\n{file_path}")

        except Exception as e:
            self.logger.error(f"保存文件失败: {e}")
            QMessageBox.critical(self, "错误", f"保存文件失败:\n{str(e)}")

    def _on_quick_save_clicked(self):
        """快速保存按钮点击事件（使用设置中的保存路径，不显示文件对话框）"""
        content = self.text_editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "警告", "编辑器内容为空")
            return

        # 获取默认保存路径
        default_path_str = self.settings.get("editor.save_path", "../Metadata Patches")
        default_path = Path(default_path_str)

        # 判断是否为绝对路径
        if not default_path.is_absolute():
            # 相对路径：相对于项目根目录
            base_dir = Path(__file__).parent.parent.parent
            default_path = (base_dir / default_path_str).resolve()

        # 确保目录存在
        try:
            default_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            QMessageBox.critical(self, "错误", f"无法创建保存目录:\n{str(e)}")
            return

        # 提取第一行作为文件名
        first_line = content.split('\n')[0].strip()
        if first_line.startswith("# "):
            filename_base = first_line[2:]  # 去掉 "# "
        else:
            filename_base = first_line  # 如果没有#，直接使用

        # 如果文件名基础为空，使用默认名称
        if not filename_base:
            filename_base = "untitled"

        # 替换非法字符
        import re
        # Windows文件名非法字符: \ / : * ? " < > |
        illegal_chars = r'[\\/*?:"<>|]'
        safe_filename = re.sub(illegal_chars, '_', filename_base)
        # 替换空格为下划线（可选）
        safe_filename = safe_filename.replace(' ', '_')
        # 限制文件名长度
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]

        # 添加.txt扩展名
        if not safe_filename.endswith('.txt'):
            safe_filename += '.txt'

        # 构建完整文件路径
        file_path = default_path / safe_filename

        # 检查文件是否存在，如果存在则询问是否覆盖
        if file_path.exists():
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件 '{file_path.name}' 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.status_label.setText("快速保存已取消")
                return

        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"文件快速保存成功: {file_path}")
            self.status_label.setText(f"文件已快速保存: {file_path.name}")
            # 更新当前文件路径
            self.current_file_path = file_path
            # 快速保存不显示成功对话框，只在状态栏显示

        except Exception as e:
            self.logger.error(f"快速保存文件失败: {e}")
            QMessageBox.critical(self, "错误", f"快速保存文件失败:\n{str(e)}")

    def _on_open_clicked(self):
        """打开文件按钮点击事件"""
        # 获取默认打开路径
        default_path_str = self.settings.get("editor.save_path", "../Metadata Patches")
        default_path = Path(default_path_str)

        # 判断是否为绝对路径
        if not default_path.is_absolute():
            # 相对路径：相对于项目根目录
            base_dir = Path(__file__).parent.parent.parent
            default_path = (base_dir / default_path_str).resolve()

        # 确保目录存在
        try:
            default_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            default_path = Path.home()  # 失败时使用用户主目录

        # 打开文件对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开文件",
            str(default_path),
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if not file_path:
            return  # 用户取消

        file_path = Path(file_path)

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 清除之前的搜索高亮
            self._clear_editor_search_highlights()
            # 重置编辑器当前字符格式
            self._reset_editor_char_format()
            # 设置编辑器内容
            self.text_editor.setPlainText(content)
            # 记录当前文件路径
            self.current_file_path = file_path
            self.logger.info(f"文件打开成功: {file_path}")
            self.status_label.setText(f"文件已打开: {file_path.name}")

        except Exception as e:
            self.logger.error(f"打开文件失败: {e}")
            QMessageBox.critical(self, "错误", f"打开文件失败:\n{str(e)}")

    def _on_delete_patch_clicked(self):
        """删除补丁按钮点击事件"""
        # 检查当前内容是否来自本地文件
        if self.current_file_path is None:
            QMessageBox.information(
                self,
                "无法删除",
                "当前内容非本地文件，无法删除。\n\n内容可能是从API生成或尚未保存到本地。"
            )
            return

        # 检查文件是否存在
        if not self.current_file_path.exists():
            QMessageBox.warning(
                self,
                "文件不存在",
                f"文件 '{self.current_file_path.name}' 不存在，可能已被删除或移动。"
            )
            # 清除无效的文件路径记录
            self.current_file_path = None
            return

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除文件 '{self.current_file_path.name}' 吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 执行删除
        try:
            file_path = self.current_file_path  # 保存引用
            file_path.unlink()  # 删除文件
            self.logger.info(f"文件已删除: {file_path}")
            self.status_label.setText(f"文件已删除: {file_path}")

            # 清除文件路径记录（文件已不存在）
            self.current_file_path = None

            # 可选：不清除编辑器内容，用户可以继续编辑并另存为新文件

        except Exception as e:
            self.logger.error(f"删除文件失败: {e}")
            QMessageBox.critical(
                self,
                "删除失败",
                f"删除文件失败:\n{str(e)}"
            )

    def _on_undo_clicked(self):
        """撤销按钮点击事件"""
        if self.text_editor.document().isUndoAvailable():
            self.text_editor.undo()
            self.status_label.setText("已执行撤销操作")
        else:
            self.status_label.setText("无可撤销的操作")

    def _on_redo_clicked(self):
        """重做按钮点击事件"""
        if self.text_editor.document().isRedoAvailable():
            self.text_editor.redo()
            self.status_label.setText("已执行重做操作")
        else:
            self.status_label.setText("无可重做的操作")

    def _on_clear_editor_clicked(self):
        """清空编辑器按钮点击事件"""
        # 检查编辑器是否有内容
        content = self.text_editor.toPlainText()
        if not content.strip():
            # 清除搜索高亮和重置格式
            self._clear_editor_search_highlights()
            self._reset_editor_char_format()
            self.text_editor.clear()
            # 清除文件路径记录
            self.current_file_path = None
            self.status_label.setText("编辑器已清空")
            return

        # 确认是否清空
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空编辑器内容吗？\n所有未保存的更改将会丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 清除搜索高亮和重置格式
            self._clear_editor_search_highlights()
            self._reset_editor_char_format()
            self.text_editor.clear()
            # 清除文件路径记录
            self.current_file_path = None
            self.status_label.setText("编辑器已清空")
        else:
            self.status_label.setText("清空操作已取消")

    def _perform_search(self, query: str):
        """执行搜索"""
        language_name = self.language_combo.currentText()
        self.status_label.setText(f"正在搜索({language_name}): {query}...")
        self.results_list.clear()

        # 获取搜索设置
        min_chars = self.settings.get("search.min_chars", 2)
        max_results = self.settings.get("search.max_results", 50)

        # 检查查询长度
        if len(query) < min_chars:
            self.status_label.setText(f"搜索词至少需要 {min_chars} 个字符")
            return

        try:
            # 执行实际搜索（使用当前语言）
            results = self.search_engine.search_by_language(
                query, self.current_language, limit=max_results
            )

            # 显示结果
            self._display_search_results(results, query)

            count = len(results)
            self.count_label.setText(f"项目: {count}")

            if count > 0:
                self.status_label.setText(f"搜索完成({language_name})，找到 {count} 个匹配结果")
            else:
                self.status_label.setText(f"未找到包含 '{query}' 的物品({language_name})")

        except Exception as e:
            self.logger.error(f"搜索执行失败: {e}")
            self.status_label.setText(f"搜索失败: {e}")
            self.results_list.addItem(f"搜索错误: {str(e)}")

    def _display_search_results(self, results: list, query: str = ""):
        """
        显示搜索结果

        Args:
            results: 搜索结果列表，每个元素为 (内部名称, 本地化名称)
            query: 搜索查询（用于调试）
        """
        if not results:
            self.results_list.addItem("未找到匹配的结果")
            return

        for internal_name, localized_name in results:
            # 创建显示文本，总是显示短内部名称（如果可用）
            # 提取内部名称的最后部分作为简化的标识
            parts = internal_name.split('/')
            if len(parts) > 2:
                short_internal = '/'.join(parts[-2:])
            else:
                short_internal = internal_name

            # 如果内部名称与本地化名称不同，则显示括号内的短内部名称
            if internal_name != localized_name:
                display_text = f"{localized_name} ({short_internal})"
            else:
                # 如果相同，只显示本地化名称（可能内部名称就是显示名称）
                display_text = localized_name

            # 创建列表项并存储内部名称数据
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, internal_name)
            self.results_list.addItem(item)

        self.logger.debug(f"显示 {len(results)} 个搜索结果，查询: '{query}'")

    def toggle_toolbar(self, visible: bool):
        """切换工具栏显示（已弃用，保留兼容性）"""
        pass

    def toggle_editor_menubar(self, visible: bool):
        """切换编辑器菜单栏显示"""
        if hasattr(self, 'editor_menubar') and self.editor_menubar:
            self.editor_menubar.setVisible(visible)

    def toggle_statusbar(self, visible: bool):
        """切换状态栏显示"""
        self.statusBar().setVisible(visible)

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>WarframePatchManager</h3>
        <p>版本: 0.1.0</p>
        <p>一个用于快速生成openWF游戏补丁的辅助工具。</p>
        <p>功能:</p>
        <ul>
          <li>多语言搜索游戏物品</li>
          <li>通过 API 获取metadata</li>
          <li>生成初始补丁文件</li>
          <li>视觉优化的编辑器窗口</li>
          <li>快速保存到补丁目录</li>
        </ul>
        <p>©2026 Brzjomo</p>
        """
        QMessageBox.about(self, "关于 WarframePatchManager", about_text)

    def show_settings(self):
        """显示设置对话框"""
        from src.gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_saved.connect(self.on_settings_saved)
        dialog.exec()

    def on_settings_saved(self):
        """设置保存后的处理"""
        # 重新加载设置以应用更改
        self.load_settings()

        # 更新API客户端的metadata_base_url
        self.update_api_client_metadata_url()

        self.logger.info("设置已更新并应用")

    def update_api_client_metadata_url(self):
        """更新API客户端的metadata_base_url"""
        from src.core.api_client import get_api_client

        try:
            metadata_url = self.settings.get("api.metadata_base_url", "http://localhost:6155")
            self.logger.info(f"元数据服务器URL已更新: {metadata_url}")

            # 更新API客户端的metadata_base_url
            client = get_api_client()
            client.set_metadata_base_url(metadata_url)

            self.logger.info("API客户端元数据URL已更新")

        except Exception as e:
            self.logger.error(f"更新API客户端metadata URL失败: {e}")

    # 编辑器文本搜索相关方法
    def _on_editor_search_text_changed(self, text: str):
        """编辑器搜索文本变化事件"""
        # 重置定时器
        self.editor_search_timer.stop()

        if len(text) >= 1:
            # 延迟搜索（避免频繁搜索）
            delay = 300  # 300毫秒
            self.editor_search_timer.start(delay)
        elif len(text) == 0:
            # 清空搜索框，清除高亮
            self._clear_editor_search_highlights()
            self.status_label.setText("编辑器搜索已清除")
        else:
            # 字符数不足，显示提示
            self.status_label.setText("请输入至少 1 个字符进行编辑器搜索")

    def _on_editor_search_timer_timeout(self):
        """编辑器搜索定时器超时"""
        search_text = self.editor_search_input.text().strip()
        if search_text:
            self._perform_editor_search(search_text)

    def _on_editor_search_clicked(self):
        """编辑器搜索按钮点击事件"""
        search_text = self.editor_search_input.text().strip()
        if search_text:
            self._perform_editor_search(search_text)

    def _on_editor_clear_clicked(self):
        """编辑器清除按钮点击事件"""
        self.editor_search_input.clear()
        self._clear_editor_search_highlights()
        self.status_label.setText("编辑器搜索已清除")

    def _perform_editor_search(self, query: str):
        """执行编辑器文本搜索"""
        if not query:
            return

        content = self.text_editor.toPlainText()
        if not content:
            self.status_label.setText("编辑器内容为空")
            return

        # 清除之前的高亮
        self._clear_editor_search_highlights()

        # 执行搜索（不区分大小写）
        cursor = self.text_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)

        found_count = 0
        format = self.text_editor.currentCharFormat()
        format.setBackground(Qt.cyan)        # 青色背景，在暗色和亮色模式下都醒目
        # 不设置前景色，保持原始文字颜色，确保在各种主题下都可读

        while True:
            # 搜索文本（不区分大小写）
            cursor = self.text_editor.document().find(query, cursor, QTextDocument.FindFlag())
            if cursor.isNull():
                break

            # 高亮匹配的文本
            cursor.mergeCharFormat(format)
            found_count += 1

            # 移动到匹配位置之后继续搜索
            cursor.setPosition(cursor.selectionEnd())

        if found_count > 0:
            self.status_label.setText(f"在编辑器中找到 {found_count} 个匹配项")
            # 滚动到第一个匹配项（不选中文本）
            cursor = self.text_editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor = self.text_editor.document().find(query, cursor, QTextDocument.FindFlag())
            if not cursor.isNull():
                # 清除选中状态，只移动光标到匹配位置
                cursor.clearSelection()
                self.text_editor.setTextCursor(cursor)
        else:
            self.status_label.setText(f"在编辑器中未找到 '{query}'")

    def _clear_editor_search_highlights(self):
        """清除编辑器搜索高亮"""
        cursor = self.text_editor.textCursor()
        # 选择整个文档
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        format = self.text_editor.currentCharFormat()
        format.setBackground(Qt.transparent)
        # 不修改前景色，保持原始文字颜色
        cursor.mergeCharFormat(format)
        cursor.clearSelection()

    def _reset_editor_char_format(self):
        """重置编辑器当前字符格式为默认值"""
        # 创建一个新的默认字符格式
        default_format = QTextCharFormat()
        # 设置编辑器当前字符格式为默认值
        cursor = self.text_editor.textCursor()
        cursor.setCharFormat(default_format)
        # 将默认格式设置为编辑器的当前字符格式
        self.text_editor.setCurrentCharFormat(default_format)

    # ===== 本地补丁管理方法 =====

    def refresh_local_patches_list(self):
        """刷新本地补丁列表"""
        # 获取补丁目录路径
        save_path_str = self.settings.get("editor.save_path", "../Metadata Patches")
        save_path = Path(save_path_str)

        # 判断是否为绝对路径
        if not save_path.is_absolute():
            # 相对路径：相对于项目根目录
            base_dir = Path(__file__).parent.parent.parent
            save_path = (base_dir / save_path_str).resolve()

        # 清空列表
        self.local_patches_list.clear()

        # 检查目录是否存在
        if not save_path.exists():
            self.logger.warning(f"补丁目录不存在: {save_path}")
            self.local_patches_list.addItem(f"目录不存在: {save_path}")
            return

        # 扫描txt和txt.bk文件
        txt_files = list(save_path.glob("*.txt"))
        bk_files = list(save_path.glob("*.txt.bk"))

        all_files = []
        for file in txt_files:
            all_files.append((file, True))  # True表示激活状态
        for file in bk_files:
            all_files.append((file, False))  # False表示未激活状态

        # 按文件名排序
        all_files.sort(key=lambda x: x[0].name.lower())

        # 添加到列表
        for file, is_active in all_files:
            if is_active:
                display_name = file.name
                icon_text = "[激活] "
            else:
                display_name = file.name
                icon_text = "[未激活] "

            item_text = f"{icon_text}{display_name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, file)  # 存储完整路径
            item.setData(Qt.UserRole + 1, is_active)  # 存储激活状态
            self.local_patches_list.addItem(item)

        self.logger.info(f"本地补丁列表已刷新，找到 {len(all_files)} 个文件")
        self.status_label.setText(f"本地补丁列表已刷新 ({len(all_files)} 个文件)")

    def _on_local_patch_selected(self):
        """本地补丁列表项选择事件"""
        selected_items = self.local_patches_list.selectedItems()
        if not selected_items:
            return

        selected_item = selected_items[0]
        file_path = selected_item.data(Qt.UserRole)
        is_active = selected_item.data(Qt.UserRole + 1)

        if file_path and file_path.exists():
            # 加载文件内容到编辑器
            self._load_patch_file(file_path)

            # 更新状态显示
            status_text = f"已选择补丁文件: {file_path.name}"
            if not is_active:
                status_text += " (未激活)"
            self.status_label.setText(status_text)
        else:
            self.status_label.setText("选择的文件不存在")

    def _load_patch_file(self, file_path: Path):
        """加载补丁文件到编辑器"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 清除之前的搜索高亮
            self._clear_editor_search_highlights()
            # 重置编辑器当前字符格式
            self._reset_editor_char_format()
            # 设置编辑器内容
            self.text_editor.setPlainText(content)
            # 记录当前文件路径
            self.current_file_path = file_path
            self.logger.info(f"补丁文件已加载: {file_path}")

        except Exception as e:
            self.logger.error(f"加载补丁文件失败: {e}")
            QMessageBox.critical(self, "错误", f"加载补丁文件失败:\n{str(e)}")

    def _on_refresh_patches_clicked(self):
        """刷新列表按钮点击事件"""
        self.refresh_local_patches_list()

    def _on_enable_patch_clicked(self):
        """启用补丁按钮点击事件"""
        selected_items = self.local_patches_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个补丁文件")
            return

        selected_item = selected_items[0]
        file_path = selected_item.data(Qt.UserRole)
        is_active = selected_item.data(Qt.UserRole + 1)

        if not file_path or not file_path.exists():
            QMessageBox.warning(self, "警告", "选择的文件不存在")
            return

        # 如果已经是激活状态（txt文件），则无需操作
        if is_active:
            QMessageBox.information(self, "信息", "补丁已处于激活状态")
            return

        # 检查是否为txt.bk文件
        if not file_path.name.endswith('.txt.bk'):
            QMessageBox.warning(self, "警告", "只有未激活的补丁文件(.txt.bk)才能被激活")
            return

        # 确认操作
        reply = QMessageBox.question(
            self,
            "确认启用",
            f"确定要启用补丁 '{file_path.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 重命名文件：去掉.bk扩展名
        new_path = file_path.with_suffix('')  # 移除.bk

        # 检查目标文件是否已存在
        if new_path.exists():
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件 '{new_path.name}' 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        try:
            file_path.rename(new_path)
            self.logger.info(f"补丁已启用: {file_path.name} -> {new_path.name}")
            self.status_label.setText(f"补丁已启用: {file_path.name}")

            # 如果当前编辑器打开的是这个文件，更新current_file_path
            if self.current_file_path == file_path:
                self.current_file_path = new_path

            # 刷新列表
            self.refresh_local_patches_list()

        except Exception as e:
            self.logger.error(f"启用补丁失败: {e}")
            QMessageBox.critical(self, "错误", f"启用补丁失败:\n{str(e)}")

    def _on_disable_patch_clicked(self):
        """禁用补丁按钮点击事件"""
        selected_items = self.local_patches_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个补丁文件")
            return

        selected_item = selected_items[0]
        file_path = selected_item.data(Qt.UserRole)
        is_active = selected_item.data(Qt.UserRole + 1)

        if not file_path or not file_path.exists():
            QMessageBox.warning(self, "警告", "选择的文件不存在")
            return

        # 如果已经是未激活状态（txt.bk文件），则无需操作
        if not is_active:
            QMessageBox.information(self, "信息", "补丁已处于未激活状态")
            return

        # 检查是否为txt文件
        if not file_path.name.endswith('.txt'):
            QMessageBox.warning(self, "警告", "只有激活的补丁文件(.txt)才能被禁用")
            return

        # 确认操作
        reply = QMessageBox.question(
            self,
            "确认禁用",
            f"确定要禁用补丁 '{file_path.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 重命名文件：添加.bk扩展名
        new_path = file_path.with_suffix('.txt.bk')

        # 检查目标文件是否已存在
        if new_path.exists():
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件 '{new_path.name}' 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        try:
            file_path.rename(new_path)
            self.logger.info(f"补丁已禁用: {file_path.name} -> {new_path.name}")
            self.status_label.setText(f"补丁已禁用: {file_path.name}")

            # 如果当前编辑器打开的是这个文件，更新current_file_path
            if self.current_file_path == file_path:
                self.current_file_path = new_path

            # 刷新列表
            self.refresh_local_patches_list()

        except Exception as e:
            self.logger.error(f"禁用补丁失败: {e}")
            QMessageBox.critical(self, "错误", f"禁用补丁失败:\n{str(e)}")

    def _on_delete_patch_clicked(self):
        """删除补丁按钮点击事件（已移动到本地补丁管理区域）"""
        # 检查当前是否有选中的本地补丁
        selected_items = self.local_patches_list.selectedItems()
        if selected_items:
            # 如果本地补丁列表有选中项，删除选中的补丁文件
            selected_item = selected_items[0]
            file_path = selected_item.data(Qt.UserRole)

            if not file_path or not file_path.exists():
                QMessageBox.warning(self, "警告", "选择的文件不存在")
                return

            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除补丁文件 '{file_path.name}' 吗？\n\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            # 执行删除
            try:
                file_path.unlink()
                self.logger.info(f"补丁文件已删除: {file_path}")
                self.status_label.setText(f"补丁文件已删除: {file_path.name}")

                # 刷新列表
                self.refresh_local_patches_list()

                # 如果删除的文件是当前编辑器打开的文件，清除当前文件路径
                if self.current_file_path == file_path:
                    self.current_file_path = None

            except Exception as e:
                self.logger.error(f"删除补丁文件失败: {e}")
                QMessageBox.critical(
                    self,
                    "删除失败",
                    f"删除补丁文件失败:\n{str(e)}"
                )
        else:
            # 如果没有在本地补丁列表中选择，则使用原来的逻辑（删除当前编辑器中的文件）
            # 检查当前内容是否来自本地文件
            if self.current_file_path is None:
                QMessageBox.information(
                    self,
                    "无法删除",
                    "当前内容非本地文件，无法删除。\n\n内容可能是从API生成或尚未保存到本地。"
                )
                return

            # 检查文件是否存在
            if not self.current_file_path.exists():
                QMessageBox.warning(
                    self,
                    "文件不存在",
                    f"文件 '{self.current_file_path.name}' 不存在，可能已被删除或移动。"
                )
                # 清除无效的文件路径记录
                self.current_file_path = None
                return

            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除文件 '{self.current_file_path.name}' 吗？\n\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            # 执行删除
            try:
                file_path = self.current_file_path  # 保存引用
                file_path.unlink()  # 删除文件
                self.logger.info(f"文件已删除: {file_path}")
                self.status_label.setText(f"文件已删除: {file_path}")

                # 清除文件路径记录（文件已不存在）
                self.current_file_path = None

                # 可选：不清除编辑器内容，用户可以继续编辑并另存为新文件

            except Exception as e:
                self.logger.error(f"删除文件失败: {e}")
                QMessageBox.critical(
                    self,
                    "删除失败",
                    f"删除文件失败:\n{str(e)}"
                )


if __name__ == "__main__":
    # 测试窗口
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())