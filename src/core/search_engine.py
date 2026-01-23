"""
搜索引擎模块
处理物品搜索逻辑
"""

import csv
import logging
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Set

from .wf_items_loader import get_wf_items_loader

logger = logging.getLogger(__name__)


class SearchEngine:
    """搜索引擎"""

    def __init__(self, data_file: Optional[str] = None):
        """
        初始化搜索引擎

        Args:
            data_file: CSV 数据文件路径，如果为 None 则使用默认路径
        """
        if data_file is None:
            # 查找数据文件
            data_file = self._find_data_file("data/InternalName.csv")

        self.data_file = Path(data_file)
        self.items: List[Tuple[str, str]] = []

        # 加载数据
        self.load_items()

        # 初始化 Warframe Items 数据加载器（懒加载）
        self.wf_items_loader = None

        logger.info(f"搜索引擎初始化完成，加载了 {len(self.items)} 个物品")

    def _find_data_file(self, relative_path: str) -> str:
        """查找数据文件路径，处理PyInstaller打包环境"""
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

        return str(file_path)

    def load_items(self) -> bool:
        """
        从 CSV 文件加载物品数据

        Returns:
            是否成功加载
        """
        self.items.clear()

        if not self.data_file.exists():
            logger.error(f"数据文件不存在: {self.data_file}")
            return False

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)

                # 跳过标题行（如果存在）
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
                        localized_name = row[1].strip()

                        if internal_name and localized_name:
                            self.items.append((internal_name, localized_name))
                            row_count += 1
                    else:
                        logger.warning(f"跳过格式不正确的行: {row}")

            logger.info(f"从 {self.data_file} 加载了 {row_count} 个物品")
            return True

        except Exception as e:
            logger.error(f"加载数据文件失败: {e}", exc_info=True)
            return False

    def _get_wf_items_loader(self):
        """获取 Warframe Items 数据加载器（懒加载）"""
        if self.wf_items_loader is None:
            self.wf_items_loader = get_wf_items_loader()
            # 尝试加载数据，但忽略失败（允许降级到基础搜索）
            try:
                self.wf_items_loader.load_data()
            except Exception as e:
                logger.warning(f"Warframe Items 数据加载失败，将使用基础搜索: {e}")
                self.wf_items_loader = None
        return self.wf_items_loader

    def search(self, query: str, limit: int = 50) -> List[Tuple[str, str]]:
        """
        搜索物品

        Args:
            query: 搜索查询（支持中文或英文）
            limit: 返回结果数量限制

        Returns:
            匹配的物品列表，每个元素为 (内部名称, 本地化名称)
        """
        if not query or len(query) < 2:
            return []

        query_lower = query.lower()
        results = []

        for internal_name, localized_name in self.items:
            # 在内部名称和本地化名称中搜索
            if (query_lower in internal_name.lower() or
                query_lower in localized_name.lower()):

                results.append((internal_name, localized_name))

                if len(results) >= limit:
                    break

        logger.debug(f"搜索 '{query}' 找到 {len(results)} 个结果")
        return results

    def search_by_language(self, query: str, language: str = "en", limit: int = 50) -> List[Tuple[str, str]]:
        """
        按语言搜索物品

        Args:
            query: 搜索查询
            language: 语言代码（如 'zh', 'en'）
            limit: 返回结果数量限制

        Returns:
            匹配的物品列表，每个元素为 (内部名称, 本地化名称)
        """
        if not query or len(query) < 2:
            return []

        # 尝试使用 Warframe Items 数据加载器
        loader = self._get_wf_items_loader()
        if loader is not None:
            try:
                results = loader.search_by_language(query, language, limit)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"多语言搜索失败，降级到基础搜索: {e}")

        # 降级方案：如果多语言搜索没有结果或失败，使用基础搜索
        # 这样即使物品没有目标语言的翻译，也能通过英文名称被搜索到
        return self.search(query, limit)

    def get_supported_languages(self) -> Set[str]:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码集合
        """
        loader = self._get_wf_items_loader()
        if loader is not None:
            try:
                languages = loader.get_supported_languages()
                logger.debug(f"从WFItemsLoader获取支持语言: {sorted(languages)}")
                return languages
            except Exception as e:
                logger.warning(f"获取支持的语言失败: {e}")

        # 默认至少支持英文
        logger.debug("WFItemsLoader不可用或失败，仅支持英文")
        return {"en"}

    def get_by_internal_name(self, internal_name: str) -> str:
        """
        根据内部名称获取本地化名称

        Args:
            internal_name: 内部名称

        Returns:
            本地化名称，如果未找到返回空字符串
        """
        for int_name, loc_name in self.items:
            if int_name == internal_name:
                return loc_name
        return ""

    def get_by_localized_name(self, localized_name: str) -> str:
        """
        根据本地化名称获取内部名称

        Args:
            localized_name: 本地化名称

        Returns:
            内部名称，如果未找到返回空字符串
        """
        for int_name, loc_name in self.items:
            if loc_name == localized_name:
                return int_name
        return ""

    def get_all_items(self) -> List[Tuple[str, str]]:
        """
        获取所有物品

        Returns:
            所有物品列表
        """
        return self.items.copy()

    def get_item_count(self) -> int:
        """
        获取物品数量

        Returns:
            CSV文件和i18n文件中去重后的物品总数
        """
        # 获取CSV物品数
        csv_count = len(self.items)

        # 尝试获取wf_items_loader的合并计数（包括i18n）
        try:
            loader = self._get_wf_items_loader()
            if loader is not None:
                # 使用loader的get_item_count()，它返回CSV和i18n的去重总数
                return loader.get_item_count()
            else:
                # 如果loader不可用，只返回CSV计数
                return csv_count
        except Exception as e:
            logger.warning(f"获取wf_items_loader计数失败，使用CSV计数: {e}")
            return csv_count

    def rebuild_index(self):
        """重建搜索索引"""
        # TODO: 如果需要更高级的搜索功能，可以实现索引
        pass

    def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """
        获取搜索建议

        Args:
            prefix: 前缀字符串
            limit: 建议数量限制

        Returns:
            建议列表
        """
        if len(prefix) < 1:
            return []

        suggestions = []
        prefix_lower = prefix.lower()

        for _, localized_name in self.items:
            if localized_name.lower().startswith(prefix_lower):
                if localized_name not in suggestions:
                    suggestions.append(localized_name)

                    if len(suggestions) >= limit:
                        break

        return suggestions


# 全局搜索引擎实例
_search_engine_instance: Optional[SearchEngine] = None


def get_search_engine() -> SearchEngine:
    """获取全局搜索引擎实例"""
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = SearchEngine()
    return _search_engine_instance


if __name__ == "__main__":
    # 测试搜索引擎
    import sys

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    engine = SearchEngine()

    print(f"加载了 {engine.get_item_count()} 个物品")
    print()

    # 测试搜索
    test_queries = ["Lavos", "测试", "Prime", "Nova"]

    for query in test_queries:
        print(f"搜索 '{query}':")
        results = engine.search(query, limit=5)

        for internal_name, localized_name in results:
            print(f"  {localized_name} ({internal_name})")

        print()

    # 测试根据内部名称获取
    test_internal_name = "/Lotus/Powersuits/Alchemist/Alchemist"
    localized_name = engine.get_by_internal_name(test_internal_name)
    print(f"内部名称 '{test_internal_name}' 的本地化名称: {localized_name}")

    # 测试建议
    suggestions = engine.get_suggestions("Lav", limit=5)
    print(f"前缀 'Lav' 的建议: {suggestions}")