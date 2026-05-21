#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级定投计算器UI组件
对标蚂蚁财富、天天基金等大厂应用的设计标准
"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient
from PySide6.QtWidgets import (QComboBox, QDialog, QDoubleSpinBox, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSpinBox, QTabWidget, QVBoxLayout,
                               QWidget)

from services.investment_calculator import (PREDEFINED_STRATEGIES,
                                            InvestmentCalculator,
                                            InvestmentResult,
                                            InvestmentStrategy)
from ui.theme.dark_theme import DarkTheme
from ui.theme.professional_theme import ProfessionalTheme
from ui.theme.theme_manager import get_theme_manager

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei',
                                   'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class AnimatedCard(QFrame):
    """带动画效果的卡片组件"""

    def __init__(
            self,
            title: str = "",
            color: str = ProfessionalTheme.PRIMARY_COLOR,
            parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: none;
                border-radius: {ProfessionalTheme.RADIUS_MEDIUM}px;
            }}
            QFrame:hover {{
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )
        layout.setSpacing(ProfessionalTheme.SPACING_SM)

        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.color};
                    font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
                    font-weight: {ProfessionalTheme.FONT_WEIGHT_SEMI_BOLD};
                    background: transparent;
                    letter-spacing: 0.5px;
                }}
            """)
            layout.addWidget(title_label)


class MetricCard(QFrame):
    """专业级指标卡片 - 带图标和趋势指示"""

    def __init__(self, title: str, value: str = "¥0", subtitle: str = "",
                 icon: str = "📊", color: str = ProfessionalTheme.PRIMARY_COLOR,
                 trend: str = "neutral", parent=None):
        super().__init__(parent)
        self.title = title
        self.value_text = value
        self.subtitle = subtitle
        self.icon = icon
        self.color = color
        self.trend = trend

        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: none;
                border-radius: {ProfessionalTheme.RADIUS_LARGE}px;
            }}
            QFrame:hover {{
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )
        layout.setSpacing(ProfessionalTheme.SPACING_XS)

        # 标题行（图标 + 标题）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(ProfessionalTheme.SPACING_SM)

        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(
            f"QLabel {{ font-size: 20px; background: transparent; }}")
        header_layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                background: transparent;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 数值
        value_label = QLabel(self.value_text)
        value_label.setObjectName("value_label")
        trend_color = self._get_trend_color()
        value_label.setStyleSheet(f"""
            QLabel#value_label {{
                color: {trend_color};
                font-size: {ProfessionalTheme.FONT_SIZE_H3}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_BOLD};
                background: transparent;
                letter-spacing: -0.5px;
            }}
        """)
        layout.addWidget(value_label)

        # 副标题/描述
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: {ProfessionalTheme.TEXT_TERTIARY};
                    font-size: {ProfessionalTheme.FONT_SIZE_CAPTION}px;
                    background: transparent;
                }}
            """)
            layout.addWidget(subtitle_label)

        self.value_label = value_label

    def _get_trend_color(self) -> str:
        """根据趋势获取颜色"""
        colors = {
            "up": ProfessionalTheme.SUCCESS_COLOR,
            "down": ProfessionalTheme.ERROR_COLOR,
            "neutral": self.color
        }
        return colors.get(self.trend, self.color)

    def update_value(self, new_value: str, trend: str = None):
        """更新数值"""
        self.value_label.setText(new_value)
        if trend:
            self.trend = trend
            self.value_label.setStyleSheet(f"""
                QLabel#value_label {{
                    color: {self._get_trend_color()};
                    font-size: {ProfessionalTheme.FONT_SIZE_H3}px;
                    font-weight: {ProfessionalTheme.FONT_WEIGHT_BOLD};
                    background: transparent;
                }}
            """)


class GradientHeader(QFrame):
    """渐变头部组件"""

    def __init__(
            self,
            title: str,
            subtitle: str = "",
            gradient_colors: tuple = (
                ProfessionalTheme.PRIMARY_COLOR,
                "#4096FF"),
            parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.gradient_colors = gradient_colors
        self.setFixedHeight(100)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.gradient_colors[0]}, stop:1 {self.gradient_colors[1]});
                border-radius: {ProfessionalTheme.RADIUS_LARGE}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            ProfessionalTheme.SPACING_XL,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL,
            ProfessionalTheme.SPACING_LG
        )
        layout.setSpacing(ProfessionalTheme.SPACING_XS)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 26px;
                font-weight: bold;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(title_label)

        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.85);
                    font-size: 13px;
                    background: transparent;
                }
            """)
            layout.addWidget(subtitle_label)


class InvestmentCalculatorDialog(QDialog):
    """专业级定投计算器对话框 - 对标大厂应用"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能定投计算器")
        self.setMinimumSize(1300, 850)

        # 使用主题管理器应用当前主题
        self.theme_manager = get_theme_manager()
        theme_class = DarkTheme if self.theme_manager.is_dark_mode else ProfessionalTheme
        theme_class.apply_to_widget(self)

        self.current_result = None

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # 渐变头部
        header = GradientHeader(
            title="💰 智能定投计算器",
            subtitle="专业的投资收益测算与策略分析工具"
        )
        main_layout.addWidget(header)

        # Tab页面容器
        tab_container = QFrame()
        tab_container.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: {ProfessionalTheme.RADIUS_LARGE}px;
                border: 1px solid {ProfessionalTheme.BORDER_LIGHT};
            }}
        """)
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(4, 4, 4, 4)  # 为Tab留出圆角空间
        tab_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
                border-radius: {ProfessionalTheme.RADIUS_LARGE - 4}px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {ProfessionalTheme.TEXT_SECONDARY};
                padding: 12px 24px;
                margin-right: 2px;
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                border-top-left-radius: {ProfessionalTheme.RADIUS_MEDIUM}px;
                border-top-right-radius: {ProfessionalTheme.RADIUS_MEDIUM}px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {ProfessionalTheme.PRIMARY_COLOR};
                border-bottom: 3px solid {ProfessionalTheme.PRIMARY_COLOR};
            }}
            QTabBar::tab:hover:!selected {{
                background: {ProfessionalTheme.BG_HOVER};
                color: {ProfessionalTheme.PRIMARY_COLOR};
            }}
        """)

        # 创建各个标签页
        self.create_calculator_tab()
        self.create_strategy_comparison_tab()
        self.create_lump_sum_vs_dca_tab()
        self.create_compound_interest_tab()
        self.create_investment_advice_tab()

        tab_layout.addWidget(self.tab_widget)
        main_layout.addWidget(tab_container)
        self.setLayout(main_layout)

    def create_calculator_tab(self):
        """创建基础计算器标签页 - 专业版"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "QScrollArea {border: none; background: transparent;}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # 参数输入区
        input_card = AnimatedCard(
            title="📊 投资参数",
            color=ProfessionalTheme.INFO_COLOR)
        input_layout = QGridLayout(input_card)
        input_layout.setSpacing(20)
        input_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        # 每月投入金额
        amount_label = QLabel("每月定投金额")
        amount_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                background: transparent;
            }}
        """)
        input_layout.addWidget(amount_label, 0, 0)

        self.monthly_amount_input = QDoubleSpinBox()
        self.monthly_amount_input.setRange(100, 10000000)
        self.monthly_amount_input.setValue(2000)
        self.monthly_amount_input.setSuffix(" 元")
        self.monthly_amount_input.setSingleStep(500)
        self.monthly_amount_input.setStyleSheet(
            ProfessionalTheme.get_input_style())
        input_layout.addWidget(self.monthly_amount_input, 0, 1)

        # 预期年化收益率
        return_label = QLabel("预期年化收益率")
        return_label.setStyleSheet(amount_label.styleSheet())
        input_layout.addWidget(return_label, 1, 0)

        self.expected_return_input = QDoubleSpinBox()
        self.expected_return_input.setRange(0, 50)
        self.expected_return_input.setValue(10)
        self.expected_return_input.setSuffix(" %")
        self.expected_return_input.setSingleStep(1)
        self.expected_return_input.setStyleSheet(
            ProfessionalTheme.get_input_style())
        input_layout.addWidget(self.expected_return_input, 1, 1)

        # 投资年限
        years_label = QLabel("投资年限")
        years_label.setStyleSheet(amount_label.styleSheet())
        input_layout.addWidget(years_label, 2, 0)

        self.years_input = QSpinBox()
        self.years_input.setRange(1, 40)
        self.years_input.setValue(10)
        self.years_input.setSuffix(" 年")
        self.years_input.setStyleSheet(ProfessionalTheme.get_input_style())
        input_layout.addWidget(self.years_input, 2, 1)

        # 通胀率
        inflation_label = QLabel("预期通胀率")
        inflation_label.setStyleSheet(amount_label.styleSheet())
        input_layout.addWidget(inflation_label, 3, 0)

        self.inflation_rate_input = QDoubleSpinBox()
        self.inflation_rate_input.setRange(0, 10)
        self.inflation_rate_input.setValue(3)
        self.inflation_rate_input.setSuffix(" %")
        self.inflation_rate_input.setDecimals(1)
        self.inflation_rate_input.setStyleSheet(
            ProfessionalTheme.get_input_style())
        input_layout.addWidget(self.inflation_rate_input, 3, 1)

        layout.addWidget(input_card)

        # 结果展示区
        result_card = AnimatedCard(
            title="📈 计算结果",
            color=ProfessionalTheme.SUCCESS_COLOR)
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )
        result_layout.setSpacing(16)

        # 指标卡片网格
        metrics_container = QWidget()
        metrics_container.setStyleSheet("background: transparent;")
        metrics_grid = QGridLayout(metrics_container)
        metrics_grid.setSpacing(16)

        metric_items = [
            ("累计本金", "principal_value", "💰", ProfessionalTheme.TEXT_SECONDARY),
            ("最终资产", "final_value", "💎", ProfessionalTheme.SUCCESS_COLOR),
            ("总收益", "profit_value", "📈", ProfessionalTheme.ERROR_COLOR),
            ("总收益率", "return_pct", "📊", ProfessionalTheme.WARNING_COLOR),
            ("购买力等值", "inflation_adjusted", "⚖️", "#722ED1"),
            ("实际收益率", "real_return", "🎯", "#14C9C9"),
        ]

        self.result_labels = {}
        for row, (name, key, icon, color) in enumerate(metric_items):
            card = MetricCard(
                title=name,
                value="¥0",
                icon=icon,
                color=color
            )
            metrics_grid.addWidget(card, row // 3, row % 3)
            self.result_labels[key] = card

        result_layout.addWidget(metrics_container)

        # 详细说明文本
        self.detail_text = QLabel("")
        self.detail_text.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
                background: {ProfessionalTheme.BG_SECONDARY};
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_MD}px;
                line-height: 1.8;
            }}
        """)
        self.detail_text.setWordWrap(True)
        self.detail_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        result_layout.addWidget(self.detail_text)

        layout.addWidget(result_card)
        layout.addStretch()

        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "🧮 定投计算")

    def create_strategy_comparison_tab(self):
        """创建策略对比标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "QScrollArea {border: none; background: transparent;}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 说明卡片
        intro_card = AnimatedCard(
            title="💡 策略对比说明",
            color=ProfessionalTheme.INFO_COLOR)
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        intro_label = QLabel(
            "对比不同投资策略的长期表现，帮助您选择最适合的投资方式。\n\n"
            "系统预设了5种经典策略：保守型、稳健型、平衡型、成长型、激进型。"
        )
        intro_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                line-height: 1.8;
                background: transparent;
            }}
        """)
        intro_label.setWordWrap(True)
        intro_layout.addWidget(intro_label)

        # 对比按钮
        compare_btn = QPushButton("🔄 开始策略对比")
        compare_btn.clicked.connect(self.compare_strategies)
        compare_btn.setStyleSheet(
            ProfessionalTheme.get_button_style('primary'))
        compare_btn.setFixedHeight(44)
        intro_layout.addWidget(compare_btn)

        layout.addWidget(intro_card)

        # 结果展示区域
        results_card = AnimatedCard(
            title="🏆 策略排名",
            color=ProfessionalTheme.WARNING_COLOR)
        strategy_layout = QVBoxLayout(results_card)
        strategy_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        self.strategy_table_container = QWidget()
        self.strategy_table_container.setStyleSheet("background: transparent;")
        self.strategy_table_layout = QVBoxLayout(self.strategy_table_container)
        self.strategy_table_layout.setContentsMargins(0, 0, 0, 0)
        self.strategy_table_layout.setSpacing(12)
        strategy_layout.addWidget(self.strategy_table_container)

        layout.addWidget(results_card)
        layout.addStretch()

        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "⚖️ 策略对比")

    def create_lump_sum_vs_dca_tab(self):
        """创建一次性vs定投对比标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "QScrollArea {border: none; background: transparent;}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 参数设置卡片
        params_card = AnimatedCard(title="⚙️ 对比参数", color="#8B5CF6")
        params_grid = QGridLayout(params_card)
        params_grid.setSpacing(16)
        params_grid.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        label_style = f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                background: transparent;
            }}
        """

        params_grid.addWidget(QLabel("总投资金额"), 0, 0)
        self.lump_sum_principal = QDoubleSpinBox()
        self.lump_sum_principal.setRange(1000, 100000000)
        self.lump_sum_principal.setValue(240000)
        self.lump_sum_principal.setSuffix(" 元")
        self.lump_sum_principal.setStyleSheet(
            ProfessionalTheme.get_input_style())
        params_grid.addWidget(self.lump_sum_principal, 0, 1)

        params_grid.addWidget(QLabel("预期年化收益率"), 1, 0)
        self.lump_sum_return = QDoubleSpinBox()
        self.lump_sum_return.setRange(0, 30)
        self.lump_sum_return.setValue(10)
        self.lump_sum_return.setSuffix(" %")
        self.lump_sum_return.setStyleSheet(ProfessionalTheme.get_input_style())
        params_grid.addWidget(self.lump_sum_return, 1, 1)

        params_grid.addWidget(QLabel("投资年限"), 2, 0)
        self.lump_sum_years = QSpinBox()
        self.lump_sum_years.setRange(1, 30)
        self.lump_sum_years.setValue(10)
        self.lump_sum_years.setSuffix(" 年")
        self.lump_sum_years.setStyleSheet(ProfessionalTheme.get_input_style())
        params_grid.addWidget(self.lump_sum_years, 2, 1)

        compare_btn = QPushButton("🔍 开始对比分析")
        compare_btn.clicked.connect(self.compare_lump_sum_dca)
        compare_btn.setStyleSheet(ProfessionalTheme.get_button_style('ghost'))
        compare_btn.setStyleSheet(compare_btn.styleSheet().replace(
            "border: 1px solid #1677FF;",
            "border: 1px solid #8B5CF6;"
        ).replace(
            "color: #1677FF;",
            "color: #8B5CF6;"
        ))
        compare_btn.setFixedHeight(40)
        params_grid.addWidget(compare_btn, 3, 0, 1, 2)

        layout.addWidget(params_card)

        # 结果展示
        result_card = AnimatedCard(title="📊 对比结果", color="#8B5CF6")
        dca_layout = QVBoxLayout(result_card)
        dca_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        self.dca_result_label = QLabel(
            "<div style='text-align: center; padding: 40px;'>"
            "<p style='color: #86909C; font-size: 15px;'>点击「开始对比分析」查看一次性投入与定投的差异</p>"
            "<p style='color: #C9CDD4; font-size: 13px; margin-top: 16px;'>💡 提示：在市场持续上涨时，一次性投入通常更优；<br>在市场波动较大时，定投可以降低平均成本风险。</p>"
            "</div>")
        self.dca_result_label.setTextFormat(Qt.RichText)
        self.dca_result_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                background: {ProfessionalTheme.BG_SECONDARY};
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_LG}px;
                line-height: 2;
            }}
        """)
        self.dca_result_label.setWordWrap(True)
        dca_layout.addWidget(self.dca_result_label)

        layout.addWidget(result_card)
        layout.addStretch()

        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "💵 一次 vs 定投")

    def create_compound_interest_tab(self):
        """创建复利计算标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "QScrollArea {border: none; background: transparent;}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 公式说明卡片
        formula_card = AnimatedCard(
            title="📐 复利公式",
            color=ProfessionalTheme.WARNING_COLOR)
        formula_layout = QVBoxLayout(formula_card)
        formula_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        formula_label = QLabel(
            "<h3 style='color: #1D2129; margin: 0 0 12px 0;'>A = P(1 + r/n)<sup>nt</sup></h3>"
            "<table style='width: 100%; color: #4E5969; font-size: 14px;'>"
            "<tr><td><b>A</b> = 最终金额</td><td><b>P</b> = 本金</td></tr>"
            "<tr><td><b>r</b> = 年利率</td><td><b>n</b> = 每年复利次数</td></tr>"
            "<tr><td colspan='2'><b>t</b> = 年数</td></tr>"
            "</table>")
        formula_label.setTextFormat(Qt.RichText)
        formula_label.setStyleSheet("background: transparent;")
        formula_layout.addWidget(formula_label)

        layout.addWidget(formula_card)

        # 参数输入
        compound_params = QCompoundInterestParamsGroup()
        layout.addWidget(compound_params)

        # 计算按钮
        calc_btn = QPushButton("🧮 计算复利收益")
        calc_btn.clicked.connect(
            lambda: self.calculate_compound(compound_params))
        calc_btn.setStyleSheet(ProfessionalTheme.get_button_style('success'))
        calc_btn.setFixedHeight(44)
        layout.addWidget(calc_btn)

        # 结果显示
        result_card = AnimatedCard(
            title="✨ 计算结果",
            color=ProfessionalTheme.WARNING_COLOR)
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        self.compound_result_label = QLabel("")
        self.compound_result_label.setTextFormat(Qt.RichText)
        self.compound_result_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                background: linear-gradient(135deg, #FFF7E8, #FEF3C7);
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_LG}px;
                line-height: 2;
                border-left: 4px solid {ProfessionalTheme.WARNING_COLOR};
            }}
        """)
        self.compound_result_label.setWordWrap(True)
        result_layout.addWidget(self.compound_result_label)

        layout.addWidget(result_card)
        layout.addStretch()

        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "📈 复利计算")

    def create_investment_advice_tab(self):
        """创建投资建议标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            "QScrollArea {border: none; background: transparent;}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 投资画像卡片
        advice_card = AnimatedCard(title="🎯 您的投资画像", color="#EC4899")
        advice_grid = QGridLayout(advice_card)
        advice_grid.setSpacing(16)
        advice_grid.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        label_style = f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                background: transparent;
            }}
        """

        advice_grid.addWidget(QLabel("风险承受能力"), 0, 0)
        self.risk_tolerance_combo = QComboBox()
        self.risk_tolerance_combo.addItems(["保守型", "稳健型", "激进型"])
        self.risk_tolerance_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ProfessionalTheme.BG_PRIMARY};
                border: 1.5px solid {ProfessionalTheme.BORDER_COLOR};
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_SM}px {ProfessionalTheme.SPACING_MD}px;
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                min-width: 180px;
                color: {ProfessionalTheme.TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {ProfessionalTheme.PRIMARY_COLOR};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background: {ProfessionalTheme.BG_PRIMARY};
                border: 1px solid {ProfessionalTheme.BORDER_COLOR};
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                selection-background-color: {ProfessionalTheme.PRIMARY_BG};
                selection-color: {ProfessionalTheme.PRIMARY_DARK};
            }}
        """)
        advice_grid.addWidget(self.risk_tolerance_combo, 0, 1)

        advice_grid.addWidget(QLabel("投资目标"), 1, 0)
        self.goal_combo = QComboBox()
        self.goal_combo.addItems(["养老储备", "子女教育", "应急资金", "财富增值"])
        self.goal_combo.setStyleSheet(self.risk_tolerance_combo.styleSheet())
        advice_grid.addWidget(self.goal_combo, 1, 1)

        advice_grid.addWidget(QLabel("投资期限"), 2, 0)
        self.horizon_spin = QSpinBox()
        self.horizon_spin.setRange(1, 40)
        self.horizon_spin.setValue(10)
        self.horizon_spin.setSuffix(" 年")
        self.horizon_spin.setStyleSheet(ProfessionalTheme.get_input_style())
        advice_grid.addWidget(self.horizon_spin, 2, 1)

        generate_btn = QPushButton("✨ 生成个性化建议")
        generate_btn.clicked.connect(self.generate_advice)
        generate_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #EC4899, stop:1 #DB2777);
                color: white;
                border: none;
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_SM}px {ProfessionalTheme.SPACING_MD}px;
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #DB2777, stop:1 #BE185D);
            }}
            QPushButton:pressed {{
                background: #BE185D;
            }}
        """)
        generate_btn.setFixedHeight(44)
        advice_grid.addWidget(generate_btn, 3, 0, 1, 2)

        layout.addWidget(advice_card)

        # 建议展示
        result_card = AnimatedCard(title="💡 个性化投资方案", color="#EC4899")
        advice_layout = QVBoxLayout(result_card)
        advice_layout.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        self.advice_text = QLabel(
            "<div style='text-align: center; padding: 30px;'>"
            "<p style='color: #86909C; font-size: 15px;'>填写您的情况后，点击「生成个性化建议」</p>"
            "<p style='color: #C9CDD4; font-size: 13px; margin-top: 12px;'>系统将根据您的风险偏好、投资目标和时间规划<br>为您提供专业的资产配置建议和预期收益测算</p>"
            "</div>")
        self.advice_text.setTextFormat(Qt.RichText)
        self.advice_text.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: {ProfessionalTheme.FONT_SIZE_SMALL}px;
                background: linear-gradient(135deg, #FDF2F8, #FCE7F3);
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_LG}px;
                line-height: 2;
                border-left: 4px solid #EC4899;
            }}
        """)
        self.advice_text.setWordWrap(True)
        self.advice_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        advice_layout.addWidget(self.advice_text)

        layout.addWidget(result_card)
        layout.addStretch()

        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "🤖 智能建议")

    def connect_signals(self):
        """连接信号和槽"""
        try:
            if hasattr(self, 'monthly_amount_input'):
                self.monthly_amount_input.valueChanged.connect(
                    self.calculate_basic)
                self.expected_return_input.valueChanged.connect(
                    self.calculate_basic)
                self.years_input.valueChanged.connect(self.calculate_basic)
                self.inflation_rate_input.valueChanged.connect(
                    self.calculate_basic)

                from utils.logger import logger
                logger.info("定投计算器：已连接基本计算信号")

            self.calculate_basic()

        except Exception as e:
            from utils.logger import logger
            logger.error(f"连接定投计算器信号失败: {e}")

    def calculate_basic(self):
        """执行基本定投计算"""
        try:
            monthly_amount = self.monthly_amount_input.value()
            expected_return = self.expected_return_input.value()
            years = self.years_input.value()
            inflation_rate = self.inflation_rate_input.value() / 100

            result = InvestmentCalculator.calculate_fixed_investment(
                monthly_amount=monthly_amount,
                expected_return=expected_return,
                years=years,
                inflation_rate=inflation_rate
            )

            self.current_result = result
            self.update_basic_result_display(result)

        except Exception as e:
            from utils.logger import logger
            logger.error(f"定投计算错误: {e}")

    def update_basic_result_display(self, result: InvestmentResult):
        """更新基本计算结果展示"""
        profit_trend = "up" if result.total_profit >= 0 else "down"
        profit_sign = "+" if result.total_profit >= 0 else ""
        pct_sign = "+" if result.profit_percentage >= 0 else ""
        real_pct_sign = "+" if result.real_return_rate >= 0 else ""

        self.result_labels['principal_value'].update_value(
            f"¥{result.total_principal:,.2f}"
        )
        self.result_labels['final_value'].update_value(
            f"¥{result.final_amount:,.2f}"
        )
        self.result_labels['profit_value'].update_value(
            f"{profit_sign}¥{result.total_profit:,.2f}",
            trend=profit_trend
        )
        self.result_labels['return_pct'].update_value(
            f"{pct_sign}{result.profit_percentage:.2f}%",
            trend=profit_trend
        )

        real_profit_trend = "up" if result.real_profit >= 0 else "down"
        self.result_labels['inflation_adjusted'].update_value(
            f"¥{result.inflation_adjusted_value:,.2f}"
        )
        self.result_labels['real_return'].update_value(
            f"{real_pct_sign}{result.real_return_rate:.2f}%",
            trend=real_profit_trend
        )

        if result.summary_text:
            self.detail_text.setText(result.summary_text.strip())

    def compare_strategies(self):
        """对比预设策略"""
        try:
            comparison = InvestmentCalculator.compare_strategies(
                PREDEFINED_STRATEGIES)

            while self.strategy_table_layout.count():
                item = self.strategy_table_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            results = comparison['results']

            for idx, (name, result) in enumerate(results.items()):
                frame = QFrame()
                is_best = name == comparison['best_by_profit']

                rank_emoji = ["🥇", "🥈", "🥉"][idx] if idx < 3 else f"#{idx+1}"
                badge = f" {rank_emoji}" if is_best else f" #{idx+1}"

                bg_color = "#F6FFED" if is_best else "#FAFBFC"
                border_color = ProfessionalTheme.SUCCESS_COLOR if is_best else ProfessionalTheme.BORDER_LIGHT

                frame.setStyleSheet(f"""
                    QFrame {{
                        background: {bg_color};
                        border-radius: {ProfessionalTheme.RADIUS_MEDIUM}px;
                        border-left: 4px solid {border_color};
                        padding: {ProfessionalTheme.SPACING_MD}px;
                    }}
                    QFrame:hover {{
                        background: white;
                    }}
                """)

                h_layout = QHBoxLayout(frame)
                h_layout.setSpacing(ProfessionalTheme.SPACING_MD)

                name_lbl = QLabel(f"{name}{badge}")
                name_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {'#00B42A' if is_best else ProfessionalTheme.TEXT_PRIMARY};
                        font-size: {ProfessionalTheme.FONT_SIZE_H4}px;
                        font-weight: {'bold' if is_best else ProfessionalTheme.FONT_WEIGHT_SEMI_BOLD};
                        background: transparent;
                    }}
                """)
                h_layout.addWidget(name_lbl)

                h_layout.addStretch()

                final_lbl = QLabel(f"¥{result.final_amount:,.0f}")
                final_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {ProfessionalTheme.SUCCESS_COLOR};
                        font-size: {ProfessionalTheme.FONT_SIZE_H3}px;
                        font-weight: bold;
                        background: transparent;
                    }}
                """)
                h_layout.addWidget(final_lbl)

                ret_lbl = QLabel(f"{result.profit_percentage:+.1f}%")
                ret_color = ProfessionalTheme.SUCCESS_COLOR if result.profit_percentage >= 0 else ProfessionalTheme.ERROR_COLOR
                ret_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {ret_color};
                        font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                        font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                        background: transparent;
                    }}
                """)
                h_layout.addWidget(ret_lbl)

                self.strategy_table_layout.addWidget(frame)

            self.strategy_table_layout.addStretch()

        except Exception as e:
            from utils.logger import logger
            logger.error(f"策略对比失败: {e}")

    def compare_lump_sum_dca(self):
        """对比一次性投入 vs 定投"""
        try:
            principal = self.lump_sum_principal.value()
            expected_return = self.lump_sum_return.value()
            years = self.lump_sum_years.value()

            result = InvestmentCalculator.calculate_lump_sum_vs_dca(
                principal=principal,
                expected_return=expected_return,
                years=years
            )

            lump = result['lump_sum']
            dca = result['dca']
            winner = result['winner']
            diff = result['difference']

            text = f"""
<div style='padding: 8px;'>
<h3 style='color: #1D2129; margin: 0 0 20px 0; font-size: 18px;'>💰 一次性投入 vs 定投（DCA）对比</h3>

<table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
<tr>
<td style='padding: 16px; background: #F0F5FF; border-radius: 8px; vertical-align: top; width: 48%;'>
<h4 style='color: #8B5CF6; margin: 0 0 12px 0;'>🏆 一次性投入</h4>
<p style='margin: 8px 0; color: #4E5969;'><b>最终资产：</b><span style='color: #00B42A; font-size: 18px; font-weight: bold;'>¥{lump.final_amount:,.2f}</span></p>
<p style='margin: 8px 0; color: #4E5969;'><b>总收益：</b><span style='color: {"#F53F3F" if lump.total_profit >= 0 else "#00B42A"}; font-weight: bold;'>¥{lump.total_profit:+,.2f}</span></p>
<p style='margin: 8px 0; color: #86909C;'><b>收益率：</b>{lump.profit_percentage:+.2f}%</p>
</td>

<td style='width: 4%;'></td>

<td style='padding: 16px; background: #F6FFED; border-radius: 8px; vertical-align: top; width: 48%;'>
<h4 style='color: #00B42A; margin: 0 0 12px 0;'>📅 分期定投</h4>
<p style='margin: 8px 0; color: #4E5969;'><b>最终资产：</b><span style='color: #00B42A; font-size: 18px; font-weight: bold;'>¥{dca.final_amount:,.2f}</span></p>
<p style='margin: 8px 0; color: #4E5969;'><b>总收益：</b><span style='color: {"#F53F3F" if dca.total_profit >= 0 else "#00B42A"}; font-weight: bold;'>¥{dca.total_profit:+,.2f}</span></p>
<p style='margin: 8px 0; color: #86909C;'><b>收益率：</b>{dca.profit_percentage:+.2f}%</p>
</td>
</tr>
</table>

<div style='background: #FFF7E8; padding: 16px; border-radius: 8px; border-left: 4px solid #FF7D00;'>
<p style='margin: 0; color: #1D2129;'><b>⚖️ 差异分析</b></p>
<p style='margin: 8px 0 0 0; color: #4E5969;'>差额：<b style='color: #FF7D00; font-size: 16px;'>¥{diff:+,.2f}</b>&nbsp;&nbsp;|&nbsp;&nbsp;获胜方：<b style='color: #8B5CF6; font-size: 16px;'>{winner}</b></p>
</div>

<p style='margin-top: 16px; color: #86909C; font-size: 13px; font-style: italic;'>💡 提示：此对比假设市场稳定上涨。实际中，定投可以平滑市场波动风险。</p>
</div>
"""
            self.dca_result_label.setText(text)
            self.dca_result_label.setTextFormat(Qt.RichText)

        except Exception as e:
            from utils.logger import logger
            logger.error(f"一次性vs定投对比失败: {e}")

    def calculate_compound(self, params_group):
        """计算复利收益"""
        try:
            principal = params_group.principal_input.value()
            rate = params_group.rate_input.value()
            times_per_year = params_group.times_combo.currentData()
            years = params_group.years_input.value()

            result = InvestmentCalculator.calculate_compound_interest(
                principal=principal,
                rate=rate,
                times_per_year=times_per_year,
                years=years
            )

            multiplier = result.final_amount / principal

            text = f"""
<div style='padding: 8px;'>
<h3 style='color: #1D2129; margin: 0 0 20px 0; font-size: 18px;'>📈 复利计算结果</h3>

<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px;'>
<div style='background: #FAFBFC; padding: 16px; border-radius: 8px;'>
<p style='margin: 0; color: #86909C; font-size: 13px;'>💰 本金</p>
<p style='margin: 8px 0 0 0; color: #1D2129; font-size: 20px; font-weight: bold;'>¥{principal:,.2f}</p>
</div>

<div style='background: #FAFBFC; padding: 16px; border-radius: 8px;'>
<p style='margin: 0; color: #86909C; font-size: 13px;'>📊 利率</p>
<p style='margin: 8px 0 0 0; color: #1D2129; font-size: 20px; font-weight: bold;'>{rate:.1f}% / 年</p>
</div>

<div style='background: #FAFBFC; padding: 16px; border-radius: 8px;'>
<p style='margin: 0; color: #86909C; font-size: 13px;'>🔄 复利频率</p>
<p style='margin: 8px 0 0 0; color: #1D2129; font-size: 20px; font-weight: bold;'>每年{times_per_year}次</p>
</div>

<div style='background: #FAFBFC; padding: 16px; border-radius: 8px;'>
<p style='margin: 0; color: #86909C; font-size: 13px;'>⏱️ 期限</p>
<p style='margin: 8px 0 0 0; color: #1D2129; font-size: 20px; font-weight: bold;'>{years}年</p>
</div>
</div>

<div style='background: #F6FFED; padding: 20px; border-radius: 8px; border: 2px solid #00B42A; text-align: center;'>
<p style='margin: 0; color: #00B42A; font-size: 14px; font-weight: medium;'>最终资产</p>
<p style='margin: 8px 0 0 0; color: #00B42A; font-size: 32px; font-weight: bold;'>¥{result.final_amount:,.2f}</p>
</div>

<div style='margin-top: 16px; display: flex; gap: 16px;'>
<div style='flex: 1; background: #FFECE8; padding: 16px; border-radius: 8px; text-align: center;'>
<p style='margin: 0; color: #F53F3F; font-size: 13px;'>总收益</p>
<p style='margin: 8px 0 0 0; color: #F53F3F; font-size: 22px; font-weight: bold;'>¥{result.total_profit:+,.2f}</p>
</div>

<div style='flex: 1; background: #FFF7E8; padding: 16px; border-radius: 8px; text-align: center;'>
<p style='margin: 0; color: #FF7D00; font-size: 13px;'>总收益率</p>
<p style='margin: 8px 0 0 0; color: #FF7D00; font-size: 22px; font-weight: bold;'>{result.profit_percentage:+.2f}%</p>
</div>
</div>

<p style='margin-top: 20px; padding: 16px; background: #F0F5FF; border-radius: 8px; text-align: center; color: #1677FF; font-size: 15px; font-weight: medium;'>
✨ 复利的威力：经过{years}年，您的本金增长了 <b>{multiplier:.1f}</b> 倍！
</p>
</div>
"""
            self.compound_result_label.setText(text)
            self.compound_result_label.setTextFormat(Qt.RichText)

        except Exception as e:
            from utils.logger import logger
            logger.error(f"复利计算失败: {e}")

    def generate_advice(self):
        """生成个性化投资建议"""
        try:
            risk_tolerance_map = {
                '保守型': 'conservative',
                '稳健型': 'moderate',
                '激进型': 'aggressive'
            }

            goal_map = {
                '养老储备': 'retirement',
                '子女教育': 'education',
                '应急资金': 'emergency',
                '财富增值': 'wealth'
            }

            risk = risk_tolerance_map.get(
                self.risk_tolerance_combo.currentText(), 'moderate')
            goal = goal_map.get(self.goal_combo.currentText(), 'wealth')
            horizon = self.horizon_spin.value()

            advice = InvestmentCalculator.generate_investment_advice(
                risk_tolerance=risk,
                investment_goal=goal,
                time_horizon=horizon
            )

            proj = advice['example_projection']
            alloc = advice['asset_allocation']

            tips_html = '<br>'.join(
                [f"<p style='margin: 6px 0;'>• {tip}</p>" for tip in advice['tips']])

            text = f"""
<div style='padding: 8px;'>
<h3 style='color: #1D2129; margin: 0 0 20px 0; font-size: 18px;'>💡 为您量身定制的投资方案</h3>

<div style='background: #F0F5FF; padding: 20px; border-radius: 8px; margin-bottom: 20px;'>
<h4 style='color: #1677FF; margin: 0 0 16px 0;'>👤 您的投资画像</h4>
<p style='margin: 6px 0; color: #4E5969;'>• 风险承受：<b>{self.risk_tolerance_combo.currentText()}</b></p>
<p style='margin: 6px 0; color: #4E5969;'>• 投资目标：<b>{self.goal_combo.currentText()}</b></p>
<p style='margin: 6px 0; color: #4E5969;'>• 投资期限：<b>{horizon}年</b></p>
</div>

<div style='background: #FAFBFC; padding: 20px; border-radius: 8px; margin-bottom: 20px;'>
<h4 style='color: #1D2129; margin: 0 0 16px 0;'>📊 推荐资产配置</h4>
<div style='display: flex; gap: 16px; align-items: center;'>
<div style='flex: 1; background: #E8F3FF; padding: 16px; border-radius: 8px; text-align: center;'>
<p style='margin: 0; color: #1677FF; font-size: 13px;'>权益类（股票/混合）</p>
<p style='margin: 8px 0 0 0; color: #1677FF; font-size: 28px; font-weight: bold;'>{alloc['equity']}%</p>
</div>
<div style='flex: 1; background: #F6FFED; padding: 16px; border-radius: 8px; text-align: center;'>
<p style='margin: 0; color: #00B42A; font-size: 13px;'>固收类（债券/货币）</p>
<p style='margin: 8px 0 0 0; color: #00B42A; font-size: 28px; font-weight: bold;'>{alloc['fixed_income']}%</p>
</div>
</div>
</div>

<div style='background: #F6FFED; padding: 20px; border-radius: 8px; border: 2px solid #00B42A; margin-bottom: 20px;'>
<h4 style='color: #00B42A; margin: 0 0 16px 0;'>🎯 预期收益测算（{horizon}年后）</h4>
<p style='margin: 8px 0; color: #4E5969;'>• 累计本金：<b>¥{proj.total_principal:,.2f}</b></p>
<p style='margin: 8px 0; color: #4E5969;'>• 最终资产：<b style='color: #00B42A; font-size: 20px;'>¥{proj.final_amount:,.2f}</b></p>
<p style='margin: 8px 0; color: #4E5969;'>• 总收益：<b style='color: {"#F53F3F" if proj.total_profit >= 0 else "#00B42A"}; font-size: 18px;'>¥{proj.total_profit:+,.2f}</b> (<b>{proj.profit_percentage:+.2f}%</b>)</p>
</div>

<div style='background: #FDF2F8; padding: 20px; border-radius: 8px; border-left: 4px solid #EC4899;'>
<h4 style='color: #EC4899; margin: 0 0 12px 0;'>💡 专业建议</h4>
{tips_html}
</div>
</div>
"""
            self.advice_text.setText(text)
            self.advice_text.setTextFormat(Qt.RichText)

        except Exception as e:
            from utils.logger import logger
            logger.error(f"生成投资建议失败: {e}")


class QCompoundInterestParamsGroup(QFrame):
    """复利计算参数组 - 专业版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: none;
                border-radius: {ProfessionalTheme.RADIUS_LARGE}px;
            }}
        """)
        self.setup_ui()

    def setup_ui(self):
        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setContentsMargins(
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_XL + 8,
            ProfessionalTheme.SPACING_LG,
            ProfessionalTheme.SPACING_LG
        )

        label_style = f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                font-weight: {ProfessionalTheme.FONT_WEIGHT_MEDIUM};
                background: transparent;
            }}
        """

        grid.addWidget(QLabel("本金（P）"), 0, 0)
        self.principal_input = QDoubleSpinBox()
        self.principal_input.setRange(1000, 100000000)
        self.principal_input.setValue(100000)
        self.principal_input.setSuffix(" 元")
        self.principal_input.setStyleSheet(ProfessionalTheme.get_input_style())
        grid.addWidget(self.principal_input, 0, 1)

        grid.addWidget(QLabel("年利率（r）"), 1, 0)
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.5, 30)
        self.rate_input.setValue(8)
        self.rate_input.setSuffix(" %")
        self.rate_input.setDecimals(2)
        self.rate_input.setStyleSheet(ProfessionalTheme.get_input_style())
        grid.addWidget(self.rate_input, 1, 1)

        grid.addWidget(QLabel("复利频率（n）"), 2, 0)
        self.times_combo = QComboBox()
        self.times_combo.addItem("按年复利", 1)
        self.times_combo.addItem("按季复利", 4)
        self.times_combo.addItem("按月复利", 12)
        self.times_combo.addItem("按日复利", 365)
        self.times_combo.setCurrentIndex(2)
        self.times_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ProfessionalTheme.BG_PRIMARY};
                border: 1.5px solid {ProfessionalTheme.BORDER_COLOR};
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                padding: {ProfessionalTheme.SPACING_SM}px {ProfessionalTheme.SPACING_MD}px;
                font-size: {ProfessionalTheme.FONT_SIZE_BODY}px;
                min-width: 160px;
                color: {ProfessionalTheme.TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {ProfessionalTheme.PRIMARY_COLOR};
            }}
            QComboBox QAbstractItemView {{
                background: {ProfessionalTheme.BG_PRIMARY};
                border: 1px solid {ProfessionalTheme.BORDER_COLOR};
                border-radius: {ProfessionalTheme.RADIUS_SMALL}px;
                selection-background-color: {ProfessionalTheme.PRIMARY_BG};
                selection-color: {ProfessionalTheme.PRIMARY_DARK};
            }}
        """)
        grid.addWidget(self.times_combo, 2, 1)

        grid.addWidget(QLabel("投资年限（t）"), 3, 0)
        self.years_input = QSpinBox()
        self.years_input.setRange(1, 50)
        self.years_input.setValue(10)
        self.years_input.setSuffix(" 年")
        self.years_input.setStyleSheet(ProfessionalTheme.get_input_style())
        grid.addWidget(self.years_input, 3, 1)

        self.setLayout(grid)
