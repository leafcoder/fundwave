#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数和装饰器模块
提供通用的工具函数和装饰器
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, TypeVar

from utils.logger import logger

F = TypeVar('F', bound=Callable[..., Any])


def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """重试装饰器

    在函数执行失败时自动重试指定次数

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）

    Returns:
        装饰后的函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"第{attempt + 1}次尝试失败: {e}, "
                        f"{delay}秒后重试..."
                    )
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def measure_time(func: F) -> F:
    """测量函数执行时间的装饰器

    Args:
        func: 要测量的函数

    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"{func.__name__} 执行时间: {execution_time:.3f}秒")
        return result
    return wrapper
