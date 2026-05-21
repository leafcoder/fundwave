#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题管理器
提供主题切换、动画效果、响应式适配等功能
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import (QAbstractAnimation, QEasingCurve,
                            QParallelAnimationGroup, QPoint,
                            QPropertyAnimation, QRect,
                            QSequentialAnimationGroup, QSize, Qt)
from PySide6.QtGui import QColor, QFont, QPalette, QScreen
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QWidget

from ui.theme.dark_theme import DarkTheme
from ui.theme.professional_theme import ProfessionalTheme


class ThemeType(Enum):
    """主题类型枚举"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # 跟随系统


class AnimationType(Enum):
    """动画类型枚举"""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    BOUNCE = "bounce"


class ThemeManager:
    """
    主题管理器 - 单例模式
    
    功能：
    1. 主题切换（亮色/暗黑/跟随系统）
    2. 动画效果（淡入淡出、滑动、缩放）
    3. 响应式布局（适配不同分辨率）
    4. 主题偏好持久化
    """
    
    _instance: Optional['ThemeManager'] = None
    
    def __new__(cls) -> 'ThemeManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._current_theme: ThemeType = ThemeType.LIGHT
        self._theme_changed_callbacks: List[Callable] = []
        self._animation_enabled: bool = True
        self._screen_size: QSize = QSize(1920, 1080)
        
        # 响应式断点（基于宽度）
        self.breakpoints = {
            'xs': 480,   # 手机竖屏
            'sm': 768,   # 平板竖屏/手机横屏
            'md': 1024,  # 平板横屏/小笔记本
            'lg': 1280,  # 桌面显示器
            'xl': 1536,  # 大屏显示器
            'xxl': 1920  # 超大屏
        }
        
        self._load_preferences()
    
    @classmethod
    def instance(cls) -> 'ThemeManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 主题管理 ====================
    
    @property
    def current_theme(self) -> ThemeType:
        """获取当前主题"""
        return self._current_theme
    
    @property
    def is_dark_mode(self) -> bool:
        """是否为暗黑模式"""
        if self._current_theme == ThemeType.AUTO:
            return self._is_system_dark()
        return self._current_theme == ThemeType.DARK
    
    def get_current_theme_class(self):
        """获取当前主题类"""
        if self.is_dark_mode:
            return DarkTheme
        return ProfessionalTheme
    
    def set_theme(self, theme_type: ThemeType):
        """
        设置主题
        
        Args:
            theme_type: 主题类型（LIGHT/DARK/AUTO）
        """
        old_theme = self._current_theme
        self._current_theme = theme_type
        
        # 触发回调
        for callback in self._theme_changed_callbacks:
            try:
                callback(old_theme, theme_type)
            except Exception as e:
                from utils.logger import logger
                logger.error(f"主题切换回调失败: {e}")
        
        # 保存偏好
        self._save_preferences()
        
        from utils.logger import logger
        logger.info(f"主题已切换为: {theme_type.value}")
    
    def toggle_theme(self):
        """切换亮色/暗黑模式"""
        if self.is_dark_mode:
            self.set_theme(ThemeType.LIGHT)
        else:
            self.set_theme(ThemeType.DARK)
    
    def on_theme_changed(self, callback: Callable[[ThemeType, ThemeType], None]):
        """
        注册主题变更回调
        
        Args:
            callback: 回调函数 (old_theme, new_theme) -> None
        """
        self._theme_changed_callbacks.append(callback)
    
    def apply_theme_to_widget(self, widget: QWidget):
        """
        将当前主题应用到指定控件
        
        Args:
            widget: 目标控件
        """
        theme_class = self.get_current_theme_class()
        theme_class.apply_to_widget(widget)
    
    def _is_system_dark(self) -> bool:
        """检测系统是否为暗黑模式"""
        try:
            app = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.Window).name()
                # 如果窗口背景色较暗，则认为是暗黑模式
                r, g, b = int(window_color[1:3], 16), int(window_color[3:5], 16), int(window_color[5:7], 16)
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                return brightness < 128
        except Exception:
            pass
        return False
    
    # ==================== 动画效果 ====================
    
    @property
    def animation_enabled(self) -> bool:
        """动画是否启用"""
        return self._animation_enabled
    
    @animation_enabled.setter
    def animation_enabled(self, enabled: bool):
        """设置动画开关"""
        self._animation_enabled = enabled
    
    def create_fade_animation(
        self,
        widget: QWidget,
        duration: int = 300,
        start_opacity: float = 0.0,
        end_opacity: float = 1.0,
        easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutCubic
    ) -> QPropertyAnimation:
        """
        创建淡入淡出动画
        
        Args:
            widget: 目标控件
            duration: 动画时长（毫秒）
            start_opacity: 起始透明度
            end_opacity: 结束透明度
            easing_curve: 缓动曲线
            
        Returns:
            动画对象
        """
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(easing_curve)
        
        return animation
    
    def create_slide_animation(
        self,
        widget: QWidget,
        direction: str = "left",
        distance: int = 100,
        duration: int = 400,
        easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutCubic
    ) -> QPropertyAnimation:
        """
        创建滑动动画
        
        Args:
            widget: 目标控件
            direction: 滑动方向（left/right/up/down）
            distance: 滑动距离（像素）
            duration: 动画时长（毫秒）
            easing_curve: 缓动曲线
            
        Returns:
            动画对象
        """
        start_pos = widget.pos()
        end_pos = QPoint(start_pos)
        
        if direction == "left":
            start_pos.setX(start_pos.x() + distance)
        elif direction == "right":
            start_pos.setX(start_pos.x() - distance)
        elif direction == "up":
            start_pos.setY(start_pos.y() + distance)
        elif direction == "down":
            start_pos.setY(start_pos.y() - distance)
        
        widget.move(start_pos)
        widget.show()
        
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(easing_curve)
        
        return animation
    
    def create_scale_animation(
        self,
        widget: QWidget,
        start_scale: float = 0.8,
        end_scale: float = 1.0,
        duration: int = 300,
        easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutBack
    ) -> QPropertyAnimation:
        """
        创建缩放动画
        
        Args:
            widget: 目标控件
            start_scale: 起始缩放比例
            end_scale: 结束缩放比例
            duration: 动画时长（毫秒）
            easing_curve: 缓动曲线
            
        Returns:
            动画对象
        """
        original_geometry = widget.geometry()
        center = widget.geometry().center()
        
        start_rect = QRect(
            int(center.x() - original_geometry.width() * start_scale / 2),
            int(center.y() - original_geometry.height() * start_scale / 2),
            int(original_geometry.width() * start_scale),
            int(original_geometry.height() * start_scale)
        )
        
        end_rect = original_geometry
        
        widget.setGeometry(start_rect)
        widget.show()
        
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(easing_curve)
        
        return animation
    
    def animate_widget_show(
        self,
        widget: QWidget,
        animation_type: AnimationType = AnimationType.FADE_IN,
        duration: int = 300,
        on_finished: Optional[Callable] = None
    ):
        """
        显示控件时播放动画
        
        Args:
            widget: 目标控件
            animation_type: 动画类型
            duration: 动画时长
            on_finished: 动画完成回调
        """
        if not self._animation_enabled:
            widget.show()
            if on_finished:
                on_finished()
            return
        
        if animation_type == AnimationType.FADE_IN:
            anim = self.create_fade_animation(widget, duration)
        elif animation_type in [AnimationType.SLIDE_LEFT, AnimationType.SLIDE_RIGHT,
                                AnimationType.SLIDE_UP, AnimationType.SLIDE_DOWN]:
            direction = animation_type.value.replace("slide_", "")
            anim = self.create_slide_animation(widget, direction, duration=duration)
        elif animation_type in [AnimationType.SCALE_UP, AnimationType.SCALE_DOWN]:
            scale = 0.8 if animation_type == AnimationType.SCALE_UP else 1.2
            anim = self.create_scale_animation(widget, start_scale=scale, duration=duration)
        elif animation_type == AnimationType.BOUNCE:
            anim = self.create_scale_animation(
                widget, 
                start_scale=0.5, 
                duration=duration,
                easing_curve=QEasingCurve.Type.OutElastic
            )
        else:
            widget.show()
            if on_finished:
                on_finished()
            return
        
        if on_finished:
            anim.finished.connect(on_finished)
        
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    
    def animate_widget_hide(
        self,
        widget: QWidget,
        animation_type: AnimationType = AnimationType.FADE_OUT,
        duration: int = 300,
        on_finished: Optional[Callable] = None
    ):
        """
        隐藏控件时播放动画
        
        Args:
            widget: 目标控件
            animation_type: 动画类型
            duration: 动画时长
            on_finished: 动画完成回调
        """
        if not self._animation_enabled:
            widget.hide()
            if on_finished:
                on_finished()
            return
        
        if animation_type == AnimationType.FADE_OUT:
            anim = self.create_fade_animation(
                widget, 
                duration, 
                start_opacity=1.0, 
                end_opacity=0.0
            )
            anim.finished.connect(widget.hide)
        else:
            widget.hide()
            if on_finished:
                on_finished()
            return
        
        if on_finished:
            anim.finished.connect(on_finished)
        
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    
    def animate_value_change(
        self,
        label_widget: QWidget,
        start_value: float,
        end_value: float,
        duration: int = 500,
        formatter: Callable[[float], str] = lambda x: f"{x:.2f}",
        steps: int = 60
    ):
        """
        数值变化动画（滚动效果）
        
        Args:
            label_widget: 显示数值的标签控件
            start_value: 起始值
            end_value: 结束值
            duration: 动画时长（毫秒）
            formatter: 格式化函数
            steps: 动画步数
        """
        if not self._animation_enabled or not hasattr(label_widget, 'setText'):
            label_widget.setText(formatter(end_value))
            return
        
        from PySide6.QtCore import QTimer
        
        current_step = 0
        value_range = end_value - start_value
        
        def update_value():
            nonlocal current_step
            current_step += 1
            
            if current_step >= steps:
                label_widget.setText(formatter(end_value))
                timer.stop()
                return
            
            # 使用缓动函数计算当前值
            progress = current_step / steps
            eased_progress = self._ease_out_cubic(progress)
            
            current_value = start_value + value_range * eased_progress
            label_widget.setText(formatter(current_value))
        
        timer = QTimer()
        timer.timeout.connect(update_value)
        timer.start(duration // steps)
    
    def _ease_out_cubic(self, t: float) -> float:
        """缓出三次方函数"""
        t -= 1
        return t * t * t + 1
    
    # ==================== 响应式适配 ====================
    
    def update_screen_info(self):
        """更新屏幕信息"""
        app = QApplication.instance()
        if app and app.primaryScreen():
            screen = app.primaryScreen()
            self._screen_size = screen.availableSize()
    
    @property
    def screen_width(self) -> int:
        """屏幕宽度"""
        return self._screen_size.width()
    
    @property
    def screen_height(self) -> int:
        """屏幕高度"""
        return self._screen_size.height()
    
    def get_breakpoint(self) -> str:
        """
        获取当前屏幕对应的断点
        
        Returns:
            断点名称（xs/sm/md/lg/xl/xxl）
        """
        width = self.screen_width
        
        if width < self.breakpoints['sm']:
            return 'xs'
        elif width < self.breakpoints['md']:
            return 'sm'
        elif width < self.breakpoints['lg']:
            return 'md'
        elif width < self.breakpoints['xl']:
            return 'lg'
        elif width < self.breakpoints['xxl']:
            return 'xl'
        else:
            return 'xxl'
    
    def is_mobile(self) -> bool:
        """是否为移动设备尺寸"""
        return self.get_breakpoint() in ['xs', 'sm']
    
    def is_tablet(self) -> bool:
        """是否为平板设备尺寸"""
        return self.get_breakpoint() in ['sm', 'md']
    
    def is_desktop(self) -> bool:
        """是否为桌面设备尺寸"""
        return self.get_breakpoint() in ['md', 'lg', 'xl', 'xxl']
    
    def get_responsive_value(self, values: Dict[str, Any], default: Any = None) -> Any:
        """
        根据屏幕尺寸获取响应式值
        
        Args:
            values: 各断点的值映射 {'xs': ..., 'sm': ..., 'md': ..., ...}
            default: 默认值（如果找不到对应断点）
            
        Returns:
            当前断点对应的值
        """
        breakpoint = self.get_breakpoint()
        
        # 从当前断点向上查找第一个可用的值
        breakpoints_order = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl']
        current_idx = breakpoints_order.index(breakpoint)
        
        for i in range(current_idx, len(breakpoints_order)):
            bp = breakpoints_order[i]
            if bp in values:
                return values[bp]
        
        # 如果没找到，向下查找
        for i in range(current_idx - 1, -1, -1):
            bp = breakpoints_order[i]
            if bp in values:
                return values[bp]
        
        return default
    
    def get_responsive_font_size(self, base_size: int) -> int:
        """
        获取响应式字号
        
        Args:
            base_size: 基础字号（针对lg断点设计）
            
        Returns:
            调整后的字号
        """
        size_map = {
            'xs': int(base_size * 0.85),
            'sm': int(base_size * 0.9),
            'md': int(base_size * 0.95),
            'lg': base_size,
            'xl': int(base_size * 1.05),
            'xxl': int(base_size * 1.1)
        }
        return self.get_responsive_value(size_map, base_size)
    
    def get_responsive_spacing(self, base_spacing: int) -> int:
        """
        获取响应式间距
        
        Args:
            base_spacing: 基础间距（针对lg断点设计）
            
        Returns:
            调整后的间距
        """
        spacing_map = {
            'xs': int(base_spacing * 0.75),
            'sm': int(base_spacing * 0.85),
            'md': int(base_spacing * 0.95),
            'lg': base_spacing,
            'xl': int(base_spacing * 1.05),
            'xxl': int(base_spacing * 1.15)
        }
        return self.get_responsive_value(spacing_map, base_spacing)
    
    def get_responsive_padding(self, base_padding: int) -> int:
        """获取响应式内边距"""
        return self.get_responsive_spacing(base_padding)
    
    # ==================== 持久化 ====================
    
    def _save_preferences(self):
        """保存用户偏好到数据库"""
        try:
            from models.database import DatabaseManager
            db = DatabaseManager()

            with db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value) 
                    VALUES ('animation_enabled', ?)
                ''', (str(self._animation_enabled),))
            
            from utils.logger import logger
            logger.debug("主题偏好已保存")
            
        except Exception as e:
            from utils.logger import logger
            logger.error(f"保存主题偏好失败: {e}")
    
    def _load_preferences(self):
        """从数据库加载用户偏好"""
        try:
            from models.database import DatabaseManager
            db = DatabaseManager()

            with db.get_cursor() as cursor:
                # 加载动画设置
                cursor.execute("SELECT value FROM settings WHERE key = 'animation_enabled'")
                result = cursor.fetchone()
                if result and result[0]:
                    self._animation_enabled = result[0].lower() == 'true'

            from utils.logger import logger
            logger.info(f"主题: {self._current_theme.value}, 动画: {'开启' if self._animation_enabled else '关闭'}")

        except Exception as e:
            from utils.logger import logger
            logger.warning(f"加载主题偏好失败，使用默认值: {e}")


# 全局实例
theme_manager = ThemeManager.instance()


def get_theme_manager() -> ThemeManager:
    """获取主题管理器全局实例"""
    return theme_manager
