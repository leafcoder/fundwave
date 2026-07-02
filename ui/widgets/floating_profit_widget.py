#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浮窗盈亏组件
关闭主窗口后显示的迷你浮窗，仅展示今日盈亏
支持吸附屏幕边缘、半隐藏为小标签、悬停滑出展开
"""

from typing import Optional

from PySide6.QtCore import (QPoint, QRect, QTimer, Qt, Signal,
                            QPropertyAnimation, QEasingCurve)
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy, QVBoxLayout,
                               QWidget)

from ui.theme.theme_manager import get_theme_manager
from utils.logger import logger

# 吸附边缘的像素阈值
SNAP_THRESHOLD = 15
# 半隐藏时标签露出尺寸
PEEK_SIZE = 32
# 鼠标离开后延迟隐藏的毫秒数
HIDE_DELAY = 800
# 通用位移动画时长
ANIM_DURATION = 250
# 吸附动画时长
SNAP_ANIM_DURATION = 300
# 缩放动画时长
SCALE_ANIM_DURATION = 150
# 拖动按下缩放比例
DRAG_SCALE = 0.92

# 浮窗正常尺寸
WIDGET_W = 200
WIDGET_H = 64

# 方向箭头字符（使用ASCII替代，更可靠跨平台渲染）
ARROW = {'left': '<', 'right': '>', 'top': '^', 'bottom': 'v'}


class FloatingProfitWidget(QWidget):
    """可拖动的浮窗，显示今日盈亏

    Features:
        - 无边框、置顶、不显示在任务栏
        - 鼠标拖动移动位置，松手自动吸附到最近屏幕边缘
        - 吸附后自动收缩为边缘小标签，鼠标悬停滑出展开完整浮窗
        - 所有位置变化均有平滑动画过渡
        - 拖动按下时有缩放反馈
        - 双击金额标签恢复主窗口
        - 关闭按钮仅隐藏浮窗
    """

    show_main_window = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._daily_profit = 0.0

        # 拖动状态
        self._drag_offset = QPoint()
        self._drag_start_pos: Optional[QPoint] = None
        self._is_dragging = False

        # 边缘吸附与隐藏状态
        self._anchored_pos: Optional[QPoint] = None
        self._peek_geo: Optional[QRect] = None
        self._is_peeking = False
        self._anchor_edge: Optional[str] = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._slide_to_peek)

        # 唯一的动画通道
        self._anim = QPropertyAnimation(self, b"geometry")

        self._setup_window_flags()
        self._setup_ui()
        self._apply_theme()
        self._move_to_top_right()

        get_theme_manager().on_theme_changed(self._on_theme_changed)
        logger.info("浮窗组件初始化完成")

    # ==================== 初始化 ====================

    def _setup_window_flags(self) -> None:
        """设置窗口标志"""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    def _setup_ui(self) -> None:
        """构建浮窗UI"""
        self.resize(WIDGET_W, WIDGET_H)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # --- 完整内容层 ---
        self._content = QWidget(self)
        content_layout = QHBoxLayout(self._content)
        content_layout.setContentsMargins(12, 8, 8, 8)
        content_layout.setSpacing(8)

        self.title_label = QLabel("今日盈亏")
        self.title_label.setFixedHeight(20)

        self.profit_label = QLabel("¥0.00")
        self.profit_label.setFixedHeight(24)
        self.profit_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.profit_label.mouseDoubleClickEvent = lambda _: self.show_main_window.emit()

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.clicked.connect(self.hide)

        content_layout.addWidget(self.title_label)
        content_layout.addStretch()
        content_layout.addWidget(self.profit_label)
        content_layout.addWidget(self.close_btn)

        # --- 半隐藏标签层 ---
        self._peek_tab = QWidget(self)
        self._peek_tab.setCursor(QCursor(Qt.PointingHandCursor))

        # 根据边缘方向使用不同布局，初始用垂直布局（左右边缘）
        peek_layout = QVBoxLayout(self._peek_tab)
        peek_layout.setContentsMargins(2, 4, 2, 4)
        peek_layout.setSpacing(0)

        # 箭头指示展开方向
        self._peek_arrow = QLabel("▶")
        self._peek_arrow.setAlignment(Qt.AlignCenter)
        self._peek_arrow.setFixedHeight(12)

        # 盈亏数值
        self._peek_label = QLabel("¥0")
        self._peek_label.setAlignment(Qt.AlignCenter)

        peek_layout.addWidget(self._peek_arrow)
        peek_layout.addWidget(self._peek_label)

        # 初始：显示完整内容
        self._peek_tab.hide()
        self._content.show()

    # ==================== 主题 ====================

    def _get_theme_class(self):
        """获取当前主题类"""
        return get_theme_manager().get_current_theme_class()

    def _apply_theme(self) -> None:
        """应用当前主题样式"""
        theme = self._get_theme_class()

        self.setStyleSheet(f"""
            FloatingProfitWidget {{
                background-color: {theme.BG_PRIMARY};
                border: 1px solid {theme.BORDER_COLOR};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: normal;
            }}
        """)

        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {theme.TEXT_TERTIARY};
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                color: {theme.TEXT_PRIMARY};
                background-color: {theme.BG_TERTIARY};
            }}
        """)

        self._style_profit_label(self._daily_profit, theme)
        self._style_peek_tab(theme)

    def _style_profit_label(self, daily_profit: float, theme=None) -> None:
        """根据盈亏值设置金额标签样式"""
        if theme is None:
            theme = self._get_theme_class()

        if daily_profit > 0:
            color = theme.RISE_COLOR
            text = f"+¥{daily_profit:.2f}"
        elif daily_profit < 0:
            color = theme.FALL_COLOR
            text = f"-¥{abs(daily_profit):.2f}"
        else:
            color = theme.FLAT_COLOR
            text = f"¥{daily_profit:.2f}"

        self.profit_label.setText(text)
        self.profit_label.setToolTip(f"今日盈亏: {text}")
        self.profit_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)

    def _style_peek_tab(self, theme=None) -> None:
        """设置半隐藏标签样式——渐变背景 + 箭头 + 盈亏色"""
        if theme is None:
            theme = self._get_theme_class()

        profit = self._daily_profit
        if profit > 0:
            bg = theme.RISE_LIGHT
            border = theme.RISE_COLOR
            text_color = theme.RISE_COLOR
            text = f"+{abs(profit):.0f}"
            tooltip = f"今日盈亏: +¥{profit:.2f}\n悬停展开"
        elif profit < 0:
            bg = theme.FALL_LIGHT
            border = theme.FALL_COLOR
            text_color = theme.FALL_COLOR
            text = f"-{abs(profit):.0f}"
            tooltip = f"今日盈亏: -¥{abs(profit):.2f}\n悬停展开"
        else:
            bg = theme.BG_TERTIARY
            border = theme.BORDER_COLOR
            text_color = theme.TEXT_TERTIARY
            text = "0"
            tooltip = "今日盈亏: ¥0.00\n悬停展开"

        # 箭头方向
        arrow_char = ARROW.get(self._anchor_edge or 'right', '▶')

        self._peek_arrow.setText(arrow_char)
        self._peek_label.setText(text)
        self._peek_tab.setToolTip(tooltip)

        self._peek_arrow.setStyleSheet(f"""
            QLabel {{
                color: {border};
                font-size: 9px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        self._peek_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        self._peek_tab.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QWidget:hover {{
                background-color: {border};
            }}
            QWidget:hover > QLabel {{
                color: white;
            }}
        """)

    # ==================== 核心：完整/标签模式切换 ====================

    def _show_full_content(self) -> None:
        """切换到完整内容模式"""
        self._peek_tab.hide()
        self._content.show()
        self._content.setGeometry(0, 0, WIDGET_W, WIDGET_H)

    def _show_peek_content(self) -> None:
        """切换到半隐藏标签模式"""
        self._content.hide()
        self._peek_tab.show()

        # 重新布局标签：左右边缘用纵向，上下边缘用横向
        edge = self._anchor_edge or 'right'
        want_vertical = edge in ('left', 'right')
        old_layout = self._peek_tab.layout()
        is_vertical = isinstance(old_layout, QVBoxLayout)

        if is_vertical != want_vertical:
            # 先将子控件从旧布局中取出，避免被临时 QWidget 销毁
            old_layout.removeWidget(self._peek_arrow)
            old_layout.removeWidget(self._peek_label)
            # 临时 QWidget 接管旧布局使其被安全销毁
            QWidget().setLayout(old_layout)

            if want_vertical:
                layout = QVBoxLayout(self._peek_tab)
                layout.setContentsMargins(2, 6, 2, 6)
                layout.setSpacing(1)
            else:
                layout = QHBoxLayout(self._peek_tab)
                layout.setContentsMargins(6, 2, 6, 2)
                layout.setSpacing(2)

            layout.addWidget(self._peek_arrow, alignment=Qt.AlignCenter)
            layout.addWidget(self._peek_label, alignment=Qt.AlignCenter)

        if want_vertical:
            self._peek_tab.setGeometry(0, 0, PEEK_SIZE, WIDGET_H)
        else:
            self._peek_tab.setGeometry(0, 0, WIDGET_W, PEEK_SIZE)

        # 更新箭头方向和样式
        self._style_peek_tab()

    # ==================== 核心动画 ====================

    def _stop_anim(self) -> None:
        """停止当前动画"""
        if self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()

    def _run_anim(self, target: QRect, duration: int = ANIM_DURATION,
                  easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
                  on_finished=None) -> None:
        """启动 geometry 动画"""
        self._stop_anim()
        self._anim.setDuration(duration)
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(easing)
        if on_finished:
            self._anim.finished.connect(on_finished, Qt.ConnectionType.SingleShotConnection)
        self._anim.start()

    def _normal_geo_at(self, pos: QPoint) -> QRect:
        """在指定左上角位置生成正常大小的矩形"""
        return QRect(pos.x(), pos.y(), WIDGET_W, WIDGET_H)

    def _scaled_geo(self, scale: float) -> QRect:
        """以当前中心点为基准，生成缩放后的矩形"""
        cur = self.geometry()
        cx, cy = cur.center().x(), cur.center().y()
        nw = int(WIDGET_W * scale)
        nh = int(WIDGET_H * scale)
        return QRect(cx - nw // 2, cy - nh // 2, nw, nh)

    # ==================== 屏幕边缘 ====================

    def _screen_rect(self) -> QRect:
        """获取可用屏幕区域"""
        screen = QApplication.primaryScreen()
        if screen:
            return screen.availableGeometry()
        return QRect(0, 0, 1920, 1080)

    def _detect_edge(self, anchor: QPoint) -> str:
        """检测吸附位置对应的屏幕边缘"""
        screen = self._screen_rect()
        x, y = anchor.x(), anchor.y()

        if x <= screen.left():
            return 'left'
        elif x + WIDGET_W >= screen.right():
            return 'right'
        elif y <= screen.top():
            return 'top'
        elif y + WIDGET_H >= screen.bottom():
            return 'bottom'
        dists = {
            'left': abs(x - screen.left()),
            'right': abs(x + WIDGET_W - screen.right()),
            'top': abs(y - screen.top()),
            'bottom': abs(y + WIDGET_H - screen.bottom()),
        }
        return min(dists, key=dists.get)

    def _snap_position(self, pos: QPoint) -> QPoint:
        """将位置吸附到最近的屏幕边缘"""
        screen = self._screen_rect()
        x, y = pos.x(), pos.y()

        dist_left = abs(x - screen.left())
        dist_right = abs(x + WIDGET_W - screen.right())
        dist_top = abs(y - screen.top())
        dist_bottom = abs(y + WIDGET_H - screen.bottom())

        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

        if min_dist > SNAP_THRESHOLD:
            return pos

        if min_dist == dist_left:
            x = screen.left()
        elif min_dist == dist_right:
            x = screen.right() - WIDGET_W
        elif min_dist == dist_top:
            y = screen.top()
        else:
            y = screen.bottom() - WIDGET_H

        return QPoint(x, y)

    def _compute_peek_geo(self, anchor: QPoint, edge: str) -> QRect:
        """计算半隐藏标签的几何矩形"""
        screen = self._screen_rect()
        x, y = anchor.x(), anchor.y()

        if edge == 'left':
            return QRect(screen.left(), y, PEEK_SIZE, WIDGET_H)
        elif edge == 'right':
            return QRect(screen.right() - PEEK_SIZE, y, PEEK_SIZE, WIDGET_H)
        elif edge == 'top':
            return QRect(x, screen.top(), WIDGET_W, PEEK_SIZE)
        else:
            return QRect(x, screen.bottom() - PEEK_SIZE, WIDGET_W, PEEK_SIZE)

    def _move_to_top_right(self) -> None:
        """将浮窗移至屏幕右上角并吸附"""
        screen = self._screen_rect()
        pos = QPoint(screen.right() - WIDGET_W, screen.top())
        edge = self._detect_edge(pos)
        self._anchored_pos = pos
        self._anchor_edge = edge
        self._peek_geo = self._compute_peek_geo(pos, edge)
        self._show_full_content()
        self.setGeometry(self._normal_geo_at(pos))
        self._hide_timer.start(HIDE_DELAY)

    def _anchor_at(self, snap_pos: QPoint) -> None:
        """设置吸附位置和对应的边缘/标签几何"""
        edge = self._detect_edge(snap_pos)
        self._anchored_pos = snap_pos
        self._anchor_edge = edge
        self._peek_geo = self._compute_peek_geo(snap_pos, edge)

    # ==================== 半隐藏展开/收起 ====================

    def _slide_to_full(self) -> None:
        """从标签模式动画滑出为完整浮窗"""
        if not self._is_peeking or not self._anchored_pos:
            return
        self._is_peeking = False
        self._hide_timer.stop()
        self._show_full_content()
        self._run_anim(self._normal_geo_at(self._anchored_pos))

    def _slide_to_peek(self) -> None:
        """从完整浮窗动画收缩为边缘标签"""
        if self._is_peeking or not self._peek_geo:
            return
        if self.underMouse():
            return
        self._is_peeking = True
        self._run_anim(
            self._peek_geo,
            duration=ANIM_DURATION,
            easing=QEasingCurve.Type.InCubic,
            on_finished=self._on_peek_anim_finished
        )

    def _on_peek_anim_finished(self) -> None:
        """收缩动画完成，切换为标签内容"""
        self._show_peek_content()

    # ==================== 数据更新 ====================

    def update_profit(self, daily_profit: float) -> None:
        """更新今日盈亏数据"""
        self._daily_profit = daily_profit
        self._style_profit_label(daily_profit)
        self._style_peek_tab()

    def _on_theme_changed(self) -> None:
        """主题变更回调"""
        self._apply_theme()

    # ==================== 拖动逻辑 ====================

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """按下：停止动画，跳到正常尺寸，播放缩小反馈"""
        if event.button() == Qt.LeftButton:
            self._stop_anim()
            self._hide_timer.stop()

            if self._is_peeking and self._anchored_pos:
                self._is_peeking = False
                self._show_full_content()
                self.setGeometry(self._normal_geo_at(self._anchored_pos))

            if self.size() != self._normal_geo_at(QPoint(0, 0)).size():
                center = self.geometry().center()
                self.setGeometry(
                    center.x() - WIDGET_W // 2,
                    center.y() - WIDGET_H // 2,
                    WIDGET_W, WIDGET_H
                )

            self._drag_offset = (event.globalPosition().toPoint()
                                 - self.frameGeometry().topLeft())
            self._drag_start_pos = self.pos()
            self._is_dragging = False

            self._run_anim(
                self._scaled_geo(DRAG_SCALE),
                duration=SCALE_ANIM_DURATION,
                easing=QEasingCurve.Type.OutCubic
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """拖动窗口"""
        if event.buttons() & Qt.LeftButton and not self._drag_offset.isNull():
            if not self._is_dragging:
                self._is_dragging = True
                self._stop_anim()

                cur_center = self.geometry().center()
                self.setGeometry(
                    cur_center.x() - WIDGET_W // 2,
                    cur_center.y() - WIDGET_H // 2,
                    WIDGET_W, WIDGET_H
                )
                self._drag_offset = (event.globalPosition().toPoint()
                                     - self.frameGeometry().topLeft())

            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """松手：吸附边缘或回到原位"""
        if event.button() == Qt.LeftButton:
            self._drag_offset = QPoint()

            if self._is_dragging:
                snap = self._snap_position(self.pos())
                self._anchor_at(snap)
                self._is_peeking = False
                self._run_anim(
                    self._normal_geo_at(snap),
                    duration=SNAP_ANIM_DURATION,
                    easing=QEasingCurve.Type.OutBack,
                    on_finished=self._on_snap_finished
                )
            else:
                self._is_peeking = False
                self._run_anim(
                    self._scaled_geo(1.0),
                    duration=SCALE_ANIM_DURATION,
                    easing=QEasingCurve.Type.OutBack,
                    on_finished=self._on_drag_cancel_finished
                )

            self._is_dragging = False
        super().mouseReleaseEvent(event)

    def _on_snap_finished(self) -> None:
        """吸附动画完成后，延迟半隐藏"""
        self._hide_timer.start(HIDE_DELAY)

    def _on_drag_cancel_finished(self) -> None:
        """拖动取消，缩放恢复后回到原位"""
        if self._anchored_pos:
            target = self._normal_geo_at(self._anchored_pos)
            self._run_anim(target, ANIM_DURATION, QEasingCurve.Type.OutCubic)
            self._hide_timer.start(HIDE_DELAY)

    # ==================== 悬停展开/收起 ====================

    def enterEvent(self, event) -> None:
        """鼠标进入时展开浮窗"""
        self._hide_timer.stop()
        if self._is_peeking:
            self._slide_to_full()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """鼠标离开后延迟半隐藏"""
        if self._anchored_pos and not self._is_peeking:
            self._hide_timer.start(HIDE_DELAY)
        super().leaveEvent(event)
