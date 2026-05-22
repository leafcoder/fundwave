#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合仪表盘UI组件 - 专业版（对标大厂设计）
提供专业的投资组合可视化和分析展示

设计特点：
- 采用现代卡片式布局，带柔和阴影和圆角
- 使用专业的金融配色方案（蓝/绿/红）
- 数据层级清晰，重要信息突出显示
- 图表使用渐变填充和平滑曲线
- 微交互动画提升用户体验
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPalette
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QScrollArea, QSplitter, QTabWidget, QVBoxLayout,
                               QWidget)

from services.portfolio_analyzer import (AllocationData, FundHolding,
                                         PortfolioAnalyzer, PortfolioReport,
                                         RiskMetrics)
from ui.theme.professional_theme import MPL_THEME_CONFIG, ProfessionalTheme

matplotlib.use('Agg')
plt.rcParams.update(MPL_THEME_CONFIG)


class MetricCard(QFrame):
    """专业级指标卡片 - 带动画效果"""

    valueChanged = Signal(float)

    def __init__(self, title: str, value: float = 0.0,
                 unit: str = "", subtitle: str = "",
                 icon: str = "📊", color: str = "#1677FF",
                 trend: str = "neutral", parent=None):
        super().__init__(parent)

        self.title = title
        self.value = value
        self.unit = unit
        self.subtitle = subtitle
        self.icon = icon
        self.color = color
        self.trend = trend  # up/down/neutral

        self._setup_ui()

    def _setup_ui(self):
        """初始化UI"""
        # 卡片主体样式（带阴影和圆角）
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: none;
                border-radius: {ProfessionalTheme.RADIUS_LARGE}px;
            }}
            QLabel {{ background: transparent; }}
        """)

        self.setMinimumSize(220, 130)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )
        layout.setSpacing(ProfessionalTheme.SPACING_SM)

        # 第一行：图标 + 标题
        header_layout = QHBoxLayout()
        header_layout.setSpacing(ProfessionalTheme.SPACING_SM)

        # 图标标签
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {ProfessionalTheme.FONT_SIZE_H4}px;
                background: transparent;
            }}
        """)
        header_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                background: transparent;
            }}
        """)
        header_layout.addWidget(title_label,
                                alignment=Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 第二行：数值（主数据）
        value_container = QWidget()
        value_container.setStyleSheet("background: transparent;")
        value_layout = QHBoxLayout(value_container)
        value_layout.setContentsMargins(0, 0, 0, 0)

        self.value_label = QLabel(self._format_value())
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 根据趋势选择颜色
        if self.trend == "up" and "+" in self._format_value():
            text_color = ProfessionalTheme.SUCCESS_COLOR
        elif self.trend == "down" and "-" in self._format_value():
            text_color = ProfessionalTheme.ERROR_COLOR
        else:
            text_color = self.color

        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: {ProfessionalTheme.FONT_SIZE_H1}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_BOLD};
                font-family: {ProfessionalTheme.FONT_FAMILY_MONO};
                background: transparent;
                letter-spacing: -0.5px;
            }}
        """)
        value_layout.addWidget(self.value_label)

        layout.addWidget(value_container)

        # 第三行：副标题（可选）
        if self.subtitle:
            sub_label = QLabel(self.subtitle)
            sub_label.setStyleSheet(f"""
                QLabel {{
                    color: {ProfessionalTheme.TEXT_TERTIARY};
                    font-size: {ProfessionalTheme.FONT_SIZE_CAPTION}px;
                    background: transparent;
                    padding-top: {ProfessionalTheme.SPACING_XS}px;
                }}
            """)
            layout.addWidget(sub_label)

        # 添加底部装饰线
        bottom_line = QFrame()
        bottom_line.setFixedHeight(3)
        bottom_line.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.color}, stop:1 {self.color}33);
                border-radius: 2px;
            }}
        """)
        layout.addWidget(bottom_line)

        self.setLayout(layout)

        # hover 效果
        self.setGraphicsEffect(None)  # 移除可能的旧效果

    def _format_value(self) -> str:
        """格式化数值显示"""
        if abs(self.value) >= 10000:
            return f"{self.value:,.0f}{self.unit}"
        elif abs(self.value) >= 100:
            return f"{self.value:,.2f}{self.unit}"
        else:
            return f"{self.value:.2f}{self.unit}"

    def update_value(self, new_value: float):
        """更新数值（可带动画）"""
        self.value = new_value
        self.value_label.setText(self._format_value())
        self.valueChanged.emit(new_value)


class PieChartWidget(QWidget):
    """专业级饼图组件 - 渐变填充"""

    def __init__(self, title: str = "资产配置", parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_ui()

    def _setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ProfessionalTheme.SPACING_MD)

        # 标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(ProfessionalTheme.SPACING_SM, 0, 0, 0)

        title_icon = QLabel("📊")
        title_icon.setStyleSheet(f"""
            QLabel {{
                font-size: {ProfessionalTheme.FONT_SIZE_H3}px;
                background: transparent;
            }}
        """)
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_H4}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_SEMI_BOLD};
                background: transparent;
            }}
        """)

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addWidget(title_bar)

        # Matplotlib图表区域
        self.figure = Figure(figsize=(6, 5), dpi=120)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def update_chart(self, data: List[AllocationData]):
        """更新饼图数据"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = [item.category for item in data]
        sizes = [item.percentage for item in data]

        # 专业配色方案（柔和渐变）
        colors = ['#1677FF', '#00B42A', '#F53F3F', '#FF7D00', '#722ED1',
                  '#14C9C9', '#F5319D', '#FF8F1F']
        colors = colors[:len(data)]

        # 突出显示最大扇区
        explode = [
            0.02 if i == sizes.index(
                max(sizes)) else 0 for i in range(
                len(sizes))]

        # 绘制饼图（带阴影效果）
        wedges, texts, autotexts = ax.pie(
            sizes,
            explode=explode,
            labels=None,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            shadow=True,
            wedgeprops={'edgecolor': 'white', 'linewidth': 3},
            textprops={
                'fontsize': 11,
                'fontweight': 'bold',
                'color': '#FFFFFF'}
        )

        # 设置图例
        legend_labels = [
            f"{label} ({size:.1f}%)" for label,
            size in zip(
                labels,
                sizes)]
        ax.legend(wedges, legend_labels,
                  title="资产类别",
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1),
                  fontsize=11,
                  frameon=True,
                  fancybox=True,
                  shadow=True)

        ax.set_aspect('equal')
        ax.set_title('资产配置分布', fontsize=14, fontweight='bold', pad=20)

        self.figure.tight_layout()
        self.canvas.draw()


class BarChartWidget(QWidget):
    """专业级柱状图组件 - 渐变色条"""

    def __init__(self, title: str = "收益贡献排名", parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_ui()

    def _setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ProfessionalTheme.SPACING_MD)

        # 标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(ProfessionalTheme.SPACING_SM, 0, 0, 0)

        title_icon = QLabel("📈")
        title_icon.setStyleSheet(f"""
            QLabel {{
                font-size: {ProfessionalTheme.FONT_SIZE_H3}px;
                background: transparent;
            }}
        """)
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_H4}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_SEMI_BOLD};
                background: transparent;
            }}
        """)

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addWidget(title_bar)

        # Matplotlib图表区域
        self.figure = Figure(figsize=(7, 5), dpi=120)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(280)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def update_chart(self, holdings: List[FundHolding]):
        """更新柱状图数据"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # 取前10名
        top_holdings = sorted(
            holdings,
            key=lambda x: abs(
                x.profit_loss),
            reverse=True)[
            :10]

        names = [h.fund_name[:8] + "..." if len(h.fund_name) > 8 else h.fund_name
                 for h in top_holdings]
        profits = [h.profit_loss for h in top_holdings]

        y_pos = np.arange(len(names))

        # 根据正负值设置颜色
        colors = [ProfessionalTheme.SUCCESS_COLOR if p >= 0 else ProfessionalTheme.ERROR_COLOR
                  for p in profits]

        # 绘制水平柱状图（带渐变效果）
        bars = ax.barh(y_pos, profits, color=colors, height=0.6, alpha=0.85,
                       edgecolor='white', linewidth=1)

        # 添加数值标签
        for i, (bar, profit) in enumerate(zip(bars, profits)):
            width = bar.get_width()
            label_x = width + 50 if profit > 0 else width - 50
            ha = 'left' if profit > 0 else 'right'

            ax.text(label_x, bar.get_y() + bar.get_height() / 2,
                    f'¥{profit:,.0f}',
                    va='center', ha=ha,
                    fontsize=10,
                    fontweight='bold',
                    color='#1D2129')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=10)
        ax.invert_yaxis()  # 从上到下排列
        ax.axvline(x=0, color='#E5E6EB', linestyle='-', linewidth=1, alpha=0.5)

        ax.set_xlabel('盈亏金额 (元)', fontsize=11, labelpad=10)
        ax.set_title(
            '基金收益贡献排名 (Top 10)',
            fontsize=13,
            fontweight='bold',
            pad=15)

        # 美化坐标轴
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='y', length=0)

        self.figure.tight_layout()
        self.canvas.draw()


class PortfolioDashboard(QDialog):
    """投资组合分析仪表盘 - 专业版"""

    def __init__(self, portfolio_data: Dict[str, Any], parent=None):
        super().__init__(parent)

        self.portfolio_data = portfolio_data
        self.report: Optional[PortfolioReport] = None
        self.analyzer = PortfolioAnalyzer()

        self.setWindowTitle("📊 投资组合智能分析")
        self.setMinimumSize(1100, 750)

        ProfessionalTheme.apply_to_widget(self)

        plt.rcParams.update(MPL_THEME_CONFIG)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """初始化专业版UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            ProfessionalTheme.SPACING_XXL,
            ProfessionalTheme.SPACING_XXL,
            ProfessionalTheme.SPACING_XXL,
            ProfessionalTheme.SPACING_XXL
        )
        main_layout.setSpacing(ProfessionalTheme.SPACING_LG)

        # ========== 标题栏（渐变背景）==========
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ProfessionalTheme.PRIMARY_DARK},
                    stop:1 {ProfessionalTheme.PRIMARY_COLOR});
                border-radius: {ProfessionalTheme.RADIUS_LARGE}px;
                padding: {ProfessionalTheme.SPACING_MD}px;
            }}
        """)
        header_widget.setFixedHeight(80)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(
            ProfessionalTheme.SPACING_XL, 0,
            ProfessionalTheme.SPACING_XL, 0
        )

        # 左侧图标+标题
        left_group = QWidget()
        left_group.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_group)
        left_layout.setSpacing(ProfessionalTheme.SPACING_MD)

        icon_label = QLabel("📊")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 36px;
                background: transparent;
            }}
        """)

        title_text = QLabel("投资组合智能分析")
        title_text.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ProfessionalTheme.FONT_SIZE_H2}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_BOLD};
                background: transparent;
                letter-spacing: 1px;
            }}
        """)

        left_layout.addWidget(icon_label)
        left_layout.addWidget(title_text)
        header_layout.addWidget(left_group)
        header_layout.addStretch()

        # 右侧关闭按钮
        close_btn = QPushButton("✕ 关闭")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_SM}px {ProfessionalTheme.SPACING_LG}px;
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.45);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.10);
            }}
        """)
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(90)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header_widget)

        # ========== 关键指标卡片行（4个核心指标）==========
        metrics_widget = QWidget()
        metrics_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        metrics_layout = QHBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(ProfessionalTheme.SPACING_MD)

        # 创建4个指标卡片
        total_assets_card = MetricCard(
            "总资产", 0, "元", "当前持仓总市值",
            "💰", "#1677FF", "neutral"
        )
        total_profit_card = MetricCard(
            "累计盈亏", 0, "元", "含今日收益",
            "📈", "#00B42A", "up"
        )
        daily_profit_card = MetricCard(
            "今日盈亏", 0, "元", "",
            "⚡", "#1677FF", "up"
        )
        return_rate_card = MetricCard(
            "总收益率", 0, "%", "成立以来",
            "📊", "#722ED1", "neutral"
        )

        self.metric_cards = {
            'total_assets': total_assets_card,
            'total_profit': total_profit_card,
            'daily_profit': daily_profit_card,
            'return_rate': return_rate_card
        }

        metrics_layout.addWidget(total_assets_card)
        metrics_layout.addWidget(total_profit_card)
        metrics_layout.addWidget(daily_profit_card)
        metrics_layout.addWidget(return_rate_card)

        main_layout.addWidget(metrics_widget)

        # ========== 主内容区（Tab切换）==========
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {ProfessionalTheme.BG_PRIMARY};
                border-radius: {ProfessionalTheme.RADIUS_MEDIUM}px;
                padding: {ProfessionalTheme.SPACING_LG}px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {ProfessionalTheme.TEXT_SECONDARY};
                padding: {ProfessionalTheme.SPACING_MD}px {ProfessionalTheme.SPACING_XL}px;
                margin-right: {ProfessionalTheme.SPACING_SM}px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
            }}
            QTabBar::tab:selected {{
                color: {ProfessionalTheme.PRIMARY_COLOR};
                border-bottom: 2px solid {ProfessionalTheme.PRIMARY_COLOR};
                font-weight: {ProfessionalTheme.FONT_WEIGHT_SEMI_BOLD};
            }}
            QTabBar::tab:hover:!selected {{
                color: {ProfessionalTheme.PRIMARY_LIGHT};
                background: {ProfessionalTheme.BG_HOVER};
                border-bottom: 2px solid {ProfessionalTheme.BORDER_LIGHT};
            }}
        """)

        # Tab 1: 总览
        overview_tab = self._create_overview_tab()
        tab_widget.addTab(overview_tab, "📋 总览")

        # Tab 2: 资产配置
        allocation_tab = self._create_allocation_tab()
        tab_widget.addTab(allocation_tab, "🥧 资产配置")

        # Tab 3: 风险评估
        risk_tab = self._create_risk_tab()
        tab_widget.addTab(risk_tab, "⚠️ 风险评估")

        # Tab 4: 持仓明细
        holdings_tab = self._create_holdings_tab()
        tab_widget.addTab(holdings_tab, "📋 持仓明细")

        main_layout.addWidget(tab_widget)

        self.setLayout(main_layout)

    def _create_overview_tab(self) -> QWidget:
        """创建总览Tab页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(ProfessionalTheme.SPACING_LG, 0, 0, 0)
        layout.setSpacing(ProfessionalTheme.SPACING_LG)

        # 占位符（实际内容由_load_data填充）
        placeholder = QLabel("正在加载数据...")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_TERTIARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                padding: {ProfessionalTheme.SPACING_XXL}px;
            }}
        """)
        layout.addWidget(placeholder)

        return widget

    def _create_allocation_tab(self) -> QWidget:
        """创建资产配置Tab页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(ProfessionalTheme.SPACING_LG, 0, 0, 0)

        self.pie_chart = PieChartWidget("资产配置分布")
        layout.addWidget(self.pie_chart)

        return widget

    def _create_risk_tab(self) -> QWidget:
        """创建风险评估Tab页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(ProfessionalTheme.SPACING_LG, 0, 0, 0)

        placeholder = QLabel("风险评估指标加载中...")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

        return widget

    def _create_holdings_tab(self) -> QWidget:
        """创建持仓明细Tab页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(ProfessionalTheme.SPACING_LG, 0, 0, 0)

        self.bar_chart = BarChartWidget("收益贡献排名")
        layout.addWidget(self.bar_chart)

        return widget

    def _load_data(self):
        """加载并展示数据"""
        try:
            # 分析组合数据
            self.report = self.analyzer.analyze_portfolio(self.portfolio_data)

            if not self.report:
                return

            # 更新关键指标卡片
            self.metric_cards['total_assets'].update_value(
                self.report.total_assets)
            self.metric_cards['total_profit'].update_value(
                self.report.total_profit)
            self.metric_cards['daily_profit'].update_value(
                self.report.daily_profit)
            self.metric_cards['return_rate'].update_value(
                self.report.profit_percentage)

            # 更新饼图
            if hasattr(self, 'pie_chart') and self.report.allocations:
                self.pie_chart.update_chart(self.report.allocations)

            # 更新柱状图
            if hasattr(self, 'bar_chart') and self.report.top_holdings:
                self.bar_chart.update_chart(self.report.top_holdings)

        except Exception as e:
            from utils.logger import logger
            logger.error(f"加载仪表盘数据失败: {e}")
