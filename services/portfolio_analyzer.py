#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合分析模块
提供专业的投资组合分析、风险评估、收益归因等功能
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import logger


@dataclass
class FundHolding:
    """基金持仓数据"""
    fund_code: str
    fund_name: str
    fund_type: str  # 股票型/债券型/混合型/指数型/QDII
    cost_price: float
    shares: float
    current_value: float
    daily_profit: float
    total_profit: float
    dividend: float
    profit_percentage: float = 0.0  # 收益率百分比（计算得出）


@dataclass
class RiskMetrics:
    """风险指标"""
    volatility: float  # 波动率（标准差）
    max_drawdown: float  # 最大回撤
    sharpe_ratio: float  # 夏普比率
    beta: float  # Beta系数
    alpha: float  # Alpha系数
    var_95: float  # 95% VaR (Value at Risk)
    

@dataclass
class AllocationData:
    """资产配置数据"""
    category: str  # 配置类别
    value: float  # 金额
    percentage: float  # 百分比
    color: str  # 显示颜色


@dataclass
class PortfolioReport:
    """投资组合分析报告"""
    total_assets: float  # 总资产
    total_cost: float  # 总成本
    total_profit: float  # 总盈亏
    profit_percentage: float  # 总收益率
    daily_profit: float  # 当日盈亏
    
    risk_metrics: RiskMetrics  # 风险指标
    
    allocations: List[AllocationData]  # 资产配置（按类型）
    top_holdings: List[FundHolding]  # 持仓TOP5
    worst_performers: List[FundHolding]  # 表现最差的3只
    
    sector_allocation: Dict[str, float]  # 行业配置（如果有数据）
    
    performance_vs_benchmark: Dict[str, Any]  # 与基准对比
    profit_attribution: Dict[str, Tuple[float, float]]  # 收益归因


class PortfolioAnalyzer:
    """投资组合分析器 - 专业级分析引擎"""
    
    def __init__(self):
        self.historical_returns = []  # 历史收益率序列（用于计算风险指标）
        
    def analyze_portfolio(
        self,
        holdings: List[Dict[str, Any]],
        benchmark_return: Optional[float] = None
    ) -> PortfolioReport:
        """
        分析投资组合，生成专业报告
        
        Args:
            holdings: 持仓列表，每个元素包含：
                - fund_code: 基金代码
                - fund_name: 基金名称
                - cost_price: 成本价
                - shares: 份额
                - current_value: 当前价值
                - daily_profit: 当日盈亏
                - total_profit: 累计盈亏
                - dividend: 分红
                
            benchmark_return: 基准指数收益率（可选）
            
        Returns:
            PortfolioReport: 完整的分析报告
        """
        logger.info("开始分析投资组合...")
        
        fund_objects = [
            FundHolding(
                fund_code=h.get('fund_code', ''),
                fund_name=h.get('fund_name', ''),
                fund_type=self._classify_fund_type(h.get('fund_name', '')),
                cost_price=h.get('cost_price', 0),
                shares=h.get('shares', 0),
                current_value=h.get('current_value', 0),
                daily_profit=h.get('daily_profit', 0),
                total_profit=h.get('total_profit', 0),
                dividend=h.get('dividend', 0),
                profit_percentage=0.0  # 将在后面计算
            )
            for h in holdings
        ]
        
        # 计算每只基金的收益率
        for f in fund_objects:
            position_cost = f.cost_price * f.shares
            if position_cost > 0:
                f.profit_percentage = (f.total_profit / position_cost) * 100
            else:
                f.profit_percentage = 0.0
        
        report = PortfolioReport(
            total_assets=sum(h.current_value for h in fund_objects if h.current_value > 0),
            total_cost=sum(h.cost_price * h.shares for h in fund_objects),
            total_profit=sum(h.total_profit for h in fund_objects),
            daily_profit=sum(h.daily_profit for h in fund_objects),
            profit_percentage=0.0,  # 将在后面计算
            
            risk_metrics=self._calculate_risk_metrics(fund_objects),
            allocations=self._calculate_allocations(fund_objects),
            top_holdings=sorted(fund_objects, key=lambda x: x.current_value, reverse=True)[:5],
            worst_performers=sorted(fund_objects, key=lambda x: x.profit_percentage)[:3],
            
            sector_allocation={},  # 暂不实现行业配置
            performance_vs_benchmark={},  # 暂不实现基准对比
            profit_attribution={}  # 将在后面填充
        )
        
        # 计算总收益率
        if report.total_cost > 0:
            report.profit_percentage = (report.total_profit / report.total_cost) * 100
        else:
            report.profit_percentage = 0.0
        
        # 收益归因分析
        report.profit_attribution = self._analyze_profit_contribution(fund_objects)
        
        # 基准对比
        if benchmark_return is not None:
            report.performance_vs_benchmark = {
                'portfolio_return': report.profit_percentage,
                'benchmark_return': benchmark_return,
                'excess_return': report.profit_percentage - benchmark_return,
                'is_outperforming': report.profit_percentage > benchmark_return
            }
        
        logger.info(f"投资组合分析完成: 总资产 ¥{report.total_assets:.2f}, 盈亏 {report.total_profit:+.2f}")
        
        return report
    
    def _classify_fund_type(self, fund_name: str) -> str:
        """根据基金名称简单分类基金类型"""
        name_lower = fund_name.lower()
        
        type_keywords = {
            '股票': ['股票', '成长', '价值', '蓝筹', '中小盘'],
            '债券': ['债券', '纯债', '信用', '利率'],
            '混合': ['混合', '配置', '灵活', '平衡'],
            '指数': ['指数', 'ETF', '沪深', '中证', '创业板'],
            'QDII': ['QDII', '海外', '美股', '港股', '全球'],
            '货币': ['货币', '理财', '现金']
        }
        
        for fund_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return fund_type
        
        return '其他'
    
    def _calculate_risk_metrics(self, holdings: List[FundHolding]) -> RiskMetrics:
        """计算风险指标"""
        if not holdings or len(holdings) < 2:
            return RiskMetrics(0, 0, 0, 0, 0, 0)
        
        returns = []
        for h in holdings:
            if h.cost_price > 0 and h.shares > 0:
                position_cost = h.cost_price * h.shares
                if position_cost > 0:
                    ret = (h.total_profit / position_cost) * 100
                    returns.append(ret)
        
        if len(returns) < 2:
            return RiskMetrics(0, 0, 0, 0, 0, 0)
        
        mean_return = sum(returns) / len(returns)
        
        # 波动率（标准差）
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        volatility = math.sqrt(variance)
        
        # 最大回撤（简化版：基于当前数据估算）
        max_loss = min(returns) if returns else 0
        max_drawdown = abs(max_loss) if max_loss < 0 else 0
        
        # 夏普比率（假设无风险利率为3%）
        risk_free_rate = 3.0
        excess_returns = [r - risk_free_rate for r in returns]
        avg_excess = sum(excess_returns) / len(excess_returns) if excess_returns else 0
        sharpe_ratio = avg_excess / volatility if volatility > 0 else 0
        
        # Beta和Alpha（简化计算）
        beta = volatility / 15.0 if volatility > 0 else 1.0  # 假设市场波动率为15%
        alpha = mean_return - (risk_free_rate + beta * (12.0 - risk_free_rate))  # 假设市场收益12%
        
        # VaR 95% (简化：使用正态分布近似)
        var_95 = -(mean_return - 1.65 * volatility) if volatility > 0 else 0
        
        return RiskMetrics(
            volatility=round(volatility, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            beta=round(beta, 2),
            alpha=round(alpha, 2),
            var_95=round(var_95, 2)
        )
    
    def _calculate_allocations(self, holdings: List[FundHolding]) -> List[AllocationData]:
        """计算资产配置（按基金类型）"""
        total_value = sum(h.current_value for h in holdings if h.current_value > 0)
        
        if total_value == 0:
            return []
        
        type_values = {}
        for h in holdings:
            if h.fund_type not in type_values:
                type_values[h.fund_type] = 0
            type_values[h.fund_type] += h.current_value
        
        colors = {
            '股票': '#ef4444',
            '债券': '#3b82f6',
            '混合': '#f59e0b',
            '指数': '#10b981',
            'QDII': '#8b5cf6',
            '货币': '#6b7280',
            '其他': '#94a3b8'
        }
        
        allocations = []
        for fund_type, value in sorted(type_values.items(), key=lambda x: x[1], reverse=True):
            percentage = (value / total_value) * 100
            allocations.append(AllocationData(
                category=fund_type,
                value=value,
                percentage=round(percentage, 2),
                color=colors.get(fund_type, '#94a3b8')
            ))
        
        return allocations
    
    def _analyze_profit_contribution(self, holdings: List[FundHolding]) -> Dict[str, Tuple[float, float]]:
        """分析各基金的收益贡献"""
        contribution = {}
        total_profit = sum(h.total_profit for h in holdings)
        
        for h in holdings:
            abs_contribution = abs(h.total_profit)
            pct_contribution = (abs_contribution / total_profit * 100) if total_profit != 0 else 0
            contribution[h.fund_code] = (
                round(abs_contribution, 2),
                round(pct_contribution, 2)
            )
        
        return dict(sorted(contribution.items(), key=lambda x: x[1][0], reverse=True))
    
    def generate_summary_text(self, report: PortfolioReport) -> str:
        """生成人类可读的摘要文本"""
        lines = []
        lines.append("=" * 60)
        lines.append("📊 投资组合分析报告")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"💰 总资产: ¥{report.total_assets:,.2f}")
        lines.append(f"📈 总成本: ¥{report.total_cost:,.2f}")
        lines.append(f"{'🔴' if report.total_profit >= 0 else '🟢'} 累计盈亏: ¥{report.total_profit:+,.2f} ({report.profit_percentage:+.2f}%)")
        lines.append(f"{'🔴' if report.daily_profit >= 0 else '🟢'} 今日盈亏: ¥{report.daily_profit:+,.2f}")
        lines.append("")
        
        lines.append("⚠️ 风险指标:")
        lines.append(f"   波动率: {report.risk_metrics.volatility:.2f}%")
        lines.append(f"   最大回撤: {report.risk_metrics.max_drawdown:.2f}%")
        lines.append(f"   夏普比率: {report.risk_metrics.sharpe_ratio:.2f}")
        lines.append(f"   Beta系数: {report.risk_metrics.beta:.2f}")
        lines.append(f"   Alpha: {report.risk_metrics.alpha:+.2f}")
        lines.append("")
        
        if report.allocations:
            lines.append("🥧 资产配置:")
            for alloc in report.allocations:
                bar = "█" * int(alloc.percentage / 5) + "░" * (20 - int(alloc.percentage / 5))
                lines.append(f"   {alloc.category:6s}: {bar} {alloc.percentage:5.1f}% (¥{alloc.value:,.2f})")
            lines.append("")
        
        if report.top_holdings:
            lines.append("🏆 TOP5持仓:")
            for i, h in enumerate(report.top_holdings[:5], 1):
                pct = ((h.total_profit / (h.cost_price * h.shares)) * 100) if (h.cost_price * h.shares) > 0 else 0
                lines.append(f"   {i}. {h.fund_name:12s} | 金额:¥{h.current_value:>10,.2f} | 收益:{pct:>+6.2f}%")
            lines.append("")
        
        if report.performance_vs_benchmark:
            perf = report.performance_vs_benchmark
            status = "跑赢基准 🎉" if perf['is_outperforming'] else "落后基准 ⚠️"
            lines.append(f"📊 基准对比 ({status}):")
            lines.append(f"   组合收益: {perf['portfolio_return']:.2f}%")
            lines.append(f"   基准收益: {perf['benchmark_return']:.2f}%")
            lines.append(f"   超额收益: {perf['excess_return']:+.2f}%")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
