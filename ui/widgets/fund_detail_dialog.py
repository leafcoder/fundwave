#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金详情对话框
展示基金的完整信息：基本信息、持仓明细、历史走势等
"""

from __future__ import annotations
from utils.logger import logger
from services.fund_data_service import FundDataService, get_fund_data_service

import json
from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
import requests
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QMainWindow, QMessageBox,
                               QProgressBar, QPushButton, QSplitter,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei',
                                   'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class FundDetailFetcher(QThread):
    """基金详情数据获取线程 - 专业版（使用真实API）"""

    data_ready = Signal(dict)
    error_occurred = Signal(str)
    progress_updated = Signal(int, str)

    def __init__(self, fund_code: str):
        super().__init__()
        self.fund_code = fund_code
        self._is_running = True
        self.data_service: Optional[FundDataService] = None

    def run(self):
        """获取基金详细信息（专业版）"""
        try:
            if not self._is_running:
                return

            # 初始化数据服务
            self.data_service = get_fund_data_service()
            self.progress_updated.emit(5, "正在初始化数据服务...")

            # 1. 获取基本信息（10%-30%）
            self.progress_updated.emit(10, "正在获取基本信息...")
            basic_info = self.data_service.get_fund_basic_info(self.fund_code)
            self.progress_updated.emit(
                30, f"基本信息获取完成: {basic_info.get('name', '')}")

            if not self._is_running:
                return

            # 2. 获取历史净值（30%-60%）
            self.progress_updated.emit(35, "正在获取历史净值数据...")
            nav_history = self.data_service.get_fund_history_nav(
                self.fund_code, days=365)
            self.progress_updated.emit(60, f"历史净值获取完成: {len(nav_history)}天")

            if not self._is_running:
                return

            # 3. 获取持仓信息（60%-80%）
            self.progress_updated.emit(65, "正在获取股票持仓...")
            holdings_data = self.data_service.get_fund_holdings(self.fund_code)
            self.progress_updated.emit(
                80, f"持仓数据获取完成: {holdings_data['total_holdings']}只股票")

            if not self._is_running:
                return

            # 4. 计算风险指标（80%-90%）
            self.progress_updated.emit(85, "正在计算风险指标...")
            risk_metrics = self.data_service.calculate_risk_metrics(
                nav_history)
            self.progress_updated.emit(90, "风险指标计算完成")

            if not self._is_running:
                return

            # 5. 获取同类对比（90%-100%）
            self.progress_updated.emit(92, "正在获取同类排名...")
            peer_comparison = self.data_service.compare_with_peers(
                self.fund_code)
            self.progress_updated.emit(100, "所有数据加载完成！")

            # 组装完整数据
            detail_data = {
                'basic_info': basic_info,
                'nav_history': nav_history,
                'holdings': holdings_data,
                'risk_metrics': risk_metrics,
                'peer_comparison': peer_comparison,
                'data_source': 'real_api'  # 标记为真实数据
            }

            if self._is_running:
                self.data_ready.emit(detail_data)

        except Exception as e:
            if self._is_running:
                logger.error(f"获取基金{self.fund_code}详情失败: {e}")
                import traceback
                logger.debug(f"详细错误堆栈:\n{traceback.format_exc()}")
                self.error_occurred.emit(str(e))

    def stop(self):
        """停止数据获取"""
        self._is_running = False


class FundDetailDialog(QDialog):
    """基金详情对话框"""

    def __init__(self, parent: QMainWindow = None,
                 fund_code: str = "", fund_name: str = ""):
        super().__init__(parent)
        self.fund_code = fund_code
        self.fund_name = fund_name

        self.setWindowTitle(f"📊 基金详情 - {fund_name}({fund_code})")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QGroupBox {
                background: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                margin-top: 12px;
                padding-top: 24px;
                font-size: 14px;
                font-weight: bold;
                color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
            QLabel {
                color: #334155;
            }
            QTableWidget {
                gridline-color: #e2e8f0;
                background: white;
                alternate-background-color: #f8fafc;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #f1f5f9;
                color: #475569;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """)

        self.detail_data = {}
        self.fetch_thread = None

        self.setup_ui()
        self.load_fund_detail()

    def setup_ui(self):
        """初始化UI界面"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 标题栏
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 12px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 16, 24, 16)

        title_label = QLabel(f"📊 {self.fund_name} ({self.fund_code})")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addWidget(header_widget)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #e2e8f0;
                border-radius: 4px;
                height: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # 主内容区域（使用分割器）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：基本信息 + 净值走势
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # 基本信息卡片
        info_group = QGroupBox("📋 基本信息")
        info_grid = QGridLayout(info_group)
        info_grid.setSpacing(12)

        self.info_labels = {}
        basic_fields = [
            ("基金全称", "full_name", "#1e293b"),
            ("基金类型", "fund_type", "#3b82f6"),
            ("基金规模", "scale", "#10b981"),
            ("成立日期", "establish_date", "#f59e0b"),
            ("基金经理", "manager", "#8b5cf6"),
            ("管理费率", "fee_rate", "#ef4444"),
            ("托管银行", "custodian", "#06b6d4"),
            ("最新净值", "latest_nav", "#059669"),
            ("估值涨跌", "estimated_change", "#dc2626"),
            ("更新时间", "update_time", "#64748b"),
        ]

        for row, (label_text, key, color) in enumerate(basic_fields):
            label = QLabel(f"{label_text}:")
            label.setStyleSheet(f"color: {color}; font-weight: 500;")
            info_grid.addWidget(label, row, 0)

            value_label = QLabel("加载中...")
            value_label.setStyleSheet(f"color: #334155; font-weight: bold;")
            info_grid.addWidget(value_label, row, 1)

            self.info_labels[key] = value_label

        left_layout.addWidget(info_group)

        # 净值走势图
        chart_group = QGroupBox("📈 净值走势")
        chart_layout = QVBoxLayout(chart_group)

        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        left_layout.addWidget(chart_group)
        splitter.addWidget(left_widget)

        # 右侧：持仓明细
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # 持仓概览
        overview_group = QGroupBox("🎯 持仓概览")
        overview_layout = QGridLayout(overview_group)

        self.overview_labels = {}
        overview_items = [
            ("股票占比", "stock_percent", "#3b82f6"),
            ("债券占比", "bond_percent", "#10b981"),
            ("现金占比", "cash_percent", "#f59e0b"),
            ("持有股票数", "stock_count", "#8b5cf6"),
            ("集中度", "concentration", "#ef4444"),
        ]

        for col, (label_text, key, color) in enumerate(overview_items):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            overview_layout.addWidget(label, 0, col)

            value_label = QLabel("--")
            value_label.setStyleSheet(
                f"color: {color}; font-size: 18px; font-weight: bold;")
            overview_layout.addWidget(value_label, 1, col)

            self.overview_labels[key] = value_label

        right_layout.addWidget(overview_group)

        # 持仓明细表格
        holdings_group = QGroupBox("📊 股票持仓明细（前十大重仓股）")
        holdings_layout = QVBoxLayout(holdings_group)

        self.holdings_table = QTableWidget()
        self.holdings_table.setColumnCount(5)
        self.holdings_table.setHorizontalHeaderLabels(
            ["排名", "股票代码", "股票名称", "持仓占比", "占净值比"]
        )

        header = self.holdings_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.holdings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.holdings_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.holdings_table.setAlternatingRowColors(True)
        self.holdings_table.verticalHeader().setVisible(False)

        holdings_layout.addWidget(self.holdings_table)
        right_layout.addWidget(holdings_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([600, 600])

        main_layout.addWidget(splitter)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #64748b;
                color: white;
            }
            QPushButton:hover {
                background: #475569;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def load_fund_detail(self):
        """加载基金详情"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.fetch_thread = FundDetailFetcher(self.fund_code)
        self.fetch_thread.data_ready.connect(self.on_data_ready)
        self.fetch_thread.error_occurred.connect(self.on_error)
        self.fetch_thread.progress_updated.connect(self.on_progress)
        self.fetch_thread.start()

    def on_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(message)

    def on_data_ready(self, detail_data: dict):
        """数据处理完成（专业版）"""
        self.detail_data = detail_data
        self.progress_bar.setVisible(False)

        # 1. 更新基本信息（真实API数据）
        self.update_basic_info_display(detail_data.get('basic_info', {}))

        # 2. 更新持仓信息（真实API数据）
        self.update_holdings_display(detail_data.get('holdings', {}))

        # 3. 更新净值走势图（真实历史数据）
        self.update_chart(detail_data.get('nav_history', []))

        # 4. 更新风险指标（阶段3新功能）
        risk_metrics = detail_data.get('risk_metrics', {})
        if risk_metrics:
            self.update_risk_metrics_display(risk_metrics)

        # 5. 更新同类对比（阶段3新功能）
        peer_comparison = detail_data.get('peer_comparison', [])
        if peer_comparison:
            self.update_peer_comparison_display(peer_comparison)

        # 显示数据来源标记
        data_source = detail_data.get('data_source', 'unknown')
        logger.info(f"基金{self.fund_code}详情加载完成 (数据源: {data_source})")

    def on_error(self, error_msg: str):
        """处理错误"""
        self.progress_bar.setVisible(False)
        logger.error(f"加载基金详情失败: {error_msg}")

        QMessageBox.warning(
            self,
            "加载失败",
            f"无法加载基金详情:\n{error_msg}\n\n请检查网络连接后重试。"
        )

    def update_basic_info_display(self, basic_info: Dict[str, Any]):
        """更新基本信息显示（专业版）"""
        if not basic_info:
            return

        # 使用真实API数据
        field_mapping = {
            'full_name': basic_info.get('name', self.fund_name),
            'fund_type': basic_info.get('fund_type', '--'),
            'scale': basic_info.get('scale', '--'),
            'establish_date': basic_info.get('establish_date', '--'),
            'manager': basic_info.get('manager', '--'),
            'fee_rate': f"{basic_info.get('management_fee', '--')} / {basic_info.get('custodian_fee', '--')}",
            'custodian': basic_info.get('benchmark', '--'),
            'latest_nav': f"¥{basic_info.get('nav', 0):.4f}" if basic_info.get('nav') else "--",
            'estimated_change': f"{basic_info.get('estimated_change', '--')}%",
            'update_time': basic_info.get('nav_date', '--')
        }

        for key, value in field_mapping.items():
            if key in self.info_labels:
                self.info_labels[key].setText(str(value))

    def update_holdings_display(self, holdings_data: Dict[str, Any]):
        """更新持仓数据显示（专业版）"""
        holdings = holdings_data.get('holdings', [])
        self.holdings_table.setRowCount(len(holdings))

        total_percent = 0.0
        for row_idx, holding in enumerate(holdings):
            rank_item = QTableWidgetItem(str(holding.get('rank', row_idx + 1)))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.holdings_table.setItem(row_idx, 0, rank_item)

            code_item = QTableWidgetItem(holding.get('code', ''))
            code_item.setTextAlignment(Qt.AlignCenter)
            self.holdings_table.setItem(row_idx, 1, code_item)

            name_item = QTableWidgetItem(holding.get('name', ''))
            self.holdings_table.setItem(row_idx, 2, name_item)

            percent = holding.get('percent', 0)
            total_percent += percent

            percent_item = QTableWidgetItem(f"{percent:.2f}%")
            percent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            percent_item.setForeground(Qt.darkGreen)
            self.holdings_table.setItem(row_idx, 3, percent_item)

            # 持仓市值
            market_value = holding.get('market_value', '')
            nav_item = QTableWidgetItem(
                f"{market_value}万" if market_value else "--")
            nav_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.holdings_table.setItem(row_idx, 4, nav_item)

        # 更新持仓概览（使用真实数据）
        stock_pct = holdings_data.get('stock_percent', total_percent)
        bond_pct = holdings_data.get('bond_percent', 0)
        cash_pct = holdings_data.get('cash_percent', 0)

        self.overview_labels['stock_percent'].setText(f"{stock_pct:.1f}%")
        self.overview_labels['bond_percent'].setText(f"{bond_pct:.1f}%")
        self.overview_labels['cash_percent'].setText(f"{cash_pct:.1f}%")
        self.overview_labels['stock_count'].setText(
            str(holdings_data.get('total_holdings', len(holdings))))

        # 集中度（前3大持仓占比）
        if len(holdings) >= 3:
            concentration = sum(h['percent'] for h in holdings[:3])
        else:
            concentration = total_percent
        self.overview_labels['concentration'].setText(f"{concentration:.1f}%")

    def update_risk_metrics_display(self, risk_metrics: Dict[str, Any]):
        """更新风险指标显示（阶段3新功能）"""
        if not hasattr(self, 'risk_group'):
            return

        # 更新风险指标标签
        metrics_to_update = [
            ('annualized_return_label',
             f"{risk_metrics['annualized_return']*100:.2f}%",
             '#10b981'),
            ('volatility_label',
             f"{risk_metrics['volatility']*100:.2f}%",
             '#f59e0b'),
            ('sharpe_ratio_label',
             f"{risk_metrics['sharpe_ratio']:.2f}",
             '#3b82f6' if risk_metrics['sharpe_ratio'] > 1 else '#ef4444'),
            ('max_drawdown_label',
             f"{risk_metrics['max_drawdown']*100:.2f}%",
             '#ef4444'),
            ('calmar_ratio_label',
             f"{risk_metrics['calmar_ratio']:.2f}",
             '#8b5cf6'),
            ('win_rate_label',
             f"{risk_metrics['win_rate']*100:.1f}%",
             '#059669'),
        ]

        for label_key, value, color in metrics_to_update:
            if hasattr(self, label_key):
                getattr(self, label_key).setText(value)
                getattr(self, label_key).setStyleSheet(
                    f"color: {color}; font-size: 16px; font-weight: bold;")

        logger.info(
            f"风险指标已更新: Sharpe={risk_metrics['sharpe_ratio']:.2f}, MaxDD={risk_metrics['max_drawdown']:.2%}")

    def update_peer_comparison_display(
            self, peer_comparison: List[Dict[str, Any]]):
        """更新同类基金对比显示（阶段3新功能）"""
        if not hasattr(self, 'peer_table') or not peer_comparison:
            return

        self.peer_table.setRowCount(len(peer_comparison))

        for row_idx, peer in enumerate(peer_comparison):
            rank_item = QTableWidgetItem(str(peer.get('rank', row_idx + 1)))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.peer_table.setItem(row_idx, 0, rank_item)

            code_item = QTableWidgetItem(peer.get('code', ''))
            code_item.setTextAlignment(Qt.AlignCenter)
            self.peer_table.setItem(row_idx, 1, code_item)

            name_item = QTableWidgetItem(peer.get('name', ''))
            if peer.get('is_current'):
                name_item.setForeground(Qt.blue)
                name_item.setFont(name_item.font().bold())
            self.peer_table.setItem(row_idx, 2, name_item)

            ret_1y = peer.get('return_1y', 0)
            ret_sign = '+' if ret_1y >= 0 else ''
            ret_item = QTableWidgetItem(f"{ret_sign}{ret_1y*100:.2f}%")
            ret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            if peer.get('is_current'):
                ret_item.setBackground(QColor(230, 240, 255))
                ret_item.setForeground(Qt.blue)
            elif ret_1y > 0:
                ret_item.setForeground(Qt.darkGreen)
            else:
                ret_item.setForeground(Qt.red)

            self.peer_table.setItem(row_idx, 3, ret_item)

        logger.info(f"同类对比已更新: {len(peer_comparison)}只基金")

    def update_chart(self, nav_history: List[Dict[str, Any]]):
        """更新净值走势图"""
        if not nav_history:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        dates = [item['date'] for item in nav_history]
        values = [item['nav'] for item in nav_history]

        ax.plot(dates, values, 'b-', linewidth=1.5, label='单位净值')
        ax.fill_between(dates, values, alpha=0.3)

        ax.set_title('历史净值走势', fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel('日期', fontsize=10)
        ax.set_ylabel('净值（元）', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')

        # 设置x轴标签间隔
        if len(dates) > 30:
            step = len(dates) // 12
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i]
                               for i in range(0, len(dates), step)], rotation=45)

        self.figure.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.fetch_thread and self.fetch_thread.isRunning():
            self.fetch_thread.stop()
            self.fetch_thread.wait(2000)

        event.accept()
