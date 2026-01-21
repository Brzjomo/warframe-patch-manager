"""
API 客户端模块
用于与游戏 API 交互
"""

import requests
import json
import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class APIClient:
    """API 客户端"""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        初始化 API 客户端

        Args:
            base_url: API 基础 URL，如果为 None 则从配置加载
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url or "http://localhost:8080"
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建会话
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update({
            "User-Agent": "WarframePatchManager/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        # 缓存
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl: Dict[str, float] = {}  # 缓存过期时间

        logger.info(f"API 客户端初始化完成，基础URL: {self.base_url}")

    def set_base_url(self, base_url: str):
        """设置基础 URL"""
        self.base_url = base_url.rstrip('/')
        logger.info(f"API 基础URL已更新: {self.base_url}")

    def test_connection(self) -> bool:
        """
        测试 API 连接

        Returns:
            连接是否成功
        """
        endpoint = f"{self.base_url}/health"

        try:
            response = self.session.get(endpoint, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"API 连接测试失败: {e}")
            return False

    def get_item_data(self, internal_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取物品数据

        Args:
            internal_name: 物品内部名称
            use_cache: 是否使用缓存

        Returns:
            物品数据字典，如果失败返回 None
        """
        # 检查缓存
        cache_key = f"item:{internal_name}"
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取物品数据: {internal_name}")
            return self.cache[cache_key]

        # TODO: 根据实际 API 文档实现具体请求
        # 这里需要根据 Reference Manual.html 和 Script API Reference.pluto 实现

        # 模拟 API 响应（用于开发测试）
        if self.base_url == "http://localhost:8080":
            logger.debug(f"模拟获取物品数据: {internal_name}")
            mock_data = self._get_mock_item_data(internal_name)

            # 缓存结果
            if mock_data and use_cache:
                self._set_cache(cache_key, mock_data, ttl=300)  # 5分钟缓存

            return mock_data

        # 实际 API 请求
        endpoint = f"{self.base_url}/api/item"
        params = {"name": internal_name}

        try:
            response = self._request_with_retry("GET", endpoint, params=params)

            if response.status_code == 200:
                data = response.json()

                # 缓存结果
                if use_cache:
                    self._set_cache(cache_key, data, ttl=300)  # 5分钟缓存

                logger.info(f"成功获取物品数据: {internal_name}")
                return data
            else:
                logger.error(f"获取物品数据失败，状态码: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"获取物品数据请求失败: {e}")
            return None

    def get_multiple_items(self, internal_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        批量获取多个物品数据

        Args:
            internal_names: 内部名称列表

        Returns:
            物品数据字典，键为内部名称，值为数据或 None
        """
        results = {}

        for name in internal_names:
            results[name] = self.get_item_data(name)

        return results

    def search_items(self, query: str, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        搜索物品

        Args:
            query: 搜索查询
            category: 物品类别（可选）
            limit: 结果数量限制

        Returns:
            物品数据列表
        """
        # TODO: 实现 API 搜索
        # 这里需要根据实际 API 实现

        endpoint = f"{self.base_url}/api/search"
        params = {"q": query, "limit": limit}
        if category:
            params["category"] = category

        try:
            response = self._request_with_retry("GET", endpoint, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"搜索 '{query}' 找到 {len(data)} 个结果")
                return data
            else:
                logger.error(f"搜索失败，状态码: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"搜索请求失败: {e}")
            return []

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        带重试的请求

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 请求参数

        Returns:
            响应对象
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"请求失败，{wait_time}秒后重试 ({attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求失败，已达到最大重试次数: {e}")
                    raise

        # 理论上不会执行到这里
        raise last_exception

    def _set_cache(self, key: str, value: Dict[str, Any], ttl: int = 300):
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存生存时间（秒）
        """
        self.cache[key] = value
        self.cache_ttl[key] = time.time() + ttl

        # 清理过期缓存
        self._clean_expired_cache()

    def _is_cache_valid(self, key: str) -> bool:
        """
        检查缓存是否有效

        Args:
            key: 缓存键

        Returns:
            缓存是否有效
        """
        if key not in self.cache:
            return False

        expire_time = self.cache_ttl.get(key, 0)
        return time.time() < expire_time

    def _clean_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for key, expire_time in self.cache_ttl.items():
            if current_time >= expire_time:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]
            del self.cache_ttl[key]

        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_ttl.clear()
        logger.info("API 缓存已清空")

    def _get_mock_item_data(self, internal_name: str) -> Dict[str, Any]:
        """
        获取模拟物品数据（用于开发测试）

        Args:
            internal_name: 内部名称

        Returns:
            模拟数据
        """
        # 从 CSV 文件获取本地化名称
        from .search_engine import get_search_engine

        engine = get_search_engine()
        localized_name = engine.get_by_internal_name(internal_name)

        if not localized_name:
            localized_name = "未知物品"

        # 生成模拟数据
        mock_data = {
            "internalName": internal_name,
            "localizedName": localized_name,
            "category": self._guess_category(internal_name),
            "tradable": True,
            "masteryRank": 0,
            "description": f"{localized_name} 的描述信息。",
            "patchlogs": [
                {"version": "40.0.0", "changes": "初始添加"}
            ],
            "wikiaUrl": f"https://warframe.fandom.com/wiki/{localized_name.replace(' ', '_')}",
            "imageName": f"{internal_name.replace('/', '_')}.png",
            "components": [
                {"name": "组件1", "itemCount": 1},
                {"name": "组件2", "itemCount": 2}
            ],
            "buildPrice": 25000,
            "buildTime": 24,
            "skipBuildTimePrice": 25,
            "buildQuantity": 1,
            "consumeOnBuild": True,
            "isPrime": "Prime" in internal_name,
            "marketCost": 150,
            "productCategory": "Equipment"
        }

        return mock_data

    def _guess_category(self, internal_name: str) -> str:
        """
        根据内部名称猜测物品类别

        Args:
            internal_name: 内部名称

        Returns:
            类别名称
        """
        if "/Powersuits/" in internal_name:
            return "Warframes"
        elif "/Weapons/" in internal_name:
            return "Weapons"
        elif "/Mods/" in internal_name:
            return "Mods"
        elif "/Resources/" in internal_name:
            return "Resources"
        elif "/Upgrades/" in internal_name:
            return "Upgrades"
        elif "/Arcane/" in internal_name:
            return "Arcanes"
        else:
            return "Misc"

    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """
        获取 API 信息

        Returns:
            API 信息字典
        """
        endpoint = f"{self.base_url}/api/info"

        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    def get_effective_metadata(self, internal_name: str) -> Optional[str]:
        """
        获取有效元数据文本

        Args:
            internal_name: 物品内部名称

        Returns:
            元数据文本，如果失败返回 None
        """
        # 使用特定的元数据 API 端点
        metadata_base_url = "http://localhost:6155"
        endpoint = f"{metadata_base_url}/get_effective_metadata?{internal_name}"

        try:
            logger.info(f"请求元数据: {endpoint}")
            response = self.session.get(endpoint, timeout=self.timeout)

            if response.status_code == 200:
                # 返回原始文本
                text = response.text
                logger.info(f"成功获取元数据，长度: {len(text)} 字符")
                return text
            else:
                logger.error(f"获取元数据失败，状态码: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"获取元数据请求失败: {e}")
            return None


# 全局 API 客户端实例
_api_client_instance: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """获取全局 API 客户端实例"""
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = APIClient()
    return _api_client_instance


if __name__ == "__main__":
    # 测试 API 客户端
    import sys

    # 设置日志
    logging.basicConfig(level=logging.DEBUG)

    client = APIClient()

    # 测试连接
    if client.test_connection():
        print("✓ API 连接测试成功")
    else:
        print("✗ API 连接测试失败，使用模拟数据")

    # 测试获取物品数据
    test_items = [
        "/Lotus/Powersuits/Alchemist/Alchemist",
        "/Lotus/Weapons/Tenno/Primary/TestWeapon",
        "/NonExistent/Item"
    ]

    for item in test_items:
        print(f"\n获取物品数据: {item}")
        data = client.get_item_data(item)

        if data:
            print(f"  名称: {data.get('localizedName')}")
            print(f"  类别: {data.get('category')}")
            print(f"  可交易: {data.get('tradable')}")
        else:
            print("  获取失败")

    # 测试缓存
    print("\n测试缓存...")
    item = "/Lotus/Powersuits/Alchemist/Alchemist"

    # 第一次获取（应调用 API/模拟）
    start_time = time.time()
    data1 = client.get_item_data(item)
    time1 = time.time() - start_time
    print(f"第一次获取耗时: {time1:.3f}秒")

    # 第二次获取（应从缓存读取）
    start_time = time.time()
    data2 = client.get_item_data(item)
    time2 = time.time() - start_time
    print(f"第二次获取耗时: {time2:.3f}秒")

    if time2 < time1:
        print("✓ 缓存生效")
    else:
        print("✗ 缓存未生效")

    # 清空缓存
    client.clear_cache()
    print("缓存已清空")