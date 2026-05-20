#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金表格组件
提供基金数据展示、排序、交互等功能
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QMenu, QTableWidget, QTableWidgetItem)

from utils.logger import logger


class PercentageItem(QTableWidgetItem):
    """用于百分比排序的表格项"""

    def __lt__(self, other):
        try:
            return float(
                self.text().strip('%')) < float(
                other.text().strip('%'))
        except ValueError:
            return super().__lt__(other)


class NumericItem(QTableWidgetItem):
    """用于数字排序的表格项"""

    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class FundTableWidget(QTableWidget):
    """基金表格组件"""

    def __init__(self, parent_monitor=None):
        super().__init__()
        self.parent_monitor = parent_monitor
        self.setup_ui()
        self.fund_history = {}

    def setup_ui(self):
        self.setColumnCount(14)
        self.setHorizontalHeaderLabels(
            ['基金代码', '基金名称', '估算时间', '估算涨跌%', '估算值', '单位净值', '日期',
             '持仓成本价', '持有份额', '持仓成本', '持有金额', '当日盈亏', '累计盈亏', '盈亏%'])
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                gridline-color: transparent;
                border: none;
                border-radius: 8px;
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f1f5f9;
                background: #ffffff;
            }
            QTableWidget::item:alternate {
                background: #f8fafc;
            }
            QTableWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QTableWidget::item:hover {
                background: #e0e7ff;
                color: #1e293b;
            }
            QTableWidget::item:selected:hover {
                background: #2563eb;
                color: white;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #475569;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background: #e2e8f0;
                color: #1e293b;
            }
            QScrollBar:vertical {
                background: #f8fafc;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Interactive)
        self.setColumnWidth(0, 90)
        header.setSectionResizeMode(1, header.ResizeMode.Interactive)
        self.setColumnWidth(1, 200)
        header.setSectionResizeMode(2, header.ResizeMode.Interactive)
        self.setColumnWidth(2, 100)
        for i in range(3, self.columnCount()):
            header.setSectionResizeMode(i, header.ResizeMode.Interactive)
            if i == 3:
                self.setColumnWidth(i, 80)
            elif i == 4:
                self.setColumnWidth(i, 80)
            elif i == 5:
                self.setColumnWidth(i, 80)
            elif i == 6:
                self.setColumnWidth(i, 100)
            elif i == 7:
                self.setColumnWidth(i, 100)
            elif i == 8:
                self.setColumnWidth(i, 100)
            elif i == 9:
                self.setColumnWidth(i, 100)
            elif i == 10:
                self.setColumnWidth(i, 100)
            elif i == 11:
                self.setColumnWidth(i, 100)
            elif i == 12:
                self.setColumnWidth(i, 100)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        if item is not None:
            row = item.row()
            code_item = self.item(row, 0)
            if code_item:
                fund_code = code_item.text()

                parent_widget = self.parent()
                while parent_widget and not isinstance(
                        parent_widget, FundMonitor):
                    parent_widget = parent_widget.parent()

                if parent_widget and isinstance(parent_widget, FundMonitor):
                    is_monitored = fund_code in parent_widget.monitored_codes

                    menu = QMenu()

                    if is_monitored:
                        remove_action = menu.addAction("删除基金监控")
                        menu.addSeparator()
                        cost_price_action = menu.addAction("设置持仓成本价")
                        shares_action = menu.addAction("设置持有份额")
                        dividend_action = menu.addAction("记录分红")

                        action = menu.exec(self.mapToGlobal(position))

                        if action == remove_action:
                            parent_widget.remove_specific_fund(fund_code)
                        elif action == cost_price_action:
                            parent_widget.set_fund_cost_price(fund_code)
                        elif action == shares_action:
                            parent_widget.set_fund_shares(fund_code)
                        elif action == dividend_action:
                            parent_widget.record_dividend(fund_code)
                    else:
                        add_action = menu.addAction("添加基金监控")

                        action = menu.exec(self.mapToGlobal(position))

                        if action == add_action:
                            parent_widget.add_fund_to_monitor(fund_code)
        else:
            parent_widget = self.parent()
            while parent_widget and not isinstance(parent_widget, FundMonitor):
                parent_widget = parent_widget.parent()

            if parent_widget and isinstance(parent_widget, FundMonitor):
                menu = QMenu()
                add_new_fund_action = menu.addAction("添加新基金")
                menu.addSeparator()

                column_menu = menu.addMenu("显示/隐藏列")
                for col in range(self.columnCount()):
                    header_text = self.horizontalHeaderItem(col).text()
                    is_hidden = self.isColumnHidden(col)
                    action_text = f"{'✓' if not is_hidden else '✗'} {header_text}"
                    col_action = column_menu.addAction(action_text)
                    col_action.triggered.connect(
                        lambda c=col: self.toggle_column_visibility(c))

                action = menu.exec(self.mapToGlobal(position))

                if action == add_new_fund_action:
                    parent_widget.show_add_fund_dialog()

    def toggle_column_visibility(self, column: int):
        """切换列的可见性

        Args:
            column: 列索引
        """
        if self.isColumnHidden(column):
            self.showColumn(column)
        else:
            self.hideColumn(column)

    def update_data(self, fund_data):
        self.setSortingEnabled(False)
        self.setRowCount(0)

        total_profit = 0.0
        total_daily_profit = 0.0
        total_position_cost = 0.0
        total_current_value = 0.0

        for code, fund in fund_data.items():
            row_idx = self.rowCount()
            self.insertRow(row_idx)

            code_item = QTableWidgetItem(code)
            self.setItem(row_idx, 0, code_item)

            name_item = QTableWidgetItem(fund.get('name', ''))
            self.setItem(row_idx, 1, name_item)

            gztime_item = QTableWidgetItem(fund.get('gztime', ''))
            self.setItem(row_idx, 2, gztime_item)

            gszzl = fund.get('gszzl', '0')
            gszzl_item = PercentageItem(f"{gszzl}%")
            gszzl_val = float(gszzl)
            if gszzl_val > 0:
                gszzl_item.setForeground(QColor(255, 0, 0))
            elif gszzl_val < 0:
                gszzl_item.setForeground(QColor(0, 128, 0))
            self.setItem(row_idx, 3, gszzl_item)

            gsz = fund.get('gsz', '')
            gsz_item = NumericItem(gsz)
            self.setItem(row_idx, 4, gsz_item)

            dwjz = fund.get('dwjz', '')
            dwjz_item = NumericItem(dwjz)
            self.setItem(row_idx, 5, dwjz_item)

            jzrq_item = QTableWidgetItem(fund.get('jzrq', ''))
            self.setItem(row_idx, 6, jzrq_item)

            cost_price = 0.0
            shares = 0.0
            holdings_amount = 0.0

            if self.parent_monitor:
                cost_price, shares, holdings_amount = self.parent_monitor.get_fund_holdings_detail(
                    code)

            cost_price_item = NumericItem(
                f"{cost_price:.4f}" if cost_price > 0 else "0.0000")
            self.setItem(row_idx, 7, cost_price_item)

            shares_item = NumericItem(
                f"{shares:.2f}" if shares > 0 else "0.00")
            self.setItem(row_idx, 8, shares_item)

            position_cost = cost_price * shares
            position_cost_item = NumericItem(f"{position_cost:.2f}")
            self.setItem(row_idx, 9, position_cost_item)

            current_value = 0.0
            try:
                gsz_val = float(gsz) if gsz else 0.0
                current_value = gsz_val * shares
            except Exception:
                pass

            holdings_item = NumericItem(f"{current_value:.2f}")
            self.setItem(row_idx, 10, holdings_item)

            daily_profit = current_value * gszzl_val / 100
            daily_profit_item = NumericItem(f"{daily_profit:.2f}")
            if daily_profit > 0:
                daily_profit_item.setForeground(QColor(255, 0, 0))
            elif daily_profit < 0:
                daily_profit_item.setForeground(QColor(0, 128, 0))
            self.setItem(row_idx, 11, daily_profit_item)

            dividend = 0.0
            if self.parent_monitor:
                dividend = self.parent_monitor.get_fund_dividend(code)

            total_profit_loss = current_value - position_cost + dividend
            profit_loss_item = NumericItem(f"{total_profit_loss:.2f}")
            if total_profit_loss > 0:
                profit_loss_item.setForeground(QColor(255, 0, 0))
            elif total_profit_loss < 0:
                profit_loss_item.setForeground(QColor(0, 128, 0))
            self.setItem(row_idx, 12, profit_loss_item)

            if position_cost > 0:
                profit_percentage = (total_profit_loss / position_cost) * 100
            else:
                profit_percentage = 0.0
            
            profit_pct_item = PercentageItem(f"{profit_percentage:.2f}%")
            if profit_percentage > 0:
                profit_pct_item.setForeground(QColor(255, 0, 0))
            elif profit_percentage < 0:
                profit_pct_item.setForeground(QColor(0, 128, 0))
            self.setItem(row_idx, 13, profit_pct_item)

            total_profit += total_profit_loss
            total_daily_profit += daily_profit
            total_position_cost += position_cost
            total_current_value += current_value

        self.setSortingEnabled(True)
        self.sortItems(3, Qt.DescendingOrder)

        if self.parent_monitor:
            self.parent_monitor.update_total_profit(
                total_profit, total_daily_profit, total_position_cost, total_current_value)

