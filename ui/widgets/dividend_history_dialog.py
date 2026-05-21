#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分红记录历史对话框
显示基金的分红历史记录，支持添加、编辑、删除操作
"""

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from utils.logger import logger


class DividendHistoryDialog(QDialog):
    """分红记录历史对话框"""

    def __init__(self, parent: QMainWindow = None, fund_code: str = "", fund_name: str = ""):
        super().__init__(parent)
        self.fund_code = fund_code
        self.fund_name = fund_name
        self.db_manager = parent.db_manager if parent and hasattr(parent, 'db_manager') else None

        self.setWindowTitle(f"分红记录 - {fund_name}({fund_code})")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #1e293b;
            }
            QTableWidget {
                gridline-color: #e2e8f0;
                background: white;
                alternate-background-color: #f8fafc;
                selection-background-color: #dbeafe;
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
            QLabel {
                color: #334155;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)

        self.setup_ui()
        self.load_dividend_records()

    def setup_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel(f"📊 {self.fund_name} ({self.fund_code}) - 分红历史")
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)

        summary_group = QGroupBox("分红汇总")
        summary_layout = QGridLayout()

        summary_layout.addWidget(QLabel("分红次数:"), 0, 0)
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("font-weight: bold; color: #3b82f6;")
        summary_layout.addWidget(self.count_label, 0, 1)

        summary_layout.addWidget(QLabel("分红总额:"), 0, 2)
        self.total_label = QLabel("¥0.00")
        self.total_label.setStyleSheet("font-weight: bold; color: #10b981;")
        summary_layout.addWidget(self.total_label, 0, 3)

        summary_layout.addWidget(QLabel("最近分红:"), 1, 0)
        self.latest_label = QLabel("-")
        self.latest_label.setStyleSheet("color: #64748b;")
        summary_layout.addWidget(self.latest_label, 1, 1, 1, 3)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        table_group = QGroupBox("分红明细")
        table_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(
            ["序号", "分红金额 (元)", "分红日期", "备注", "记录时间"]
        )

        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.verticalHeader().setVisible(False)

        table_layout.addWidget(self.table_widget)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        add_btn = QPushButton("+ 添加分红")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        add_btn.clicked.connect(self.add_dividend)
        btn_layout.addWidget(add_btn)

        delete_btn = QPushButton("- 删除选中")
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

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

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_dividend_records(self):
        """加载分红记录"""
        if not self.db_manager:
            logger.warning("数据库管理器未初始化")
            return

        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    SELECT id, dividend_amount, dividend_date, note, created_at
                    FROM dividend_records
                    WHERE fund_code = ?
                    ORDER BY dividend_date DESC, created_at DESC
                ''', (self.fund_code,))

                records = cursor.fetchall()

                self.table_widget.setRowCount(len(records))

                total_amount = 0.0
                for row_idx, record in enumerate(records):
                    record_id = record[0]
                    amount = record[1] or 0.0
                    date = record[2] or "-"
                    note = record[3] or ""

                    if record[4]:
                        if isinstance(record[4], str):
                            created_at = record[4][:16]
                        else:
                            created_at = record[4].strftime('%Y-%m-%d %H:%M')
                    else:
                        created_at = "-"

                    total_amount += amount

                    idx_item = QTableWidgetItem(str(row_idx + 1))
                    idx_item.setData(Qt.UserRole, record_id)
                    idx_item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row_idx, 0, idx_item)

                    amount_item = QTableWidgetItem(f"¥{amount:.2f}")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    amount_item.setForeground(Qt.darkGreen)
                    self.table_widget.setItem(row_idx, 1, amount_item)

                    date_item = QTableWidgetItem(str(date))
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row_idx, 2, date_item)

                    note_item = QTableWidgetItem(note)
                    self.table_widget.setItem(row_idx, 3, note_item)

                    created_item = QTableWidgetItem(created_at)
                    created_item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row_idx, 4, created_item)

                count = len(records)
                self.count_label.setText(str(count))
                self.total_label.setText(f"¥{total_amount:.2f}")

                if records:
                    latest_date = records[0][2]
                    self.latest_label.setText(str(latest_date))
                else:
                    self.latest_label.setText("暂无记录")

                logger.info(f"加载基金{self.fund_code}分红记录: {count}条，总额 ¥{total_amount:.2f}")

        except Exception as e:
            logger.error(f"加载分红记录失败: {e}")
            QMessageBox.critical(self, "错误", f"加载分红记录失败: {str(e)}")

    def add_dividend(self):
        """添加分红记录"""
        from PySide6.QtWidgets import QInputDialog

        amount, ok = QInputDialog.getDouble(
            self,
            "添加分红",
            f"请输入基金 {self.fund_code} 的分红金额:",
            value=0.0,
            minValue=0,
            maxValue=1000000,
            decimals=2
        )

        if not ok:
            return

        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO dividend_records (fund_code, dividend_amount, dividend_date)
                    VALUES (?, ?, ?)
                ''', (self.fund_code, amount, datetime.now().strftime('%Y-%m-%d')))

            self.load_dividend_records()
            QMessageBox.information(self, "成功", f"分红已记录: ¥{amount:.2f}")
            logger.info(f"添加基金{self.fund_code}分红: ¥{amount:.2f}")

        except Exception as e:
            logger.error(f"添加分红失败: {e}")
            QMessageBox.critical(self, "错误", f"添加分红失败: {str(e)}")

    def delete_selected(self):
        """删除选中的分红记录"""
        selected_rows = set(item.row() for item in self.table_widget.selectedItems())

        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 条分红记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            with self.db_manager.get_cursor() as cursor:
                for row in sorted(selected_rows, reverse=True):
                    record_id_item = self.table_widget.item(row, 0)
                    if record_id_item:
                        record_id = record_id_item.data(Qt.UserRole)
                        cursor.execute(
                            'DELETE FROM dividend_records WHERE id = ?',
                            (record_id,)
                        )

            self.load_dividend_records()
            QMessageBox.information(self, "成功", f"已删除 {len(selected_rows)} 条记录")
            logger.info(f"删除基金{self.fund_code}分红记录: {len(selected_rows)}条")

        except Exception as e:
            logger.error(f"删除分红记录失败: {e}")
            QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def showEvent(self, event):
        """窗口显示时刷新数据"""
        super().showEvent(event)
        self.load_dividend_records()
