#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
集中管理系统配置和常量定义
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FundConfig:
    """基金监控配置"""
    db_path: str = 'fund_monitor.db'
    default_refresh_interval: int = 60
    min_refresh_interval: int = 5
    max_refresh_interval: int = 3600
    request_timeout: int = 10
    max_retry_times: int = 3
    retry_delay: float = 1.0
    fund_api_url: str = "http://fundgz.1234567.com.cn/js/{code}.js"
    fund_list_url: str = "https://fund.eastmoney.com/js/fundcode_search.js"


config = FundConfig()
