#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投计算器模块
提供专业的定投收益计算、策略对比、复利分析等功能
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import logger


@dataclass
class InvestmentResult:
    """投资结果数据"""
    total_principal: float  # 本金总额
    final_amount: float  # 最终资产（名义值）
    total_profit: float  # 总收益（名义值）
    profit_percentage: float  # 总收益率（名义值）
    annualized_return: float  # 年化收益率
    expected_return: float = 0.0  # 预期年化收益率（输入参数）
    inflation_rate: float = 0.03  # 通胀率
    inflation_adjusted_value: float = 0.0  # 通胀调整后的购买力
    real_profit: float = 0.0  # 实际收益（扣除通胀）
    real_return_rate: float = 0.0  # 实际收益率（扣除通胀）

    monthly_data: List[Dict[str, float]] = field(default_factory=list)  # 月度数据
    summary_text: str = ""  # 摘要文本


@dataclass
class InvestmentStrategy:
    """投资策略定义"""
    name: str  # 策略名称
    description: str  # 策略描述
    monthly_amount: float  # 每月投资金额
    years: int  # 投资年限
    expected_return: float  # 预期年化收益率
    inflation_rate: float = 0.03  # 通胀率（默认3%）
    
    def __post_init__(self):
        if self.inflation_rate is None:
            self.inflation_rate = 0.03


class InvestmentCalculator:
    """专业级定投计算器"""
    
    @staticmethod
    def calculate_fixed_investment(
        monthly_amount: float,
        expected_return: float,
        years: int,
        inflation_rate: float = 0.03,
        start_date: Optional[date] = None
    ) -> InvestmentResult:
        """
        计算定期定额投资（定投）的收益
        
        Args:
            monthly_amount: 每月定投金额（元）
            expected_return: 预期年化收益率（%）
            years: 投资年限
            inflation_rate: 年通胀率（%，默认3%）
            start_date: 开始日期，默认为今天
            
        Returns:
            InvestmentResult: 完整的投资结果
            
        Example:
            >>> result = InvestmentCalculator.calculate_fixed_investment(
            ...     monthly_amount=1000,
            ...     expected_return=10,
            ...     years=10
            ... )
            >>> print(f"最终资产: ¥{result.final_amount:,.2f}")
            >>> print(f"总收益率: {result.profit_percentage:.2f}%")
        """
        logger.info(
            f"计算定投: 月投¥{monthly_amount}, 收益率{expected_return}%, "
            f"期限{years}年, 通胀{inflation_rate}%"
        )
        
        if start_date is None:
            start_date = date.today()
        
        monthly_return = (expected_return / 100) / 12  # 月利率
        
        total_principal = 0.0
        current_value = 0.0
        monthly_data = []
        
        current_date = start_date
        for month in range(years * 12):
            # 本月投入本金
            total_principal += monthly_amount
            
            # 复利计算：每月投入的资金按剩余时间计算收益
            remaining_months = years * 12 - month - 1
            future_value = monthly_amount * (
                (1 + monthly_return) ** remaining_months
            ) if remaining_months > 0 else monthly_amount
            current_value += future_value / (1 + monthly_return)
            
            # 记录月度数据
            monthly_data.append({
                'month': month + 1,
                'date': current_date.isoformat(),
                'principal': round(total_principal, 2),
                'value': round(current_value, 2),
                'profit': round(current_value - total_principal, 2),
                'return_pct': round(
                    ((current_value - total_principal) / total_principal * 100)
                    if total_principal > 0 else 0, 2
                )
            })
            
            current_date += timedelta(days=30)
        
        final_amount = current_value
        total_profit = final_amount - total_principal
        profit_percentage = (total_profit / total_principal * 100) if total_principal > 0 else 0
        
        # 年化收益率（简化计算）
        annualized_return = (
            (final_amount / total_principal) ** (1 / years) - 1
        ) * 100 if total_principal > 0 and years > 0 else 0
        
        # 实际收益率（扣除通胀后）
        real_profit_pct = profit_percentage - (inflation_rate * years)

        # 计算通胀调整后的购买力
        # 公式：实际购买力 = 最终资产 / (1 + 通胀率)^年限
        inflation_factor = (1 + inflation_rate) ** years
        inflation_adjusted_value = final_amount / inflation_factor if inflation_factor > 0 else final_amount

        # 实际收益（扣除通胀）
        real_profit = inflation_adjusted_value - total_principal

        # 实际收益率
        real_return_rate = (real_profit / total_principal * 100) if total_principal > 0 else 0

        result = InvestmentResult(
            total_principal=round(total_principal, 2),
            final_amount=round(final_amount, 2),
            total_profit=round(total_profit, 2),
            profit_percentage=round(profit_percentage, 2),
            annualized_return=round(annualized_return, 2),
            expected_return=expected_return,
            inflation_rate=inflation_rate,
            inflation_adjusted_value=round(inflation_adjusted_value, 2),
            real_profit=round(real_profit, 2),
            real_return_rate=round(real_return_rate, 2),
            monthly_data=monthly_data
        )
        
        # 生成摘要文本
        result.summary_text = f"""
📊 定投计算结果
{'='*50}
💰 投入参数：
   • 每月定投：¥{monthly_amount:,.2f}
   • 投资年限：{years}年 ({years*12}个月)
   • 预期年化：{expected_return:.1f}%
   • 通胀率：{inflation_rate*100:.1f}%

💎 最终结果：
   • 累计本金：¥{total_principal:,.2f}
   • 最终资产：¥{final_amount:,.2f}
   • 💰 总收益：¥{total_profit:+,.2f}
   • 📈 总收益率：{profit_percentage:+.2f}%
   • 📊 年化收益：{annualized_return:.2f}%
   • ✅ 实际收益（扣除通胀）：{real_profit_pct:+.2f}%

🔍 关键指标：
   • 盈利倍数：{final_amount/total_principal:.2f}x
   • 平均月收益：¥{total_profit/(years*12):+,.2f}
"""
        
        logger.info(f"定投计算完成: 最终资产 ¥{final_amount:,.2f}, 收益率 {profit_percentage:.2f}%")
        
        return result
    
    @staticmethod
    def compare_strategies(
        strategies: List[InvestmentStrategy]
    ) -> Dict[str, Any]:
        """
        对比多种投资策略
        
        Args:
            strategies: 投资策略列表
            
        Returns:
            包含对比结果的字典：
            - results: 各策略的计算结果
            - best_by_profit: 收益最高的策略
            - best_by_risk_adjusted: 风险调整后最优策略
            - comparison_chart_data: 图表数据
        """
        logger.info(f"对比 {len(strategies)} 种投资策略...")
        
        results = {}
        for strategy in strategies:
            results[strategy.name] = InvestmentCalculator.calculate_fixed_investment(
                monthly_amount=strategy.monthly_amount,
                expected_return=strategy.expected_return,
                years=strategy.years,
                inflation_rate=strategy.inflation_rate
            )
        
        # 找出收益最高的策略
        best_by_profit = max(results.items(), key=lambda x: x[1].total_profit)[0] if results else ""
        
        # 风险调整后收益（简化版夏普比率）
        best_risk_adjusted = max(
            results.items(),
            key=lambda x: x[1].annualized_return / abs(x[1].expected_return) 
            if x[1].expected_return != 0 else 0
        )[0] if results else ""
        
        comparison_data = {
            'results': results,
            'best_by_profit': best_by_profit,
            'best_by_risk_adjusted': best_risk_adjusted,
            
            # 用于图表的数据
            'chart_data': {
                'strategies': list(results.keys()),
                'final_amounts': [r.final_amount for r in results.values()],
                'profits': [r.total_profit for r in results.values()],
                'returns': [r.profit_percentage for r in results.values()]
            }
        }
        
        return comparison_data
    
    @staticmethod
    def calculate_lump_sum_vs_dca(
        principal: float,
        expected_return: float,
        years: int,
        dca_months: int = 12
    ) -> Dict[str, InvestmentResult]:
        """
        对比一次性投入 vs 定投（Dollar Cost Averaging）
        
        Args:
            principal: 总投入金额
            expected_return: 预期年化收益率（%）
            years: 投资年限
            dca_months: 定投分多少个月投入
            
        Returns:
            {'lump_sum': ..., 'dca': ...}
        """
        logger.info(f"对比一次性投入vs定投: 本金¥{principal}")
        
        # 一次性投入
        lump_sum_result = InvestmentResult(
            total_principal=principal,
            final_amount=principal * (1 + expected_return/100) ** years,
            total_profit=principal * ((1 + expected_return/100) ** years - 1),
            profit_percentage=((1 + expected_return/100) ** years - 1) * 100,
            annualized_return=expected_return,
            expected_return=expected_return
        )
        
        # 定投方式
        monthly_amount = principal / dca_months
        dca_years = years  # 假设同样长的投资周期
        dca_result = InvestmentCalculator.calculate_fixed_investment(
            monthly_amount=monthly_amount,
            expected_return=expected_return,
            years=dca_years
        )
        
        return {
            'lump_sum': lump_sum_result,
            'dca': dca_result,
            'difference': lump_sum_result.final_amount - dca_result.final_amount,
            'winner': '一次性投入' if lump_sum_result.final_amount > dca_result.final_amount else '定投'
        }
    
    @staticmethod
    def generate_investment_advice(
        risk_tolerance: str,  # conservative/moderate/aggressive
        investment_goal: str,  # retirement/education/emergency/wealth
        time_horizon: int,  # 投资年限
        initial_capital: float = 0
    ) -> Dict[str, Any]:
        """
        根据用户情况生成投资建议
        
        Args:
            risk_tolerance: 风险承受能力
            investment_goal: 投资目标
            time_horizon: 投资年限
            initial_capital: 初始资金
            
        Returns:
            投资建议字典
        """
        logger.info(
            f"生成投资建议: 风险={risk_tolerance}, 目标={investment_goal}, "
            f"期限={time_horizon}年"
        )
        
        # 根据风险偏好确定预期收益率范围
        risk_returns = {
            'conservative': (4, 8),      # 保守型：4%-8%
            'moderate': (6, 12),         # 稳健型：6%-12%
            'aggressive': (10, 20)       # 激进型：10%-20%
        }
        
        min_ret, max_ret = risk_returns.get(risk_tolerance, (6, 12))
        recommended_return = (min_ret + max_ret) / 2
        
        # 根据目标确定建议配置
        goal_configs = {
            'retirement': {
                'stock_allocation': 80 if time_horizon > 15 else 60,
                'bond_allocation': 20 if time_horizon > 15 else 40,
                'suggested_monthly': 5000,
                'description': '养老储备需要长期坚持，建议提高权益类资产比例'
            },
            'education': {
                'stock_allocation': 60 if time_horizon > 5 else 40,
                'bond_allocation': 40 if time_horizon > 5 else 60,
                'suggested_monthly': 3000,
                'description': '教育金需注意流动性，临近用钱时降低风险'
            },
            'emergency': {
                'stock_allocation': 20,
                'bond_allocation': 80,
                'suggested_monthly': 2000,
                'description': '应急资金首要考虑安全性和流动性'
            },
            'wealth': {
                'stock_allocation': 90 if time_horizon > 10 else 70,
                'bond_allocation': 10 if time_horizon > 10 else 30,
                'suggested_monthly': 8000,
                'description': '财富增值可承受较高波动，追求长期高收益'
            }
        }
        
        config = goal_configs.get(investment_goal, goal_configs['wealth'])
        
        advice = {
            'risk_profile': risk_tolerance,
            'recommended_return_range': (min_ret, max_ret),
            'suggested_monthly_investment': config['suggested_monthly'],
            'asset_allocation': {
                'equity': config['stock_allocation'],
                'fixed_income': config['bond_allocation']
            },
            'strategy_description': config['description'],
            
            # 示例计算
            'example_projection': InvestmentCalculator.calculate_fixed_investment(
                monthly_amount=config['suggested_monthly'],
                expected_return=recommended_return,
                years=time_horizon
            ),
            
            'tips': [
                "✅ 坚持长期投资，避免频繁操作",
                "✅ 定期复盘，适时再平衡",
                "✅ 分散投资降低单一风险",
                "✅ 保持应急资金3-6个月生活费",
                "✅ 根据市场变化动态调整"
            ]
        }
        
        return advice
    
    @staticmethod
    def calculate_compound_interest(
        principal: float,
        rate: float,
        times_per_year: int,
        years: int
    ) -> InvestmentResult:
        """
        计算复利收益
        
        公式: A = P(1 + r/n)^(nt)
        
        Args:
            principal: 本金
            rate: 年利率（%）
            times_per_year: 每年复利次数（12=月复利，4=季复利，1=年复利）
            years: 年限
            
        Returns:
            InvestmentResult
        """
        r = rate / 100
        n = times_per_year
        t = years
        
        final_amount = principal * (1 + r/n) ** (n*t)
        total_profit = final_amount - principal
        profit_percentage = (total_profit / principal * 100) if principal > 0 else 0
        annualized_return = rate  # 复利情况下年化就是给定利率
        
        return InvestmentResult(
            total_principal=principal,
            final_amount=round(final_amount, 2),
            total_profit=round(total_profit, 2),
            profit_percentage=round(profit_percentage, 2),
            annualized_return=round(annualized_return, 2)
        )


# 预定义的常用策略示例
PREDEFINED_STRATEGIES = [
    InvestmentStrategy(
        name="保守型定投",
        description="低风险稳健增长，适合保守投资者",
        monthly_amount=2000,
        years=10,
        expected_return=6,
        inflation_rate=0.03
    ),
    InvestmentStrategy(
        name="平衡型定投",
        description="中等风险收益均衡，适合大多数投资者",
        monthly_amount=3000,
        years=10,
        expected_return=10,
        inflation_rate=0.03
    ),
    InvestmentStrategy(
        name="进取型定投",
        description="高风险高收益，适合年轻激进投资者",
        monthly_amount=3000,
        years=10,
        expected_return=15,
        inflation_rate=0.03
    ),
    InvestmentStrategy(
        name="智能定投(低点多买)",
        description="模拟市场波动，低点加大投入",
        monthly_amount=2500,
        years=10,
        expected_return=12,
        inflation_rate=0.03
    )
]
