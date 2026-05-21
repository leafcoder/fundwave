#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
提供应用程序主界面和核心业务逻辑
"""

import json
import logging
import os
import signal
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style as style
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog,
                               QDoubleSpinBox, QGridLayout, QGroupBox,
                               QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMessageBox, QPushButton,
                               QStyle, QSystemTrayIcon, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

from config import config
from models.database import DatabaseManager
from services.data_fetcher import FundDataFetcher
from services.notification import NotificationManager
from ui.widgets.dividend_history_dialog import DividendHistoryDialog
from ui.widgets.investment_calculator_dialog import InvestmentCalculatorDialog
from ui.widgets.portfolio_dashboard import PortfolioDashboard
from ui.widgets.search_widget import FundSearchWidget
from ui.widgets.table_widget import FundTableWidget
from utils.logger import logger

matplotlib.use('Agg')
style.use('ggplot')
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei',
                                   'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class DataUpdateThread(QThread):
    """数据更新线程"""
    data_updated = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, codes):
        super().__init__()
        self.codes = codes
        self._is_running = True

    def run(self):
        try:
            fund_data = {}
            for code in self.codes:
                if not self._is_running:
                    break
                fund = FundDataFetcher.get_fund(code)
                if fund:
                    fund_data[code] = fund
            if self._is_running:
                self.data_updated.emit(fund_data)
        except Exception as e:
            if self._is_running:
                self.error_occurred.emit(str(e))

    def stop(self):
        """停止线程"""
        self._is_running = False


class FundMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能基金监控系统")
        self.resize(1200, 800)

        app_icon = None
        icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.png')

        if os.path.exists(icon_path):
            try:
                app_icon = QIcon(icon_path)
                if not app_icon.isNull():
                    self.setWindowIcon(app_icon)
                    logger.info("使用自定义应用图标")
            except Exception as e:
                logger.warning(f"加载自定义图标失败: {e}")

        if app_icon is None or app_icon.isNull():
            try:
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    app_icon = icon
                else:
                    icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        app_icon = icon
            except Exception as e:
                logger.warning(f"设置窗口图标失败: {e}")

        self.app_icon = app_icon

        self.db_manager = DatabaseManager()
        self.notification_manager = NotificationManager(self.db_manager)

        self.init_tray()

        self.default_codes = [
            "011329",
            "011854",
            "161903",
            "160630",
            "012255",
            "006229",
            "161725",
            "501207",
            "000083",
            "260108",
            "013196",
            "502056",
            "002079",
            "005693",
            "003877",
            "006555",
        ]

        self.monitored_codes = self.load_monitored_funds()
        self.fund_data = {}

        ui_settings = self.db_manager.get_ui_settings()
        self.visible_stats = {
            "今日盈亏": ui_settings.get('daily_profit_visible', True),
            "持仓成本": ui_settings.get('position_cost_visible', True),
            "持有金额": ui_settings.get('current_value_visible', True)
        }
        self.profit_visible = ui_settings.get('profit_visible', True)

        self.setup_ui()
        self.setup_timers()
        self.update_data_async()

        self.update_total_profit(0.0)

        logger.info("基金监控系统初始化完成")

    def init_tray(self):
        """初始化系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon()

            if hasattr(
                    self, 'app_icon') and self.app_icon and not self.app_icon.isNull():
                self.tray_icon.setIcon(self.app_icon)
            else:
                app_icon = self.windowIcon()
                if not app_icon.isNull():
                    self.tray_icon.setIcon(app_icon)
                else:
                    icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
                    if not icon.isNull():
                        self.tray_icon.setIcon(icon)
                    else:
                        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
                        if not icon.isNull():
                            self.tray_icon.setIcon(icon)

            self.tray_icon.setToolTip("智能基金监控系统")

            tray_menu = QMenu()

            show_action = tray_menu.addAction("显示主界面")
            show_action.triggered.connect(self.show_window)

            tray_menu.addSeparator()

            quit_action = tray_menu.addAction("退出程序")
            quit_action.triggered.connect(self.quit_application)

            self.tray_icon.setContextMenu(tray_menu)

            self.tray_icon.activated.connect(self.on_tray_icon_activated)

            self.tray_icon.show()
        else:
            QMessageBox.warning(self, "警告", "系统不支持系统托盘功能")

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        logger.debug(f"托盘图标被激活，原因: {reason}")

        if reason == QSystemTrayIcon.DoubleClick:
            logger.info("双击托盘图标 → 显示主界面")
            self.show_window()
        elif reason == QSystemTrayIcon.Trigger:
            logger.debug("单击托盘图标")

    def show_window(self):
        """显示主窗口"""
        logger.info("正在显示主窗口...")

        if self.isMinimized():
            self.showNormal()
        else:
            self.show()

        self.raise_()
        self.activateWindow()
        self.setWindowTitle("智能基金监控系统")

    def quit_application(self):
        """退出应用程序"""
        logger.info("正在退出应用程序...")

        try:
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
                logger.debug("定时器已停止")

            if hasattr(
                    self, 'update_thread') and self.update_thread.isRunning():
                self.update_thread.stop()
                if not self.update_thread.wait(3000):
                    logger.warning("线程未在规定时间内结束，强制终止")
                    self.update_thread.terminate()
                    self.update_thread.wait()
                logger.debug("更新线程已停止")

            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon = None
                logger.debug("托盘图标已隐藏")

            self.db_manager.close()
            logger.info("应用程序正常退出")
        except Exception as e:
            logger.error(f"退出应用程序时出错: {e}")

        QApplication.instance().quit()
        sys.exit(0)

    def closeEvent(self, event):
        """关闭事件，最小化到托盘而不是退出"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()

        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            self.update_thread.stop()
            self.update_thread.wait(3000)

        if QSystemTrayIcon.isSystemTrayAvailable() and hasattr(self, 'tray_icon'):
            self.hide()
            event.ignore()
        else:
            try:
                self.db_manager.close()
            except Exception as e:
                logger.error(f"关闭数据库连接时出错: {e}")
            event.accept()

    def load_monitored_funds(self) -> List[str]:
        """从数据库加载用户选择的基金列表"""
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT fund_code FROM monitored_funds ORDER BY created_at'
                )
                result = cursor.fetchall()
                funds = [row[0] for row in result]

                if not funds:
                    funds = self.default_codes[:]
                    self.save_monitored_funds(funds)
                    logger.info(f"使用默认基金列表: {len(funds)}只")
                else:
                    logger.info(f"从数据库加载基金列表: {len(funds)}只")

                return funds
        except Exception as e:
            logger.error(f"加载基金列表失败: {e}")
            return self.default_codes[:]

    def save_monitored_funds(self,
                             funds_list: Optional[List[str]] = None) -> bool:
        """将用户选择的基金列表保存到数据库

        Args:
            funds_list: 基金代码列表，为None时使用self.monitored_codes

        Returns:
            是否保存成功
        """
        if funds_list is None:
            funds_list = self.monitored_codes

        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('DELETE FROM monitored_funds')
                for fund_code in funds_list:
                    cursor.execute(
                        'INSERT OR IGNORE INTO monitored_funds (fund_code) VALUES (?)', (fund_code,))
            logger.info(f"保存基金列表成功: {len(funds_list)}只")
            return True
        except Exception as e:
            logger.error(f"保存基金列表失败: {e}")
            return False

    def add_fund_to_monitor(self, fund_code: str) -> bool:
        """添加特定基金到监控列表

        Args:
            fund_code: 基金代码

        Returns:
            是否添加成功
        """
        is_valid, error_msg = FundDataFetcher.validate_fund_code(fund_code)
        if not is_valid:
            QMessageBox.warning(self, "提示", error_msg)
            logger.warning(f"添加基金失败: {error_msg}")
            return False

        if fund_code in self.monitored_codes:
            QMessageBox.information(self, "提示", f"基金{fund_code}已在监控列表中")
            logger.info(f"基金{fund_code}已在监控列表中")
            return False

        try:
            fund_data = FundDataFetcher.get_fund(fund_code)
            if not fund_data:
                QMessageBox.warning(
                    self,
                    "提示",
                    f"无法获取基金{fund_code}的数据，请确认基金代码是否正确"
                )
                logger.warning(f"无法获取基金{fund_code}的数据")
                return False

            fund_name = fund_data.get('name', '')

            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'INSERT OR IGNORE INTO monitored_funds (fund_code, fund_name) VALUES (?, ?)',
                    (fund_code, fund_name)
                )

            self.monitored_codes.append(fund_code)
            self.update_data_async()

            QMessageBox.information(
                self,
                "成功",
                f"成功添加基金: {fund_name}({fund_code})"
            )
            logger.info(f"成功添加基金: {fund_name}({fund_code})")
            return True

        except Exception as e:
            logger.error(f"添加基金{fund_code}时出错: {e}")
            QMessageBox.critical(self, "错误", f"添加基金失败: {str(e)}")
            return False

    def remove_specific_fund(self, fund_code: str) -> bool:
        """从监控列表中删除特定基金

        Args:
            fund_code: 基金代码

        Returns:
            是否删除成功
        """
        if fund_code not in self.monitored_codes:
            logger.warning(f"基金{fund_code}不在监控列表中")
            return False

        if len(self.monitored_codes) <= 1:
            QMessageBox.information(self, "提示", "至少需要保留一只基金进行监控")
            logger.warning("至少需要保留一只基金进行监控")
            return False

        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'DELETE FROM monitored_funds WHERE fund_code = ?',
                    (fund_code,)
                )
                cursor.execute(
                    'DELETE FROM fund_holdings WHERE fund_code = ?',
                    (fund_code,)
                )

            self.monitored_codes.remove(fund_code)
            self.update_data_async()

            logger.info(f"成功删除基金{fund_code}")
            return True

        except Exception as e:
            logger.error(f"删除基金{fund_code}时出错: {e}")
            QMessageBox.critical(self, "错误", f"删除基金失败: {str(e)}")
            return False

    def setup_ui(self):
        """设置UI界面"""
        self.setStyleSheet("""
            QMainWindow {
                background: #f8fafc;
            }
            QWidget {
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        header_widget.setFixedHeight(80)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(32, 0, 32, 0)

        title_label = QLabel("智能基金监控系统")
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

        profit_layout = QHBoxLayout()
        profit_layout.setSpacing(8)

        self.total_profit_label = QLabel("累计盈亏: ¥0.00")
        self.total_profit_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)
        profit_layout.addWidget(self.total_profit_label)

        self.profit_eye_btn = QPushButton("👁")
        self.profit_eye_btn.setFixedSize(28, 28)
        self.profit_eye_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.profit_eye_btn.clicked.connect(self.toggle_profit_visibility)
        profit_layout.addWidget(self.profit_eye_btn)

        self.profit_real_value = 0.0

        if not getattr(self, 'profit_visible', True):
            self.total_profit_label.setText("累计盈亏: ¥****")
            self.profit_eye_btn.setText("🔒")
        else:
            self.profit_eye_btn.setText("👁")

        header_layout.addLayout(profit_layout)

        main_layout.addWidget(header_widget)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: #f8fafc;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        stats_widget = QWidget()
        stats_widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
            }
        """)
        stats_widget.setFixedHeight(100)

        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(24, 16, 24, 16)
        stats_layout.setSpacing(32)

        stat_items = [
            ("监控基金", f"{len(self.monitored_codes)}", "#3b82f6", False),
            ("今日盈亏", "¥0.00", "#10b981", True),
            ("持仓成本", "¥0.00", "#f59e0b", True),
            ("持有金额", "¥0.00", "#8b5cf6", True)
        ]

        for label_text, value_text, color, can_hide in stat_items:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setSpacing(4)

            label = QLabel(label_text)
            label.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    font-size: 13px;
                    background: transparent;
                }
            """)
            stat_layout.addWidget(label)

            value_layout = QHBoxLayout()
            value_layout.setContentsMargins(0, 0, 0, 0)
            value_layout.setSpacing(8)

            value_label = QLabel(value_text)
            value_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 24px;
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            value_layout.addWidget(value_label)

            if can_hide:
                eye_btn = QPushButton("👁")
                eye_btn.setFixedSize(24, 24)
                eye_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: #f1f5f9;
                        border-radius: 4px;
                    }
                """)
                eye_btn.clicked.connect(
                    lambda lt=label_text, vl=value_label, eb=eye_btn:
                    self.toggle_stat_visibility(lt, vl, eb))
                value_layout.addWidget(eye_btn)

            value_layout.addStretch()
            stat_layout.addLayout(value_layout)

            if label_text == "监控基金":
                self.count_label = value_label
            elif label_text == "今日盈亏":
                self.daily_profit_label = value_label
            elif label_text == "持仓成本":
                self.position_cost_label = value_label
            elif label_text == "持有金额":
                self.current_value_label = value_label

            stats_layout.addWidget(stat_widget)

        content_layout.addWidget(stats_widget)

        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
            }
        """)
        toolbar_widget.setFixedHeight(60)

        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        toolbar_layout.setSpacing(8)

        refresh_interval_label = QLabel("刷新间隔")
        refresh_interval_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 13px;
                background: transparent;
            }
        """)
        toolbar_layout.addWidget(refresh_interval_label)

        refresh_interval, auto_refresh_enabled = self.get_settings()
        self.refresh_interval_input = QLineEdit(str(refresh_interval))
        self.refresh_interval_input.setFixedWidth(60)
        self.refresh_interval_input.setStyleSheet("""
            QLineEdit {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                color: #475569;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        toolbar_layout.addWidget(self.refresh_interval_input)

        toolbar_layout.addWidget(
            self.create_button(
                "秒",
                "#64748b",
                None,
                is_label=True))

        set_interval_btn = self.create_button(
            "设置", "#f59e0b", self.set_refresh_interval)
        toolbar_layout.addWidget(set_interval_btn)

        toolbar_layout.addSpacing(16)

        self.auto_refresh_btn = self.create_button(
            "停止刷新" if auto_refresh_enabled else "启动刷新",
            "#10b981" if auto_refresh_enabled else "#64748b",
            self.toggle_auto_refresh
        )
        toolbar_layout.addWidget(self.auto_refresh_btn)

        refresh_btn = self.create_button(
            "手动刷新", "#3b82f6", self.update_data_async)
        toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addStretch()

        add_fund_btn = self.create_button(
            "添加基金", "#10b981", self.show_add_fund_dialog)
        toolbar_layout.addWidget(add_fund_btn)

        remove_fund_btn = self.create_button(
            "删除基金", "#ef4444", self.remove_fund)
        toolbar_layout.addWidget(remove_fund_btn)

        settings_btn = self.create_button(
            "通知设置", "#8b5cf6", self.show_notification_settings)
        toolbar_layout.addWidget(settings_btn)

        portfolio_btn = self.create_button(
            "📊 投资组合分析", "#3b82f6", self.show_portfolio_dashboard)
        toolbar_layout.addWidget(portfolio_btn)

        calculator_btn = self.create_button(
            "💰 定投计算器", "#10b981", self.show_investment_calculator)
        toolbar_layout.addWidget(calculator_btn)

        content_layout.addWidget(toolbar_widget)

        table_widget = QWidget()
        table_widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
            }
        """)

        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
                border-radius: 12px;
            }
            QTabBar::tab {
                background: transparent;
                color: #64748b;
                padding: 12px 24px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: white;
                color: #3b82f6;
                border-bottom: 2px solid #3b82f6;
            }
            QTabBar::tab:hover:!selected {
                background: #f8fafc;
                color: #475569;
            }
        """)

        self.create_table_tab()
        self.create_search_tab()

        table_layout.addWidget(self.tab_widget)
        content_layout.addWidget(table_widget)

        main_layout.addWidget(content_widget)

        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: white;
                color: #64748b;
                font-size: 12px;
                border-top: 1px solid #e2e8f0;
            }
        """)
        self.statusBar().showMessage(
            f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def create_button(self, text, color, callback, is_label=False):
        """创建现代化按钮"""
        if is_label:
            btn = QLabel(text)
            btn.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 13px;
                    background: transparent;
                }}
            """)
            return btn

        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background: {self.darken_color(color, 0.2)};
            }}
        """)
        if callback:
            btn.clicked.connect(callback)
        return btn

    def darken_color(self, hex_color, amount=0.1):
        """加深颜色"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        return f'#{r:02x}{g:02x}{b:02x}'

    def create_table_tab(self):
        """创建表格标签页"""
        table_widget = QWidget()
        layout = QVBoxLayout(table_widget)

        self.fund_table = FundTableWidget(parent_monitor=self)
        layout.addWidget(self.fund_table)

        table_widget.setLayout(layout)
        self.tab_widget.addTab(table_widget, "基金数据表")

    def create_search_tab(self):
        """创建搜索标签页"""
        self.search_widget = FundSearchWidget()
        self.search_widget.fund_selected.connect(self.add_fund_from_search)
        self.tab_widget.addTab(self.search_widget, "基金搜索")

    def setup_timers(self):
        """设置定时器"""
        refresh_interval, auto_refresh_enabled = self.get_settings()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data_async)
        self.refresh_timer.start(refresh_interval * 1000)

        if not auto_refresh_enabled:
            self.refresh_timer.stop()

    def update_data_async(self):
        """异步更新数据"""
        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            return

        self.update_thread = DataUpdateThread(self.monitored_codes)
        self.update_thread.data_updated.connect(self.on_data_updated)
        self.update_thread.error_occurred.connect(self.on_error)
        self.update_thread.start()

    def on_data_updated(self, fund_data):
        """数据更新完成"""
        self.fund_data = fund_data
        self.fund_table.update_data(fund_data)
        self.count_label.setText(f"监控基金数: {len(self.monitored_codes)}")
        self.statusBar().showMessage(
            f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if hasattr(self, 'notification_manager') and hasattr(
                self, 'total_profit'):
            daily_profit = getattr(self, 'daily_profit', 0.0)
            self.notification_manager.check_and_notify(
                fund_data, self.total_profit, daily_profit)

    def on_error(self, error_msg):
        """错误处理"""
        QMessageBox.warning(self, "错误", f"数据更新失败: {error_msg}")

    def show_add_fund_dialog(self):
        """显示添加基金对话框"""
        dialog = AddFundDialog(self)
        if dialog.exec() == 1:
            code = dialog.get_code()
            if code:
                self.add_fund_to_monitor(code)

    def show_notification_settings(self):
        """显示通知设置对话框"""
        dialog = NotificationSettingsDialog(self)
        dialog.exec()

    def show_portfolio_dashboard(self):
        """显示投资组合分析仪表盘"""
        holdings_data = self._get_all_holdings_data()
        
        if not holdings_data:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "提示",
                "暂无持仓数据\n请先设置基金持仓信息（成本价和份额）"
            )
            return
        
        dialog = PortfolioDashboard(holdings_data, parent=self)
        dialog.exec()

    def show_investment_calculator(self):
        """显示定投计算器对话框"""
        dialog = InvestmentCalculatorDialog(parent=self)
        dialog.exec()

    def _get_all_holdings_data(self) -> List[Dict[str, Any]]:
        """获取所有基金的持仓数据
        
        Returns:
            持仓数据列表
        """
        holdings = []
        
        for code in self.monitored_codes:
            cost_price, shares, current_value = self.get_fund_holdings_detail(code)
            
            if cost_price > 0 and shares > 0:
                fund_info = self.fund_data.get(code, {})
                
                daily_profit = current_value * float(
                    fund_info.get('gszzl', '0')
                ) / 100 if fund_info else 0
                
                total_profit = current_value - (cost_price * shares)
                dividend = self.get_fund_dividend(code)
                total_profit += dividend
                
                holding = {
                    'fund_code': code,
                    'fund_name': fund_info.get('name', code),
                    'cost_price': cost_price,
                    'shares': shares,
                    'current_value': current_value,
                    'daily_profit': daily_profit,
                    'total_profit': total_profit,
                    'dividend': dividend
                }
                holdings.append(holding)
        
        return holdings

    def add_fund_from_search(self, code: str):
        """从搜索结果添加基金

        Args:
            code: 基金代码
        """
        if code:
            if self.add_fund_to_monitor(code):
                self.tab_widget.setCurrentIndex(0)

    def remove_fund(self):
        """删除基金"""
        if len(self.monitored_codes) <= 1:
            QMessageBox.information(self, "提示", "至少需要保留一只基金进行监控")
            return

        current_item = self.fund_table.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请选择要删除的基金")
            return

        row = current_item.row()
        code_item = self.fund_table.item(row, 0)
        if code_item:
            code = code_item.text()
            reply = QMessageBox.question(
                self,
                "确认",
                f"确定要删除基金 {code} 吗？\n删除后将同时清除该基金的持有金额数据。"
            )
            if reply == QMessageBox.Yes:
                self.remove_specific_fund(code)

    def get_settings(self) -> Tuple[int, bool]:
        """从数据库获取设置

        Returns:
            (刷新间隔, 是否启用自动刷新)
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT refresh_interval, auto_refresh_enabled FROM settings LIMIT 1'
                )
                result = cursor.fetchone()
                if result:
                    return result[0], bool(result[1])
                else:
                    return config.default_refresh_interval, True
        except Exception as e:
            logger.error(f"获取设置失败: {e}")
            return config.default_refresh_interval, True

    def toggle_stat_visibility(
            self, stat_name: str, value_label: QLabel, eye_btn: QPushButton):
        """切换统计数据的可见性

        Args:
            stat_name: 统计项名称
            value_label: 数值标签
            eye_btn: 眼睛按钮
        """
        if stat_name in self.visible_stats:
            self.visible_stats[stat_name] = not self.visible_stats[stat_name]
            visible = self.visible_stats[stat_name]

            setting_map = {
                "今日盈亏": "daily_profit_visible",
                "持仓成本": "position_cost_visible",
                "持有金额": "current_value_visible"
            }

            if stat_name in setting_map:
                self.db_manager.save_ui_setting(setting_map[stat_name], visible)

            original_value = value_label.property("original_value")

            if visible:
                if original_value:
                    value_label.setText(original_value)
                eye_btn.setText("👁")
            else:
                if original_value:
                    value_label.setText("¥****")
                eye_btn.setText("🔒")

    def toggle_profit_visibility(self):
        """切换累计盈亏的可见性"""
        self.profit_visible = not self.profit_visible

        self.db_manager.save_ui_setting('profit_visible', self.profit_visible)

        if self.profit_visible:
            if self.profit_real_value > 0:
                self.total_profit_label.setText(
                    f"累计盈亏: +¥{self.profit_real_value:.2f}")
            elif self.profit_real_value < 0:
                self.total_profit_label.setText(
                    f"累计盈亏: -¥{abs(self.profit_real_value):.2f}")
            else:
                self.total_profit_label.setText(
                    f"累计盈亏: ¥{self.profit_real_value:.2f}")
            self.profit_eye_btn.setText("👁")
        else:
            self.total_profit_label.setText("累计盈亏: ¥****")
            self.profit_eye_btn.setText("🔒")

    def update_total_profit(
            self,
            profit: float,
            daily_profit: float = 0.0,
            position_cost: float = 0.0,
            current_value: float = 0.0):
        """更新总盈亏显示

        Args:
            profit: 累计盈亏金额
            daily_profit: 当日盈亏金额
            position_cost: 持仓成本
            current_value: 持有金额
        """
        self.total_profit = profit
        self.profit_real_value = profit

        if self.profit_visible:
            if profit > 0:
                self.total_profit_label.setText(f"累计盈亏: +¥{profit:.2f}")
                self.total_profit_label.setStyleSheet("""
                    QLabel {
                        color: #ef4444;
                        font-size: 18px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
            elif profit < 0:
                self.total_profit_label.setText(f"累计盈亏: -¥{abs(profit):.2f}")
                self.total_profit_label.setStyleSheet("""
                    QLabel {
                        color: #10b981;
                        font-size: 18px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
            else:
                self.total_profit_label.setText(f"累计盈亏: ¥{profit:.2f}")
                self.total_profit_label.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 18px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
        else:
            self.total_profit_label.setText("累计盈亏: ¥****")

        if hasattr(self, 'daily_profit_label'):
            original_text = f"+¥{daily_profit:.2f}" if daily_profit > 0 else f"-¥{abs(daily_profit):.2f}" if daily_profit < 0 else f"¥{daily_profit:.2f}"
            self.daily_profit_label.setProperty(
                "original_value", original_text)

            if self.visible_stats.get("今日盈亏", True):
                if daily_profit > 0:
                    self.daily_profit_label.setText(f"+¥{daily_profit:.2f}")
                    self.daily_profit_label.setStyleSheet("""
                        QLabel {
                            color: #ef4444;
                            font-size: 24px;
                            font-weight: bold;
                            background: transparent;
                        }
                    """)
                elif daily_profit < 0:
                    self.daily_profit_label.setText(
                        f"-¥{abs(daily_profit):.2f}")
                    self.daily_profit_label.setStyleSheet("""
                        QLabel {
                            color: #10b981;
                            font-size: 24px;
                            font-weight: bold;
                            background: transparent;
                        }
                    """)
                else:
                    self.daily_profit_label.setText(f"¥{daily_profit:.2f}")
                    self.daily_profit_label.setStyleSheet("""
                        QLabel {
                            color: #10b981;
                            font-size: 24px;
                            font-weight: bold;
                            background: transparent;
                        }
                    """)
            else:
                self.daily_profit_label.setText("¥****")

        if hasattr(self, 'position_cost_label'):
            original_text = f"¥{position_cost:.2f}"
            self.position_cost_label.setProperty(
                "original_value", original_text)

            if self.visible_stats.get("持仓成本", True):
                self.position_cost_label.setText(f"¥{position_cost:.2f}")
            else:
                self.position_cost_label.setText("¥****")

        if hasattr(self, 'current_value_label'):
            original_text = f"¥{current_value:.2f}"
            self.current_value_label.setProperty(
                "original_value", original_text)

            if self.visible_stats.get("持有金额", True):
                self.current_value_label.setText(f"¥{current_value:.2f}")
            else:
                self.current_value_label.setText("¥****")

    def get_fund_holdings(self, fund_code: str) -> float:
        """获取某只基金的持有金额

        Args:
            fund_code: 基金代码

        Returns:
            持有金额
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT amount FROM fund_holdings WHERE fund_code = ?',
                    (fund_code,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception as e:
            logger.error(f"获取基金{fund_code}持有金额失败: {e}")
            return 0.0

    def get_fund_holdings_detail(
            self, fund_code: str) -> Tuple[float, float, float]:
        """获取基金的详细持仓信息

        Args:
            fund_code: 基金代码

        Returns:
            (成本价, 持有份额, 持有金额)
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT cost_price, shares, amount FROM fund_holdings WHERE fund_code = ?',
                    (fund_code,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0] or 0.0, result[1] or 0.0, result[2] or 0.0
                return 0.0, 0.0, 0.0
        except Exception as e:
            logger.error(f"获取基金{fund_code}持仓详情失败: {e}")
            return 0.0, 0.0, 0.0

    def get_fund_dividend(self, fund_code: str) -> float:
        """获取基金的分红总额

        Args:
            fund_code: 基金代码

        Returns:
            分红总额
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT SUM(dividend_amount) FROM dividend_records WHERE fund_code = ?',
                    (fund_code,)
                )
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0.0
        except Exception as e:
            logger.error(f"获取基金{fund_code}分红总额失败: {e}")
            return 0.0

    def set_fund_cost_price(self, fund_code: str):
        """设置基金持仓成本价

        Args:
            fund_code: 基金代码
        """
        cost_price, _, _ = self.get_fund_holdings_detail(fund_code)
        price, ok = QInputDialog.getDouble(
            self,
            "设置持仓成本价",
            f"请输入基金 {fund_code} 的持仓成本价:",
            value=cost_price,
            minValue=0,
            maxValue=1000,
            decimals=4
        )
        if ok:
            if self.update_fund_holdings_detail(fund_code, cost_price=price):
                self.update_data_async()
                QMessageBox.information(
                    self,
                    "成功",
                    f"基金{fund_code}持仓成本价已设置为: {price:.4f}元"
                )

    def set_fund_shares(self, fund_code: str):
        """设置基金持有份额

        Args:
            fund_code: 基金代码
        """
        _, shares, _ = self.get_fund_holdings_detail(fund_code)
        shares_val, ok = QInputDialog.getDouble(
            self,
            "设置持有份额",
            f"请输入基金 {fund_code} 的持有份额:",
            value=shares,
            minValue=0,
            maxValue=100000000,
            decimals=2
        )
        if ok:
            if self.update_fund_holdings_detail(fund_code, shares=shares_val):
                self.update_data_async()
                QMessageBox.information(
                    self,
                    "成功",
                    f"基金{fund_code}持有份额已设置为: {shares_val:.2f}份"
                )

    def record_dividend(self, fund_code: str):
        """记录基金分红

        Args:
            fund_code: 基金代码
        """
        dividend_amount, ok = QInputDialog.getDouble(
            self,
            "记录分红",
            f"请输入基金 {fund_code} 的分红金额:",
            value=0.0,
            minValue=0,
            maxValue=1000000,
            decimals=2
        )
        if ok:
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO dividend_records (fund_code, dividend_amount, dividend_date)
                        VALUES (?, ?, ?)
                    ''', (fund_code, dividend_amount, datetime.now().strftime('%Y-%m-%d')))

                self.update_data_async()
                QMessageBox.information(
                    self,
                    "成功",
                    f"基金{fund_code}分红已记录: ¥{dividend_amount:.2f}"
                )
                logger.info(f"记录基金{fund_code}分红: ¥{dividend_amount:.2f}")
            except Exception as e:
                logger.error(f"记录分红失败: {e}")
                QMessageBox.critical(self, "错误", f"记录分红失败: {str(e)}")

    def show_dividend_history(self, fund_code: str):
        """显示基金分红历史记录

        Args:
            fund_code: 基金代码
        """
        try:
            fund_name = ""
            if hasattr(self, 'fund_data') and fund_code in self.fund_data:
                fund_name = self.fund_data[fund_code].get('name', '')

            dialog = DividendHistoryDialog(
                parent=self,
                fund_code=fund_code,
                fund_name=fund_name
            )
            dialog.exec()

            self.update_data_async()
            logger.info(f"查看基金{fund_code}({fund_name})的分红历史")

        except Exception as e:
            logger.error(f"显示分红历史失败: {e}")
            QMessageBox.critical(self, "错误", f"显示分红历史失败: {str(e)}")

    def update_fund_holdings(self, fund_code: str, amount: float) -> bool:
        """更新基金持有金额

        Args:
            fund_code: 基金代码
            amount: 持有金额

        Returns:
            是否更新成功
        """
        return self.update_fund_holdings_detail(fund_code, amount=amount)

    def update_fund_holdings_detail(
            self,
            fund_code: str,
            cost_price: Optional[float] = None,
            shares: Optional[float] = None,
            amount: Optional[float] = None
    ) -> bool:
        """更新基金持仓详情

        Args:
            fund_code: 基金代码
            cost_price: 持仓成本价
            shares: 持有份额
            amount: 持有金额

        Returns:
            是否更新成功
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT id, cost_price, shares, amount FROM fund_holdings WHERE fund_code = ?',
                    (fund_code,)
                )
                existing = cursor.fetchone()

                if existing:
                    current_cost_price = existing[1] or 0.0
                    current_shares = existing[2] or 0.0
                    current_amount = existing[3] or 0.0

                    new_cost_price = cost_price if cost_price is not None else current_cost_price
                    new_shares = shares if shares is not None else current_shares
                    new_amount = amount if amount is not None else current_amount

                    cursor.execute('''
                        UPDATE fund_holdings
                        SET cost_price = ?, shares = ?, amount = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE fund_code = ?
                    ''', (new_cost_price, new_shares, new_amount, fund_code))
                else:
                    new_cost_price = cost_price if cost_price is not None else 0.0
                    new_shares = shares if shares is not None else 0.0
                    new_amount = amount if amount is not None else 0.0

                    cursor.execute('''
                        INSERT INTO fund_holdings (fund_code, cost_price, shares, amount)
                        VALUES (?, ?, ?, ?)
                    ''', (fund_code, new_cost_price, new_shares, new_amount))

            logger.info(
                f"更新基金{fund_code}持仓详情: 成本价={new_cost_price:.4f}, 份额={new_shares:.2f}, 金额={new_amount:.2f}")
            return True
        except Exception as e:
            logger.error(f"更新基金{fund_code}持仓详情失败: {e}")
            QMessageBox.critical(self, "错误", f"更新持仓详情失败: {str(e)}")
            return False

    def update_settings(
            self,
            refresh_interval: Optional[int] = None,
            auto_refresh_enabled: Optional[bool] = None
    ) -> bool:
        """更新数据库中的设置

        Args:
            refresh_interval: 刷新间隔（秒）
            auto_refresh_enabled: 是否启用自动刷新

        Returns:
            是否更新成功
        """
        try:
            with self.db_manager.get_cursor() as cursor:
                if refresh_interval is not None:
                    if refresh_interval < config.min_refresh_interval:
                        refresh_interval = config.min_refresh_interval
                    elif refresh_interval > config.max_refresh_interval:
                        refresh_interval = config.max_refresh_interval

                    cursor.execute(
                        'UPDATE settings SET refresh_interval = ? WHERE id = 1',
                        (refresh_interval,)
                    )

                if auto_refresh_enabled is not None:
                    cursor.execute(
                        'UPDATE settings SET auto_refresh_enabled = ? WHERE id = 1',
                        (auto_refresh_enabled,)
                    )

            logger.info(
                f"更新设置: refresh_interval={refresh_interval}, auto_refresh_enabled={auto_refresh_enabled}")
            return True
        except Exception as e:
            logger.error(f"更新设置失败: {e}")
            return False

    def set_refresh_interval(self):
        """设置刷新间隔"""
        try:
            interval = int(self.refresh_interval_input.text())
            if interval < config.min_refresh_interval:
                QMessageBox.warning(
                    self,
                    "警告",
                    f"刷新间隔不能少于{config.min_refresh_interval}秒"
                )
                return

            if interval > config.max_refresh_interval:
                QMessageBox.warning(
                    self,
                    "警告",
                    f"刷新间隔不能超过{config.max_refresh_interval}秒"
                )
                return

            if self.update_settings(refresh_interval=interval):
                self.refresh_timer.stop()
                self.refresh_timer.start(interval * 1000)
                QMessageBox.information(
                    self,
                    "提示",
                    f"刷新间隔已设置为 {interval} 秒"
                )
                logger.info(f"刷新间隔已设置为{interval}秒")
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的数字")
        except Exception as e:
            logger.error(f"设置刷新间隔失败: {e}")
            QMessageBox.critical(self, "错误", f"设置刷新间隔失败: {str(e)}")

    def toggle_auto_refresh(self):
        """切换自动刷新状态"""
        try:
            current_interval, auto_refresh_enabled = self.get_settings()
            new_state = not auto_refresh_enabled

            if self.update_settings(auto_refresh_enabled=new_state):
                if new_state:
                    self.refresh_timer.start()
                    self.auto_refresh_btn.setText("停止刷新")
                    self.auto_refresh_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: #10b981;
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 6px;
                            font-size: 13px;
                            font-weight: 500;
                        }}
                        QPushButton:hover {{
                            background: {self.darken_color('#10b981')};
                        }}
                    """)
                else:
                    self.refresh_timer.stop()
                    self.auto_refresh_btn.setText("启动刷新")
                    self.auto_refresh_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: #64748b;
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 6px;
                            font-size: 13px;
                            font-weight: 500;
                        }}
                        QPushButton:hover {{
                            background: {self.darken_color('#64748b')};
                        }}
                    """)

                QMessageBox.information(
                    self,
                    "提示",
                    f"自动刷新已{'启用' if new_state else '停用'}"
                )
                logger.info(f"自动刷新已{'启用' if new_state else '停用'}")
        except Exception as e:
            logger.error(f"切换自动刷新状态失败: {e}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")


class AddFundDialog(QDialog):
    """添加基金对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加基金")
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel("添加基金")
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("请输入6位基金代码...")
        self.code_input.setMaxLength(6)
        self.code_input.textChanged.connect(self.validate_input)
        self.code_input.setStyleSheet("""
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
        layout.addWidget(self.code_input)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #64748b;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.on_add_clicked)
        self.add_btn.setEnabled(False)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:disabled {
                background: #cbd5e1;
                color: #94a3b8;
            }
        """)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def validate_input(self, text: str):
        """验证输入的基金代码"""
        text = text.strip()
        is_valid, error_msg = FundDataFetcher.validate_fund_code(text)

        if not text:
            self.status_label.setText("")
            self.add_btn.setEnabled(False)
        elif is_valid:
            self.status_label.setText("✓ 基金代码格式正确")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #10b981;
                    font-size: 12px;
                }
            """)
            self.add_btn.setEnabled(True)
        else:
            self.status_label.setText(f"✗ {error_msg}")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ef4444;
                    font-size: 12px;
                }
            """)
            self.add_btn.setEnabled(False)

    def on_add_clicked(self):
        """添加按钮点击事件"""
        code = self.get_code()
        is_valid, _ = FundDataFetcher.validate_fund_code(code)
        if is_valid:
            self.accept()

    def get_code(self) -> str:
        """获取输入的基金代码"""
        return self.code_input.text().strip()


class FundHistoryChartWindow(QDialog):
    """基金历史估值图表窗口"""

    def __init__(self, fund_code, parent=None):
        super().__init__(parent)
        self.fund_code = fund_code

        self.setWindowTitle(f"基金 {self.fund_code} 单位净值变化")
        self.resize(800, 600)

        self.init_ui()
        self.load_history_data()

    def init_ui(self):
        layout = QVBoxLayout()

        self.fig = Figure(figsize=(10, 6), facecolor='white')
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('axes_leave_event', self.on_mouse_leave)

        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.points_data = []
        self.annotation = None

    def on_mouse_move(self, event):
        """鼠标移动事件处理"""
        if event.inaxes != self.ax:
            if self.annotation:
                self.annotation.set_visible(False)
                self.canvas.draw_idle()
            return

        if not self.points_data:
            return

        closest_point = None
        min_distance = float('inf')

        for x, y, date in self.points_data:
            distance = ((x - event.xdata) ** 2 + (y - event.ydata) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_point = (x, y, date)

        threshold = 0.05

        if closest_point and min_distance < threshold:
            x, y, date = closest_point
            if self.annotation is None:
                self.annotation = self.ax.annotate(
                    '', xy=(
                        x, y), xytext=(
                        20, 20), textcoords="offset points", bbox=dict(
                        boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8), arrowprops=dict(
                        arrowstyle="->", connectionstyle="arc3,rad=0"))
                self.annotation.set_visible(True)
                self.ax.add_artist(self.annotation)
            else:
                self.annotation.xy = (x, y)
                self.annotation.set_text(f'{date}\n净值: {y:.4f}')
                self.annotation.set_visible(True)

            self.canvas.draw_idle()
        elif self.annotation and self.annotation.get_visible():
            self.annotation.set_visible(False)
            self.canvas.draw_idle()

    def on_mouse_leave(self, event):
        """鼠标离开图表区域事件处理"""
        if self.annotation:
            self.annotation.set_visible(False)
            self.canvas.draw_idle()

    def load_history_data(self):
        """加载历史数据"""
        try:
            url = f"http://fund.eastmoney.com/f10/FundArchivesDatas.aspx?type=lsjz&code={self.fund_code}&per=20&page=1"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': f'http://fundf10.eastmoney.com/history/{self.fund_code}.html',
                'Accept': 'application/json, text/plain, */*'}
            import requests
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and 'Data' in data and 'LSJZList' in data['Data']:
                        lsjz_list = data['Data']['LSJZList']
                        dates = []
                        values = []

                        for item in reversed(lsjz_list):
                            date_str = item.get('FSRQ', '')
                            if date_str:
                                dates.append(date_str)
                            dwjz = item.get('DWJZ', '')
                            if dwjz is not None and dwjz != '':
                                try:
                                    values.append(float(dwjz))
                                except ValueError:
                                    values.append(0.0)
                            else:
                                values.append(0.0)

                        self.plot_history(dates, values)
                        return
                except ValueError:
                    pass

            backup_url = f"https://fundmobapi.eastmoney.com/FundMApi/FundNetValueList.ashx?FCODE={self.fund_code}&RANGE=3M"
            backup_response = requests.get(backup_url, headers=headers)

            if backup_response.status_code == 200:
                backup_data = backup_response.json()
                if backup_data.get('Datas'):
                    lsjz_list = backup_data['Datas']
                    dates = []
                    values = []

                    for item in reversed(lsjz_list):
                        date_str = item.get('FSRQ', '')
                        if date_str:
                            dates.append(date_str)
                        dwjz = item.get('DWJZ', '')
                        if dwjz is not None and dwjz != '':
                            try:
                                values.append(float(dwjz))
                            except ValueError:
                                values.append(0.0)
                        else:
                            values.append(0.0)

                    self.plot_history(dates, values)
                    return
        except Exception as e:
            print(f"获取基金历史数据失败: {e}")

        self.generate_mock_data()

    def generate_mock_data(self):
        """生成模拟历史数据"""
        import random
        from datetime import timedelta

        dates = []
        values = []
        base_date = datetime.now() - timedelta(days=29)

        base_value = 1.0
        for i in range(30):
            current_date = base_date + timedelta(days=i)
            dates.append(current_date.strftime('%Y-%m-%d'))

            if i == 0:
                value = base_value + random.uniform(-0.05, 0.05)
            else:
                value = values[-1] + random.uniform(-0.02, 0.02)
            values.append(round(value, 4))

        self.plot_history(dates, values)

    def plot_history(self, dates, values):
        """绘制历史数据图表"""
        self.ax.clear()

        self.ax.plot(
            range(len(dates)),
            values,
            marker='o',
            linestyle='-',
            linewidth=2,
            markersize=6,
            color='#1f77b4')

        for i in range(len(values)):
            if i == 0:
                color = 'black'
            elif i > 0 and values[i] > values[i - 1]:
                color = 'red'
            elif i > 0 and values[i] < values[i - 1]:
                color = 'green'
            else:
                color = 'gray'
            self.ax.scatter(i, values[i], color=color, s=30, zorder=5)

        self.ax.set_title(
            f'基金 {self.fund_code} 单位净值变化趋势',
            fontsize=14,
            fontweight='bold')
        self.ax.set_ylabel('单位净值', fontsize=12)
        self.ax.set_xlabel('日期', fontsize=12)

        step = max(1, len(dates) // 10)
        x_ticks = range(0, len(dates), step)
        x_labels = [dates[i] for i in x_ticks]
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(x_labels, rotation=45, ha='right')

        self.ax.grid(True, linestyle='--', alpha=0.6)

        self.ax.margins(x=0)

        self.points_data = [(i, values[i], dates[i])
                            for i in range(len(dates))]

        self.fig.tight_layout()

        self.canvas.draw()


class NotificationSettingsDialog(QDialog):
    """通知设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通知设置")
        self.setFixedSize(600, 560)
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)

        self.parent_monitor = parent
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel("通知设置")
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)

        popup_group = QGroupBox("弹窗通知")
        popup_layout = QVBoxLayout()

        self.popup_enabled = QCheckBox("启用弹窗通知")
        popup_layout.addWidget(self.popup_enabled)
        popup_group.setLayout(popup_layout)
        layout.addWidget(popup_group)

        dingtalk_group = QGroupBox("钉钉通知")
        dingtalk_layout = QVBoxLayout()

        self.dingtalk_enabled = QCheckBox("启用钉钉通知")
        dingtalk_layout.addWidget(self.dingtalk_enabled)

        webhook_layout = QHBoxLayout()
        webhook_layout.addWidget(QLabel("Webhook地址:"))
        self.dingtalk_webhook = QLineEdit()
        self.dingtalk_webhook.setPlaceholderText(
            "https://oapi.dingtalk.com/robot/send?access_token=...")
        webhook_layout.addWidget(self.dingtalk_webhook)
        dingtalk_layout.addLayout(webhook_layout)

        secret_layout = QHBoxLayout()
        secret_layout.addWidget(QLabel("加签密钥:"))
        self.dingtalk_secret = QLineEdit()
        self.dingtalk_secret.setPlaceholderText("SEC开头的密钥（选填，机器人安全设置中的加签密钥）")
        self.dingtalk_secret.setEchoMode(QLineEdit.Password)
        secret_layout.addWidget(self.dingtalk_secret)
        dingtalk_layout.addLayout(secret_layout)

        dingtalk_group.setLayout(dingtalk_layout)
        layout.addWidget(dingtalk_group)

        threshold_group = QGroupBox("预警阈值")
        threshold_layout = QGridLayout()

        threshold_layout.addWidget(QLabel("涨幅预警阈值(%):"), 0, 0)
        self.rise_threshold = QDoubleSpinBox()
        self.rise_threshold.setRange(0, 20)
        self.rise_threshold.setValue(3.0)
        self.rise_threshold.setSingleStep(0.5)
        threshold_layout.addWidget(self.rise_threshold, 0, 1)

        threshold_layout.addWidget(QLabel("跌幅预警阈值(%):"), 1, 0)
        self.fall_threshold = QDoubleSpinBox()
        self.fall_threshold.setRange(-20, 0)
        self.fall_threshold.setValue(-3.0)
        self.fall_threshold.setSingleStep(0.5)
        threshold_layout.addWidget(self.fall_threshold, 1, 1)

        threshold_layout.addWidget(QLabel("盈利预警阈值(元):"), 2, 0)
        self.profit_threshold = QDoubleSpinBox()
        self.profit_threshold.setRange(0, 100000)
        self.profit_threshold.setValue(1000.0)
        self.profit_threshold.setSingleStep(100)
        threshold_layout.addWidget(self.profit_threshold, 2, 1)

        threshold_layout.addWidget(QLabel("亏损预警阈值(元):"), 3, 0)
        self.loss_threshold = QDoubleSpinBox()
        self.loss_threshold.setRange(-100000, 0)
        self.loss_threshold.setValue(-1000.0)
        self.loss_threshold.setSingleStep(100)
        threshold_layout.addWidget(self.loss_threshold, 3, 1)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #64748b;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_settings(self):
        """加载设置"""
        if self.parent_monitor and hasattr(
                self.parent_monitor, 'notification_manager'):
            settings = self.parent_monitor.notification_manager.get_notification_settings()

            self.popup_enabled.setChecked(settings['popup_enabled'])
            self.dingtalk_enabled.setChecked(settings['dingtalk_enabled'])
            self.dingtalk_webhook.setText(settings['dingtalk_webhook'])
            self.dingtalk_secret.setText(settings['dingtalk_secret'])
            self.rise_threshold.setValue(settings['rise_threshold'])
            self.fall_threshold.setValue(settings['fall_threshold'])
            self.profit_threshold.setValue(settings['profit_threshold'])
            self.loss_threshold.setValue(settings['loss_threshold'])

    def save_settings(self):
        """保存设置"""
        try:
            if self.parent_monitor and hasattr(
                    self.parent_monitor, 'db_manager'):
                with self.parent_monitor.db_manager.get_cursor() as cursor:
                    cursor.execute('''
                        UPDATE notification_settings
                        SET popup_enabled = ?,
                            dingtalk_enabled = ?,
                            dingtalk_webhook = ?,
                            dingtalk_secret = ?,
                            rise_threshold = ?,
                            fall_threshold = ?,
                            profit_threshold = ?,
                            loss_threshold = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = 1
                    ''', (
                        self.popup_enabled.isChecked(),
                        self.dingtalk_enabled.isChecked(),
                        self.dingtalk_webhook.text(),
                        self.dingtalk_secret.text(),
                        self.rise_threshold.value(),
                        self.fall_threshold.value(),
                        self.profit_threshold.value(),
                        self.loss_threshold.value()
                    ))

                QMessageBox.information(self, "成功", "通知设置已保存")
                self.accept()
        except Exception as e:
            logger.error(f"保存通知设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("智能基金监控系统")
    app.setApplicationVersion("2.0")
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    window = FundMonitor()
    window.show()

    def signal_handler(signum, frame):
        """信号处理函数"""
        logger.info(f"收到信号 {signum}，准备退出...")
        window.quit_application()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("收到键盘中断，准备退出...")
        window.quit_application()


if __name__ == "__main__":
    main()
