#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器单元测试
"""

import os
import pytest
import tempfile

from models.database import DatabaseManager


@pytest.fixture(scope='module')
def db_manager():
    """创建测试用数据库管理器"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name
    
    manager = DatabaseManager(db_path=db_path)
    yield manager
    manager.close()
    
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestDatabaseManager:
    """DatabaseManager测试类"""
    
    def test_init_database(self, db_manager):
        """测试数据库初始化"""
        assert db_manager is not None
        
        with db_manager.get_cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'monitored_funds' in tables
            assert 'fund_holdings' in tables
            assert 'settings' in tables
            assert 'notification_settings' in tables
            assert 'ui_settings' in tables
            print("✅ 数据库表结构初始化正确")
    
    def test_ui_settings_default(self, db_manager):
        """测试UI设置默认值"""
        settings = db_manager.get_ui_settings()
        
        assert isinstance(settings, dict)
        assert 'profit_visible' in settings
        assert 'daily_profit_visible' in settings
        assert 'position_cost_visible' in settings
        assert 'current_value_visible' in settings
        
        assert settings['profit_visible'] is True
        assert settings['daily_profit_visible'] is True
        assert settings['position_cost_visible'] is True
        assert settings['current_value_visible'] is True
        print("✅ UI设置默认值正确")
    
    def test_save_and_load_ui_setting(self, db_manager):
        """测试UI设置保存和加载"""
        result = db_manager.save_ui_setting('profit_visible', False)
        assert result is True
        
        settings = db_manager.get_ui_settings()
        assert settings['profit_visible'] is False
        
        result = db_manager.save_ui_setting('profit_visible', True)
        assert result is True
        
        settings = db_manager.get_ui_settings()
        assert settings['profit_visible'] is True
        print("✅ UI设置保存和加载功能正常")
    
    def test_save_invalid_ui_setting(self, db_manager):
        """测试保存无效的UI设置名称"""
        result = db_manager.save_ui_setting('invalid_setting', True)
        assert result is False
        print("✅ 无效设置名称被正确拒绝")
    
    def test_monitored_funds_crud(self, db_manager):
        """测试监控基金的增删改查操作"""
        fund_code = "000001"
        fund_name = "测试基金"
        
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                'INSERT INTO monitored_funds (fund_code, fund_name) VALUES (?, ?)',
                (fund_code, fund_name)
            )
            
            cursor.execute('SELECT * FROM monitored_funds WHERE fund_code = ?', (fund_code,))
            result = cursor.fetchone()
            assert result is not None
            assert result[1] == fund_code
            assert result[2] == fund_name
            
            cursor.execute('DELETE FROM monitored_funds WHERE fund_code = ?', (fund_code,))
            
            cursor.execute('SELECT COUNT(*) FROM monitored_funds WHERE fund_code = ?', (fund_code,))
            count = cursor.fetchone()[0]
            assert count == 0
        
        print("✅ 监控基金CRUD操作正常")
    
    def test_fund_holdings_crud(self, db_manager):
        """测试基金持仓信息的增删改查操作"""
        fund_code = "000002"
        cost_price = 1.5
        shares = 1000.0
        amount = 1500.0
        
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                '''INSERT INTO fund_holdings 
                   (fund_code, cost_price, shares, amount) 
                   VALUES (?, ?, ?, ?)''',
                (fund_code, cost_price, shares, amount)
            )
            
            cursor.execute(
                'SELECT cost_price, shares, amount FROM fund_holdings WHERE fund_code = ?',
                (fund_code,)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == cost_price
            assert result[1] == shares
            assert result[2] == amount
            
            new_cost_price = 2.0
            cursor.execute(
                '''UPDATE fund_holdings 
                   SET cost_price = ? 
                   WHERE fund_code = ?''',
                (new_cost_price, fund_code)
            )
            
            cursor.execute(
                'SELECT cost_price FROM fund_holdings WHERE fund_code = ?',
                (fund_code,)
            )
            result = cursor.fetchone()
            assert result[0] == new_cost_price
            
            cursor.execute('DELETE FROM fund_holdings WHERE fund_code = ?', (fund_code,))
        
        print("✅ 基金持仓信息CRUD操作正常")
    
    def test_dividend_records(self, db_manager):
        """测试分红记录功能"""
        fund_code = "000003"
        dividend_amount = 100.50
        
        from datetime import datetime
        dividend_date = datetime.now().strftime('%Y-%m-%d')
        
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                '''INSERT INTO dividend_records 
                   (fund_code, dividend_amount, dividend_date) 
                   VALUES (?, ?, ?)''',
                (fund_code, dividend_amount, dividend_date)
            )
            
            cursor.execute(
                'SELECT SUM(dividend_amount) FROM dividend_records WHERE fund_code = ?',
                (fund_code,)
            )
            total = cursor.fetchone()[0]
            assert total == dividend_amount
        
        print("✅ 分红记录功能正常")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
