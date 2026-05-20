#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理单元测试
"""

import pytest

from config import FundConfig, config


class TestFundConfig:
    """FundConfig配置类测试"""
    
    def test_default_config_values(self):
        """测试默认配置值"""
        assert config.db_path == 'fund_monitor.db'
        assert config.default_refresh_interval == 60
        assert config.min_refresh_interval == 5
        assert config.max_refresh_interval == 3600
        assert config.request_timeout == 10
        assert config.max_retry_times == 3
        assert config.retry_delay == 1.0
        
        print("✅ 默认配置值正确")
    
    def test_custom_config(self):
        """测试自定义配置"""
        custom_config = FundConfig(
            db_path='custom.db',
            default_refresh_interval=30,
            min_refresh_interval=10,
            max_refresh_interval=1800,
            request_timeout=15,
            max_retry_times=5,
            retry_delay=2.0
        )
        
        assert custom_config.db_path == 'custom.db'
        assert custom_config.default_refresh_interval == 30
        assert custom_config.min_refresh_interval == 10
        assert custom_config.max_refresh_interval == 1800
        assert custom_config.request_timeout == 15
        assert custom_config.max_retry_times == 5
        assert custom_config.retry_delay == 2.0
        
        print("✅ 自定义配置正确")
    
    def test_fund_api_url_format(self):
        """测试基金API URL格式"""
        code = "000001"
        expected_url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        
        actual_url = config.fund_api_url.format(code=code)
        
        assert actual_url == expected_url
        print(f"✅ 基金API URL格式正确: {actual_url}")
    
    def test_fund_list_url(self):
        """测试基金列表URL"""
        assert "eastmoney.com" in config.fund_list_url
        assert "fundcode_search" in config.fund_list_url
        print("✅ 基金列表URL正确")


class TestConfigValidation:
    """配置验证测试"""
    
    def test_refresh_interval_bounds(self):
        """测试刷新间隔边界值"""
        min_interval = config.min_refresh_interval
        max_interval = config.max_refresh_interval
        
        assert min_interval < max_interval
        assert min_interval > 0
        assert max_interval > min_interval
        
        print(f"✅ 刷新间隔范围合理: {min_interval} - {max_interval}秒")
    
    def test_retry_settings(self):
        """测试重试设置合理性"""
        assert config.max_retry_times > 0
        assert config.retry_delay > 0
        
        total_timeout = config.retry_delay * config.max_retry_times * config.request_timeout
        
        print(f"✅ 重试设置合理:")
        print(f"   最大重试次数: {config.max_retry_times}")
        print(f"   重试延迟: {config.retry_delay}秒")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
