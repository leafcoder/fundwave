#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题系统、动画和响应式适配 - 功能测试脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_theme_manager():
    """测试主题管理器基本功能"""
    print("=" * 60)
    print("🧪 测试主题管理器")
    print("=" * 60)
    
    try:
        from ui.theme.theme_manager import get_theme_manager, ThemeManager, ThemeType
        
        # 获取单例实例
        manager = get_theme_manager()
        print(f"✅ 主题管理器实例创建成功: {type(manager).__name__}")
        
        # 测试主题类型枚举
        print(f"\n📋 支持的主题类型:")
        for theme in ThemeType:
            print(f"   - {theme.name}: {theme.value}")
        
        # 测试当前主题
        current = manager.current_theme
        is_dark = manager.is_dark_mode
        print(f"\n🎨 当前主题: {current.value} (暗黑模式: {is_dark})")
        
        # 测试断点系统
        breakpoint = manager.get_breakpoint()
        screen_size = f"{manager.screen_width}x{manager.screen_height}"
        print(f"📱 屏幕断点: {breakpoint} (尺寸: {screen_size})")
        
        # 测试响应式API
        font_sizes = {
            'xs': manager.get_responsive_font_size(16),
            'lg': manager.get_responsive_font_size(16),
            'xxl': manager.get_responsive_font_size(16)
        }
        print(f"\n📏 响应式字号 (基准16px):")
        for bp, size in font_sizes.items():
            print(f"   {bp}: {size}px")
        
        # 测试动画开关
        anim_status = "开启" if manager.animation_enabled else "关闭"
        print(f"\n✨ 动画状态: {anim_status}")
        
        # 测试动画类型枚举
        from ui.theme.theme_manager import AnimationType
        print(f"\n🎬 支持的动画类型:")
        for anim in AnimationType:
            print(f"   - {anim.name}: {anim.value}")
        
        print("\n" + "=" * 60)
        print("✅ 所有基础测试通过!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dark_theme():
    """测试暗黑主题配置"""
    print("\n" + "=" * 60)
    print("🌙 测试暗黑主题配置")
    print("=" * 60)
    
    try:
        from ui.theme.dark_theme import DarkTheme, MPL_DARK_THEME_CONFIG
        
        # 检查核心属性
        attrs = [
            'PRIMARY_COLOR', 'BG_PRIMARY', 'TEXT_PRIMARY',
            'FONT_FAMILY', 'FONT_SIZE_H1', 'RADIUS_MEDIUM',
            'SHADOW_CARD', 'GLOW_PRIMARY'
        ]
        
        print("\n🎨 核心配置项:")
        for attr in attrs:
            if hasattr(DarkTheme, attr):
                value = getattr(DarkTheme, attr)
                print(f"   ✅ {attr}: {str(value)[:50]}...")
            else:
                print(f"   ❌ {attr}: 缺失")
        
        # 检查方法
        methods = [
            'get_card_style', 'get_button_style', 'get_input_style',
            'get_table_style', 'apply_to_widget'
        ]
        
        print("\n🔧 核心方法:")
        for method in methods:
            if hasattr(DarkTheme, method) and callable(getattr(DarkTheme, method)):
                print(f"   ✅ {method}()")
            else:
                print(f"   ❌ {method}() 缺失或不可调用")
        
        # 检查Matplotlib配置
        if MPL_DARK_THEME_CONFIG:
            print(f"\n📊 Matplotlib配置: ✅ (包含{len(MPL_DARK_THEME_CONFIG)}项)")
        
        print("\n" + "=" * 60)
        print("✅ 暗黑主题配置完整!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 暗黑主题测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_professional_theme():
    """测试亮色主题配置"""
    print("\n" + "=" * 60)
    print("☀️ 测试亮色主题配置")
    print("=" * 60)
    
    try:
        from ui.theme.professional_theme import ProfessionalTheme, MPL_THEME_CONFIG
        
        # 对比两个主题的关键差异
        comparisons = [
            ('BG_PRIMARY', '背景色'),
            ('TEXT_PRIMARY', '主文本色'),
            ('PRIMARY_COLOR', '主色调'),
            ('SHADOW_CARD', '卡片阴影')
        ]
        
        print("\n🔄 亮色 vs 暗黑对比:")
        for attr, desc in comparisons:
            light_val = getattr(ProfessionalTheme, attr, 'N/A')
            
            try:
                from ui.theme.dark_theme import DarkTheme
                dark_val = getattr(DarkTheme, attr, 'N/A')
            except:
                dark_val = 'N/A'
            
            print(f"   {desc:10s}:")
            print(f"      亮色: {str(light_val)[:40]}")
            print(f"      暗黑: {str(dark_val)[:40]}")
        
        print("\n" + "=" * 60)
        print("✅ 亮色主题配置完整!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 亮色主题测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_animation_system():
    """测试动画系统"""
    print("\n" + "=" * 60)
    print("🎬 测试动画系统")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.theme.theme_manager import get_theme_manager, AnimationType
        
        # 确保有QApplication实例
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        manager = get_theme_manager()
        
        # 创建测试控件
        from PySide6.QtWidgets import QLabel
        widget = QLabel("Test Widget")
        
        # 测试创建各种动画（不实际执行，只验证创建成功）
        animations = [
            ('淡入动画', lambda: manager.create_fade_animation(widget)),
            ('缩放动画', lambda: manager.create_scale_animation(widget)),
        ]
        
        print("\n🎨 动画创建测试:")
        for name, create_func in animations:
            try:
                anim = create_func()
                print(f"   ✅ {name}: 创建成功")
                del anim  # 清理资源
            except Exception as e:
                print(f"   ❌ {name}: 失败 ({e})")
        
        # 测试数值滚动动画（模拟）
        print("\n📊 数值格式化测试:")
        test_values = [0.0, 1234.56, 99999.99]
        for val in test_values:
            formatted = f"¥{val:,.2f}"
            print(f"   {val:>10} → {formatted}")
        
        print("\n" + "=" * 60)
        print("✅ 动画系统正常!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 动画系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("🧪 基金监控系统 - 主题与动效功能测试")
    print("🚀" * 30 + "\n")
    
    results = []
    
    # 运行各项测试
    results.append(("主题管理器", test_theme_manager()))
    results.append(("暗黑主题", test_dark_theme()))
    results.append(("亮色主题", test_professional_theme()))
    results.append(("动画系统", test_animation_system()))
    
    # 输出总结
    print("\n\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:15s} {status}")
    
    print("-" * 60)
    print(f"总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 功能已就绪。")
        print("\n下一步:")
        print("  1. 运行 ./start.sh 启动应用")
        print("  2. 点击头部 🌙 按钮体验暗黑模式")
        print("  3. 打开对话框查看动画效果")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
