#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
提供线程安全的数据库操作和UI设置持久化功能
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

from config import config
from utils.logger import logger


class DatabaseManager:
    """数据库管理器 - 线程安全的数据库操作"""

    def __init__(self, db_path: str = config.db_path):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取线程本地的数据库连接"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()

    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitored_funds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code TEXT UNIQUE NOT NULL,
                    fund_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fund_holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code TEXT UNIQUE NOT NULL,
                    amount REAL DEFAULT 0.0,
                    cost_price REAL DEFAULT 0.0,
                    shares REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    refresh_interval INTEGER DEFAULT 60,
                    auto_refresh_enabled BOOLEAN DEFAULT 1,
                    total_profit REAL DEFAULT 0.0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_settings (
                    id INTEGER PRIMARY KEY,
                    popup_enabled BOOLEAN DEFAULT 1,
                    dingtalk_enabled BOOLEAN DEFAULT 0,
                    dingtalk_webhook TEXT,
                    email_enabled BOOLEAN DEFAULT 0,
                    email_smtp_server TEXT,
                    email_sender TEXT,
                    email_password TEXT,
                    email_receiver TEXT,
                    rise_threshold REAL DEFAULT 3.0,
                    fall_threshold REAL DEFAULT -3.0,
                    profit_threshold REAL DEFAULT 1000.0,
                    loss_threshold REAL DEFAULT -1000.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fund_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code TEXT NOT NULL,
                    net_value REAL,
                    estimated_value REAL,
                    estimated_change REAL,
                    record_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dividend_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code TEXT NOT NULL,
                    dividend_amount REAL NOT NULL,
                    dividend_date DATE,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ui_settings (
                    id INTEGER PRIMARY KEY,
                    profit_visible BOOLEAN DEFAULT 1,
                    daily_profit_visible BOOLEAN DEFAULT 1,
                    position_cost_visible BOOLEAN DEFAULT 1,
                    current_value_visible BOOLEAN DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('SELECT COUNT(*) FROM notification_settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'INSERT INTO notification_settings DEFAULT VALUES'
                )

            cursor.execute('SELECT COUNT(*) FROM settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'INSERT INTO settings (refresh_interval, auto_refresh_enabled, total_profit) '
                    'VALUES (?, ?, ?)',
                    (config.default_refresh_interval, 1, 0.0)
                )

            cursor.execute('SELECT COUNT(*) FROM ui_settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'INSERT INTO ui_settings (profit_visible, daily_profit_visible, position_cost_visible, current_value_visible) '
                    'VALUES (1, 1, 1, 1)'
                )

            self._migrate_database(cursor)

        logger.info("数据库初始化完成")

    def _migrate_database(self, cursor):
        """数据库迁移 - 修复旧版本的表结构问题"""
        try:
            cursor.execute("PRAGMA table_info(monitored_funds)")
            columns = {row[1] for row in cursor.fetchall()}

            if 'fund_name' not in columns or 'updated_at' not in columns:
                logger.info("迁移数据库: 重建 monitored_funds 表")
                cursor.execute('''
                    CREATE TABLE monitored_funds_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fund_code TEXT UNIQUE NOT NULL,
                        fund_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('SELECT COUNT(*) FROM monitored_funds')
                count = cursor.fetchone()[0]

                if count > 0:
                    cursor.execute('''
                        INSERT INTO monitored_funds_new (fund_code, created_at, updated_at)
                        SELECT fund_code,
                               COALESCE(created_at, CURRENT_TIMESTAMP),
                               CURRENT_TIMESTAMP
                        FROM monitored_funds
                    ''')
                    logger.info(f"迁移了 {count} 条监控基金记录")

                cursor.execute('DROP TABLE monitored_funds')
                cursor.execute(
                    'ALTER TABLE monitored_funds_new RENAME TO monitored_funds')

            cursor.execute("PRAGMA table_info(fund_holdings)")
            columns = {row[1] for row in cursor.fetchall()}

            need_rebuild = False
            if 'cost_price' not in columns or 'shares' not in columns:
                need_rebuild = True
                logger.info("迁移数据库: 添加 cost_price 和 shares 字段")

            if 'updated_at' not in columns:
                need_rebuild = True
                logger.info("迁移数据库: 添加 fund_holdings.updated_at 字段")

            if need_rebuild:
                cursor.execute('''
                    CREATE TABLE fund_holdings_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fund_code TEXT UNIQUE NOT NULL,
                        amount REAL DEFAULT 0.0,
                        cost_price REAL DEFAULT 0.0,
                        shares REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('SELECT COUNT(*) FROM fund_holdings')
                count = cursor.fetchone()[0]

                if count > 0:
                    cursor.execute('''
                        INSERT INTO fund_holdings_new (fund_code, amount, cost_price, shares, created_at, updated_at)
                        SELECT fund_code,
                               COALESCE(amount, 0.0),
                               COALESCE(cost_price, 0.0),
                               COALESCE(shares, 0.0),
                               COALESCE(created_at, CURRENT_TIMESTAMP),
                               COALESCE(updated_at, CURRENT_TIMESTAMP)
                        FROM fund_holdings
                    ''')
                    logger.info(f"迁移了 {count} 条持有金额记录")

                cursor.execute('DROP TABLE fund_holdings')
                cursor.execute(
                    'ALTER TABLE fund_holdings_new RENAME TO fund_holdings')

        except Exception as e:
            logger.warning(f"数据库迁移检查失败（可能是新数据库）: {e}")

    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
            logger.info("数据库连接已关闭")

    def get_ui_settings(self) -> Dict[str, bool]:
        """获取UI设置（眼睛图标状态）

        Returns:
            包含各可见性状态的字典
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    SELECT profit_visible, daily_profit_visible, position_cost_visible, current_value_visible
                    FROM ui_settings LIMIT 1
                ''')
                result = cursor.fetchone()
                if result:
                    return {
                        'profit_visible': bool(result[0]),
                        'daily_profit_visible': bool(result[1]),
                        'position_cost_visible': bool(result[2]),
                        'current_value_visible': bool(result[3])
                    }
        except Exception as e:
            logger.error(f"获取UI设置失败: {e}")

        return {
            'profit_visible': True,
            'daily_profit_visible': True,
            'position_cost_visible': True,
            'current_value_visible': True
        }

    def save_ui_setting(self, setting_name: str, value: bool) -> bool:
        """保存单个UI设置

        Args:
            setting_name: 设置名称
            value: 可见性状态

        Returns:
            是否保存成功
        """
        valid_settings = [
            'profit_visible', 'daily_profit_visible',
            'position_cost_visible', 'current_value_visible'
        ]
        if setting_name not in valid_settings:
            logger.error(f"无效的UI设置名称: {setting_name}")
            return False

        try:
            with self.get_cursor() as cursor:
                cursor.execute(f'''
                    UPDATE ui_settings
                    SET {setting_name} = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (int(value),))
            logger.debug(f"已保存UI设置: {setting_name} = {value}")
            return True
        except Exception as e:
            logger.error(f"保存UI设置失败: {e}")
            return False
