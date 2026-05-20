#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合仪表盘UI组件
提供专业的投资组合可视化和分析展示
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QScrollArea, QSplitter,
                               QTabWidget, QVBoxLayout, QWidget)

from services.portfolio_analyzer import (
    AllocationData,
    FundHolding,
    PortfolioAnalyzer,
    PortfolioReport,
    RiskMetrics,
)

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class MetricCard(QFrame):
    """指标卡片组件"""
    
    def __init__(self, title: str, value: str, subtitle: str = "",
                 color: str = "#3b82f6", parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        self.setFixedHeight(120)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #64748b;
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        layout.addWidget(title_label)
        
        # 数值
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(value_label)
        
        # 副标题
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("""
                QLabel {
                    color: #94a3b8;
                    font-size: 11px;
                }
            """)
            layout.addWidget(sub_label)
        
        self.setLayout(layout)


class PieChartWidget(QWidget):
    """饼图组件"""
    
    def __init__(self, title: str = "资产配置", parent=None):
        super().__init__(parent)
        
        self.fig = Figure(figsize=(5, 5), facecolor='white')
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def update_chart(self, data: List[AllocationData], title: str = "资产配置"):
        """更新饼图数据"""
        self.ax.clear()
        
        if not data:
            self.ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                        fontsize=14, color='#94a3b8')
            self.canvas.draw()
            return
        
        labels = [d.category for d in data]
        sizes = [d.value for d in data]
        colors = [d.color for d in data]
        explode = [0.05] + [0] * (len(data) - 1)  # 突出显示最大项
        
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            textprops={'fontsize': 10}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        self.fig.tight_layout()
        self.canvas.draw()


class BarChartWidget(QWidget):
    """柱状图组件"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        
        self.fig = Figure(figsize=(6, 4), facecolor='white')
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def update_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str = "",
        colors: Optional[List[str]] = None,
        horizontal: bool = False
    ):
        """更新柱状图"""
        self.ax.clear()
        
        if not categories or not values:
            self.ax.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                        fontsize=14, color='#94a3b8')
            self.canvas.draw()
            return
        
        if colors is None:
            colors = ['#3b82f6'] * len(categories)
        
        if horizontal:
            bars = self.ax.barh(categories, values, color=colors)
            self.ax.set_xlabel('金额（元）')
        else:
            x_pos = range(len(categories))
            bars = self.ax.bar(x_pos, values, color=colors)
            self.ax.set_xticks(x_pos)
            self.ax.set_xticklabels(categories, rotation=45, ha='right')
            self.ax.set_ylabel('金额（元）')
        
        if title:
            self.ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        
        self.ax.grid(axis='y' if not horizontal else 'x', alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw()


class PortfolioDashboard(QDialog):
    """投资组合仪表盘对话框"""
    
    def __init__(self, holdings_data: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.holdings_data = holdings_data
        self.analyzer = PortfolioAnalyzer()
        
        self.setWindowTitle("📊 投资组合分析仪表盘")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QTabWidget::pane {
                border: none;
                background: white;
                border-radius: 12px;
            }
            QTabBar::tab {
                background: transparent;
                color: #64748b;
                padding: 10px 20px;
                margin-right: 4px;
                font-size: 13px;
                font-weight: 500;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #3b82f6;
                border-bottom: 2px solid #3b82f6;
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
        """)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 标题栏
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
            }
        """)
        header_widget.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(32, 0, 32, 0)
        
        title_label = QLabel("📊 投资组合智能分析")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        header_layout.addWidget(close_btn)
        
        main_layout.addWidget(header_widget)
        
        # 核心指标卡片区域
        metrics_container = QWidget()
        metrics_container.setStyleSheet("background: transparent;")
        metrics_layout = QHBoxLayout(metrics_container)
        metrics_layout.setSpacing(16)
        
        self.total_assets_card = MetricCard("总资产", "¥0", "")
        self.total_profit_card = MetricCard("累计盈亏", "¥0", "", "#ef4444")
        self.daily_profit_card = MetricCard("今日盈亏", "¥0", "", "#10b981")
        self.profit_pct_card = MetricCard("总收益率", "0%", "", "#f59e0b")
        
        metrics_layout.addWidget(self.total_assets_card)
        metrics_layout.addWidget(self.total_profit_card)
        metrics_layout.addWidget(self.daily_profit_card)
        metrics_layout.addWidget(self.profit_pct_card)
        
        main_layout.addWidget(metrics_container)
        
        # Tab页面
        self.tab_widget = QTabWidget()
        
        # 创建各个标签页
        self.create_overview_tab()
        self.create_allocation_tab()
        self.create_risk_tab()
        self.create_holdings_tab()
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def create_overview_tab(self):
        """创建概览标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(16)
        
        # 左侧：资产配置饼图
        left_group = QGroupBox("🥧 资产配置分布")
        left_layout = QVBoxLayout(left_group)
        self.allocation_pie = PieChartWidget("按基金类型配置")
        left_layout.addWidget(self.allocation_pie)
        
        # 右侧：收益贡献柱状图
        right_group = QGroupBox("💰 收益贡献排名")
        right_layout = QVBoxLayout(right_group)
        self.profit_bar = BarChartWidget()
        right_layout.addWidget(self.profit_bar)
        
        layout.addWidget(left_group, stretch=1)
        layout.addWidget(right_group, stretch=1)
        
        self.tab_widget.addTab(tab, "📈 总览")
    
    def create_allocation_tab(self):
        """创建资产配置详情标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea {border: none; background: transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        
        # 配置明细表格
        config_group = QGroupBox("📊 配置明细")
        config_layout = QGridLayout(config_group)
        
        headers = ['类型', '金额', '占比', '建议']
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet("""
                QLabel {
                    color: #475569;
                    font-size: 13px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            config_layout.addWidget(label, 0, col)
        
        self.config_labels = []
        for row in range(6):  # 预留6行
            row_labels = []
            for col in range(4):
                label = QLabel("")
                label.setStyleSheet("""
                    QLabel {
                        color: #334155;
                        font-size: 12px;
                        background: transparent;
                        padding: 8px;
                    }
                """)
                row_labels.append(label)
                config_layout.addWidget(label, row + 1, col)
            self.config_labels.append(row_labels)
        
        layout.addWidget(config_group)
        
        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "🥧 资产配置")
    
    def create_risk_tab(self):
        """创建风险评估标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 风险指标卡片
        risk_metrics_group = QGroupBox("⚠️ 风险指标评估")
        risk_grid = QGridLayout(risk_metrics_group)
        
        risk_items = [
            ("波动率", "volatility", "%", "衡量投资组合价格波动程度"),
            ("最大回撤", "max_drawdown", "%", "历史最大亏损幅度"),
            ("夏普比率", "sharpe_ratio", "", "风险调整后收益，越高越好"),
            ("Beta系数", "beta", "", "相对市场波动性，>1表示更波动"),
            ("Alpha", "alpha", "", "超额收益能力，>0表示跑赢市场"),
            ("VaR(95%)", "var_95", "元", "95%概率下最大损失")
        ]
        
        self.risk_value_labels = {}
        for row, (name_cn, name_en, unit, desc) in enumerate(risk_items):
            name_label = QLabel(name_cn)
            name_label.setStyleSheet("""
                QLabel {
                    color: #1e293b;
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            risk_grid.addWidget(name_label, row, 0)
            
            value_label = QLabel("--")
            value_label.setStyleSheet("""
                QLabel {
                    color: #3b82f6;
                    font-size: 18px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            risk_grid.addWidget(value_label, row, 1)
            
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    font-size: 12px;
                    background: transparent;
                }
            """)
            risk_grid.addWidget(unit_label, row, 2)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #94a3b8;
                    font-size: 11px;
                    background: transparent;
                }
            """)
            risk_grid.addWidget(desc_label, row, 3)
            
            self.risk_value_labels[name_en] = value_label
        
        layout.addWidget(risk_metrics_group)
        
        # 风险等级说明
        level_group = QGroupBox("📊 风险等级参考")
        level_layout = QVBoxLayout(level_group)
        
        levels_text = """
        <p style="line-height: 1.8; color: #475569;">
        <b style="color: #10b981;">● 低风险</b>: 波动率 &lt; 10%，适合保守型投资者<br>
        <b style="color: #f59e0b;">● 中风险</b>: 波动率 10%-20%，适合稳健型投资者<br>
        <b style="color: #ef4444;">● 高风险</b>: 波动率 &gt; 20%，适合激进型投资者<br><br>
        <b>夏普比率解读</b>: &gt;1优秀，&gt;2非常优秀<br>
        <b>Beta系数</b>: 1.0=与市场同步，&gt;1更波动，&lt;1较稳定<br>
        <b>Alpha</b>: 正值表示跑赢基准，负值表示落后
        </p>
        """
        level_label = QLabel(levels_text)
        level_label.setTextFormat(Qt.RichText)
        level_label.setWordWrap(True)
        level_label.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 12px;
                border-left: 3px solid #3b82f6;
            }
        """)
        level_layout.addWidget(level_label)
        
        layout.addWidget(level_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "⚠️ 风险评估")
    
    def create_holdings_tab(self):
        """创建持仓明细标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea {border: none; background: transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        
        # TOP5持仓
        top_group = QGroupBox("🏆 TOP5持仓（按市值排序）")
        top_layout = QVBoxLayout(top_group)
        
        self.top_holding_labels = []
        for i in range(5):
            holding_frame = QFrame()
            holding_frame.setStyleSheet("""
                QFrame {
                    background: #f8fafc;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            h_layout = QHBoxLayout(holding_frame)
            h_layout.setContentsMargins(12, 8, 12, 8)
            
            rank_label = QLabel(f"#{i+1}")
            rank_label.setStyleSheet("""
                QLabel {
                    color: #3b82f6;
                    font-size: 18px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            rank_label.setFixedWidth(40)
            h_layout.addWidget(rank_label)
            
            name_label = QLabel("")
            name_label.setStyleSheet("""
                QLabel {
                    color: #1e293b;
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                }
            """)
            h_layout.addWidget(name_label)
            
            h_layout.addStretch()
            
            value_label = QLabel("")
            value_label.setStyleSheet("""
                QLabel {
                    color: #059669;
                    font-size: 15px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            h_layout.addWidget(value_label)
            
            profit_label = QLabel("")
            profit_label.setStyleSheet("""
                QLabel {
                    color: #dc2626;
                    font-size: 13px;
                    background: transparent;
                }
            """)
            h_layout.addWidget(profit_label)
            
            top_layout.addWidget(holding_frame)
            self.top_holding_labels.append({
                'rank': rank_label,
                'name': name_label,
                'value': value_label,
                'profit': profit_label
            })
        
        layout.addWidget(top_group)
        layout.addStretch()
        
        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "📋 持仓明细")
    
    def load_data(self):
        """加载并显示数据"""
        try:
            report = self.analyzer.analyze_portfolio(self.holdings_data)
            self.update_ui_with_report(report)
        except Exception as e:
            from utils.logger import logger
            logger.error(f"加载投资组合数据失败: {e}")
    
    def update_ui_with_report(self, report: PortfolioReport):
        """使用报告数据更新UI"""
        # 更新核心指标卡片
        self._update_metric_card(
            self.total_assets_card,
            f"¥{report.total_assets:,.2f}",
            f"成本 ¥{report.total_cost:,.2f}"
        )
        
        profit_color = "#ef4444" if report.total_profit >= 0 else "#10b981"
        profit_sign = "+" if report.total_profit >= 0 else ""
        self._update_metric_card(
            self.total_profit_card,
            f"{profit_sign}¥{report.total_profit:,.2f}",
            "",
            profit_color
        )
        
        daily_color = "#ef4444" if report.daily_profit >= 0 else "#10b981"
        daily_sign = "+" if report.daily_profit >= 0 else ""
        self._update_metric_card(
            self.daily_profit_card,
            f"{daily_sign}¥{report.daily_profit:,.2f}",
            "",
            daily_color
        )
        
        pct_color = "#ef4444" if report.profit_percentage >= 0 else "#10b981"
        pct_sign = "+" if report.profit_percentage >= 0 else ""
        self._update_metric_card(
            self.profit_pct_card,
            f"{pct_sign}{report.profit_percentage:.2f}%",
            "",
            pct_color
        )
        
        # 更新资产配置饼图
        self.allocation_pie.update_chart(report.allocations)
        
        # 更新收益贡献柱状图
        if report.profit_attribution:
            codes = list(report.profit_attribution.keys())[:10]
            values = [report.profit_attribution[code][0] for code in codes]
            colors = ['#ef4444' if v >= 0 else '#10b981' for v in values]
            self.profit_bar.update_chart(codes, values, "收益绝对贡献（元）", colors, horizontal=True)
        
        # 更新配置明细表
        for i, alloc in enumerate(report.allocations[:6]):
            if i < len(self.config_labels):
                self.config_labels[i][0].setText(alloc.category)
                self.config_labels[i][0].setStyleSheet(
                    f"QLabel {{color: {alloc.color}; font-weight: bold; background: transparent;}}"
                )
                self.config_labels[i][1].setText(f"¥{alloc.value:,.2f}")
                self.config_labels[i][2].setText(f"{alloc.percentage:.1f}%")
                
                advice = ""
                if alloc.percentage > 50:
                    advice = "⚠️ 过度集中"
                elif alloc.percentage > 30:
                    advice = "✅ 合理"
                else:
                    advice = "ℹ️ 分散良好"
                self.config_labels[i][3].setText(advice)
        
        # 更新风险指标
        risk = report.risk_metrics
        self.risk_value_labels['volatility'].setText(f"{risk.volatility:.2f}")
        self.risk_value_labels['max_drawdown'].setText(f"{risk.max_drawdown:.2f}")
        self.risk_value_labels['sharpe_ratio'].setText(f"{risk.sharpe_ratio:.2f}")
        self.risk_value_labels['beta'].setText(f"{risk.beta:.2f}")
        self.risk_value_labels['alpha'].setText(f"{risk.alpha:+.2f}")
        self.risk_value_labels['var_95'].setText(f"¥{risk.var_95:,.2f}")
        
        # 根据风险等级调整颜色
        vol = risk.volatility
        if vol < 10:
            self.risk_value_labels['volatility'].setStyleSheet(
                "QLabel {color: #10b981; font-size: 18px; font-weight: bold;}"
            )
        elif vol < 20:
            self.risk_value_labels['volatility'].setStyleSheet(
                "QLabel {color: #f59e0b; font-size: 18px; font-weight: bold;}"
            )
        else:
            self.risk_value_labels['volatility'].setStyleSheet(
                "QLabel {color: #ef4444; font-size: 18px; font-weight: bold;}"
            )
        
        # 更新TOP5持仓
        for i, holding in enumerate(report.top_holdings[:5]):
            if i < len(self.top_holding_labels):
                self.top_holding_labels[i]['name'].setText(
                    f"{holding.fund_name} ({holding.fund_code})"
                )
                self.top_holding_labels[i]['value'].setText(
                    f"¥{holding.current_value:,.2f}"
                )
                
                cost = holding.cost_price * holding.shares
                if cost > 0:
                    pct = ((holding.current_value - cost) / cost) * 100
                else:
                    pct = 0
                
                profit_sign = "+" if pct >= 0 else ""
                profit_color = "#ef4444" if pct >= 0 else "#10b981"
                self.top_holding_labels[i]['profit'].setText(
                    f"{profit_sign}{pct:.2f}%"
                )
                self.top_holding_labels[i]['profit'].setStyleSheet(
                    f"QLabel {{color: {profit_color}; font-size: 13px; background: transparent;}}"
                )
    
    def _update_metric_card(
        self,
        card: MetricCard,
        value: str,
        subtitle: str = "",
        color: str = "#3b82f6"
    ):
        """更新指标卡片的数值"""
        layout = card.layout()
        if layout and layout.count() >= 2:
            value_label = layout.itemAt(1).widget()
            if value_label:
                value_label.setText(value)
                value_label.setStyleSheet(f"""
                    QLabel {{
                        color: {color};
                        font-size: 28px;
                        font-weight: bold;
                    }}
                """)
            
            if subtitle and layout.count() >= 3:
                sub_label = layout.itemAt(2).widget()
                if sub_label:
                    sub_label.setText(subtitle)
