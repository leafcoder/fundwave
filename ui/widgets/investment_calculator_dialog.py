#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投计算器UI组件
提供专业的定投计算、策略对比、可视化展示功能
"""

from __future__ import annotations

from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QComboBox, QDialog, QDoubleSpinBox, QFrame,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QScrollArea, QSpinBox,
                               QTabWidget, QVBoxLayout, QWidget)

from services.investment_calculator import (
    InvestmentCalculator,
    InvestmentResult,
    InvestmentStrategy,
    PREDEFINED_STRATEGIES,
)

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class InvestmentCalculatorDialog(QDialog):
    """专业级定投计算器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💰 智能定投计算器")
        self.setMinimumSize(1200, 800)
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
        
        self.current_result = None
        
        self.setup_ui()
        self.connect_signals()
    
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
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 12px;
            }
        """)
        header_widget.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(32, 0, 32, 0)
        
        title_label = QLabel("💰 智能定投计算器")
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
        
        # Tab页面
        self.tab_widget = QTabWidget()
        
        # 创建各个标签页
        self.create_calculator_tab()
        self.create_strategy_comparison_tab()
        self.create_lump_sum_vs_dca_tab()
        self.create_compound_interest_tab()
        self.create_investment_advice_tab()
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def create_calculator_tab(self):
        """创建基础计算器标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(16)
        
        # 左侧：参数输入
        input_group = QGroupBox("📝 投资参数设置")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(16)
        
        # 每月投入金额
        amount_row = QHBoxLayout()
        amount_label = QLabel("每月定投金额：")
        amount_label.setStyleSheet("""
            QLabel {
                color: #334155;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }
        """)
        self.monthly_amount_input = QDoubleSpinBox()
        self.monthly_amount_input.setRange(100, 10000000)
        self.monthly_amount_input.setValue(2000)
        self.monthly_amount_input.setSuffix(" 元")
        self.monthly_amount_input.setSingleStep(500)
        self.monthly_amount_input.setStyleSheet("""
            QDoubleSpinBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 15px;
                color: #334155;
            }
        """)
        amount_row.addWidget(amount_label)
        amount_row.addWidget(self.monthly_amount_input)
        input_layout.addLayout(amount_row)
        
        # 预期年化收益率
        return_row = QHBoxLayout()
        return_label = QLabel("预期年化收益率：")
        return_label.setStyleSheet(amount_label.styleSheet())
        self.expected_return_input = QDoubleSpinBox()
        self.expected_return_input.setRange(0, 50)
        self.expected_return_input.setValue(10)
        self.expected_return_input.setSuffix(" %")
        self.expected_return_input.setSingleStep(1)
        self.expected_return_input.setStyleSheet(self.monthly_amount_input.styleSheet())
        return_row.addWidget(return_label)
        return_row.addWidget(self.expected_return_input)
        input_layout.addLayout(return_row)
        
        # 投资年限
        years_row = QHBoxLayout()
        years_label = QLabel("投资年限：")
        years_label.setStyleSheet(amount_label.styleSheet())
        self.years_input = QSpinBox()
        self.years_input.setRange(1, 40)
        self.years_input.setValue(10)
        self.years_input.setSuffix(" 年")
        self.years_input.setStyleSheet(self.monthly_amount_input.styleSheet())
        years_row.addWidget(years_label)
        years_row.addWidget(self.years_input)
        input_layout.addLayout(years_row)
        
        # 通胀率
        inflation_row = QHBoxLayout()
        inflation_label = QLabel("通胀率（可选）：")
        inflation_label.setStyleSheet(amount_label.styleSheet())
        self.inflation_rate_input = QDoubleSpinBox()
        self.inflation_rate_input.setRange(0, 10)
        self.inflation_rate_input.setValue(3)
        self.inflation_rate_input.setSuffix(" %")
        self.inflation_rate_input.setDecimals(1)
        self.inflation_rate_input.setStyleSheet(self.monthly_amount_input.styleSheet())
        inflation_row.addWidget(inflation_label)
        inflation_row.addWidget(self.inflation_rate_input)
        input_layout.addLayout(inflation_row)
        
        # 计算按钮
        calculate_btn = QPushButton("📊 开始计算")
        calculate_btn.clicked.connect(self.calculate_basic)
        calculate_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #059669, #047857);
            }
        """)
        input_layout.addStretch()
        input_layout.addWidget(calculate_btn)
        
        layout.addWidget(input_group, stretch=1)
        
        # 右侧：结果展示
        result_group = QGroupBox("📈 计算结果")
        result_layout = QVBoxLayout(result_group)
        
        # 核心指标卡片
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        
        metric_items = [
            ("累计本金", "principal_value", "#64748b"),
            ("最终资产", "final_value", "#059669"),
            ("总收益", "profit_value", "#dc2626"),
            ("总收益率", "return_pct", "#d97706"),
        ]
        
        self.result_labels = {}
        for row, (name, key, color) in enumerate(metric_items):
            card_frame = QFrame()
            card_frame.setStyleSheet(f"""
                QFrame {{
                    background: {color}10;
                    border-radius: 8px;
                    border-left: 4px solid {color};
                    padding: 12px;
                }}
            """)
            card_layout = QVBoxLayout(card_frame)
            
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                }}
            """)
            value_lbl = QLabel("¥0")
            value_lbl.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 22px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            
            card_layout.addWidget(name_lbl)
            card_layout.addWidget(value_lbl)
            metrics_grid.addWidget(card_frame, row // 2, row % 2)
            
            self.result_labels[key] = value_lbl
        
        result_layout.addLayout(metrics_grid)
        
        # 详细文本输出
        self.detail_text = QLabel("")
        self.detail_text.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 12px;
                background: #f8fafc;
                border-radius: 8px;
                padding: 16px;
                line-height: 1.6;
            }
        """)
        self.detail_text.setWordWrap(True)
        self.detail_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        result_layout.addWidget(self.detail_text)
        
        layout.addWidget(result_group, stretch=1)
        
        self.tab_widget.addTab(tab, "🧮 定投计算")
    
    def create_strategy_comparison_tab(self):
        """创建策略对比标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea {border: none; background: transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        
        # 说明文字
        intro_label = QLabel(
            "对比不同投资策略的长期表现，帮助您选择最适合的投资方式"
        )
        intro_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 13px;
                background: transparent;
                padding: 12px;
                border-left: 3px solid #3b82f6;
            }
        """)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # 对比按钮
        compare_btn = QPushButton("🔄 对比预设策略")
        compare_btn.clicked.connect(self.compare_strategies)
        compare_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        layout.addWidget(compare_btn)
        
        # 结果展示区域
        self.strategy_results_group = QGroupBox("📊 策略对比结果")
        strategy_layout = QVBoxLayout(self.strategy_results_group)
        
        self.strategy_table_container = QWidget()
        self.strategy_table_layout = QVBoxLayout(self.strategy_table_container)
        self.strategy_table_layout.setContentsMargins(0, 0, 0, 0)
        strategy_layout.addWidget(self.strategy_table_container)
        
        layout.addWidget(self.strategy_results_group)
        layout.addStretch()
        
        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "⚖️ 策略对比")
    
    def create_lump_sum_vs_dca_tab(self):
        """创建一次性vs定投对比标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 输入参数
        params_group = QGroupBox("📝 参数设置")
        params_grid = QGridLayout(params_group)
        
        params_grid.addWidget(QLabel("总投资金额："), 0, 0)
        self.lump_sum_principal = QDoubleSpinBox()
        self.lump_sum_principal.setRange(1000, 100000000)
        self.lump_sum_principal.setValue(240000)
        self.lump_sum_principal.setSuffix(" 元")
        self.lump_sum_principal.setStyleSheet("""
            QDoubleSpinBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        params_grid.addWidget(self.lump_sum_principal, 0, 1)
        
        params_grid.addWidget(QLabel("预期年化收益率："), 1, 0)
        self.lump_sum_return = QDoubleSpinBox()
        self.lump_sum_return.setRange(0, 30)
        self.lump_sum_return.setValue(10)
        self.lump_sum_return.setSuffix(" %")
        self.lump_sum_return.setStyleSheet(self.lump_sum_principal.styleSheet())
        params_grid.addWidget(self.lump_sum_return, 1, 1)
        
        params_grid.addWidget(QLabel("投资年限："), 2, 0)
        self.lump_sum_years = QSpinBox()
        self.lump_sum_years.setRange(1, 30)
        self.lump_sum_years.setValue(10)
        self.lump_sum_years.setSuffix(" 年")
        self.lump_sum_years.setStyleSheet(self.lump_sum_principal.styleSheet())
        params_grid.addWidget(self.lump_sum_years, 2, 1)
        
        compare_btn = QPushButton("🔍 开始对比")
        compare_btn.clicked.connect(self.compare_lump_sum_dca)
        compare_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        params_grid.addWidget(compare_btn, 3, 0, 1, 2)
        
        layout.addWidget(params_group)
        
        # 结果展示
        self.dca_result_group = QGroupBox("📊 对比结果")
        dca_layout = QVBoxLayout(self.dca_result_group)
        
        self.dca_result_label = QLabel(
            "点击「开始对比」查看一次性投入与定投的差异\n\n"
            "💡 提示：在市场持续上涨时，一次性投入通常更优；\n"
            "   在市场波动较大时，定投可以降低平均成本风险。"
        )
        self.dca_result_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                line-height: 1.8;
                background: #f8fafc;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        self.dca_result_label.setWordWrap(True)
        self.dca_result_label.setAlignment(Qt.AlignCenter)
        dca_layout.addWidget(self.dca_result_label)
        
        layout.addWidget(self.dca_result_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "💵 一次 vs 定投")
    
    def create_compound_interest_tab(self):
        """创建复利计算标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 复利公式说明
        formula_label = QLabel(
            "<h3>复利公式</h3>"
            "<p style='font-size: 14px; color: #475569;'>"
            "<b>A = P(1 + r/n)^(nt)</b><br><br>"
            "其中：<br>"
            "• A = 最终金额<br>"
            "• P = 本金<br>"
            "• r = 年利率<br>"
            "• n = 每年复利次数<br>"
            "• t = 年数</p>"
        )
        formula_label.setTextFormat(Qt.RichText)
        formula_label.setStyleSheet("""
            QLabel {
                background: white;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #e2e8f0;
            }
        """)
        formula_label.setWordWrap(True)
        layout.addWidget(formula_label)
        
        # 参数输入
        compound_params = QCompoundInterestParamsGroup()
        layout.addWidget(compound_params)
        
        # 计算按钮
        calc_btn = QPushButton("🧮 计算复利收益")
        calc_btn.clicked.connect(lambda: self.calculate_compound(compound_params))
        calc_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #d97706;
            }
        """)
        layout.addWidget(calc_btn)
        
        # 结果显示
        self.compound_result_label = QLabel("")
        self.compound_result_label.setStyleSheet("""
            QLabel {
                color: #334155;
                font-size: 14px;
                background: #fef3c7;
                border-radius: 8px;
                padding: 20px;
                line-height: 1.8;
                border: 1px solid #fbbf24;
            }
        """)
        self.compound_result_label.setWordWrap(True)
        layout.addWidget(self.compound_result_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📈 复利计算")
    
    def create_investment_advice_tab(self):
        """创建投资建议标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea {border: none; background: transparent;}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        
        # 问卷式输入
        advice_group = QGroupBox("🎯 您的投资画像")
        advice_grid = QGridLayout(advice_group)
        
        advice_grid.addWidget(QLabel("风险承受能力："), 0, 0)
        self.risk_tolerance_combo = QComboBox()
        self.risk_tolerance_combo.addItems(["保守型", "稳健型", "激进型"])
        self.risk_tolerance_combo.setStyleSheet("""
            QComboBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        advice_grid.addWidget(self.risk_tolerance_combo, 0, 1)
        
        advice_grid.addWidget(QLabel("投资目标："), 1, 0)
        self.goal_combo = QComboBox()
        self.goal_combo.addItems(["养老储备", "子女教育", "应急资金", "财富增值"])
        self.goal_combo.setStyleSheet(self.risk_tolerance_combo.styleSheet())
        advice_grid.addWidget(self.goal_combo, 1, 1)
        
        advice_grid.addWidget(QLabel("投资期限："), 2, 0)
        self.horizon_spin = QSpinBox()
        self.horizon_spin.setRange(1, 40)
        self.horizon_spin.setValue(10)
        self.horizon_spin.setSuffix(" 年")
        self.horizon_spin.setStyleSheet("""
            QSpinBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
        """)
        advice_grid.addWidget(self.horizon_spin, 2, 1)
        
        generate_btn = QPushButton("✨ 生成个性化建议")
        generate_btn.clicked.connect(self.generate_advice)
        generate_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #ec4899, #db2777);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #db2777, #be185d);
            }
        """)
        advice_grid.addWidget(generate_btn, 3, 0, 1, 2)
        
        layout.addWidget(advice_group)
        
        # 建议展示
        self.advice_result_group = QGroupBox("💡 个性化投资建议")
        advice_layout = QVBoxLayout(self.advice_result_group)
        
        self.advice_text = QLabel(
            "填写您的情况后，点击「生成个性化建议」\n\n"
            "系统将根据您的风险偏好、投资目标和时间规划，\n"
            "为您提供专业的资产配置建议和预期收益测算。"
        )
        self.advice_text.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                line-height: 1.8;
                background: #fdf2f8;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #fbcfe8;
            }
        """)
        self.advice_text.setWordWrap(True)
        self.advice_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        advice_layout.addWidget(self.advice_text)
        
        layout.addWidget(self.advice_result_group)
        layout.addStretch()
        
        scroll_area.setWidget(content)
        self.tab_widget.addTab(scroll_area, "🤖 智能建议")
    
    def connect_signals(self):
        """连接信号和槽"""
        pass
    
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
        profit_color = "#dc2626" if result.total_profit >= 0 else "#10b981"
        profit_sign = "+" if result.total_profit >= 0 else ""
        pct_sign = "+" if result.profit_percentage >= 0 else ""
        
        self.result_labels['principal_value'].setText(f"¥{result.total_principal:,.2f}")
        self.result_labels['final_value'].setText(f"¥{result.final_amount:,.2f}")
        self.result_labels['profit_value'].setText(f"{profit_sign}¥{result.total_profit:,.2f}")
        self.result_labels['return_pct'].setText(f"{pct_sign}{result.profit_percentage:.2f}%")
        
        if result.summary_text:
            self.detail_text.setText(result.summary_text.strip())
    
    def compare_strategies(self):
        """对比预设策略"""
        try:
            comparison = InvestmentCalculator.compare_strategies(PREDEFINED_STRATEGIES)
            
            # 清空旧结果
            while self.strategy_table_layout.count():
                item = self.strategy_table_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            results = comparison['results']
            
            for name, result in results.items():
                frame = QFrame()
                frame.setStyleSheet("""
                    QFrame {
                        background: #f8fafc;
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 8px;
                        border-left: 4px solid #3b82f6;
                    }
                """)
                
                h_layout = QHBoxLayout(frame)
                
                is_best = name == comparison['best_by_profit']
                badge = " 🏆" if is_best else ""
                
                name_lbl = QLabel(f"{name}{badge}")
                name_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {'#dc2626' if is_best else '#1e293b'};
                        font-size: 15px;
                        font-weight: {'bold' if is_best else 'normal'};
                        background: transparent;
                    }}
                """)
                h_layout.addWidget(name_lbl)
                
                h_layout.addStretch()
                
                final_lbl = QLabel(f"¥{result.final_amount:,.0f}")
                final_lbl.setStyleSheet("""
                    QLabel {
                        color: #059669;
                        font-size: 16px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
                h_layout.addWidget(final_lbl)
                
                ret_lbl = QLabel(f"{result.profit_percentage:+.1f}%")
                ret_color = "#dc2626" if result.profit_percentage >= 0 else "#10b981"
                ret_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {ret_color};
                        font-size: 14px;
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
<h3>💰 一次性投入 vs 定投（DCA）对比</h3>
<p style='line-height: 2;'>
<b>📊 投入参数：</b> 总金额 ¥{principal:,.0f}，预期收益 {expected_return}%，期限 {years}年

<b style='color: #8b5cf6;'>🏆 一次性投入：</b><br>
   • 最终资产：¥{lump.final_amount:,.2f}<br>
   • 总收益：¥{lump.total_profit:+,.2f} ({lump.profit_percentage:+.2f}%)<br>

<b style='color: #10b981;'>📅 分期定投：</b><br>
   • 最终资产：¥{dca.final_amount:,.2f}<br>
   • 总收益：¥{dca.total_profit:+,.2f} ({dca.profit_percentage:+.2f}%)<br>

<b style='color: #f59e0b;'>⚖️ 差异分析：</b><br>
   • 差额：¥{diff:+,.2f}<br>
   • 获胜方：<b>{winner}</b>

<em>💡 提示：此对比假设市场稳定上涨。<br>
实际中，定投可以平滑市场波动风险。</em>
</p>
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
            
            text = f"""
<h3>📈 复利计算结果</h3>
<p style='line-height: 2;'>
<b>💰 本金：</b> ¥{principal:,.2f}<br>
<b>📊 利率：</b> {rate:.1f}% / 年<br>
<b>🔄 复利频率：</b> 每年{times_per_year}次<br>
<b>⏱️ 期限：</b> {years}年<br><br>

<b style='color: #059669; font-size: 18px;'>最终资产：¥{result.final_amount:,.2f}</b><br>
<b style='color: #dc2626;'>总收益：¥{result.total_profit:+,.2f}</b><br>
<b style='color: #d97706;'>总收益率：{result.profit_percentage:+.2f}%</b><br><br>

<em>✨ 复利的威力：经过{years}年，您的本金增长了{'%.1f' % (result.final_amount / principal)}倍！</em>
</p>
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
            
            risk = risk_tolerance_map.get(self.risk_tolerance_combo.currentText(), 'moderate')
            goal = goal_map.get(self.goal_combo.currentText(), 'wealth')
            horizon = self.horizon_spin.value()
            
            advice = InvestmentCalculator.generate_investment_advice(
                risk_tolerance=risk,
                investment_goal=goal,
                time_horizon=horizon
            )
            
            proj = advice['example_projection']
            alloc = advice['asset_allocation']
            
            tips_html = '<br>'.join(advice['tips'])
            
            text = f"""
<h3>💡 为您量身定制的投资方案</h3>
<p style='line-height: 2;'>
<b>👤 您的投资画像：</b><br>
   • 风险承受：{self.risk_tolerance_combo.currentText()}<br>
   • 投资目标：{self.goal_combo.currentText()}<br>
   • 投资期限：{horizon}年<br><br>

<b>📊 推荐资产配置：</b><br>
   • 权益类（股票/混合）：{alloc['equity']}%<br>
   • 固收类（债券/货币）：{alloc['fixed_income']}%<br><br>

<b>💰 建议每月定投：</b> ¥{advice['suggested_monthly_investment']:,.0f}<br>
<b>📈 预期年化收益：</b> 
{advice['recommended_return_range'][0]:.0f}% - {advice['recommended_return_range'][1]:.0f}%<br><br>

<b style='color: #059669;'>🎯 预期收益测算（{horizon}年后）：</b><br>
   • 累计本金：¥{proj.total_principal:,.2f}<br>
   • <b>最终资产：¥{proj.final_amount:,.2f}</b><br>
   • 总收益：¥{proj.total_profit:+,.2f} ({proj.profit_percentage:+.2f}%)<br><br>

<b>💡 专业建议：</b><br>
{tips_html}
</p>
"""
            self.advice_text.setText(text)
            self.advice_text.setTextFormat(Qt.RichText)
            
        except Exception as e:
            from utils.logger import logger
            logger.error(f"生成投资建议失败: {e}")


class QCompoundInterestParamsGroup(QGroupBox):
    """复利计算参数组"""
    
    def __init__(self, parent=None):
        super().__init__("📝 复利参数", parent)
        self.setup_ui()
    
    def setup_ui(self):
        grid = QGridLayout()
        grid.setSpacing(12)
        
        grid.addWidget(QLabel("本金（P）："), 0, 0)
        self.principal_input = QDoubleSpinBox()
        self.principal_input.setRange(1000, 100000000)
        self.principal_input.setValue(100000)
        self.principal_input.setSuffix(" 元")
        self.principal_input.setStyleSheet("""
            QDoubleSpinBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        grid.addWidget(self.principal_input, 0, 1)
        
        grid.addWidget(QLabel("年利率（r）："), 1, 0)
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.5, 30)
        self.rate_input.setValue(8)
        self.rate_input.setSuffix(" %")
        self.rate_input.setDecimals(2)
        self.rate_input.setStyleSheet(self.principal_input.styleSheet())
        grid.addWidget(self.rate_input, 1, 1)
        
        grid.addWidget(QLabel("复利频率（n）："), 2, 0)
        self.times_combo = QComboBox()
        self.times_combo.addItem("按年复利", 1)
        self.times_combo.addItem("按季复利", 4)
        self.times_combo.addItem("按月复利", 12)
        self.times_combo.addItem("按日复利", 365)
        self.times_combo.setCurrentIndex(2)  # 默认月复利
        self.times_combo.setStyleSheet("""
            QComboBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 140px;
            }
        """)
        grid.addWidget(self.times_combo, 2, 1)
        
        grid.addWidget(QLabel("投资年限（t）："), 3, 0)
        self.years_input = QSpinBox()
        self.years_input.setRange(1, 50)
        self.years_input.setValue(10)
        self.years_input.setSuffix(" 年")
        self.years_input.setStyleSheet(self.principal_input.styleSheet())
        grid.addWidget(self.years_input, 3, 1)
        
        self.setLayout(grid)
