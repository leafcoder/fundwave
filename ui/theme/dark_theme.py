#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
暗黑主题配置
提供专业的深色UI主题，对标大厂应用的暗黑模式
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


class DarkTheme:
    """专业级暗黑主题 - 对标VS Code、Figma、Notion等顶级应用"""

    # ==================== 配色方案 ====================

    # 主色调（蓝色系 - 暗色模式下更柔和）
    PRIMARY_COLOR = "#4A9EFF"           # 主色调（按钮、链接）
    PRIMARY_LIGHT = "#74B9FF"         # 浅主色（hover状态）
    PRIMARY_DARK = "#2D7DD2"          # 深主色（active状态）
    PRIMARY_BG = "#1E3A5F"            # 主色背景（标签、高亮）

    # 功能色彩（语义化 - 暗色优化）
    SUCCESS_COLOR = "#34D399"        # 成功/盈利（绿色，更明亮）
    SUCCESS_LIGHT = "#064E3B"        # 成功背景
    WARNING_COLOR = "#FBBF24"         # 警告（橙色）
    WARNING_LIGHT = "#78350F"        # 警告背景
    ERROR_COLOR = "#F87171"          # 错误/亏损（红色，柔和版）
    ERROR_LIGHT = "#7F1D1D"          # 错误背景
    INFO_COLOR = "#60A5FA"           # 信息（蓝色）

    # 中性色彩（文本和边框 - 高对比度）
    TEXT_PRIMARY = "#F1F5F9"         # 主文本（标题、重要数据）- 近白
    TEXT_SECONDARY = "#94A3B8"       # 次要文本（说明、标签）
    TEXT_TERTIARY = "#64748B"       # 三级文本（占位符、辅助信息）
    TEXT_PLACEHOLDER = "#475569"      # 占位符文本

    BORDER_COLOR = "#334155"         # 边框颜色（浅灰）
    BORDER_LIGHT = "#1E293B"        # 浅边框（分割线）
    DIVIDER_COLOR = "#334155"       # 分割线颜色

    # 背景色（深色系 - 层次分明）
    BG_PRIMARY = "#0F172A"            # 主背景（深蓝黑）
    BG_SECONDARY = "#1E293B"         # 次背景（卡片外区域）
    BG_TERTIARY = "#334155"         # 三级背景（禁用状态、表头）
    BG_HOVER = "#1E293B"             # hover背景

    # 阴影（暗色模式使用光晕效果）
    SHADOW_CARD = "0 4px 20px rgba(0, 0, 0, 0.4)"              # 卡片阴影
    SHADOW_FLOATING = "0 12px 40px rgba(0, 0, 0, 0.6)"        # 浮动层阴影
    SHADOW_BUTTON = "0 4px 16px rgba(74, 158, 255, 0.3)"       # 按钮阴影（发光效果）
    SHADOW_INPUT = "inset 0 2px 4px rgba(0, 0, 0, 0.3)"     # 输入框内阴影

    # 光晕效果（暗黑模式特色）
    GLOW_PRIMARY = "0 0 20px rgba(74, 158, 255, 0.3)"
    GLOW_SUCCESS = "0 0 20px rgba(52, 211, 153, 0.3)"
    GLOW_ERROR = "0 0 20px rgba(248, 113, 113, 0.3)"

    # ==================== 字体规范 ====================

    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', " \
        "'PingFang SC', 'Hiragino Sans GB', " \
        "'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif"

    FONT_FAMILY_MONO = "'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace"

    FONT_SIZE_H1 = 28
    FONT_SIZE_H2 = 24
    FONT_SIZE_H3 = 20
    FONT_SIZE_H4 = 18
    FONT_SIZE_BODY = 15
    FONT_SIZE_SMALL = 13
    FONT_SIZE_CAPTION = 12

    FONT_WEIGHT_REGULAR = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMI_BOLD = 600
    FONT_WEIGHT_BOLD = 700

    LINE_HEIGHT_TIGHT = 1.25
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_LOOSE = 1.75

    # ==================== 间距规范 ====================

    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32
    SPACING_XXL = 48

    RADIUS_SMALL = 6
    RADIUS_MEDIUM = 10
    RADIUS_LARGE = 16
    RADIUS_XLARGE = 20
    RADIUS_CIRCLE = 9999

    # ==================== 动画规范 ====================

    TRANSITION_FAST = "all 0.15s ease"
    TRANSITION_NORMAL = "all 0.25s ease"
    TRANSITION_SLOW = "all 0.35s ease"
    TRANSITION_ELASTIC = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"

    # ==================== 组件样式模板 ====================

    @classmethod
    def get_card_style(cls, hoverable: bool = False) -> str:
        """获取卡片样式"""
        base_style = f"""
            background: {cls.BG_SECONDARY};
            border: 1px solid {cls.BORDER_COLOR};
            border-radius: {cls.RADIUS_MEDIUM}px;
            padding: {cls.SPACING_LG}px;
        """

        if hoverable:
            base_style += f"""
                QWidget:hover {{
                    border-color: {cls.PRIMARY_LIGHT};
                }}
            """

        return base_style

    @classmethod
    def get_button_style(cls, type_: str = "primary") -> str:
        """获取按钮样式 - 暗黑模式带发光效果"""
        styles = {
            "primary": f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {cls.PRIMARY_COLOR}, stop:1 {cls.PRIMARY_LIGHT});
                    color: white;
                    border: none;
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-size: {cls.FONT_SIZE_BODY}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {cls.PRIMARY_DARK}, stop:1 {cls.PRIMARY_COLOR});
                }}
                QPushButton:pressed {{
                    background: {cls.PRIMARY_DARK};
                }}
                QPushButton:disabled {{
                    background: {cls.BG_TERTIARY};
                    color: {cls.TEXT_PLACEHOLDER};
                }}
            """,

            "success": f"""
                QPushButton {{
                    background: {cls.SUCCESS_COLOR};
                    color: {cls.BG_PRIMARY};
                    border: none;
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{
                    background: #10B981;
                }}
                QPushButton:pressed {{ background: #059669; }}
            """,

            "danger": f"""
                QPushButton {{
                    background: {cls.ERROR_COLOR};
                    color: white;
                    border: none;
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{
                    background: #EF4444;
                }}
                QPushButton:pressed {{ background: #DC2626; }}
            """,

            "ghost": f"""
                QPushButton {{
                    background: transparent;
                    color: {cls.PRIMARY_COLOR};
                    border: 1px solid {cls.PRIMARY_COLOR};
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{
                    background: {cls.PRIMARY_BG};
                    border-color: {cls.PRIMARY_LIGHT};
                }}
                QPushButton:pressed {{
                    background: {cls.BG_TERTIARY};
                }}
            """,

            "default": f"""
                QPushButton {{
                    background: {cls.BG_TERTIARY};
                    color: {cls.TEXT_PRIMARY};
                    border: 1px solid {cls.BORDER_COLOR};
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{
                    background: {cls.BG_HOVER};
                    border-color: {cls.PRIMARY_COLOR};
                    color: {cls.PRIMARY_COLOR};
                }}
                QPushButton:pressed {{
                    background: {cls.BG_TERTIARY};
                }}
            """
        }

        return styles.get(type_, styles["default"])

    @classmethod
    def get_input_style(cls) -> str:
        """获取输入框样式 - 暗黑模式"""
        return f"""
            QLineEdit {{
                background: {cls.BG_PRIMARY};
                border: 1.5px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_SMALL}px;
                padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                font-size: {cls.FONT_SIZE_BODY}px;
                color: {cls.TEXT_PRIMARY};
                selection-background-color: {cls.PRIMARY_BG};
                selection-color: {cls.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {cls.PRIMARY_COLOR};
                border-width: 2px;
            }}
            QLineEdit:hover:!focus {{
                border-color: {cls.TEXT_TERTIARY};
            }}
            QLineEdit:disabled {{
                background: {cls.BG_TERTIARY};
                color: {cls.TEXT_PLACEHOLDER};
            }}
            QLineEdit::placeholder {{
                color: {cls.TEXT_PLACEHOLDER};
            }}
        """

    @classmethod
    def get_table_style(cls) -> str:
        """获取表格样式 - 暗黑模式"""
        return f"""
            QTableWidget {{
                background: {cls.BG_PRIMARY};
                alternate-background-color: {cls.BG_SECONDARY};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_MEDIUM}px;
                gridline-color: {cls.BORDER_LIGHT};
                selection-background-color: {cls.PRIMARY_BG};
                selection-color: {cls.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                border-bottom: 1px solid {cls.BORDER_LIGHT};
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {cls.BG_SECONDARY}, stop:1 {cls.BORDER_LIGHT});
                color: {cls.TEXT_SECONDARY};
                padding: {cls.SPACING_MD}px;
                border: none;
                border-right: 1px solid {cls.BORDER_LIGHT};
                border-bottom: 2px solid {cls.BORDER_COLOR};
                font-weight: {cls.FONT_WEIGHT_SEMI_BOLD};
                font-size: {cls.FONT_SIZE_SMALL}px;
            }}
            QTableWidget::item:selected {{
                background: {cls.PRIMARY_BG};
                color: {cls.PRIMARY_LIGHT};
            }}
        """

    @classmethod
    def get_groupbox_style(cls) -> str:
        """获取分组框样式 - 暗黑模式"""
        return f"""
            QGroupBox {{
                background: {cls.BG_SECONDARY};
                border: 2px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_LARGE}px;
                margin-top: {cls.SPACING_LG}px;
                padding-top: {cls.SPACING_XL + 4}px;
                font-weight: {cls.FONT_WEIGHT_SEMI_BOLD};
                font-size: {cls.FONT_SIZE_H4}px;
                color: {cls.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {cls.SPACING_LG}px;
                padding: 0 {cls.SPACING_SM}px;
                background: {cls.BG_SECONDARY};
                color: {cls.TEXT_PRIMARY};
            }}
        """

    @classmethod
    def get_scrollbar_style(cls) -> str:
        """获取滚动条样式 - 暗黑模式"""
        return f"""
            QScrollBar:vertical {{
                background: {cls.BG_PRIMARY};
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.BORDER_COLOR};
                border-radius: 5px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.TEXT_TERTIARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            QScrollBar:horizontal {{
                background: {cls.BG_PRIMARY};
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: {cls.BORDER_COLOR};
                border-radius: 5px;
                min-width: 40px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {cls.TEXT_TERTIARY};
            }}
        """

    @classmethod
    def apply_to_widget(cls, widget):
        """将暗黑主题应用到指定控件"""
        widget.setStyleSheet(f"""
            * {{
                font-family: {cls.FONT_FAMILY};
                color: {cls.TEXT_PRIMARY};
            }}
            QWidget {{
                background: {cls.BG_PRIMARY};
            }}

            /* 全局滚动条 */
            {cls.get_scrollbar_style()}

            /* 分组框 */
            {cls.get_groupbox_style()}

            /* 表格 */
            {cls.get_table_style()}

            /* 按钮 */
            {cls.get_button_style('primary')}
            {cls.get_button_style('success')}
            {cls.get_button_style('danger')}
            {cls.get_button_style('ghost')}

            /* 输入框 */
            {cls.get_input_style()}

            /* 工具提示 */
            QToolTip {{
                background: {cls.BG_TERTIARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_COLOR};
                padding: 6px 12px;
                border-radius: {cls.RADIUS_SMALL}px;
                font-size: {cls.FONT_SIZE_SMALL}px;
            }}

            /* 菜单 */
            QMenu {{
                background: {cls.BG_SECONDARY};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_SMALL}px;
                padding: {cls.SPACING_XS}px;
            }}
            QMenu::item:selected {{
                background: {cls.PRIMARY_BG};
                border-radius: {cls.RADIUS_SMALL}px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {cls.BORDER_COLOR};
                margin: {cls.SPACING_XS}px {cls.SPACING_SM}px;
            }}

            /* 下拉框 */
            QComboBox {{
                background: {cls.BG_PRIMARY};
                color: {cls.TEXT_PRIMARY};
                border: 1.5px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_SMALL}px;
                padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
            }}
            QComboBox:focus {{
                border-color: {cls.PRIMARY_COLOR};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                background: {cls.BG_SECONDARY};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_SMALL}px;
                selection-background-color: {cls.PRIMARY_BG};
                selection-color: {cls.TEXT_PRIMARY};
            }}

            /* 复选框和单选框 */
            QCheckBox, QRadioButton {{
                color: {cls.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {cls.BORDER_COLOR};
                background: {cls.BG_PRIMARY};
            }}
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                background: {cls.PRIMARY_COLOR};
                border-color: {cls.PRIMARY_COLOR};
            }}

            /* 进度条 */
            QProgressBar {{
                background: {cls.BG_TERTIARY};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: {cls.TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {cls.PRIMARY_COLOR}, stop:1 {cls.PRIMARY_LIGHT});
                border-radius: 4px;
            }}

            /* 滑块 */
            QSlider::groove:horizontal {{
                background: {cls.BG_TERTIARY};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {cls.PRIMARY_COLOR};
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {cls.PRIMARY_LIGHT};
            }}
        """)

        # 设置调色板（用于系统原生控件）
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(cls.BG_PRIMARY))
        palette.setColor(QPalette.WindowText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(cls.BG_SECONDARY))
        palette.setColor(QPalette.AlternateBase, QColor(cls.BG_TERTIARY))
        palette.setColor(QPalette.ToolTipBase, QColor(cls.BG_TERTIARY))
        palette.setColor(QPalette.ToolTipText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.Text, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.Button, QColor(cls.BG_TERTIARY))
        palette.setColor(QPalette.ButtonText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.BrightText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.Highlight, QColor(cls.PRIMARY_COLOR))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        widget.setPalette(palette)


# Matplotlib 图表暗黑主题配置
MPL_DARK_THEME_CONFIG = {
    'figure.facecolor': '#0F172A',
    'axes.facecolor': '#1E293B',
    'axes.edgecolor': '#334155',
    'axes.labelcolor': '#94A3B8',
    'axes.grid': True,
    'grid.color': '#334155',
    'grid.linestyle': '--',
    'grid.alpha': 0.6,
    'xtick.color': '#64748B',
    'ytick.color': '#64748B',
    'text.color': '#F1F5F9',
    'font.family': ['sans-serif'],
    'font.sans-serif': [
        'WenQuanYi Micro Hei',
        'PingFang SC',
        'Microsoft YaHei',
        'SimHei',
        'DejaVu Sans'
    ],
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.labelsize': 13,
    'legend.fontsize': 11,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'lines.linewidth': 2,
    'lines.solid_capstyle': 'round',
    'figure.dpi': 120,
    'savefig.facecolor': '#0F172A',
    'savefig.edgecolor': '#334155'
}
