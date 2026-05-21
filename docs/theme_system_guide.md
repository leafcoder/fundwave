# 主题系统、动画与响应式适配 - 使用指南

## 📋 功能概述

本次升级为基金监控系统添加了三大核心功能：

1. **🌗 暗黑模式** - 专业级亮色/暗黑主题切换
2. **✨ 动效增强** - 流畅的过渡动画和数据更新效果
3. **📱 响应式适配** - 自动适应不同屏幕尺寸

---

## 🎨 一、暗黑模式

### 1.1 特性亮点

- ✅ **专业配色方案**：对标VS Code、Figma、Notion等顶级应用
- ✅ **高对比度设计**：确保暗色环境下可读性
- ✅ **光晕效果**：按钮和交互元素带发光效果
- ✅ **一键切换**：头部区域月亮/太阳图标按钮
- ✅ **偏好持久化**：自动保存用户选择到数据库
- ✅ **全局应用**：所有对话框、表格、组件统一切换

### 1.2 配色规范

#### 暗黑主题色彩系统
```python
# 主色调（更柔和的蓝色）
PRIMARY_COLOR = "#4A9EFF"      # 主色
PRIMARY_LIGHT = "#74B9FF"    # 浅主色
PRIMARY_DARK = "#2D7DD2"     # 深主色

# 背景色（深蓝黑色系）
BG_PRIMARY = "#0F172A"        # 主背景（最深）
BG_SECONDARY = "#1E293B"     # 次背景（卡片）
BG_TERTIARY = "#334155"     # 三级背景（输入框）

# 文本色（高对比度）
TEXT_PRIMARY = "#F1F5F9"    # 主文本（近白）
TEXT_SECONDARY = "#94A3B8"  # 次要文本（灰色）

# 光晕效果（暗黑模式特色）
GLOW_PRIMARY = "0 0 20px rgba(74, 158, 255, 0.3)"
GLOW_SUCCESS = "0 0 20px rgba(52, 211, 153, 0.3)"
GLOW_ERROR = "0 0 20px rgba(248, 113, 113, 0.3)"
```

### 1.3 使用方法

#### 方法一：点击界面按钮
1. 启动应用后，在**头部右侧**找到主题切换按钮（🌙/☀️）
2. 点击即可切换亮色/暗黑模式
3. 所有界面会立即响应变化

#### 方法二：代码调用
```python
from ui.theme.theme_manager import get_theme_manager, ThemeType

# 获取主题管理器实例
manager = get_theme_manager()

# 切换到暗黑模式
manager.set_theme(ThemeType.DARK)

# 切换回亮色模式
manager.set_theme(ThemeType.LIGHT)

# 切换主题（toggle）
manager.toggle_theme()

# 跟随系统
manager.set_theme(ThemeType.AUTO)
```

#### 方法三：监听主题变更
```python
def on_theme_changed(old_theme, new_theme):
    print(f"主题从 {old_theme.value} 变更为 {new_theme.value}")
    # 执行自定义逻辑...

manager.on_theme_changed(on_theme_changed)
```

### 1.4 自定义组件支持暗黑模式

```python
from ui.theme.theme_manager import get_theme_manager
from ui.theme.dark_theme import DarkTheme
from ui.theme.professional_theme import ProfessionalTheme

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 应用当前主题
        manager = get_theme_manager()
        theme_class = DarkTheme if manager.is_dark_mode else ProfessionalTheme
        theme_class.apply_to_widget(self)
        
        self.setup_ui()
```

---

## ✨ 二、动效增强

### 2.1 支持的动画类型

| 动画类型 | 说明 | 适用场景 |
|---------|------|---------|
| `FADE_IN` | 淡入效果 | 对话框显示、页面加载 |
| `FADE_OUT` | 淡出效果 | 对话框关闭 |
| `SLIDE_LEFT` | 从左滑入 | 侧边栏展开 |
| `SLIDE_RIGHT` | 从右滑入 | 面板显示 |
| `SLIDE_UP` | 从上滑入 | 下拉菜单 |
| `SLIDE_DOWN` | 从下滑入 | 提示信息 |
| `SCALE_UP` | 从小放大 | 弹窗出现 |
| `SCALE_DOWN` | 从大缩小 | 元素消失 |
| `BOOUNCE` | 弹跳效果 | 强调提示 |

### 2.2 使用示例

#### 控件显示动画
```python
from ui.theme.theme_manager import get_theme_manager, AnimationType

manager = get_theme_manager()

# 显示对话框时播放淡入动画
dialog = MyDialog()
manager.animate_widget_show(
    dialog,
    animation_type=AnimationType.FADE_IN,
    duration=300
)

# 显示控件时播放滑动动画
panel = QPanel()
manager.animate_widget_show(
    panel,
    animation_type=AnimationType.SLIDE_RIGHT,
    distance=100,
    duration=400
)

# 显示控件时播放缩放动画
widget = QWidget()
manager.animate_widget_show(
    widget,
    animation_type=AnimationType.BOUNCE,
    duration=500
)
```

#### 控件隐藏动画
```python
# 隐藏时淡出
manager.animate_widget_hide(
    widget,
    animation_type=AnimationType.FADE_OUT,
    duration=250,
    on_finished=lambda: widget.deleteLater()
)
```

#### 数值滚动动画
```python
# 数值从0变化到12345.67，带滚动效果
label = QLabel("¥0.00")
manager.animate_value_change(
    label_widget=label,
    start_value=0.0,
    end_value=12345.67,
    duration=800,  # 动画时长800ms
    formatter=lambda x: f"¥{x:,.2f}",  # 格式化函数
    steps=60  # 动画帧数
)
```

### 2.3 全局动画开关

```python
# 关闭所有动画（提升性能）
manager.animation_enabled = False

# 开启动画
manager.animation_enabled = True

# 查询状态
if manager.animation_enabled:
    print("动画已启用")
```

### 2.4 自定义缓动曲线

内置多种缓动曲线：
- `OutCubic` - 缓出三次方（默认，最自然）
- `InOutCubic` - 缓入缓出三次方
- `OutBack` - 回弹效果
- `OutElastic` - 弹性效果
- `Linear` - 线性匀速

```python
from PySide6.QtCore import QEasingCurve

anim = manager.create_fade_animation(
    widget,
    easing_curve=QEasingCurve.Type.OutBack  # 回弹效果
)
```

---

## 📱 三、响应式适配

### 3.1 断点系统

基于屏幕宽度的响应式断点：

| 断点名称 | 宽度范围 | 设备类型 |
|---------|---------|---------|
| `xs` | < 768px | 手机竖屏 |
| `sm` | 768px - 1023px | 平板竖屏/手机横屏 |
| `md` | 1024px - 1279px | 平板横屏/小笔记本 |
| `lg` | 1280px - 1535px | 桌面显示器（标准） |
| `xl` | 1536px - 1919px | 大屏显示器 |
| `xxl` | ≥ 1920px | 超大屏/4K显示器 |

### 3.2 使用方法

#### 获取当前断点
```python
manager = get_theme_manager()
breakpoint = manager.get_breakpoint()  # 返回 'lg', 'xl' 等

if manager.is_mobile():
    print("移动设备")
elif manager.is_tablet():
    print("平板设备")
elif manager.is_desktop():
    print("桌面设备")
```

#### 响应式数值
```python
# 根据屏幕尺寸获取不同的值
font_size = manager.get_responsive_value({
    'xs': 12,
    'sm': 13,
    'md': 14,
    'lg': 15,   # 基准值
    'xl': 16,
    'xxl': 17
}, default=15)

# 快捷方法：响应式字号（基于基准值自动计算）
responsive_font = manager.get_responsive_font_size(base_size=16)
# 在xs屏幕返回13.6，xxl返回17.6

# 快捷方法：响应式间距
spacing = manager.get_responsive_spacing(base_size=24)
padding = manager.get_responsive_padding(base_size=32)
```

#### 屏幕信息查询
```python
# 更新屏幕信息（窗口大小改变时调用）
manager.update_screen_info()

# 获取屏幕尺寸
width = manager.screen_width   # 1920
height = manager.screen_height # 1080
```

### 3.3 实战案例：自适应布局

```python
class ResponsiveWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = get_theme_manager()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 响应式间距
        spacing = self.manager.get_responsive_spacing(16)
        layout.setSpacing(spacing)
        
        padding = self.manager.get_responsive_padding(24)
        layout.setContentsMargins(padding, padding, padding, padding)
        
        # 响应式字号
        title_font_size = self.manager.get_responsive_font_size(24)
        title = QLabel("标题")
        title.setStyleSheet(f"font-size: {title_font_size}px;")
        layout.addWidget(title)
        
        # 根据断点显示不同内容
        breakpoint = self.manager.get_breakpoint()
        if breakpoint in ['xs', 'sm']:
            # 移动端：单列布局
            self._setup_mobile_layout(layout)
        else:
            # 桌面端：多列布局
            self._setup_desktop_layout(layout)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新布局"""
        super().resizeEvent(event)
        self.manager.update_screen_info()
        # 可选：动态调整布局
```

---

## 🔧 四、高级配置

### 4.1 数据库存储

主题偏好保存在 `settings` 表中：

```sql
-- 查看当前主题设置
SELECT * FROM settings WHERE key IN ('theme', 'animation_enabled');

-- 手动修改（需重启应用）
UPDATE settings SET value = 'dark' WHERE key = 'theme';
UPDATE settings SET value = 'true' WHERE key = 'animation_enabled';
```

### 4.2 Matplotlib 图表适配

暗黑模式下图表自动使用深色配置：

```python
import matplotlib.pyplot as plt
from ui.theme.dark_theme import MPL_DARK_THEME_CONFIG
from ui.theme.professional_theme import MPL_THEME_CONFIG

# 根据主题切换图表样式
if is_dark_mode:
    plt.rcParams.update(MPL_DARK_THEME_CONFIG)  # 深色背景、浅色文字
else:
    plt.rcParams.update(MPL_THEME_CONFIG)  # 白色背景、深色文字
```

### 4.3 性能优化建议

1. **低端设备关闭动画**
```python
import sys
if sys.platform.startswith('win') or sys.platform == 'linux':
    # 检测硬件能力
    manager.animation_enabled = True
else:
    manager.animation_enabled = False
```

2. **减少重绘次数**
```python
# 批量更新UI时临时禁用动画
manager.animation_enabled = False
try:
    # 大量UI更新操作...
finally:
    manager.animation_enabled = True
```

3. **延迟加载动画资源**
```python
# 仅在需要时导入动画模块
def show_with_animation(widget):
    if manager.animation_enabled:
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect(widget)
        # ... 动画代码
    else:
        widget.show()
```

---

## 🎯 五、最佳实践

### 5.1 设计原则

1. **一致性**：所有组件遵循同一套主题规范
2. **可访问性**：暗黑模式确保4.5:1以上的对比度
3. **性能优先**：动画时长控制在200-500ms
4. **用户尊重**：记住用户的主题偏好

### 5.2 调试技巧

```python
# 查看当前主题信息
print(f"当前主题: {manager.current_theme.value}")
print(f"是否暗黑: {manager.is_dark_mode}")
print(f"动画开关: {manager.animation_enabled}")
print(f"屏幕断点: {manager.get_breakpoint()}")
print(f"屏幕尺寸: {manager.screen_width}x{manager.screen_height}")

# 强制刷新主题
manager._apply_current_theme()

# 重置为默认设置
manager.set_theme(ThemeType.LIGHT)
manager.animation_enabled = True
```

### 5.3 常见问题

**Q1: 主题切换后部分组件颜色不对？**
```python
# 确保使用主题管理器的apply_to_widget方法
# 而不是硬编码颜色值
theme_class.apply_to_widget(my_widget)
```

**Q2: 动画导致卡顿？**
```python
# 降低动画帧数或完全关闭
manager.animation_enabled = False
```

**Q3: 移动端布局错乱？**
```python
# 使用响应式API获取合适的尺寸
size = manager.get_responsive_value({'sm': 100, 'lg': 200})
```

---

## 📚 六、相关文件索引

| 文件路径 | 说明 |
|---------|------|
| [ui/theme/dark_theme.py](file:///home/zhanglei3/Desktop/dev/fundwave/ui/theme/dark_theme.py) | 暗黑主题配置 |
| [ui/theme/professional_theme.py](file:///home/zhanglei3/Desktop/dev/fundwave/ui/theme/professional_theme.py) | 亮色主题配置 |
| [ui/theme/theme_manager.py](file:///home/zhanglei3/Desktop/dev/fundwave/ui/theme/theme_manager.py) | 主题管理器核心 |
| [ui/main_window.py](file:///home/zhanglei3/Desktop/dev/fundwave/ui/main_window.py) | 主窗口集成示例 |
| [ui/widgets/investment_calculator_dialog.py](file:///home/zhanglei3/Desktop/dev/fundwave/ui/widgets/investment_calculator_dialog.py) | 定投计算器（已适配） |
| [ui/widgets/portfolio_dashboard.py](file:///home/zhanglei3/Desktop/dev/fundwave/ui/widgets/portfolio_dashboard.py) | 投资组合仪表盘（已适配） |

---

## 🚀 七、快速开始

立即体验新功能：

```bash
# 1. 启动应用
./start.sh

# 2. 点击头部右侧的 🌙 按钮切换暗黑模式

# 3. 观察所有界面的变化：
#    - 主窗口背景变深
#    - 文字变为浅色
#    - 按钮带有发光效果
#    - 图表自动适配深色

# 4. 再次点击 ☀️ 按钮切回亮色模式

# 5. 打开「定投计算器」或「投资组合分析」查看对话框的主题适配
```

---

**版本**: v2.0  
**更新日期**: 2026-05-21  
**兼容性**: Python 3.8+, PySide6 6.x+
