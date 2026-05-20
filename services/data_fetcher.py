#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金数据获取模块
提供基金数据API调用和验证功能
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import config
from utils.decorators import retry_on_failure
from utils.logger import logger


class FundDataFetcher:
    """基金数据获取器"""

    @staticmethod
    @retry_on_failure(max_retries=config.max_retry_times,
                      delay=config.retry_delay)
    def get_fund(code: str) -> Optional[Dict[str, Any]]:
        """获取单个基金数据

        Args:
            code: 基金代码

        Returns:
            基金数据字典，失败返回None
        """
        if not code or not code.isdigit() or len(code) != 6:
            logger.error(f"无效的基金代码: {code}")
            return None

        url = config.fund_api_url.format(code=code)
        try:
            r = requests.get(url, timeout=config.request_timeout)
            r.raise_for_status()
            content = r.text
            pattern = r'^jsonpgz\((.*)\)'
            search = re.findall(pattern, content)
            if search:
                data = json.loads(search[0])
                logger.debug(f"成功获取基金{code}数据: {data.get('name', 'Unknown')}")
                return data
            else:
                logger.warning(f"基金{code}数据格式异常")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"获取基金{code}数据超时")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"获取基金{code}数据网络错误: {e}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析基金{code}数据失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取基金{code}数据未知错误: {e}")
            raise

    @staticmethod
    @retry_on_failure(max_retries=config.max_retry_times,
                      delay=config.retry_delay)
    def get_all_funds() -> Dict[str, Dict[str, str]]:
        """获取所有基金列表

        Returns:
            基金字典 {code: {'name': name, 'pinyin': pinyin}}
        """
        url = config.fund_list_url
        try:
            r = requests.get(url, timeout=config.request_timeout)
            r.raise_for_status()
            content = r.text
            pattern = r'var r = (\[.*?\]);'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                fund_list_str = match.group(1)
                fund_list = json.loads(fund_list_str)
                funds = {}
                for fund in fund_list:
                    if len(fund) >= 3:
                        code = fund[0]
                        name = fund[2]
                        funds[code] = {
                            'name': name,
                            'pinyin': fund[4] if len(fund) > 4 else ''
                        }
                logger.info(f"成功获取{len(funds)}只基金列表")
                return funds
            logger.warning("基金列表数据格式异常")
            return {}
        except requests.exceptions.Timeout:
            logger.error("获取基金列表超时")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"获取基金列表网络错误: {e}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析基金列表失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取基金列表未知错误: {e}")
            raise

    @staticmethod
    def validate_fund_code(code: str) -> Tuple[bool, str]:
        """验证基金代码有效性

        Args:
            code: 基金代码

        Returns:
            (是否有效, 错误消息)
        """
        if not code:
            return False, "基金代码不能为空"

        if not code.isdigit():
            return False, "基金代码必须为数字"

        if len(code) != 6:
            return False, "基金代码必须为6位数字"

        return True, ""
