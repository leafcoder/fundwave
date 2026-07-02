#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级UI主题配置
对标蚂蚁财富、天天基金、雪球等大厂应用的设计标准
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


class ProfessionalTheme:
    """专业金融应用UI主题"""

    # ==================== 配色方案 ====================

    # 主色调（蓝色系 - 专业、可信赖）
    PRIMARY_COLOR = "#1677FF"           # 主色调（按钮、链接）
    PRIMARY_LIGHT = "#4096FF"         # 浅主色（hover状态）
    PRIMARY_DARK = "#0958D9"          # 深主色（active状态）
    PRIMARY_BG = "#E8F3FF"            # 主色背景（标签、高亮）

    # 功能色彩（语义化）
    SUCCESS_COLOR = "#00B42A"        # 成功/盈利（绿色，柔和版）
    SUCCESS_LIGHT = "#F6FFED"        # 成功背景
    WARNING_COLOR = "#FF7D00"         # 警告（橙色）
    WARNING_LIGHT = "#FFF7E8"        # 警告背景
    ERROR_COLOR = "#F53F3F"          # 错误/亏损（红色，柔和版）
    ERROR_LIGHT = "#FFECE8"          # 错误背景
    INFO_COLOR = "#1677FF"           # 信息（蓝色）

    # 金融涨跌配色（中国惯例：红涨绿跌）
    RISE_COLOR = "#F53F3F"           # 涨 - 红色
    FALL_COLOR = "#00B42A"           # 跌 - 绿色
    FLAT_COLOR = "#86909C"           # 平 - 灰色
    RISE_LIGHT = "#FFF1F0"           # 涨背景
    FALL_LIGHT = "#F6FFED"           # 跌背景

    # 按钮交互态颜色
    SUCCESS_HOVER = "#00A870"
    SUCCESS_PRESSED = "#00996B"
    ERROR_HOVER = "#CB2630"
    ERROR_PRESSED = "#B91C1C"

    # 中性色彩（文本和边框）
    TEXT_PRIMARY = "#1D2129"         # 主文本（标题、重要数据）
    TEXT_SECONDARY = "#4E5969"       # 次要文本（说明、标签）
    TEXT_TERTIARY = "#86909C"       # 三级文本（占位符、辅助信息）
    TEXT_PLACEHOLDER = "#C9CDD4"      # 占位符文本

    BORDER_COLOR = "#E5E6EB"         # 边框颜色（浅灰）
    BORDER_LIGHT = "#F2F3F5"        # 浅边框（分割线）
    DIVIDER_COLOR = "#E5E6EB"       # 分割线颜色

    # 背景色
    BG_PRIMARY = "#FFFFFF"            # 主背景（白色）
    BG_SECONDARY = "#F7F8FA"         # 次背景（页面底色、卡片外区域）
    BG_TERTIARY = "#F2F3F5"         # 三级背景（禁用状态、表头）
    BG_HOVER = "#F7F8FA"             # hover背景

    # 阴影
    SHADOW_CARD = "0 2px 12px rgba(0, 0, 0, 0.06)"              # 卡片阴影
    SHADOW_FLOATING = "0 8px 24px rgba(0, 0, 0, 0.10)"        # 浮动层阴影
    SHADOW_BUTTON = "0 2px 8px rgba(22, 119, 255, 0.25)"       # 按钮阴影
    SHADOW_INPUT = "inset 0 1px 3px rgba(0, 0, 0, 0.06)"     # 输入框内阴影

    # ==================== 字体规范 ====================

    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', " \
        "'PingFang SC', 'Hiragino Sans GB', " \
        "'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif"

    FONT_FAMILY_MONO = "'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace"

    # 字号大小（单位：px）
    FONT_SIZE_H1 = 28                    # 一级标题（页面主标题）
    FONT_SIZE_H2 = 24                    # 二级标题（区块标题）
    FONT_SIZE_H3 = 20                    # 三级标题（子模块标题）
    FONT_SIZE_H4 = 18                    # 四级标题（卡片标题）
    FONT_SIZE_BODY = 15                  # 正文（内容描述）
    FONT_SIZE_SMALL = 13                # 小字（辅助信息）
    FONT_SIZE_CAPTION = 12              # 注释（图例、提示）

    # 字重
    FONT_WEIGHT_REGULAR = 400            # 常规
    FONT_WEIGHT_MEDIUM = 500             # 中等（标签）
    FONT_WEIGHT_SEMI_BOLD = 600          # 半粗体（小标题）
    FONT_WEIGHT_BOLD = 700               # 粗体（重要数据、标题）

    # 行高
    LINE_HEIGHT_TIGHT = 1.25             # 紧凑行高（标题）
    LINE_HEIGHT_NORMAL = 1.5             # 正常行高（正文）
    LINE_HEIGHT_LOOSE = 1.75            # 宽松行长（段落）

    # ==================== 间距规范（8px基准网格）====================

    SPACING_XS = 4                      # 极小间距
    SPACING_SM = 8                      # 小间距（元素内部）
    SPACING_MD = 16                     # 中等间距（组件间）
    SPACING_LG = 24                     # 大间距（区块间）
    SPACING_XL = 32                     # 特大间距（主要区块）
    SPACING_XXL = 48                    # 超大间距（页面边缘）

    # 圆角
    RADIUS_SMALL = 6                    # 小圆角（按钮、输入框）
    RADIUS_MEDIUM = 10                  # 中圆角（卡片、面板）
    RADIUS_LARGE = 16                   # 大圆角（对话框、弹窗）
    RADIUS_XLARGE = 20                  # 超大圆角（特殊容器）
    RADIUS_CIRCLE = 9999                # 圆形（头像、图标按钮）

    # ==================== 动画规范 ====================

    TRANSITION_FAST = "all 0.15s ease"    # 快速动画（hover反馈）
    TRANSITION_NORMAL = "all 0.25s ease"  # 正常动画（展开收起）
    TRANSITION_SLOW = "all 0.35s ease"    # 慢速动画（页面切换）
    TRANSITION_ELASTIC = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"  # 弹性动画（强调效果）

    # ==================== 组件样式模板 ====================

    @classmethod
    def get_card_container_style(cls) -> str:
        """获取卡片容器样式（白色背景+圆角，无边框）"""
        return f"""
            background: {cls.BG_PRIMARY};
            border: none;
            border-radius: {cls.RADIUS_LARGE}px;
        """

    @classmethod
    def get_card_style(cls, hoverable: bool = False) -> str:
        """获取卡片样式"""
        base_style = f"""
            background: {cls.BG_PRIMARY};
            border: none;
            border-radius: {cls.RADIUS_MEDIUM}px;
            padding: {cls.SPACING_LG}px;
        """

        if hoverable:
            base_style += f"""
                QWidget:hover {{
                    background: {cls.BG_HOVER};
                }}
            """

        return base_style

    @classmethod
    def get_button_style(cls, type_: str = "primary") -> str:
        """获取按钮样式"""
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
                    color: white;
                    border: none;
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{ background: {cls.SUCCESS_HOVER}; }}
                QPushButton:pressed {{ background: {cls.SUCCESS_PRESSED}; }}
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
                QPushButton:hover {{ background: {cls.ERROR_HOVER}; }}
                QPushButton:pressed {{ background: {cls.ERROR_PRESSED}; }}
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
                    background: {cls.BG_HOVER};
                }}
            """,

            "default": f"""
                QPushButton {{
                    background: {cls.BG_SECONDARY};
                    color: {cls.TEXT_PRIMARY};
                    border: 1px solid {cls.BORDER_COLOR};
                    border-radius: {cls.RADIUS_SMALL}px;
                    padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                }}
                QPushButton:hover {{
                    background: {cls.BG_HOVER};
                    border-color: {cls.PRIMARY_LIGHT};
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
        """获取输入框样式"""
        return f"""
            QLineEdit {{
                background: {cls.BG_PRIMARY};
                border: 1.5px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_SMALL}px;
                padding: {cls.SPACING_SM}px {cls.SPACING_MD}px;
                font-size: {cls.FONT_SIZE_BODY}px;
                color: {cls.TEXT_PRIMARY};
                selection-background-color: {cls.PRIMARY_BG};
            }}
            QLineEdit:focus {{
                border-color: {cls.PRIMARY_COLOR};
                border-width: 2px;
            }}
            QLineEdit:hover:!focus {{
                border-color: {cls.PRIMARY_LIGHT};
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
        """获取表格样式"""
        return f"""
            QTableWidget {{
                background: {cls.BG_PRIMARY};
                alternate-background-color: {cls.BG_SECONDARY};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: {cls.RADIUS_MEDIUM}px;
                gridline-color: {cls.BORDER_LIGHT};
                selection-background-color: {cls.PRIMARY_BG};
                selection-color: {cls.PRIMARY_DARK};
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
                color: {cls.PRIMARY_DARK};
            }}
        """

    @classmethod
    def get_groupbox_style(cls) -> str:
        """获取分组框样式"""
        return f"""
            QGroupBox {{
                background: {cls.BG_PRIMARY};
                border: 1px solid {cls.BORDER_LIGHT};
                border-radius: {cls.RADIUS_MEDIUM}px;
                margin-top: {cls.SPACING_MD}px;
                padding-top: {cls.SPACING_LG}px;
                font-weight: {cls.FONT_WEIGHT_SEMI_BOLD};
                font-size: {cls.FONT_SIZE_SMALL}px;
                color: {cls.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {cls.SPACING_MD}px;
                padding: 0 {cls.SPACING_SM}px;
                background: {cls.BG_PRIMARY};
                color: {cls.TEXT_PRIMARY};
            }}
        """

    @classmethod
    def get_scrollbar_style(cls) -> str:
        """获取滚动条样式"""
        return f"""
            QScrollBar:vertical {{
                background: {cls.BG_TERTIARY};
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.BORDER_COLOR};
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.TEXT_PLACEHOLDER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            QScrollBar:horizontal {{
                background: {cls.BG_TERTIARY};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {cls.BORDER_COLOR};
                border-radius: 4px;
                min-width: 40px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {cls.TEXT_PLACEHOLDER};
            }}
        """

    @classmethod
    def apply_to_widget(cls, widget):
        """将主题应用到指定控件"""
        widget.setStyleSheet(f"""
            * {{
                font-family: {cls.FONT_FAMILY};
                color: {cls.TEXT_PRIMARY};
            }}
            QWidget {{
                background: {cls.BG_SECONDARY};
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
        """)


# Matplotlib 图表主题配置
MPL_THEME_CONFIG = {
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FAFBFC',
    'axes.edgecolor': '#E5E6EB',
    'axes.labelcolor': '#4E5969',
    'axes.grid': True,
    'grid.color': '#F2F3F5',
    'grid.linestyle': '--',
    'grid.alpha': 0.8,
    'xtick.color': '#86909C',
    'ytick.color': '#86909C',
    'text.color': '#1D2129',
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
}
