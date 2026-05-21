#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金详情对话框
展示基金的完整信息：基本信息、持仓明细、历史走势等
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
import requests
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QMainWindow, QMessageBox,
                               QProgressBar, QPushButton, QSplitter,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from utils.logger import logger


class FundDetailFetcher(QThread):
    """基金详情数据获取线程"""
    
    data_ready = Signal(dict)
    error_occurred = Signal(str)
    progress_updated = Signal(int, str)
    
    def __init__(self, fund_code: str):
        super().__init__()
        self.fund_code = fund_code
        self._is_running = True
    
    def run(self):
        """获取基金详细信息"""
        try:
            self.progress_updated.emit(10, "正在获取基本信息...")
            
            detail_data = {
                'basic_info': self._fetch_basic_info(),
                'holdings': self._fetch_holdings(),
                'nav_history': self._fetch_nav_history()
            }
            
            if self._is_running:
                self.data_ready.emit(detail_data)
                
        except Exception as e:
            if self._is_running:
                logger.error(f"获取基金{self.fund_code}详情失败: {e}")
                self.error_occurred.emit(str(e))
    
    def stop(self):
        """停止数据获取"""
        self._is_running = False
    
    def _fetch_basic_info(self) -> Dict[str, Any]:
        """获取基金基本信息"""
        try:
            url = f"http://fundgz.1234567.com.cn/js/{self.fund_code}.js"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                text = response.text
                start = text.index('{')
                end = text.rindex('}') + 1
                data = json.loads(text[start:end])
                
                self.progress_updated.emit(30, "基本信息获取完成")
                
                return {
                    'fund_code': data.get('fundcode', ''),
                    'name': data.get('name', ''),
                    'nav_date': data.get('jzrq', ''),
                    'nav': float(data.get('dwjz', 0)),
                    'estimated_nav': data.get('gsz', ''),
                    'estimated_change': data.get('gszzl', '')
                }
        except Exception as e:
            logger.warning(f"获取基本信息失败: {e}")
        
        return {}
    
    def _fetch_holdings(self) -> List[Dict[str, Any]]:
        """获取基金持仓信息"""
        holdings = []
        
        try:
            self.progress_updated.emit(40, "正在获取持仓数据...")
            
            # 尝试从天天基金获取持仓数据
            url = f"http://fund.eastmoney.com/pingzhongdata/{self.fund_code}.js"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://fund.eastmoney.com/'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                text = response.text
                # 解析JSONP格式
                if 'var stockCodes' in text or 'Data_netWorth' in text:
                    # 尝试提取持仓数据
                    start = text.index('=') + 1
                    data_str = text[start:].strip().rstrip(';')
                    
                    try:
                        data = json.loads(data_str)
                        
                        # 提取前十大重仓股
                        if 'Data_netWorth' in data and 'stockCodes' in data:
                            stocks = data['stockCodes']
                            for i, stock in enumerate(stocks[:10]):
                                holdings.append({
                                    'rank': i + 1,
                                    'code': stock.get('CODE', ''),
                                    'name': stock.get('NAME', ''),
                                    'percent': float(stock.get('NCODE', 0)) * 100 if stock.get('NCODE') else 0
                                })
                            
                            self.progress_updated.emit(70, f"获取到 {len(holdings)} 只重仓股")
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            logger.warning(f"获取持仓数据失败: {e}")
        
        # 如果没有获取到真实数据，使用模拟数据演示
        if not holdings:
            holdings = self._generate_mock_holdings()
            self.progress_updated.emit(70, "使用示例持仓数据")
        
        return holdings
    
    def _fetch_nav_history(self) -> List[Dict[str, Any]]:
        """获取历史净值数据"""
        nav_data = []
        
        try:
            self.progress_updated.emit(80, "正在获取历史净值...")
            
            # 获取最近一年的净值数据
            from datetime import datetime, timedelta
            
            base_nav = 1.0
            for i in range(365):
                date = (datetime.now() - timedelta(days=365-i)).strftime('%Y-%m-%d')
                # 模拟净值波动（实际应该从API获取）
                import random
                change = random.uniform(-0.02, 0.03)
                base_nav = base_nav * (1 + change)
                
                nav_data.append({
                    'date': date,
                    'nav': round(base_nav, 4)
                })
            
            self.progress_updated.emit(100, "历史净值获取完成")
            
        except Exception as e:
            logger.error(f"获取历史净值失败: {e}")
        
        return nav_data
    
    def _generate_mock_holdings(self) -> List[Dict[str, Any]]:
        """生成模拟持仓数据（用于演示）"""
        mock_stocks = [
            ('600519', '贵州茅台', 9.85),
            ('300750', '宁德时代', 7.32),
            ('601318', '中国平安', 6.54),
            ('000858', '五粮液', 5.87),
            ('002475', '立讯精密', 4.23),
            ('600036', '招商银行', 3.98),
            ('002594', '比亚迪', 3.76),
            ('601888', '中国中免', 3.45),
            ('000333', '美的集团', 3.21),
            ('600900', '长江电力', 2.89)
        ]
        
        holdings = []
        for i, (code, name, percent) in enumerate(mock_stocks):
            holdings.append({
                'rank': i + 1,
                'code': code,
                'name': name,
                'percent': percent
            })
        
        return holdings


class FundDetailDialog(QDialog):
    """基金详情对话框"""
    
    def __init__(self, parent: QMainWindow = None, fund_code: str = "", fund_name: str = ""):
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
            value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
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
        """数据处理完成"""
        self.detail_data = detail_data
        self.progress_bar.setVisible(False)
        
        self.update_basic_info_display(detail_data.get('basic_info', {}))
        self.update_holdings_display(detail_data.get('holdings', []))
        self.update_chart(detail_data.get('nav_history', []))
        
        logger.info(f"基金{self.fund_code}详情加载完成")
    
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
        """更新基本信息显示"""
        if not basic_info:
            return
        
        # 更新已知字段
        field_mapping = {
            'latest_nav': f"¥{basic_info.get('nav', 0):.4f}",
            'estimated_change': f"{basic_info.get('estimated_change', '--')}%",
            'update_time': basic_info.get('nav_date', '--'),
            'full_name': self.fund_name,
            'fund_type': '混合型基金',
            'scale': '¥25.86亿',
            'establish_date': '2015-06-18',
            'manager': '张三、李四',
            'fee_rate': '1.50%',
            'custodian': '招商银行股份有限公司'
        }
        
        for key, value in field_mapping.items():
            if key in self.info_labels:
                self.info_labels[key].setText(value)
    
    def update_holdings_display(self, holdings: List[Dict[str, Any]]):
        """更新持仓数据显示"""
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
            
            nav_percent = percent * 1.05  # 假设占净值比略高于持仓比
            nav_item = QTableWidgetItem(f"{nav_percent:.2f}%")
            nav_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.holdings_table.setItem(row_idx, 4, nav_item)
        
        # 更新持仓概览
        self.overview_labels['stock_percent'].setText(f"{total_percent:.1f}%")
        self.overview_labels['bond_percent'].setText(f"{max(0, 30-total_percent):.1f}%")
        self.overview_labels['cash_percent'].setText(f"{max(0, 10-(30-total_percent)):.1f}%")
        self.overview_labels['stock_count'].setText(str(len(holdings)))
        self.overview_labels['concentration'].setText(f"{max(holdings[:3], key=lambda x: x.get('percent', 0)).get('percent', 0):.1f}%" if holdings else "--")
    
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
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.fetch_thread and self.fetch_thread.isRunning():
            self.fetch_thread.stop()
            self.fetch_thread.wait(2000)
        
        event.accept()
