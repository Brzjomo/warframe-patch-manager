"""
文件操作工具模块
"""

import os
import shutil
import json
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def ensure_directory(directory_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建

    Args:
        directory_path: 目录路径

    Returns:
        是否成功
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {directory_path}, 错误: {e}")
        return False


def read_json_file(file_path: str, default: Any = None) -> Any:
    """
    读取 JSON 文件

    Args:
        file_path: 文件路径
        default: 读取失败时的默认值

    Returns:
        JSON 数据或默认值
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"读取 JSON 文件失败: {file_path}, 错误: {e}")
        return default


def write_json_file(file_path: str, data: Any, indent: int = 2) -> bool:
    """
    写入 JSON 文件

    Args:
        file_path: 文件路径
        data: 要写入的数据
        indent: 缩进空格数

    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        ensure_directory(os.path.dirname(file_path))

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (TypeError, IOError) as e:
        logger.error(f"写入 JSON 文件失败: {file_path}, 错误: {e}")
        return False


def read_csv_file(file_path: str) -> List[List[str]]:
    """
    读取 CSV 文件

    Args:
        file_path: 文件路径

    Returns:
        CSV 数据行列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"读取 CSV 文件失败: {file_path}, 错误: {e}")
        return []


def write_csv_file(file_path: str, data: List[List[str]], headers: Optional[List[str]] = None) -> bool:
    """
    写入 CSV 文件

    Args:
        file_path: 文件路径
        data: 数据行列表
        headers: 标题行（可选）

    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        ensure_directory(os.path.dirname(file_path))

        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            if headers:
                writer.writerow(headers)

            for row in data:
                writer.writerow(row)

        return True
    except Exception as e:
        logger.error(f"写入 CSV 文件失败: {file_path}, 错误: {e}")
        return False


def safe_delete_file(file_path: str) -> bool:
    """
    安全删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"文件已删除: {file_path}")
        return True
    except Exception as e:
        logger.error(f"删除文件失败: {file_path}, 错误: {e}")
        return False


def safe_delete_directory(directory_path: str) -> bool:
    """
    安全删除目录

    Args:
        directory_path: 目录路径

    Returns:
        是否成功
    """
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            logger.debug(f"目录已删除: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"删除目录失败: {directory_path}, 错误: {e}")
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        文件大小（字节），如果文件不存在返回 None
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名（小写）

    Args:
        file_path: 文件路径

    Returns:
        文件扩展名（不含点）
    """
    return Path(file_path).suffix.lower()[1:] if Path(file_path).suffix else ""


def find_files_by_pattern(directory: str, pattern: str = "*.txt") -> List[str]:
    """
    按模式查找文件

    Args:
        directory: 目录路径
        pattern: 文件模式（如 "*.txt", "*.json"）

    Returns:
        匹配的文件路径列表
    """
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            return []

        return [str(file) for file in directory_path.glob(pattern)]
    except Exception as e:
        logger.error(f"查找文件失败: {directory}, 模式: {pattern}, 错误: {e}")
        return []


def backup_file(original_path: str, backup_suffix: str = ".bak") -> bool:
    """
    备份文件

    Args:
        original_path: 原始文件路径
        backup_suffix: 备份文件后缀

    Returns:
        是否成功
    """
    if not os.path.exists(original_path):
        logger.warning(f"原始文件不存在，无需备份: {original_path}")
        return False

    backup_path = f"{original_path}{backup_suffix}"

    try:
        shutil.copy2(original_path, backup_path)
        logger.debug(f"文件已备份: {original_path} -> {backup_path}")
        return True
    except Exception as e:
        logger.error(f"备份文件失败: {original_path}, 错误: {e}")
        return False


def normalize_path(path: str) -> str:
    """
    规范化路径（展开用户目录，转为绝对路径）

    Args:
        path: 原始路径

    Returns:
        规范化后的路径
    """
    # 展开用户目录（如 ~/Documents）
    expanded_path = os.path.expanduser(path)

    # 转为绝对路径
    absolute_path = os.path.abspath(expanded_path)

    # 标准化路径分隔符
    normalized_path = os.path.normpath(absolute_path)

    return normalized_path


def get_unique_filename(directory: str, base_name: str, extension: str) -> str:
    """
    获取唯一的文件名（避免重复）

    Args:
        directory: 目录路径
        base_name: 基础文件名（不含扩展名）
        extension: 文件扩展名（不含点）

    Returns:
        唯一的文件路径
    """
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)

    # 尝试基础文件名
    file_path = directory_path / f"{base_name}.{extension}"

    # 如果文件已存在，添加数字后缀
    counter = 1
    while file_path.exists():
        file_path = directory_path / f"{base_name}_{counter}.{extension}"
        counter += 1

    return str(file_path)


def read_text_file(file_path: str) -> Optional[str]:
    """
    读取文本文件

    Args:
        file_path: 文件路径

    Returns:
        文件内容，如果失败返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文本文件失败: {file_path}, 错误: {e}")
        return None


def write_text_file(file_path: str, content: str) -> bool:
    """
    写入文本文件

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        ensure_directory(os.path.dirname(file_path))

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文本文件失败: {file_path}, 错误: {e}")
        return False


if __name__ == "__main__":
    # 测试文件工具
    import tempfile

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"测试目录: {temp_dir}")

        # 测试确保目录
        test_dir = os.path.join(temp_dir, "subdir", "nested")
        if ensure_directory(test_dir):
            print(f"✓ 目录创建成功: {test_dir}")
        else:
            print("✗ 目录创建失败")

        # 测试 JSON 文件操作
        json_file = os.path.join(temp_dir, "test.json")
        test_data = {"name": "测试", "value": 123}

        if write_json_file(json_file, test_data):
            print(f"✓ JSON 文件写入成功: {json_file}")

            loaded_data = read_json_file(json_file)
            if loaded_data == test_data:
                print(f"✓ JSON 文件读取成功")
            else:
                print("✗ JSON 文件读取失败")

        # 测试文本文件操作
        text_file = os.path.join(temp_dir, "test.txt")
        test_content = "这是一段测试文本\n第二行"

        if write_text_file(text_file, test_content):
            print(f"✓ 文本文件写入成功: {text_file}")

            loaded_content = read_text_file(text_file)
            if loaded_content == test_content:
                print(f"✓ 文本文件读取成功")
            else:
                print("✗ 文本文件读取失败")

        # 测试文件删除
        if safe_delete_file(text_file):
            print(f"✓ 文件删除成功: {text_file}")

        # 测试路径规范化
        test_path = "~/test/file.txt"
        normalized = normalize_path(test_path)
        print(f"路径规范化: {test_path} -> {normalized}")

        # 测试唯一文件名
        unique_file = get_unique_filename(temp_dir, "test", "txt")
        print(f"唯一文件名: {unique_file}")