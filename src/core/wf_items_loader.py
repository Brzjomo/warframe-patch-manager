"""
Warframe Items 数据加载器
负责加载 Warframe Items 库的多语言数据
"""

import csv
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

logger = logging.getLogger(__name__)


class WFItemsLoader:
    """Warframe Items 数据加载器"""

    def __init__(self, csv_file: Optional[str] = None, i18n_file: Optional[str] = None):
        """
        初始化数据加载器

        Args:
            csv_file: CSV 数据文件路径，包含内部名称和英文名称
            i18n_file: i18n.json 文件路径，包含多语言翻译
        """
        if csv_file is None:
            # 查找CSV数据文件
            csv_file = self._find_file("data/InternalName.csv")

        if i18n_file is None:
            # 查找i18n.json文件
            i18n_file = self._find_file("node_modules/@wfcd/items/data/json/i18n.json")

        self.csv_file = Path(csv_file)
        self.i18n_file = Path(i18n_file)

        # 数据存储
        self.english_names: Dict[str, str] = {}  # internal_name -> english_name
        self.i18n_data: Dict[str, Dict[str, Dict[str, str]]] = {}  # internal_name -> {lang: {field: translation}}
        self.loaded = False

        logger.info(f"WFItemsLoader 初始化完成")
        logger.info(f"CSV 文件: {self.csv_file}")
        logger.info(f"i18n 文件: {self.i18n_file}")

    def _find_file(self, relative_path: str) -> str:
        """查找文件路径，处理PyInstaller打包环境"""
        # 检查是否在PyInstaller打包环境中运行
        if getattr(sys, 'frozen', False):
            # PyInstaller打包环境，数据文件在临时目录
            # sys._MEIPASS 是临时解压目录（仅PyInstaller）
            if hasattr(sys, '_MEIPASS'):
                base_dir = Path(sys._MEIPASS)
            else:
                # 某些PyInstaller版本可能没有_MEIPASS
                base_dir = Path(sys.executable).parent
        else:
            # 开发环境：使用项目根目录
            base_dir = Path(__file__).parent.parent.parent

        file_path = base_dir / relative_path

        # 如果文件不存在，尝试其他位置
        if not file_path.exists():
            # 尝试当前工作目录
            alt_path = Path.cwd() / relative_path
            if alt_path.exists():
                return str(alt_path)

            # 尝试exe所在目录（针对打包环境）
            if getattr(sys, 'frozen', False):
                exe_dir = Path(sys.executable).parent
                exe_path = exe_dir / relative_path
                if exe_path.exists():
                    return str(exe_path)

            # 对于i18n.json，尝试在打包的数据目录中查找
            if "i18n.json" in relative_path:
                # 在PyInstaller中，i18n.json可能在node_modules子目录中
                # 或者直接在data目录中
                if hasattr(sys, '_MEIPASS'):
                    # 尝试不同的可能位置
                    possible_paths = [
                        base_dir / "i18n.json",
                        base_dir / "data" / "i18n.json",
                    ]
                    for possible_path in possible_paths:
                        if possible_path.exists():
                            return str(possible_path)

        return str(file_path)

    def load_data(self) -> bool:
        """
        加载所有数据

        Returns:
            是否成功加载
        """
        if self.loaded:
            return True

        try:
            # 加载 CSV 数据
            if not self._load_csv():
                return False

            # 加载 i18n 数据
            if not self._load_i18n():
                return False

            self.loaded = True
            logger.info(f"数据加载完成: {len(self.english_names)} 个物品")
            return True

        except Exception as e:
            logger.error(f"加载数据失败: {e}", exc_info=True)
            return False

    def _load_csv(self) -> bool:
        """加载 CSV 文件"""
        if not self.csv_file.exists():
            logger.error(f"CSV 文件不存在: {self.csv_file}")
            return False

        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)

                # 跳过标题行
                try:
                    header = next(reader)
                    if len(header) < 2:
                        logger.warning("CSV 文件格式可能不正确")
                except StopIteration:
                    logger.error("CSV 文件为空")
                    return False

                # 读取数据行
                row_count = 0
                for row in reader:
                    if len(row) >= 2:
                        internal_name = row[0].strip()
                        english_name = row[1].strip()

                        if internal_name and english_name:
                            self.english_names[internal_name] = english_name
                            row_count += 1
                    else:
                        logger.warning(f"跳过格式不正确的行: {row}")

            logger.info(f"从 CSV 加载了 {row_count} 个英文名称")
            return True

        except Exception as e:
            logger.error(f"加载 CSV 文件失败: {e}", exc_info=True)
            return False

    def _load_i18n(self) -> bool:
        """加载 i18n.json 文件"""
        if not self.i18n_file.exists():
            logger.error(f"i18n 文件不存在: {self.i18n_file}")
            return False

        try:
            logger.info(f"开始加载 i18n 文件 (可能较大)...")
            with open(self.i18n_file, 'r', encoding='utf-8') as f:
                self.i18n_data = json.load(f)

            logger.info(f"从 i18n 加载了 {len(self.i18n_data)} 个物品的多语言数据")
            return True

        except Exception as e:
            logger.error(f"加载 i18n 文件失败: {e}", exc_info=True)
            return False

    def get_item_name(self, internal_name: str, language: str = "en") -> str:
        """
        获取指定语言的物品名称

        Args:
            internal_name: 内部名称
            language: 语言代码 (如 'en', 'zh', 'de')

        Returns:
            指定语言的物品名称，如果未找到返回空字符串
        """
        if not self.loaded:
            if not self.load_data():
                return ""

        # 英文名称从 CSV 获取
        if language == "en":
            return self.english_names.get(internal_name, "")

        # 其他语言从 i18n 数据获取
        if internal_name in self.i18n_data:
            lang_data = self.i18n_data[internal_name].get(language)
            if lang_data and "name" in lang_data:
                return lang_data["name"]

        # 如果未找到翻译，返回英文名称
        return self.english_names.get(internal_name, "")

    def get_item_names(self, internal_name: str) -> Dict[str, str]:
        """
        获取物品的所有语言名称

        Args:
            internal_name: 内部名称

        Returns:
            语言代码到名称的映射
        """
        if not self.loaded:
            if not self.load_data():
                return {}

        result = {}

        # 添加英文名称
        if internal_name in self.english_names:
            result["en"] = self.english_names[internal_name]

        # 添加其他语言名称
        if internal_name in self.i18n_data:
            for lang, lang_data in self.i18n_data[internal_name].items():
                if "name" in lang_data:
                    result[lang] = lang_data["name"]

        return result

    def search_by_language(self, query: str, language: str = "en", limit: int = 50) -> List[Tuple[str, str]]:
        """
        按语言搜索物品

        Args:
            query: 搜索查询
            language: 语言代码
            limit: 返回结果数量限制

        Returns:
            匹配的物品列表，每个元素为 (内部名称, 本地化名称)
        """
        if not self.loaded:
            if not self.load_data():
                return []

        if not query or len(query) < 2:
            return []

        query_lower = query.lower()
        results = []

        # 检查查询是否只包含ASCII字符（可能是英文查询）
        # 如果查询包含非ASCII字符（如中文），则用户可能在搜索目标语言
        # 如果查询只包含ASCII字符，用户可能想搜索英文名称，即使搜索语言不是英文
        is_ascii_query = all(ord(c) < 128 for c in query)

        # 根据语言选择搜索策略
        if language == "en":
            # 在英文名称中搜索
            for internal_name, english_name in self.english_names.items():
                if query_lower in english_name.lower():
                    results.append((internal_name, english_name))
                    if len(results) >= limit:
                        break
        else:
            # 对于非英文语言，需要同时搜索目标语言和英文
            target_language_results = []
            english_results = []

            # 收集目标语言的结果
            for internal_name, lang_data_dict in self.i18n_data.items():
                if language in lang_data_dict:
                    lang_data = lang_data_dict[language]
                    if "name" in lang_data and query_lower in lang_data["name"].lower():
                        display_name = lang_data["name"]
                        target_language_results.append((internal_name, display_name))

            # 收集英文结果（包括没有目标语言翻译的物品）
            for internal_name, english_name in self.english_names.items():
                # 检查是否已经在目标语言结果中
                if any(internal_name == r[0] for r in target_language_results):
                    continue

                if query_lower in english_name.lower():
                    english_results.append((internal_name, english_name))

            # 合并结果的策略：
            # 1. 如果查询是纯ASCII（可能是英文），优先显示英文结果
            # 2. 否则，优先显示目标语言结果
            if is_ascii_query:
                # 对于英文查询，优先显示英文结果
                # 首先添加英文结果（包括没有翻译的物品）
                results = english_results[:limit]

                # 如果还有空间，添加目标语言结果
                if len(results) < limit:
                    remaining_slots = limit - len(results)
                    # 确保不重复
                    for internal_name, display_name in target_language_results:
                        if any(internal_name == r[0] for r in results):
                            continue
                        results.append((internal_name, display_name))
                        if len(results) >= limit:
                            break
            else:
                # 对于非ASCII查询（如中文），优先显示目标语言结果
                results = target_language_results[:limit]

                # 如果还有空间，添加英文结果
                if len(results) < limit:
                    remaining_slots = limit - len(results)
                    results.extend(english_results[:remaining_slots])

        logger.debug(f"按语言 '{language}' 搜索 '{query}' 找到 {len(results)} 个结果 (ASCII查询: {is_ascii_query})")
        return results

    def search_all_languages(self, query: str, limit: int = 50) -> List[Tuple[str, str, str]]:
        """
        在所有语言中搜索物品

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            匹配的物品列表，每个元素为 (内部名称, 显示名称, 语言)
        """
        if not self.loaded:
            if not self.load_data():
                return []

        if not query or len(query) < 2:
            return []

        query_lower = query.lower()
        results = []

        # 首先在英文名称中搜索
        for internal_name, english_name in self.english_names.items():
            if query_lower in english_name.lower():
                results.append((internal_name, english_name, "en"))
                if len(results) >= limit:
                    return results

        # 然后在其他语言名称中搜索
        for internal_name, lang_data_dict in self.i18n_data.items():
            for lang, lang_data in lang_data_dict.items():
                if "name" in lang_data and query_lower in lang_data["name"].lower():
                    # 检查是否已添加（可能已在英文结果中）
                    if not any(r[0] == internal_name for r in results):
                        display_name = lang_data["name"]
                        results.append((internal_name, display_name, lang))
                        if len(results) >= limit:
                            return results

        logger.debug(f"全语言搜索 '{query}' 找到 {len(results)} 个结果")
        return results

    def get_supported_languages(self) -> Set[str]:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码集合
        """
        if not self.loaded:
            if not self.load_data():
                logger.warning("数据加载失败，仅支持英文")
                return {"en"}  # 至少支持英文

        languages = {"en"}  # 英文总是支持

        # 从 i18n 数据收集所有语言
        for lang_data_dict in self.i18n_data.values():
            languages.update(lang_data_dict.keys())

        logger.debug(f"收集到的支持语言: {sorted(languages)}")
        logger.debug(f"支持语言数量: {len(languages)}")

        # 检查是否包含中文
        if "zh" in languages:
            logger.debug("语言列表中包含中文 (zh)")
        else:
            logger.warning("语言列表中不包含中文 (zh)")

        if "de" in languages:
            logger.debug("语言列表中包含德语 (de)")

        return languages

    def get_item_count(self) -> int:
        """
        获取物品数量

        Returns:
            CSV文件和i18n文件中去重后的物品总数
        """
        if not self.loaded:
            if not self.load_data():
                return 0

        # 获取所有不重复的内部名称（合并CSV和i18n数据）
        all_items = set(self.english_names.keys())
        all_items.update(self.i18n_data.keys())
        return len(all_items)


# 全局数据加载器实例
_wf_items_loader_instance: Optional[WFItemsLoader] = None


def get_wf_items_loader() -> WFItemsLoader:
    """获取全局 Warframe Items 数据加载器实例"""
    global _wf_items_loader_instance
    if _wf_items_loader_instance is None:
        _wf_items_loader_instance = WFItemsLoader()
    return _wf_items_loader_instance


if __name__ == "__main__":
    # 测试数据加载器
    import sys

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    loader = WFItemsLoader()

    if not loader.load_data():
        print("数据加载失败")
        sys.exit(1)

    print(f"加载了 {loader.get_item_count()} 个物品")
    print(f"支持的语言: {sorted(loader.get_supported_languages())}")
    print()

    # 测试搜索
    test_queries = ["Lavos", "测试", "Prime", "Nova"]

    for query in test_queries:
        print(f"搜索 '{query}':")

        # 英文搜索
        en_results = loader.search_by_language(query, "en", limit=3)
        print(f"  英文结果 ({len(en_results)}):")
        for internal_name, name in en_results[:3]:
            print(f"    {name}")

        # 中文搜索
        zh_results = loader.search_by_language(query, "zh", limit=3)
        print(f"  中文结果 ({len(zh_results)}):")
        for internal_name, name in zh_results[:3]:
            print(f"    {name}")

        print()

    # 测试获取物品名称
    test_internal_name = "/Lotus/Powersuits/Alchemist/Alchemist"
    print(f"物品 '{test_internal_name}' 的名称:")

    names = loader.get_item_names(test_internal_name)
    for lang, name in sorted(names.items()):
        print(f"  {lang}: {name}")

    # 测试全语言搜索
    print(f"\n全语言搜索 'Lavos':")
    all_results = loader.search_all_languages("Lavos", limit=5)
    for internal_name, name, lang in all_results:
        print(f"  {name} ({lang})")