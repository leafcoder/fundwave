#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 notification.py 修复后的钉钉通知功能
模拟程序运行时的真实调用流程
"""

import sqlite3
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_notification_settings():
    """测试 get_notification_settings() 是否正确读取密钥"""
    print("\n" + "="*80)
    print("🔍 验证 notification.py 的密钥读取逻辑")
    print("="*80)

    db_path = 'fund_monitor.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 使用修复后的SQL查询（与notification.py一致）
        print("\n📌 [步骤1] 执行修复后的SQL查询")
        cursor.execute('''
            SELECT id, popup_enabled, dingtalk_enabled, dingtalk_webhook,
                   email_enabled, email_smtp_server, email_sender,
                   email_password, email_receiver, rise_threshold,
                   fall_threshold, profit_threshold, loss_threshold,
                   dingtalk_secret
            FROM notification_settings LIMIT 1
        ''')

        result = cursor.fetchone()
        if not result:
            print("❌ 数据库中无记录")
            return False

        # 2. 验证字段映射
        print(f"\n📌 [步骤2] 验证字段索引映射")

        field_mapping = {
            0: ('id', result[0]),
            1: ('popup_enabled', result[1]),
            2: ('dingtalk_enabled', result[2]),
            3: ('dingtalk_webhook', result[3]),
            4: ('email_enabled', result[4]),
            5: ('email_smtp_server', result[5]),
            6: ('email_sender', result[6]),
            7: ('email_password', result[7]),
            8: ('email_receiver', result[8]),
            9: ('rise_threshold', result[9]),
            10: ('fall_threshold', result[10]),
            11: ('profit_threshold', result[11]),
            12: ('loss_threshold', result[12]),
            13: ('dingtalk_secret', result[13]),  # ← 关键！
        }

        for idx, (field_name, value) in field_mapping.items():
            display_value = str(value)
            if field_name in ['dingtalk_webhook', 'dingtalk_secret']:
                display_value = f"{value[:20]}..." if value else "(空)"
                marker = " ✅" if idx == 13 and value and value.startswith('SEC') else ""
            elif field_name == 'dingtalk_webhook':
                marker = " ✅" if value and 'access_token' in value else ""
            else:
                marker = ""

            print(f"   [{idx:2d}] {field_name:20s} = {display_value:<25}{marker}")

        # 3. 构建设置字典（与notification.py一致）
        print(f"\n📌 [步骤3] 构建设置字典")

        settings = {
            'popup_enabled': bool(result[1]),
            'dingtalk_enabled': bool(result[2]),
            'dingtalk_webhook': result[3] or '',
            'dingtalk_secret': result[13] or '',  # ← 修复后使用正确的索引
            'email_enabled': bool(result[4]),
            'rise_threshold': result[9],
            'fall_threshold': result[10],
        }

        webhook = settings['dingtalk_webhook']
        secret = settings['dingtalk_secret']

        print(f"\n   🔑 Webhook URL: {webhook[:50]}...")
        print(f"   🔐 Secret Key: {secret[:15]}..." if secret else "   🔐 Secret Key: (未配置!) ❌")
        print(f"   📧 钉钉启用: {'是' if settings['dingtalk_enabled'] else '否'}")

        # 4. 验证密钥有效性
        print(f"\n📌 [步骤4] 验证密钥有效性")

        if not secret:
            print("   ❌ 错误：密钥为空！")
            print("   → 请在程序中打开【通知设置】，粘贴加签密钥并保存")
            return False

        if not secret.startswith('SEC'):
            print(f"   ⚠️ 警告：密钥格式异常（应以SEC开头）")
            print(f"   → 当前值前缀: {secret[:10]}")
            return False

        if len(secret) != 67:  # SEC + 64位hex (但实际可能不同长度)
            print(f"   ℹ️ 信息：密钥长度为 {len(secret)} 字符")

        print(f"   ✅ 密钥格式正确：{secret[:10]}... (长度:{len(secret)})")

        # 5. 测试实际发送（使用修复后的逻辑）
        print(f"\n📌 [步骤5] 模拟程序中的 send_dingtalk_notification() 调用")

        if not settings['dingtalk_enabled']:
            print("   ⚠️ 钉钉通知未启用，跳过发送测试")
            print("   → 请在【通知设置】中勾选'启用钉钉通知'")
            return True

        if not webhook:
            print("   ❌ Webhook为空，无法发送")
            return False

        # 导入真实的NotificationService进行测试
        try:
            from services.notification import NotificationService
            from models.database import DatabaseManager

            db_manager = DatabaseManager()
            notifier = NotificationService(db_manager)

            print(f"\n   🚀 正在发送测试消息...")
            print(f"   📡 目标URL: {webhook[:60]}...")
            print(f"   🔐 密钥状态: {'已配置' if secret else '未配置'}")

            # 发送测试
            test_title = "🔧 程序内通知测试"
            test_message = (
                "这是一条来自基金监控系统的测试消息\n\n"
                "> 如果您看到此消息，说明 **钉钉通知功能已完全修复**！\n\n"
                "---\n"
                "*测试时间: 自动触发*"
            )

            notifier.send_dingtalk_notification(test_title, test_message)

            print(f"\n   ✅ 测试完成！请检查钉钉群是否收到消息")
            return True

        except Exception as e:
            print(f"\n   ❌ 发送失败: {e}")
            import traceback
            print(f"\n   详细错误:\n{traceback.format_exc()}")
            return False

    finally:
        conn.close()


def main():
    """主函数"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  🎯 钉钉通知修复验证工具".center(76) + "█")
    print("█" + "  验证 notification.py 字段索引修复是否生效".center(76) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    success = test_notification_settings()

    print("\n" + "="*80)
    if success:
        print("✅ 验证通过！钉钉通知应该能正常工作了")
        print("\n💡 下一步:")
        print("   1. 启动程序: ./start.sh")
        print("   2. 等待自动刷新或手动触发盈亏预警")
        print("   3. 检查钉钉群是否收到通知")
    else:
        print("❌ 验证失败！请检查上述错误信息")
    print("="*80 + "\n")

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
