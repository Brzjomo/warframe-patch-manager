# WarframePatchManager

一个基于Python + PySide6的Warframe游戏补丁管理工具，支持多语言物品搜索、元数据编辑和补丁文件管理。

## 主要功能

### 🎯 多语言物品搜索
- 支持15种语言搜索（中文、英文、德语、法语、日语等）
- 实时搜索，输入关键字时即时显示匹配结果
- 搜索结果包含物品内部名称和本地化名称

### 📝 智能编辑器
- Warframe元数据语法高亮
- 编辑器内文本搜索和匹配高亮
- 支持打开、保存、快速保存文件操作
- 撤销/重做功能

### 📁 本地补丁管理
- 补丁文件列表显示（激活/未激活状态）
- 一键启用/禁用补丁（`.txt` ↔ `.txt.bk`）
- 批量刷新和管理补丁文件
- 补丁文件删除功能

### ⚙️ 配置管理
- 可视化设置对话框
- 支持API服务器地址配置
- 可自定义搜索参数和编辑器设置
- 窗口大小和位置记忆

### 🔌 API集成
- 通过OpenWF元数据服务器获取物品元数据
- 可配置服务器地址（默认：http://localhost:6155）
- 超时和重试机制

## 🚀 快速开始（最终用户）

### 对于最终用户
1. **下载exe文件**：获取最新版本的 `WarframePatchManager.exe`
2. **放置文件**：将exe文件放在`OpenWF`目录下的`WarframePatchManager`目录中，或者任意目录（后续需要修改配置）
3. **首次运行**：双击exe，同目录会生成 `config.json` 配置文件
4. **使用工具**：
   - 在搜索框输入物品名称（支持多语言）
   - 选择搜索结果查看物品元数据
   - 编辑后保存为补丁文件
   - 在左侧面板管理本地补丁文件

### 补丁文件位置
- 默认保存在exe上级目录的 `Metadata Patches/` 文件夹
- 激活文件：`.txt` 扩展名
- 未激活文件：`.txt.bk` 扩展名
- 可通过设置修改保存路径

## 开发环境设置

### 系统要求
- **操作系统**：Windows 10/11, macOS, Linux
- **Python版本**：3.10 或更高版本
- **内存**：至少4GB RAM
- **磁盘空间**：至少1GB可用空间

### 环境配置步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/Brzjomo/warframe-patch-manager.git
   cd warframe-patch-manager
   ```

2. **创建虚拟环境**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **安装Node.js依赖（用于多语言数据）**
   ```bash
   npm install
   ```

5. **配置数据文件**
   - 确保 `data/InternalName.csv` 存在
   - 确保 `node_modules/@wfcd/items/data/json/i18n.json` 存在

### 运行开发版本
```bash
python src/main.py
```

## 项目结构

```
WarframePatchManager/
├── data/                    # 数据文件
│   └── InternalName.csv    # 物品名称映射表
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── config/            # 配置管理
│   │   └── settings.py    # 设置管理类
│   ├── core/              # 核心功能
│   │   ├── api_client.py         # API客户端
│   │   ├── search_engine.py      # 搜索引擎
│   │   └── wf_items_loader.py    # 多语言数据加载器
│   ├── gui/               # 图形界面
│   │   ├── main_window.py        # 主窗口
│   │   ├── settings_dialog.py    # 设置对话框
│   │   └── syntax_highlighter.py # 语法高亮器
│   └── utils/             # 工具函数
│       ├── file_utils.py         # 文件工具
│       └── path_utils.py         # 路径处理工具
├── build.py           # 打包脚本
├── requirements.txt       # Python依赖
├── package.json          # Node.js依赖
├── config.json           # 应用程序配置（运行时生成）
├── logs/                 # 日志目录（运行时生成）
├── dist/                 # 打包输出目录
├── build/                # PyInstaller构建临时文件
├── docs/                 # 文档
└── node_modules/         # Node.js依赖
```

## 打包流程

### 环境准备
确保已安装所有依赖
### 使用打包脚本（推荐）
```bash
python build.py
```
打包脚本会自动：
1. 检查PyInstaller是否安装
2. 收集所有数据文件
3. 构建PyInstaller命令
4. 生成单个可执行文件（约80MB）

### 手动打包
```bash
pyinstaller --onefile --windowed --name=WarframePatchManager \
  --add-data "data/InternalName.csv:data" \
  --add-data "node_modules/@wfcd/items/data/json/i18n.json:node_modules/@wfcd/items/data/json" \
  --hidden-import PySide6 --hidden-import PySide6.QtCore \
  --hidden-import PySide6.QtWidgets --hidden-import PySide6.QtGui \
  --hidden-import pandas --hidden-import pandas._libs.tslibs.timedeltas \
  --hidden-import pandas._libs.tslibs.np_datetime --hidden-import pandas._libs.tslibs.base \
  --hidden-import pandas._libs.skiplist --hidden-import python_dotenv \
  --exclude-module matplotlib --exclude-module scipy --exclude-module tkinter \
  src/main.py
```

### 打包输出
- **可执行文件**：`dist/WarframePatchManager.exe`（约80MB）
- **包含内容**：
  - 所有Python源代码编译为字节码
  - 数据文件：`InternalName.csv`
  - 多语言数据：`i18n.json`
  - Python运行时和依赖库

## 部署和使用

### 系统要求
- **Windows 10/11** 64位
- **Microsoft Visual C++ Redistributable**（如未安装可从微软官网下载）
- 至少100MB可用磁盘空间

### 快速开始
1. 将 `WarframePatchManager.exe` 复制到目标计算机的任意目录
2. 双击运行
3. 首次运行会自动在同目录生成 `config.json` 配置文件
4. 开始使用

### 配置文件
配置文件 `config.json` 在exe同目录生成，包含以下设置：

```json
{
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
    "auto_save": false,
    "save_path": "../Metadata Patches"
  },
  "window": {
    "width": 1500,
    "height": 800,
    "maximized": false,
    "pos_x": null,
    "pos_y": null
  },
  "recent_files": [],
  "user": {
    "language": "auto"
  }
}
```

### 重要路径说明

| 路径类型 | 默认位置 | 说明 |
|---------|---------|------|
| 配置文件 | exe同目录的 `config.json` | 应用程序设置，可编辑 |
| 日志文件 | exe同目录的 `logs/` | 运行日志，用于故障排除 |
| 补丁文件 | exe上级目录的 `Metadata Patches/` | 保存的补丁文件，可通过设置修改 |
| 临时文件 | 系统临时目录 | PyInstaller运行时解压的文件 |

### 补丁文件管理
- **默认保存路径**：`../Metadata Patches`（相对于exe位置）
- **激活状态**：`.txt` 为激活，`.txt.bk` 为未激活
- **状态切换**：通过"启用补丁"/"禁用补丁"按钮切换
- **文件操作**：支持打开、保存、删除补丁文件

## 故障排除

### 常见问题

#### 1. 无法启动exe文件
- **症状**：双击exe无反应或立即关闭
- **解决**：
  - 确保已安装 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
  - 尝试以管理员身份运行
  - 检查系统事件查看器中的错误信息

#### 2. 设置无法保存
- **症状**：修改设置后重启恢复默认值
- **解决**：
  - 确保exe所在目录有写入权限
  - 不要将exe放在系统保护目录（如Program Files）
  - 检查 `config.json` 文件是否可写

#### 3. 补丁目录找不到
- **症状**：显示"目录不存在"错误
- **解决**：
  - 确保exe上级目录存在 `Metadata Patches` 文件夹
  - 或在设置中修改 `editor.save_path` 为绝对路径
  - 手动创建所需的目录

#### 4. API连接失败
- **症状**：无法获取物品元数据
- **解决**：
  - 确保OpenWF元数据服务器运行在 http://localhost:6155
  - 在设置中检查API服务器地址
  - 检查网络连接和防火墙设置

#### 5. 多语言搜索不工作
- **症状**：只能搜索英文名称
- **解决**：
  - 确保 `i18n.json` 文件正确打包
  - 检查 `node_modules/@wfcd/items/` 目录是否存在
  - 重新打包应用程序

### 日志文件
程序运行日志保存在 `logs/warframe_patch_manager.log`，包含：
- 应用程序启动和关闭时间
- 配置加载和保存状态
- API调用记录
- 错误和异常信息

## 开发指南

### 代码结构
- **MVC模式**：界面、业务逻辑、数据分离
- **模块化设计**：功能模块独立，便于维护和扩展
- **配置驱动**：通过配置文件控制应用程序行为

### 编码规范
- 遵循 **PEP 8** Python编码规范
- 使用类型注解提高代码可读性
- 添加适当的文档字符串
- 关键函数添加日志记录

## 许可证

本项目基于开源许可证发布，具体许可证信息请查看LICENSE文件。

## 贡献指南

欢迎提交问题报告、功能请求或代码贡献！

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 相关链接

- [OpenWF项目](https://openwf.io/) - 社区Warframe项目
- [Warframe Items库](https://github.com/WFCD/warframe-items) - 多语言物品数据

---

**免责声明**：此工具为Warframe游戏辅助工具，仅供学习和研究使用。请遵守游戏使用条款和相关法律法规。

**技术支持**：如有问题，请查看日志文件或提交GitHub Issue。