#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金搜索组件
提供基金搜索、筛选和添加功能
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from services.data_fetcher import FundDataFetcher
from utils.logger import logger


class FundSearchWidget(QWidget):
    """基金搜索组件"""
    fund_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.all_funds = FundDataFetcher.get_all_funds()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        search_container = QWidget()
        search_container.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
            }
        """)
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(16, 16, 16, 16)
        search_layout.setSpacing(12)

        search_label = QLabel("基金搜索")
        search_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入基金代码或名称进行搜索...')
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 16px;
                color: #475569;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        self.search_input.textChanged.connect(self.filter_funds)
        search_layout.addWidget(self.search_input)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(['基金代码', '基金名称'])
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.cellClicked.connect(self.on_fund_selected)
        self.result_table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                gridline-color: transparent;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
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
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
            }
            QHeaderView::section:hover {
                background: #e2e8f0;
                color: #1e293b;
            }
        """)

        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Interactive)
        self.result_table.setColumnWidth(0, 100)
        header.setSectionResizeMode(1, header.ResizeMode.Interactive)
        self.result_table.setColumnWidth(1, 300)

        search_layout.addWidget(self.result_table)

        self.add_button = QPushButton('添加到监控')
        self.add_button.clicked.connect(self.emit_selected_fund)
        self.add_button.setStyleSheet("""
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
        search_layout.addWidget(self.add_button)

        layout.addWidget(search_container)
        self.setLayout(layout)
        self.display_all_funds()

    def display_all_funds(self):
        """显示所有基金"""
        self.result_table.setRowCount(0)
        for code, info in list(self.all_funds.items())[:100]:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(code))
            self.result_table.setItem(row, 1, QTableWidgetItem(info['name']))

    def filter_funds(self, text):
        """过滤基金"""
        self.result_table.setRowCount(0)
        filtered_funds = {k: v for k, v in self.all_funds.items(
        ) if text.lower() in k.lower() or text.lower() in v['name'].lower()}

        for code, info in list(filtered_funds.items())[:100]:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(code))
            self.result_table.setItem(row, 1, QTableWidgetItem(info['name']))

    def on_fund_selected(self, row, col):
        """选中基金"""
        code_item = self.result_table.item(row, 0)
        if code_item:
            self.selected_code = code_item.text()

    def emit_selected_fund(self):
        """发送选中的基金代码信号"""
        if hasattr(self, 'selected_code'):
            self.fund_selected.emit(self.selected_code)
