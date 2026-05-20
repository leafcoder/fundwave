#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合分析器和定投计算器单元测试
"""

import pytest
from datetime import date

from services.portfolio_analyzer import (
    AllocationData,
    FundHolding,
    PortfolioAnalyzer,
    PortfolioReport,
    RiskMetrics,
)
from services.investment_calculator import (
    InvestmentCalculator,
    InvestmentResult,
    InvestmentStrategy,
    PREDEFINED_STRATEGIES,
)


class TestPortfolioAnalyzer:
    """投资组合分析器测试类"""
    
    @pytest.fixture(scope='class')
    def analyzer(self):
        return PortfolioAnalyzer()
    
    @pytest.fixture(scope='class')
    def sample_holdings(self):
        """示例持仓数据"""
        return [
            {
                'fund_code': '000001',
                'fund_name': '华夏成长混合',
                'cost_price': 1.5,
                'shares': 1000,
                'current_value': 1800.0,
                'daily_profit': 45.0,
                'total_profit': 350.0,
                'dividend': 50.0
            },
            {
                'fund_code': '000002',
                'fund_name': '易方达蓝筹精选股票',
                'cost_price': 2.0,
                'shares': 500,
                'current_value': 1200.0,
                'daily_profit': -12.0,
                'total_profit': -50.0,
                'dividend': 20.0
            },
            {
                'fund_code': '000003',
                'fund_name': '嘉实债券基金',
                'cost_price': 1.0,
                'shares': 2000,
                'current_value': 2100.0,
                'daily_profit': 5.25,
                'total_profit': 150.0,
                'dividend': 30.0
            }
        ]
    
    def test_analyze_portfolio(self, analyzer, sample_holdings):
        """测试投资组合分析功能"""
        report = analyzer.analyze_portfolio(sample_holdings)
        
        assert isinstance(report, PortfolioReport)
        assert report.total_assets == 5100.0  # 1800 + 1200 + 2100
        assert report.total_cost == 4500.0  # (1.5*1000) + (2.0*500) + (1.0*2000)
        assert report.total_profit == 450.0  # 350 - 50 + 150
        assert len(report.allocations) > 0
        assert len(report.top_holdings) <= 5
        
        print("✅ 投资组合分析功能正常")
    
    def test_risk_metrics_calculation(self, analyzer, sample_holdings):
        """测试风险指标计算"""
        report = analyzer.analyze_portfolio(sample_holdings)
        
        risk = report.risk_metrics
        assert isinstance(risk, RiskMetrics)
        assert risk.volatility >= 0
        assert risk.max_drawdown >= 0
        assert isinstance(risk.sharpe_ratio, float)
        assert isinstance(risk.beta, float)
        
        print(f"✅ 风险指标计算正常: 波动率={risk.volatility}%, 夏普比率={risk.sharpe_ratio}")
    
    def test_allocation_distribution(self, analyzer, sample_holdings):
        """测试资产配置分布"""
        report = analyzer.analyze_portfolio(sample_holdings)
        
        total_percentage = sum(alloc.percentage for alloc in report.allocations)
        
        assert abs(total_percentage - 100.0) < 1.0  # 允许1%的误差
        
        for alloc in report.allocations:
            assert alloc.value >= 0
            assert alloc.percentage > 0
            assert alloc.category != ''
        
        print(f"✅ 资产配置分布正确: {len(report.allocations)}个类别")
    
    def test_profit_attribution(self, analyzer, sample_holdings):
        """测试收益归因分析"""
        report = analyzer.analyze_portfolio(sample_holdings)
        
        assert isinstance(report.profit_attribution, dict)
        assert len(report.profit_attribution) == len(sample_holdings)
        
        for code, (abs_val, pct) in report.profit_attribution.items():
            assert abs_val >= 0
            assert pct >= 0
        
        print("✅ 收益归因分析正常")
    
    def test_empty_holdings(self, analyzer):
        """测试空持仓数据"""
        report = analyzer.analyze_portfolio([])
        
        assert report.total_assets == 0
        assert report.total_cost == 0
        assert report.total_profit == 0
        
        print("✅ 空数据处理正常")
    
    def test_single_holding(self, analyzer):
        """测试单只基金持仓"""
        holdings = [
            {
                'fund_code': '000001',
                'fund_name': '测试基金',
                'cost_price': 1.0,
                'shares': 1000,
                'current_value': 1200.0,
                'daily_profit': 30.0,
                'total_profit': 250.0,
                'dividend': 0
            }
        ]
        
        report = analyzer.analyze_portfolio(holdings)
        
        assert report.total_assets == 1200.0
        assert report.total_profit == 250.0
        assert len(report.top_holdings) == 1
        
        print("✅ 单只基金处理正常")
    
    def test_fund_type_classification(self, analyzer):
        """测试基金类型分类"""
        test_cases = [
            ('华夏股票基金', '股票'),
            ('易方达债券A', '债券'),
            ('南方混合优选', '混合'),
            ('沪深300ETF', '指数'),
            ('QDII美股', 'QDII'),
            ('货币市场基金', '货币'),
        ]
        
        for name, expected_type in test_cases:
            result = analyzer._classify_fund_type(name)
            assert result == expected_type, f"{name} 应分类为 {expected_type}, 实际为 {result}"
        
        print("✅ 基金类型分类准确")
    
    def test_generate_summary_text(self, analyzer, sample_holdings):
        """测试摘要文本生成"""
        report = analyzer.analyze_portfolio(sample_holdings)
        summary = analyzer.generate_summary_text(report)
        
        assert isinstance(summary, str)
        assert '总资产' in summary
        assert '累计盈亏' in summary
        assert '风险指标' in summary
        assert len(summary) > 100  # 摘要应该足够详细
        
        print("✅ 摘要文本生成正常")


class TestInvestmentCalculator:
    """定投计算器测试类"""
    
    def test_basic_fixed_investment(self):
        """测试基本定投计算"""
        result = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=2000,
            expected_return=10,
            years=10
        )
        
        assert isinstance(result, InvestmentResult)
        assert result.total_principal == 240000.0  # 2000 * 12 * 10
        assert result.final_amount > result.total_principal  # 应该盈利
        assert result.total_profit > 0
        assert result.profit_percentage > 0
        assert len(result.monthly_data) == 120  # 10年 * 12月
        
        print(f"✅ 基本定投计算: 本金¥{result.total_principal:,.2f} → 最终¥{result.final_amount:,.2f}")
    
    def test_high_return_investment(self):
        """测试高收益定投"""
        result = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=3000,
            expected_return=15,
            years=15
        )
        
        assert result.final_amount > 500000  # 高收益长期投资应有可观回报
        assert result.profit_percentage > 100  # 收益率应超过100%
        
        print(f"✅ 高收益定投: 总收益率 {result.profit_percentage:.2f}%")
    
    def test_low_return_investment(self):
        """测试低收益定投（保守型）"""
        result = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=5000,
            expected_return=4,
            years=5
        )
        
        # 低收益情况下，收益仍然应该是正数
        assert result.total_profit > 0
        assert result.final_amount > result.total_principal
        
        print(f"✅ 低收益定投: 总收益 ¥{result.total_profit:,.2f}")
    
    def test_inflation_adjusted_return(self):
        """测试通胀调整后的实际收益"""
        result_no_inflation = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=1000,
            expected_return=8,
            years=10,
            inflation_rate=0
        )
        
        result_with_inflation = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=1000,
            expected_return=8,
            years=10,
            inflation_rate=0.03
        )
        
        # 扣除通胀后，名义收益率相同但实际购买力不同
        assert result_with_inflation.total_principal == result_no_inflation.total_principal
        
        print(f"✅ 通胀调整计算正常")
    
    def test_strategy_comparison(self):
        """测试策略对比功能"""
        comparison = InvestmentCalculator.compare_strategies(PREDEFINED_STRATEGIES)
        
        assert 'results' in comparison
        assert 'best_by_profit' in comparison
        assert 'chart_data' in comparison
        
        results = comparison['results']
        assert len(results) == len(PREDEFINED_STRATEGIES)
        
        best = comparison['best_by_profit']
        assert best in [s.name for s in PREDEFINED_STRATEGIES]
        
        chart_data = comparison['chart_data']
        assert len(chart_data['strategies']) == len(PREDEFINED_STRATEGIES)
        assert len(chart_data['final_amounts']) == len(PREDEFINED_STRATEGIES)
        
        print(f"✅ 策略对比完成: 最佳策略为「{best}」")
    
    def test_lump_sum_vs_dca(self):
        """测试一次性投入vs定投对比"""
        result = InvestmentCalculator.calculate_lump_sum_vs_dca(
            principal=240000,
            expected_return=10,
            years=10
        )
        
        assert 'lump_sum' in result
        assert 'dca' in result
        assert 'winner' in result
        assert 'difference' in result
        
        lump = result['lump_sum']
        dca = result['dca']
        
        assert lump.final_amount > 0
        assert dca.final_amount > 0
        assert result['winner'] in ['一次性投入', '定投']
        
        print(f"✅ 一次vs定投对比: {result['winner']}胜出，差额 ¥{result['difference']:+,.2f}")
    
    def test_compound_interest(self):
        """测试复利计算"""
        result = InvestmentCalculator.calculate_compound_interest(
            principal=100000,
            rate=8,
            times_per_year=12,  # 月复利
            years=10
        )
        
        assert isinstance(result, InvestmentResult)
        assert result.total_principal == 100000
        assert result.final_amount > 100000  # 复利增长
        assert result.profit_percentage > 0
        
        # 验证复利公式：A = P(1 + r/n)^(nt)
        P = 100000
        r = 0.08
        n = 12
        t = 10
        expected = P * (1 + r/n) ** (n*t)
        
        assert abs(result.final_amount - expected) < 0.01  # 允许微小误差
        
        print(f"✅ 复利计算: ¥{result.total_principal:,.2f} → ¥{result.final_amount:,.2f}")
    
    def test_compound_frequency_impact(self):
        """测试不同复利频率的影响"""
        annual = InvestmentCalculator.calculate_compound_interest(
            principal=10000, rate=10, times_per_year=1, years=5
        )
        quarterly = InvestmentCalculator.calculate_compound_interest(
            principal=10000, rate=10, times_per_year=4, years=5
        )
        monthly = InvestmentCalculator.calculate_compound_interest(
            principal=10000, rate=10, times_per_year=12, years=5
        )
        
        # 复利频率越高，最终金额越大
        assert monthly.final_amount > quarterly.final_amount
        assert quarterly.final_amount > annual.final_amount
        
        print(f"✅ 复利频率影响验证: 年<{quarterly.final_amount:.2f}<月<{monthly.final_amount:.2f}")
    
    def test_investment_advice_generation(self):
        """测试投资建议生成"""
        advice = InvestmentCalculator.generate_investment_advice(
            risk_tolerance='moderate',
            investment_goal='retirement',
            time_horizon=20
        )
        
        assert 'risk_profile' in advice
        'recommended_return_range' in advice
        'suggested_monthly_investment' in advice
        'asset_allocation' in advice
        'example_projection' in advice
        'tips' in advice
        
        projection = advice['example_projection']
        assert isinstance(projection, InvestmentResult)
        assert projection.total_principal > 0  # 验证有本金数据
        
        tips = advice['tips']
        assert len(tips) > 0
        
        print(f"✅ 投资建议生成正常: 建议月投 ¥{advice['suggested_monthly_investment']:,.0f}")
    
    def test_edge_case_zero_return(self):
        """测试零收益率边界情况"""
        result = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=1000,
            expected_return=0,
            years=5
        )
        
        # 零收益时，最终金额应等于本金
        assert abs(result.final_amount - result.total_principal) < 1.0
        
        print("✅ 零收益率边界情况处理正常")
    
    def test_short_term_investment(self):
        """测试短期投资（1年）"""
        result = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=5000,
            expected_return=6,
            years=1
        )
        
        assert result.total_principal == 60000  # 5000 * 12
        assert len(result.monthly_data) == 12
        
        print(f"✅ 短期投资(1年): 本金¥{result.total_principal:,.2f}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
