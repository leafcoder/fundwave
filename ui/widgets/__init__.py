#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI组件模块
提供表格、搜索、详情等UI组件
"""

from ui.widgets.dividend_history_dialog import DividendHistoryDialog
from ui.widgets.floating_profit_widget import FloatingProfitWidget
from ui.widgets.fund_detail_dialog import FundDetailDialog
from ui.widgets.search_widget import FundSearchWidget
from ui.widgets.table_widget import (FundTableWidget, NumericItem,
                                     PercentageItem)

__all__ = [
    'FundTableWidget', 'PercentageItem', 'NumericItem',
    'FundSearchWidget', 'FloatingProfitWidget',
    'DividendHistoryDialog', 'FundDetailDialog'
]
