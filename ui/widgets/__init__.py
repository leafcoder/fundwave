#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件模块
提供表格、搜索、仪表盘、计算器等UI组件
"""

from ui.widgets.dividend_history_dialog import DividendHistoryDialog
from ui.widgets.investment_calculator_dialog import InvestmentCalculatorDialog
from ui.widgets.portfolio_dashboard import PortfolioDashboard
from ui.widgets.search_widget import FundSearchWidget
from ui.widgets.table_widget import (FundTableWidget, NumericItem,
                                     PercentageItem)

__all__ = [
    'FundTableWidget', 'PercentageItem', 'NumericItem',
    'FundSearchWidget',
    'PortfolioDashboard', 'InvestmentCalculatorDialog',
    'DividendHistoryDialog'
]
