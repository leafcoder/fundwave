#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金表格组件
提供基金数据展示、排序、交互等功能
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMenu, QTableWidget, QTableWidgetItem

from ui.theme.professional_theme import ProfessionalTheme
from utils.logger import logger

if TYPE_CHECKING:
    from ui.main_window import FundMonitor
else:
    try:
        from ui.main_window import FundMonitor
    except ImportError:
        FundMonitor = None  # 运行时延迟导入或使用字符串检查


class PercentageItem(QTableWidgetItem):
    """用于百分比排序的表格项"""

    def __lt__(self, other):
        try:
            def parse_percentage(text):
                text = text.replace('↑', '').replace('↓', '').replace('%', '').strip()
                if text.startswith('+'):
                    text = text[1:]
                return float(text)

            return parse_percentage(self.text()) < parse_percentage(other.text())
        except ValueError:
            return super().__lt__(other)


class NumericItem(QTableWidgetItem):
    """用于数字排序的表格项"""

    def __lt__(self, other):
        try:
            def parse_numeric(text):
                text = text.replace('¥', '').replace(',', '').replace('+', '').strip()
                return float(text)

            return parse_numeric(self.text()) < parse_numeric(other.text())
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
        """设置表格UI"""
        self.setColumnCount(10)
        self.setHorizontalHeaderLabels(
            ['基金代码', '基金名称', '估算涨跌', '估算净值', '单位净值',
             '持仓成本', '持有金额', '当日盈亏', '累计盈亏', '盈亏比例'])
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # 应用专业主题样式
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {ProfessionalTheme.BG_PRIMARY};
                alternate-background-color: {ProfessionalTheme.BG_SECONDARY};
                gridline-color: {ProfessionalTheme.BORDER_LIGHT};
                border: none;
                border-radius: {ProfessionalTheme.RADIUS_MEDIUM}px;
                font-family: {ProfessionalTheme.FONT_FAMILY};
                font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
                selection-background-color: {ProfessionalTheme.PRIMARY_BG};
                selection-color: {ProfessionalTheme.PRIMARY_DARK};
            }}
            QTableWidget::item {{
                padding: {ProfessionalTheme.SPACING_SM}px {ProfessionalTheme.SPACING_MD}px;
                border: none;
                border-bottom: 1px solid {ProfessionalTheme.BORDER_LIGHT};
                background: {ProfessionalTheme.BG_PRIMARY};
            }}
            QTableWidget::item:alternate {{
                background: {ProfessionalTheme.BG_SECONDARY};
            }}
            QTableWidget::item:selected {{
                background: {ProfessionalTheme.PRIMARY_BG};
                color: {ProfessionalTheme.PRIMARY_DARK};
            }}
            QTableWidget::item:hover {{
                background: {ProfessionalTheme.PRIMARY_BG};
                color: {ProfessionalTheme.PRIMARY_COLOR};
            }}
            QTableWidget::item:selected:hover {{
                background: {ProfessionalTheme.PRIMARY_LIGHT};
                color: white;
            }}
            QHeaderView::section {{
                background: {ProfessionalTheme.BG_SECONDARY};
                color: {ProfessionalTheme.TEXT_SECONDARY};
                padding: {ProfessionalTheme.SPACING_MD}px {ProfessionalTheme.SPACING_SM}px;
                border: none;
                border-bottom: 1px solid {ProfessionalTheme.BORDER_COLOR};
                font-weight: {ProfessionalTheme.FONT_WEIGHT_SEMI_BOLD};
                font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
            }}
            QHeaderView::section:hover {{
                background: {ProfessionalTheme.BG_HOVER};
                color: {ProfessionalTheme.TEXT_PRIMARY};
            }}
            {ProfessionalTheme.get_scrollbar_style()}
        """)

        # 设置列宽
        header = self.horizontalHeader()
        column_widths = [
            (0, 100),   # 基金代码
            (1, 180),   # 基金名称
            (2, 110),   # 估算涨跌
            (3, 100),   # 估算净值
            (4, 100),   # 单位净值
            (5, 130),   # 持仓成本
            (6, 130),   # 持有金额
            (7, 120),   # 当日盈亏
            (8, 120),   # 累计盈亏
        ]
        for col, width in column_widths:
            header.setSectionResizeMode(col, header.ResizeMode.Interactive)
            self.setColumnWidth(col, width)
        # 最后一列自动拉伸
        header.setSectionResizeMode(9, header.ResizeMode.Stretch)

        # 设置列对齐
        self._setup_column_alignment()

    def _setup_column_alignment(self):
        """设置表头对齐方式"""
        header = self.horizontalHeader()
        # 基金代码居中
        header_item = self.horizontalHeaderItem(0)
        if header_item:
            header_item.setTextAlignment(Qt.AlignCenter)
        # 基金名称左对齐
        header_item = self.horizontalHeaderItem(1)
        if header_item:
            header_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # 数字列右对齐
        for col in range(2, 10):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _format_money(self, value: float, show_sign: bool = False) -> str:
        """格式化金额，加¥前缀和千分位

        Args:
            value: 金额数值
            show_sign: 是否显示正负号

        Returns:
            格式化后的字符串，如 ¥12,345.67 或 -¥1,234.56
        """
        if show_sign:
            if value > 0:
                return f"+¥{value:,.2f}"
            elif value < 0:
                return f"-¥{abs(value):,.2f}"
            else:
                return f"¥{value:,.2f}"
        else:
            return f"¥{value:,.2f}"

    def _get_rise_color(self) -> QColor:
        """获取涨色（红色）"""
        return QColor(ProfessionalTheme.RISE_COLOR)

    def _get_fall_color(self) -> QColor:
        """获取跌色（绿色）"""
        return QColor(ProfessionalTheme.FALL_COLOR)

    def _get_flat_color(self) -> QColor:
        """获取平色（灰色）"""
        return QColor(ProfessionalTheme.FLAT_COLOR)

    def on_cell_double_clicked(self, row: int, column: int):
        """处理单元格双击事件，打开基金详情"""
        try:
            code_item = self.item(row, 0)
            if code_item:
                fund_code = code_item.text()

                parent_widget = self.parent()
                while parent_widget:
                    if FundMonitor is not None and isinstance(parent_widget, FundMonitor):
                        break
                    elif hasattr(parent_widget, 'monitored_codes') and hasattr(parent_widget, 'show_fund_detail'):
                        break
                    parent_widget = parent_widget.parent()

                if parent_widget and hasattr(parent_widget, 'show_fund_detail'):
                    parent_widget.show_fund_detail(fund_code)

        except Exception as e:
            logger.error(f"双击打开基金详情失败: {e}")

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        if item is not None:
            row = item.row()
            code_item = self.item(row, 0)
            if code_item:
                fund_code = code_item.text()

                parent_widget = self.parent()
                while parent_widget:
                    if FundMonitor is not None and isinstance(parent_widget, FundMonitor):
                        break
                    elif hasattr(parent_widget, 'monitored_codes') and hasattr(parent_widget, 'remove_specific_fund'):
                        break
                    parent_widget = parent_widget.parent()

                if parent_widget and (hasattr(parent_widget, 'monitored_codes')):
                    is_monitored = fund_code in parent_widget.monitored_codes

                    menu = QMenu()

                    if is_monitored:
                        remove_action = menu.addAction("删除基金监控")
                        menu.addSeparator()
                        cost_price_action = menu.addAction("设置持仓成本价")
                        shares_action = menu.addAction("设置持有份额")
                        dividend_action = menu.addAction("记录分红")
                        dividend_history_action = menu.addAction("查看分红记录")
                        fund_detail_action = menu.addAction("查看基金详情")

                        action = menu.exec(self.mapToGlobal(position))

                        if action == remove_action:
                            parent_widget.remove_specific_fund(fund_code)
                        elif action == cost_price_action:
                            parent_widget.set_fund_cost_price(fund_code)
                        elif action == shares_action:
                            parent_widget.set_fund_shares(fund_code)
                        elif action == dividend_action:
                            parent_widget.record_dividend(fund_code)
                        elif action == dividend_history_action:
                            parent_widget.show_dividend_history(fund_code)
                        elif action == fund_detail_action:
                            parent_widget.show_fund_detail(fund_code)
                    else:
                        add_action = menu.addAction("添加基金监控")

                        action = menu.exec(self.mapToGlobal(position))

                        if action == add_action:
                            parent_widget.add_fund_to_monitor(fund_code)
        else:
            parent_widget = self.parent()
            while parent_widget:
                if FundMonitor is not None and isinstance(parent_widget, FundMonitor):
                    break
                elif hasattr(parent_widget, 'monitored_codes') and hasattr(parent_widget, 'remove_specific_fund'):
                    break
                parent_widget = parent_widget.parent()

            if parent_widget:
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
                        lambda checked, c=col: self.toggle_column_visibility(c))

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
        """更新表格数据"""
        self.setSortingEnabled(False)
        self.setRowCount(0)

        total_profit = 0.0
        total_daily_profit = 0.0
        total_position_cost = 0.0
        total_current_value = 0.0

        for code, fund in fund_data.items():
            row_idx = self.rowCount()
            self.insertRow(row_idx)

            # 0. 基金代码 - 居中对齐
            code_item = QTableWidgetItem(code)
            code_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row_idx, 0, code_item)

            # 1. 基金名称 - 左对齐
            name_item = QTableWidgetItem(fund.get('name', ''))
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setItem(row_idx, 1, name_item)

            # 2. 估算涨跌 - 右对齐，加箭头和颜色
            gszzl = fund.get('gszzl', '0')
            gszzl_val = float(gszzl)
            if gszzl_val > 0:
                gszzl_text = f"↑ +{gszzl_val:.2f}%"
                gszzl_item = PercentageItem(gszzl_text)
                gszzl_item.setForeground(self._get_rise_color())
            elif gszzl_val < 0:
                gszzl_text = f"↓ {gszzl_val:.2f}%"
                gszzl_item = PercentageItem(gszzl_text)
                gszzl_item.setForeground(self._get_fall_color())
            else:
                gszzl_item = PercentageItem("0.00%")
                gszzl_item.setForeground(self._get_flat_color())
            gszzl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_idx, 2, gszzl_item)

            # 3. 估算净值 - 右对齐，4位小数
            gsz = fund.get('gsz', '')
            try:
                gsz_val = float(gsz) if gsz else 0.0
                gsz_text = f"{gsz_val:.4f}"
            except ValueError:
                gsz_text = gsz
            gsz_item = NumericItem(gsz_text)
            gsz_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_idx, 3, gsz_item)

            # 4. 单位净值 - 右对齐，4位小数
            dwjz = fund.get('dwjz', '')
            try:
                dwjz_val = float(dwjz) if dwjz else 0.0
                dwjz_text = f"{dwjz_val:.4f}"
            except ValueError:
                dwjz_text = dwjz
            dwjz_item = NumericItem(dwjz_text)
            dwjz_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_idx, 4, dwjz_item)

            # 获取持仓信息
            cost_price = 0.0
            shares = 0.0
            holdings_amount = 0.0

            if self.parent_monitor:
                cost_price, shares, holdings_amount = self.parent_monitor.get_fund_holdings_detail(
                    code)

            # 5. 持仓成本 - 右对齐，¥前缀+千分位
            position_cost = cost_price * shares
            position_cost_item = NumericItem(self._format_money(position_cost))
            position_cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_idx, 5, position_cost_item)

            # 6. 持有金额 - 右对齐，¥前缀+千分位
            current_value = 0.0
            try:
                gsz_val = float(gsz) if gsz else 0.0
                current_value = gsz_val * shares
            except Exception:
                pass

            holdings_item = NumericItem(self._format_money(current_value))
            holdings_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_idx, 6, holdings_item)

            # 7. 当日盈亏 - 右对齐，正负号+¥前缀+千分位+涨跌色
            daily_profit = current_value * gszzl_val / 100
            daily_profit_item = NumericItem(
                self._format_money(daily_profit, show_sign=True))
            daily_profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if daily_profit > 0:
                daily_profit_item.setForeground(self._get_rise_color())
            elif daily_profit < 0:
                daily_profit_item.setForeground(self._get_fall_color())
            else:
                daily_profit_item.setForeground(self._get_flat_color())
            self.setItem(row_idx, 7, daily_profit_item)

            # 8. 累计盈亏 - 右对齐，正负号+¥前缀+千分位+涨跌色
            dividend = 0.0
            if self.parent_monitor:
                dividend = self.parent_monitor.get_fund_dividend(code)

            total_profit_loss = current_value - position_cost + dividend
            profit_loss_item = NumericItem(
                self._format_money(total_profit_loss, show_sign=True))
            profit_loss_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if total_profit_loss > 0:
                profit_loss_item.setForeground(self._get_rise_color())
            elif total_profit_loss < 0:
                profit_loss_item.setForeground(self._get_fall_color())
            else:
                profit_loss_item.setForeground(self._get_flat_color())
            self.setItem(row_idx, 8, profit_loss_item)

            # 9. 盈亏比例 - 右对齐，正负号+涨跌色
            if position_cost > 0:
                profit_percentage = (total_profit_loss / position_cost) * 100
            else:
                profit_percentage = 0.0

            if profit_percentage > 0:
                pct_text = f"+{profit_percentage:.2f}%"
                profit_pct_item = PercentageItem(pct_text)
                profit_pct_item.setForeground(self._get_rise_color())
            elif profit_percentage < 0:
                pct_text = f"{profit_percentage:.2f}%"
                profit_pct_item = PercentageItem(pct_text)
                profit_pct_item.setForeground(self._get_fall_color())
            else:
                pct_text = "0.00%"
                profit_pct_item = PercentageItem(pct_text)
                profit_pct_item.setForeground(self._get_flat_color())
            profit_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_idx, 9, profit_pct_item)

            total_profit += total_profit_loss
            total_daily_profit += daily_profit
            total_position_cost += position_cost
            total_current_value += current_value

        self.setSortingEnabled(True)
        # 默认按估算涨跌降序排序
        self.sortItems(2, Qt.DescendingOrder)

        if self.parent_monitor:
            self.parent_monitor.update_total_profit(
                total_profit, total_daily_profit, total_position_cost, total_current_value)
