#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金搜索组件
提供基金搜索、筛选和添加功能
参考天天基金、蚂蚁财富等同类软件优化
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from services.data_fetcher import FundDataFetcher
from ui.theme.professional_theme import ProfessionalTheme
from utils.logger import logger

# 基金类型映射 - 基于基金代码前缀和名称关键词
FUND_TYPE_KEYWORDS = {
    '股票型': ['股票', '价值', '成长', '蓝筹', '红利', '优选', '精选'],
    '混合型': ['混合', '平衡', '配置', '灵活'],
    '债券型': ['债券', '债', '纯债', '可转债', '信用债'],
    '货币型': ['货币', '现金', '添利'],
    '指数型': ['指数', 'ETF', '联接', '跟踪'],
    'QDII': ['QDII', '纳斯达克', '标普', '恒生', '港股', '海外'],
    'FOF': ['FOF', '养老', '目标'],
}


def detect_fund_type(code: str, name: str) -> str:
    """根据基金代码和名称检测基金类型

    Args:
        code: 基金代码
        name: 基金名称

    Returns:
        基金类型字符串
    """
    # 根据代码前缀判断
    if code.startswith('519') or code.startswith('159'):
        return '指数型'
    if code.startswith('000') or code.startswith('001'):
        return '股票型'
    if code.startswith('002'):
        return '混合型'
    if code.startswith('003'):
        return '债券型'

    # 根据名称关键词判断
    for fund_type, keywords in FUND_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                return fund_type

    return '其他'


class FundSearchWidget(QWidget):
    """基金搜索组件 - 参考天天基金等同类软件优化"""
    fund_selected = Signal(str)

    # 热门基金列表（参考天天基金热门基金）
    HOT_FUNDS = [
        ('110022', '易方达消费行业股票'),
        ('000751', '嘉实新兴产业混合'),
        ('163406', '兴全合润混合'),
        ('519778', '交银新生活力灵活配置混合'),
        ('161725', '招商中证白酒指数'),
        ('005827', '易方达蓝筹精选混合'),
        ('260108', '景顺长城新兴成长混合'),
        ('000961', '天弘沪深300指数'),
        ('510300', '华泰柏瑞沪深300ETF'),
        ('159915', '易方达深证100ETF'),
    ]

    def __init__(self):
        super().__init__()
        self.all_funds = FundDataFetcher.get_all_funds()
        self.selected_code = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 搜索容器
        search_container = QWidget()
        search_container.setStyleSheet(f"""
            QWidget {{
                background: {ProfessionalTheme.BG_PRIMARY};
                border-radius: 12px;
                border: 1px solid {ProfessionalTheme.BORDER_LIGHT};
            }}
        """)
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(16)

        # 标题
        title_layout = QHBoxLayout()
        search_label = QLabel("🔍 基金搜索")
        search_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        title_layout.addWidget(search_label)
        title_layout.addStretch()

        # 基金数量统计
        count_label = QLabel(f"共 {len(self.all_funds)} 只基金")
        count_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: 13px;
                background: transparent;
            }}
        """)
        title_layout.addWidget(count_label)
        search_layout.addLayout(title_layout)

        # 搜索输入框和类型筛选
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入基金代码、名称或拼音搜索...')
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ProfessionalTheme.BG_SECONDARY};
                border: 1px solid {ProfessionalTheme.BORDER_LIGHT};
                border-radius: 8px;
                padding: 10px 16px;
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {ProfessionalTheme.PRIMARY_COLOR};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_funds)
        filter_layout.addWidget(self.search_input, 3)

        # 基金类型筛选
        type_label = QLabel("类型:")
        type_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_SECONDARY};
                font-size: 14px;
                background: transparent;
            }}
        """)
        filter_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['全部', '股票型', '混合型', '债券型', '货币型', '指数型', 'QDII', 'FOF', '其他'])
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ProfessionalTheme.BG_SECONDARY};
                border: 1px solid {ProfessionalTheme.BORDER_LIGHT};
                border-radius: 6px;
                padding: 8px 12px;
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: 13px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border: 1px solid {ProfessionalTheme.PRIMARY_COLOR};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {ProfessionalTheme.BG_PRIMARY};
                border: 1px solid {ProfessionalTheme.BORDER_LIGHT};
                selection-background-color: {ProfessionalTheme.PRIMARY_BG};
            }}
        """)
        self.type_combo.currentTextChanged.connect(self.filter_funds)
        filter_layout.addWidget(self.type_combo, 1)

        search_layout.addLayout(filter_layout)

        # 热门基金推荐
        hot_label = QLabel("🔥 热门基金")
        hot_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        search_layout.addWidget(hot_label)

        # 热门基金按钮
        hot_layout = QHBoxLayout()
        hot_layout.setSpacing(8)
        for code, name in self.HOT_FUNDS[:6]:
            btn = QPushButton(f"{code}")
            btn.setToolTip(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {ProfessionalTheme.PRIMARY_BG};
                    color: {ProfessionalTheme.PRIMARY_COLOR};
                    border: 1px solid {ProfessionalTheme.PRIMARY_LIGHT};
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: {ProfessionalTheme.PRIMARY_LIGHT};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, c=code: self.select_hot_fund(c))
            hot_layout.addWidget(btn)
        hot_layout.addStretch()
        search_layout.addLayout(hot_layout)

        # 搜索结果表格
        result_label = QLabel("📋 搜索结果")
        result_label.setStyleSheet(f"""
            QLabel {{
                color: {ProfessionalTheme.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        search_layout.addWidget(result_label)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(['基金代码', '基金名称', '基金类型'])
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.cellClicked.connect(self.on_fund_selected)
        self.result_table.setStyleSheet(f"""
            QTableWidget {{
                background: {ProfessionalTheme.BG_PRIMARY};
                alternate-background-color: {ProfessionalTheme.BG_SECONDARY};
                gridline-color: transparent;
                border: 1px solid {ProfessionalTheme.BORDER_LIGHT};
                border-radius: 8px;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {ProfessionalTheme.BORDER_LIGHT};
            }}
            QTableWidget::item:selected {{
                background: {ProfessionalTheme.PRIMARY_BG};
                color: {ProfessionalTheme.PRIMARY_DARK};
            }}
            QTableWidget::item:hover {{
                background: {ProfessionalTheme.PRIMARY_BG};
            }}
            QHeaderView::section {{
                background: {ProfessionalTheme.BG_SECONDARY};
                color: {ProfessionalTheme.TEXT_SECONDARY};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {ProfessionalTheme.BORDER_COLOR};
                font-weight: 600;
            }}
        """)

        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Fixed)
        self.result_table.setColumnWidth(0, 100)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setSectionResizeMode(2, header.ResizeMode.Fixed)
        self.result_table.setColumnWidth(2, 80)

        search_layout.addWidget(self.result_table)

        # 添加按钮
        self.add_button = QPushButton('✓ 添加到监控')
        self.add_button.clicked.connect(self.emit_selected_fund)
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                background: {ProfessionalTheme.PRIMARY_COLOR};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {ProfessionalTheme.PRIMARY_DARK};
            }}
        """)
        search_layout.addWidget(self.add_button)

        layout.addWidget(search_container)
        self.setLayout(layout)
        self.display_all_funds()

    def select_hot_fund(self, code: str):
        """选择热门基金"""
        self.selected_code = code
        if code in self.all_funds:
            name = self.all_funds[code]['name']
            self.search_input.setText(code)
            logger.info(f"选择热门基金: {code} - {name}")

    def display_all_funds(self):
        """显示所有基金"""
        self.result_table.setRowCount(0)
        count = 0
        for code, info in self.all_funds.items():
            if count >= 100:
                break
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(code))
            self.result_table.setItem(row, 1, QTableWidgetItem(info['name']))
            fund_type = detect_fund_type(code, info['name'])
            self.result_table.setItem(row, 2, QTableWidgetItem(fund_type))
            count += 1

    def filter_funds(self):
        """过滤基金"""
        text = self.search_input.text().lower()
        selected_type = self.type_combo.currentText()

        self.result_table.setRowCount(0)

        for code, info in self.all_funds.items():
            # 类型筛选
            if selected_type != '全部':
                fund_type = detect_fund_type(code, info['name'])
                if fund_type != selected_type:
                    continue

            # 文本搜索（支持代码、名称、拼音）
            pinyin = info.get('pinyin', '').lower()
            name = info['name'].lower()

            if text and text not in code.lower() and text not in name and text not in pinyin:
                continue

            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(code))
            self.result_table.setItem(row, 1, QTableWidgetItem(info['name']))
            fund_type = detect_fund_type(code, info['name'])
            self.result_table.setItem(row, 2, QTableWidgetItem(fund_type))

            if row >= 200:  # 限制显示数量
                break

    def on_fund_selected(self, row: int, col: int):
        """选中基金"""
        code_item = self.result_table.item(row, 0)
        if code_item:
            self.selected_code = code_item.text()

    def emit_selected_fund(self):
        """发送选中的基金代码信号"""
        if self.selected_code:
            self.fund_selected.emit(self.selected_code)
