#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
刷新按钮功能单元测试
测试 toggle_auto_refresh 流程
"""

import sys
import tempfile
import os
from unittest.mock import patch

import pytest

# Ensure PySide6 can be imported in headless environments
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow, QPushButton
from PySide6.QtCore import QTimer

from config import config
from models.database import DatabaseManager


@pytest.fixture(scope='module')
def qapp():
    """Create QApplication for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def db_manager():
    """Create temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    manager = DatabaseManager(db_path=db_path)
    yield manager
    manager.close()
    os.unlink(db_path)


class TestToggleAutoRefresh:
    """toggle_auto_refresh 流程测试"""

    def _make_monitor(self, db_manager, qapp):
        """Create a properly initialized FundMonitor for toggle testing."""
        from ui.main_window import FundMonitor
        monitor = FundMonitor()
        # Replace db_manager with our test one
        monitor.db_manager = db_manager
        return monitor

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    def test_toggle_to_enabled(self, mock_critical, mock_info, db_manager, qapp):
        """测试切换到启用刷新不报 darken_color 错误"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.update_settings(auto_refresh_enabled=False)

        monitor.toggle_auto_refresh()
        assert monitor.auto_refresh_btn.text() == "停止刷新"
        assert monitor.refresh_timer.isActive()
        mock_critical.assert_not_called()

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    def test_toggle_to_disabled(self, mock_critical, mock_info, db_manager, qapp):
        """测试切换到停用刷新不报 darken_color 错误"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.update_settings(auto_refresh_enabled=True)

        monitor.toggle_auto_refresh()
        assert monitor.auto_refresh_btn.text() == "启动刷新"
        assert not monitor.refresh_timer.isActive()
        mock_critical.assert_not_called()

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    def test_toggle_roundtrip(self, mock_critical, mock_info, db_manager, qapp):
        """测试启用再停用完整流程"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.update_settings(auto_refresh_enabled=False)

        monitor.toggle_auto_refresh()
        assert monitor.auto_refresh_btn.text() == "停止刷新"

        monitor.toggle_auto_refresh()
        assert monitor.auto_refresh_btn.text() == "启动刷新"
        mock_critical.assert_not_called()

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    def test_button_stylesheet_uses_theme(self, mock_critical, mock_info, db_manager, qapp):
        """测试按钮样式表使用主题模板方法"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.update_settings(auto_refresh_enabled=False)

        monitor.toggle_auto_refresh()
        stylesheet = monitor.auto_refresh_btn.styleSheet()
        # Must contain theme-derived colors, not raw method calls
        assert 'darken_color' not in stylesheet
        # Should use ProfessionalTheme.SUCCESS_COLOR (#00B42A)
        from ui.theme.professional_theme import ProfessionalTheme
        assert ProfessionalTheme.SUCCESS_COLOR in stylesheet


class TestSetRefreshInterval:
    """set_refresh_interval 流程测试"""

    def _make_monitor(self, db_manager, qapp):
        """Create a properly initialized FundMonitor for interval testing."""
        from ui.main_window import FundMonitor
        monitor = FundMonitor()
        monitor.db_manager = db_manager
        return monitor

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_set_valid_interval(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试设置有效刷新间隔"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.refresh_interval_input.setText("120")

        monitor.set_refresh_interval()
        mock_warning.assert_not_called()
        mock_critical.assert_not_called()
        assert monitor.refresh_timer.interval() == 120 * 1000
        mock_info.assert_called_once()
        assert "120" in mock_info.call_args[0][2]

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_set_minimum_interval(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试设置最小刷新间隔"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.refresh_interval_input.setText(str(config.min_refresh_interval))

        monitor.set_refresh_interval()
        mock_warning.assert_not_called()
        mock_critical.assert_not_called()
        assert monitor.refresh_timer.interval() == config.min_refresh_interval * 1000

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_set_maximum_interval(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试设置最大刷新间隔"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.refresh_interval_input.setText(str(config.max_refresh_interval))

        monitor.set_refresh_interval()
        mock_warning.assert_not_called()
        mock_critical.assert_not_called()
        assert monitor.refresh_timer.interval() == config.max_refresh_interval * 1000

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_interval_below_minimum_rejected(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试低于最小值的间隔被拒绝"""
        monitor = self._make_monitor(db_manager, qapp)
        original_interval = monitor.refresh_timer.interval()
        monitor.refresh_interval_input.setText("1")

        monitor.set_refresh_interval()
        mock_warning.assert_called_once()
        assert "少于" in mock_warning.call_args[0][2]
        mock_info.assert_not_called()
        mock_critical.assert_not_called()
        # Timer should not change
        assert monitor.refresh_timer.interval() == original_interval

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_interval_above_maximum_rejected(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试超过最大值的间隔被拒绝"""
        monitor = self._make_monitor(db_manager, qapp)
        original_interval = monitor.refresh_timer.interval()
        monitor.refresh_interval_input.setText("9999")

        monitor.set_refresh_interval()
        mock_warning.assert_called_once()
        assert "超过" in mock_warning.call_args[0][2]
        mock_info.assert_not_called()
        mock_critical.assert_not_called()
        assert monitor.refresh_timer.interval() == original_interval

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_non_numeric_input_rejected(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试非数字输入被拒绝"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.refresh_interval_input.setText("abc")

        monitor.set_refresh_interval()
        mock_warning.assert_called_once()
        assert "有效" in mock_warning.call_args[0][2]
        mock_critical.assert_not_called()

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_empty_input_rejected(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试空输入被拒绝"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.refresh_interval_input.setText("")

        monitor.set_refresh_interval()
        mock_warning.assert_called_once()
        mock_critical.assert_not_called()

    @patch('ui.main_window.QMessageBox.information')
    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.warning')
    def test_interval_persisted_to_db(self, mock_warning, mock_critical, mock_info, db_manager, qapp):
        """测试刷新间隔持久化到数据库"""
        monitor = self._make_monitor(db_manager, qapp)
        monitor.refresh_interval_input.setText("30")

        monitor.set_refresh_interval()
        # Verify via get_settings
        interval, _ = monitor.get_settings()
        assert interval == 30
