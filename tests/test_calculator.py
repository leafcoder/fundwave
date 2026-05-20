#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盈亏计算逻辑单元测试
测试基金持仓相关的计算公式
"""

import pytest


class TestProfitCalculation:
    """盈亏计算测试类"""
    
    def test_position_cost_calculation(self):
        """测试持仓成本计算：成本价 × 份额"""
        cost_price = 1.5
        shares = 1000
        expected_position_cost = 1500.0
        
        position_cost = cost_price * shares
        
        assert position_cost == expected_position_cost
        print(f"✅ 持仓成本计算正确: {cost_price} × {shares} = {position_cost}")
    
    def test_current_value_calculation(self):
        """测试持有金额计算：估算值 × 份额"""
        estimated_value = 1.8
        shares = 1000
        expected_current_value = 1800.0
        
        current_value = estimated_value * shares
        
        assert current_value == expected_current_value
        print(f"✅ 持有金额计算正确: {estimated_value} × {shares} = {current_value}")
    
    def test_daily_profit_calculation(self):
        """测试当日盈亏计算：持有金额 × 涨跌幅% / 100"""
        current_value = 1800.0
        change_percent = 2.5
        expected_daily_profit = 45.0
        
        daily_profit = current_value * change_percent / 100
        
        assert abs(daily_profit - expected_daily_profit) < 0.01
        print(f"✅ 当日盈亏计算正确: {current_value} × {change_percent}% = {daily_profit}")
    
    def test_total_profit_loss_with_dividend(self):
        """测试累计盈亏计算（含分红）：持有金额 - 持仓成本 + 分红"""
        current_value = 1800.0
        position_cost = 1500.0
        dividend = 50.0
        expected_total_profit = 350.0
        
        total_profit_loss = current_value - position_cost + dividend
        
        assert total_profit_loss == expected_total_profit
        print(f"✅ 累计盈亏计算正确: {current_value} - {position_cost} + {dividend} = {total_profit_loss}")
    
    def test_profit_percentage_calculation(self):
        """测试盈亏百分比计算：(累计盈亏 / 持仓成本) × 100%"""
        total_profit_loss = 350.0
        position_cost = 1500.0
        expected_percentage = 23.333333333333332
        
        profit_percentage = (total_profit_loss / position_cost) * 100
        
        assert abs(profit_percentage - expected_percentage) < 0.01
        print(f"✅ 盈亏百分比计算正确: ({total_profit_loss} / {position_cost}) × 100% = {profit_percentage:.2f}%")
    
    def test_profit_percentage_zero_cost(self):
        """测试持仓成本为0时的盈亏百分比（应返回0避免除零错误）"""
        total_profit_loss = 100.0
        position_cost = 0.0
        
        if position_cost > 0:
            profit_percentage = (total_profit_loss / position_cost) * 100
        else:
            profit_percentage = 0.0
        
        assert profit_percentage == 0.0
        print("✅ 持仓成本为0时，盈亏百分比正确返回0")
    
    def test_negative_daily_profit(self):
        """测试负收益情况下的当日盈亏"""
        current_value = 1800.0
        change_percent = -1.5
        expected_daily_profit = -27.0
        
        daily_profit = current_value * change_percent / 100
        
        assert abs(daily_profit - expected_daily_profit) < 0.01
        print(f"✅ 负收益当日盈亏计算正确: {current_value} × {change_percent}% = {daily_profit}")
    
    def test_total_loss_scenario(self):
        """测试亏损场景的累计盈亏"""
        current_value = 1200.0
        position_cost = 1500.0
        dividend = 50.0
        expected_total_loss = -250.0
        
        total_profit_loss = current_value - position_cost + dividend
        
        assert total_profit_loss == expected_total_loss
        print(f"✅ 亏损场景累计盈亏计算正确: {current_value} - {position_cost} + {dividend} = {total_profit_loss}")
    
    def test_break_even_point(self):
        """测试盈亏平衡点（累计盈亏=0）"""
        current_value = 1500.0
        position_cost = 1500.0
        dividend = 0.0
        expected_profit = 0.0
        
        total_profit_loss = current_value - position_cost + dividend
        
        assert total_profit_loss == expected_profit
        print("✅ 盈亏平衡点计算正确")
    
    def test_high_return_scenario(self):
        """测试高收益场景"""
        cost_price = 1.0
        shares = 5000
        estimated_value = 2.5
        dividend = 200.0
        
        position_cost = cost_price * shares
        current_value = estimated_value * shares
        total_profit = current_value - position_cost + dividend
        profit_pct = (total_profit / position_cost) * 100 if position_cost > 0 else 0
        
        assert position_cost == 5000.0
        assert current_value == 12500.0
        assert total_profit == 7700.0
        assert abs(profit_pct - 154.0) < 0.01
        
        print(f"✅ 高收益场景:")
        print(f"   持仓成本: ¥{position_cost:.2f}")
        print(f"   持有金额: ¥{current_value:.2f}")
        print(f"   累计盈亏: ¥{total_profit:.2f}")
        print(f"   盈亏比例: {profit_pct:.2f}%")


class TestFundCodeValidation:
    """基金代码验证测试类"""
    
    def test_valid_fund_code(self):
        """测试有效的6位数字基金代码"""
        from services.data_fetcher import FundDataFetcher
        
        code = "000001"
        is_valid, error_msg = FundDataFetcher.validate_fund_code(code)
        
        assert is_valid is True
        assert error_msg == ""
        print(f"✅ 有效基金代码验证通过: {code}")
    
    def test_invalid_empty_code(self):
        """测试空基金代码"""
        from services.data_fetcher import FundDataFetcher
        
        code = ""
        is_valid, error_msg = FundDataFetcher.validate_fund_code(code)
        
        assert is_valid is False
        assert "不能为空" in error_msg
        print(f"✅ 空代码被正确拒绝: {error_msg}")
    
    def test_invalid_non_numeric(self):
        """测试非数字基金代码"""
        from services.data_fetcher import FundDataFetcher
        
        code = "ABCDEF"
        is_valid, error_msg = FundDataFetcher.validate_fund_code(code)
        
        assert is_valid is False
        assert "必须为数字" in error_msg
        print(f"✅ 非数字代码被正确拒绝: {error_msg}")
    
    def test_invalid_length(self):
        """测试长度不正确的基金代码"""
        from services.data_fetcher import FundDataFetcher
        
        code = "12345"
        is_valid, error_msg = FundDataFetcher.validate_fund_code(code)
        
        assert is_valid is False
        assert "6位" in error_msg
        print(f"✅ 长度不正确的代码被正确拒绝: {code} -> {error_msg}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
