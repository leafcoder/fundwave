#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浮窗盈亏组件单元测试
测试拖动、吸附、半隐藏标签、悬停展开等核心逻辑
"""

import sys
import pytest

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from ui.widgets.floating_profit_widget import (
    FloatingProfitWidget, WIDGET_W, WIDGET_H,
    SNAP_THRESHOLD, PEEK_SIZE, DRAG_SCALE,
    SCALE_ANIM_DURATION, ANIM_DURATION, SNAP_ANIM_DURATION
)


@pytest.fixture(scope='session')
def app():
    """确保 QApplication 实例存在"""
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication(sys.argv)
    return instance


@pytest.fixture
def floating(app):
    """创建浮窗实例"""
    w = FloatingProfitWidget()
    w.show()
    QTest.qWait(50)
    yield w
    w.close()


# ==================== 初始化测试 ====================

class TestInit:
    """初始化相关测试"""

    def test_initial_size(self, floating):
        """初始尺寸应为正常尺寸"""
        assert floating.width() == WIDGET_W
        assert floating.height() == WIDGET_H

    def test_initial_anchored_pos(self, floating):
        """初始应有吸附位置"""
        assert floating._anchored_pos is not None

    def test_initial_peek_geo(self, floating):
        """初始应有半隐藏标签几何"""
        assert floating._peek_geo is not None

    def test_initial_anchor_edge(self, floating):
        """初始应有吸附边缘方向"""
        assert floating._anchor_edge in ('left', 'right', 'top', 'bottom')

    def test_initial_not_peeking(self, floating):
        """初始不应处于半隐藏状态"""
        assert floating._is_peeking is False

    def test_initial_not_dragging(self, floating):
        """初始不应处于拖动状态"""
        assert floating._is_dragging is False

    def test_window_flags(self, floating):
        """窗口标志应包含无边框、置顶、Tool"""
        flags = floating.windowFlags()
        assert bool(flags & Qt.FramelessWindowHint)
        assert bool(flags & Qt.WindowStaysOnTopHint)
        assert bool(flags & Qt.Tool)

    def test_content_visible_initially(self, floating):
        """初始应显示完整内容"""
        assert floating._content.isVisible()
        assert not floating._peek_tab.isVisible()


# ==================== 数据更新测试 ====================

class TestUpdateProfit:
    """盈亏数据更新测试"""

    def test_positive_profit(self, floating):
        """正数盈亏应显示红色 + 前缀"""
        floating.update_profit(123.45)
        assert "+¥123.45" in floating.profit_label.text()

    def test_negative_profit(self, floating):
        """负数盈亏应显示绿色 - 前缀"""
        floating.update_profit(-67.89)
        assert "-¥67.89" in floating.profit_label.text()

    def test_zero_profit(self, floating):
        """零盈亏应显示灰色"""
        floating.update_profit(0.0)
        assert "¥0.00" in floating.profit_label.text()

    def test_profit_stored(self, floating):
        """盈亏值应被存储"""
        floating.update_profit(42.0)
        assert floating._daily_profit == 42.0

    def test_peek_label_updates(self, floating):
        """更新盈亏时标签文字应同步"""
        floating.update_profit(100.0)
        assert floating._peek_label.text() == "+100"
        floating.update_profit(-50.0)
        assert floating._peek_label.text() == "-50"
        floating.update_profit(0.0)
        assert floating._peek_label.text() == "0"


# ==================== 几何计算测试 ====================

class TestGeometryCalc:
    """几何计算测试"""

    def test_normal_geo_at(self, floating):
        """_normal_geo_at 应生成正确矩形"""
        pos = QPoint(100, 200)
        geo = floating._normal_geo_at(pos)
        assert geo == QRect(100, 200, WIDGET_W, WIDGET_H)

    def test_scaled_geo_smaller(self, floating):
        """_scaled_geo 缩小后尺寸应小于正常"""
        floating.setGeometry(100, 100, WIDGET_W, WIDGET_H)
        scaled = floating._scaled_geo(DRAG_SCALE)
        assert scaled.width() < WIDGET_W
        assert scaled.height() < WIDGET_H

    def test_scaled_geo_center_preserved(self, floating):
        """_scaled_geo 应大致保持中心点不变"""
        floating.setGeometry(100, 100, WIDGET_W, WIDGET_H)
        original_center = floating.geometry().center()
        scaled = floating._scaled_geo(DRAG_SCALE)
        dx = abs(scaled.center().x() - original_center.x())
        dy = abs(scaled.center().y() - original_center.y())
        assert dx <= 1 and dy <= 1

    def test_scaled_geo_full_scale(self, floating):
        """_scaled_geo 1.0 应等于正常尺寸"""
        floating.setGeometry(100, 100, WIDGET_W, WIDGET_H)
        full = floating._scaled_geo(1.0)
        assert full.size() == floating._normal_geo_at(QPoint(0, 0)).size()


# ==================== 边缘检测测试 ====================

class TestEdgeDetection:
    """边缘检测测试"""

    def test_detect_right_edge(self, floating):
        """右侧吸附应检测为 right"""
        screen = floating._screen_rect()
        anchor = QPoint(screen.right() - WIDGET_W, screen.top())
        assert floating._detect_edge(anchor) == 'right'

    def test_detect_left_edge(self, floating):
        """左侧吸附应检测为 left"""
        screen = floating._screen_rect()
        anchor = QPoint(screen.left(), screen.top())
        assert floating._detect_edge(anchor) == 'left'

    def test_detect_top_edge(self, floating):
        """顶部吸附应检测为 top"""
        screen = floating._screen_rect()
        anchor = QPoint(500, screen.top())
        assert floating._detect_edge(anchor) == 'top'


# ==================== 吸附位置测试 ====================

class TestSnapPosition:
    """吸附位置计算测试"""

    def test_snap_to_left_edge(self, floating):
        """靠近左边缘应吸附"""
        pos = QPoint(SNAP_THRESHOLD - 1, 100)
        result = floating._snap_position(pos)
        screen = floating._screen_rect()
        assert result.x() == screen.left()

    def test_snap_to_right_edge(self, floating):
        """靠近右边缘应吸附"""
        screen = floating._screen_rect()
        pos = QPoint(screen.right() - WIDGET_W - SNAP_THRESHOLD + 1, 100)
        result = floating._snap_position(pos)
        assert result.x() == screen.right() - WIDGET_W

    def test_no_snap_far_from_edge(self, floating):
        """远离边缘不应吸附"""
        pos = QPoint(500, 300)
        result = floating._snap_position(pos)
        assert result == pos


# ==================== 半隐藏标签几何测试 ====================

class TestPeekGeo:
    """半隐藏标签几何测试"""

    def test_peek_geo_right_edge(self, floating):
        """右边缘标签应在屏幕右侧，宽 PEEK_SIZE"""
        screen = floating._screen_rect()
        anchor = QPoint(screen.right() - WIDGET_W, screen.top())
        peek = floating._compute_peek_geo(anchor, 'right')
        assert peek.width() == PEEK_SIZE
        assert peek.x() == screen.right() - PEEK_SIZE
        assert peek.height() == WIDGET_H

    def test_peek_geo_left_edge(self, floating):
        """左边缘标签应在屏幕左侧，宽 PEEK_SIZE"""
        screen = floating._screen_rect()
        anchor = QPoint(screen.left(), screen.top())
        peek = floating._compute_peek_geo(anchor, 'left')
        assert peek.width() == PEEK_SIZE
        assert peek.x() == screen.left()
        assert peek.height() == WIDGET_H

    def test_peek_geo_top_edge(self, floating):
        """顶边缘标签应在屏幕顶部，高 PEEK_SIZE"""
        screen = floating._screen_rect()
        anchor = QPoint(500, screen.top())
        peek = floating._compute_peek_geo(anchor, 'top')
        assert peek.height() == PEEK_SIZE
        assert peek.y() == screen.top()
        assert peek.width() == WIDGET_W


# ==================== 内容切换测试 ====================

class TestContentSwitch:
    """完整内容/标签内容切换测试"""

    def test_show_full_content(self, floating):
        """_show_full_content 应显示完整内容隐藏标签"""
        floating._show_peek_content()  # 先切到标签
        floating._show_full_content()  # 再切回来
        assert floating._content.isVisible()
        assert not floating._peek_tab.isVisible()

    def test_show_peek_content(self, floating):
        """_show_peek_content 应显示标签隐藏完整内容"""
        floating._show_peek_content()
        assert floating._peek_tab.isVisible()
        assert not floating._content.isVisible()


# ==================== 拖动逻辑测试 ====================

class TestDragLogic:
    """拖动逻辑测试"""

    def test_press_sets_offset(self, floating):
        """按下应设置拖动偏移"""
        floating.setGeometry(100, 100, WIDGET_W, WIDGET_H)
        QTest.mousePress(floating, Qt.LeftButton, pos=QPoint(10, 10))
        assert not floating._drag_offset.isNull()
        assert floating._is_dragging is False
        QTest.mouseRelease(floating, Qt.LeftButton, pos=QPoint(10, 10))

    def test_drag_start_transitions_size(self, floating):
        """首次移动应将缩放状态恢复为正常尺寸"""
        floating.setGeometry(100, 100, WIDGET_W, WIDGET_H)
        QTest.mousePress(floating, Qt.LeftButton, pos=QPoint(50, 32))
        QTest.qWait(50)
        QTest.mouseMove(floating, QPoint(60, 32))
        QTest.qWait(10)
        assert floating._is_dragging is True
        assert floating.width() == WIDGET_W
        assert floating.height() == WIDGET_H
        QTest.mouseRelease(floating, Qt.LeftButton, pos=QPoint(60, 32))

    def test_drag_cancel_no_movement(self, floating):
        """按下不移动就松手应判定为拖动取消"""
        floating.setGeometry(100, 100, WIDGET_W, WIDGET_H)
        anchored = floating._anchored_pos
        QTest.mousePress(floating, Qt.LeftButton, pos=QPoint(50, 32))
        QTest.qWait(SCALE_ANIM_DURATION + 50)
        QTest.mouseRelease(floating, Qt.LeftButton, pos=QPoint(50, 32))
        assert floating._is_dragging is False
        QTest.qWait(SCALE_ANIM_DURATION + ANIM_DURATION + 100)
        assert floating.pos() == anchored

    def test_release_snaps_to_edge(self, floating):
        """拖动松手应吸附到最近边缘"""
        screen = floating._screen_rect()
        drag_target = QPoint(screen.right() - WIDGET_W - 5, 100)
        floating.setGeometry(drag_target.x(), drag_target.y(), WIDGET_W, WIDGET_H)
        QTest.mousePress(floating, Qt.LeftButton, pos=QPoint(50, 32))
        QTest.mouseMove(floating, QPoint(55, 32))
        QTest.qWait(10)
        QTest.mouseRelease(floating, Qt.LeftButton, pos=QPoint(55, 32))
        QTest.qWait(SNAP_ANIM_DURATION + 100)
        assert floating._anchored_pos is not None
        assert floating._anchored_pos.x() == screen.right() - WIDGET_W


# ==================== 半隐藏展开/收起测试 ====================

class TestPeekSlide:
    """半隐藏展开/收起测试"""

    def test_slide_to_full(self, floating):
        """_slide_to_full 应取消半隐藏状态并显示完整内容"""
        floating._is_peeking = True
        floating._anchored_pos = QPoint(100, 100)
        floating._slide_to_full()
        assert floating._is_peeking is False
        assert floating._content.isVisible()

    def test_slide_to_peek_sets_state(self, floating):
        """_slide_to_peek 应设置半隐藏状态"""
        floating._is_peeking = False
        floating._anchored_pos = QPoint(100, 100)
        floating._peek_geo = QRect(100, 100, PEEK_SIZE, WIDGET_H)
        floating._slide_to_peek()
        assert floating._is_peeking is True

    def test_peek_anim_finishes_with_tab(self, floating):
        """收缩动画完成后应切换到标签内容"""
        floating._is_peeking = True
        floating._on_peek_anim_finished()
        assert floating._peek_tab.isVisible()
        assert not floating._content.isVisible()


# ==================== 动画通道测试 ====================

class TestAnimationChannel:
    """动画通道测试"""

    def test_single_animation_instance(self, floating):
        """应只有一个动画实例"""
        assert hasattr(floating, '_anim')

    def test_stop_anim_before_new(self, floating):
        """新动画启动前应停止旧动画"""
        floating._run_anim(QRect(0, 0, WIDGET_W, WIDGET_H), duration=1000)
        assert floating._anim.state() == floating._anim.State.Running
        floating._run_anim(QRect(100, 100, WIDGET_W, WIDGET_H), duration=100)
        assert floating._anim.state() == floating._anim.State.Running

    def test_run_anim_callback(self, floating):
        """_run_anim 的 on_finished 回调应被触发"""
        callback_called = [False]

        def on_done():
            callback_called[0] = True

        floating._run_anim(
            QRect(100, 100, WIDGET_W, WIDGET_H),
            duration=50,
            on_finished=on_done
        )
        QTest.qWait(100)
        assert callback_called[0] is True


# ==================== 窗口显示/隐藏测试 ====================

class TestShowHide:
    """显示/隐藏测试"""

    def test_show_widget(self, floating):
        """show 后应可见"""
        floating.show()
        assert floating.isVisible()

    def test_hide_widget(self, floating):
        """hide 后应不可见"""
        floating.show()
        floating.hide()
        assert not floating.isVisible()

    def test_close_btn_hides(self, floating):
        """关闭按钮应隐藏浮窗"""
        floating.show()
        QTest.qWait(10)
        floating.close_btn.click()
        assert not floating.isVisible()

    def test_double_click_emits_signal(self, floating):
        """双击金额标签应发出 show_main_window 信号"""
        signal_received = [False]
        floating.show_main_window.connect(lambda: signal_received.__setitem__(0, True))
        floating.profit_label.mouseDoubleClickEvent(None)
        assert signal_received[0] is True
