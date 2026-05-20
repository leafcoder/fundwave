#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志记录器配置
"""

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
        name: str,
        log_file: str,
        level: int = logging.INFO) -> logging.Logger:
    """设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '{asctime} - {name} - {levelname} - {message}',
            datefmt='%Y-%m-%d %H:%M:%S',
            style='{'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger('fund_monitor', 'fund_monitor.log')
