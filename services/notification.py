#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理模块
提供弹窗、钉钉等多渠道通知功能
"""

import time
from typing import Any, Dict

import requests

from utils.logger import logger


class NotificationManager:
    """通知管理器"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.last_notification_time = {}
        self.notification_cooldown = 300

    def get_notification_settings(self) -> Dict[str, Any]:
        """获取通知设置"""
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('SELECT * FROM notification_settings LIMIT 1')
                result = cursor.fetchone()
                if result:
                    return {
                        'popup_enabled': bool(result[1]),
                        'dingtalk_enabled': bool(result[2]),
                        'dingtalk_webhook': result[3] or '',
                        'dingtalk_secret': result[13] if len(result) > 13 else '',
                        'email_enabled': bool(result[4]),
                        'email_smtp_server': result[5] or '',
                        'email_sender': result[6] or '',
                        'email_password': result[7] or '',
                        'email_receiver': result[8] or '',
                        'rise_threshold': result[9] or 3.0,
                        'fall_threshold': result[10] or -3.0,
                        'profit_threshold': result[11] or 1000.0,
                        'loss_threshold': result[12] or -1000.0
                    }
        except Exception as e:
            logger.error(f"获取通知设置失败: {e}")

        return {
            'popup_enabled': True,
            'dingtalk_enabled': False,
            'dingtalk_webhook': '',
            'dingtalk_secret': '',
            'email_enabled': False,
            'email_smtp_server': '',
            'email_sender': '',
            'email_password': '',
            'email_receiver': '',
            'rise_threshold': 3.0,
            'fall_threshold': -3.0,
            'profit_threshold': 1000.0,
            'loss_threshold': -1000.0
        }

    def can_notify(self, notification_type: str) -> bool:
        """检查是否可以发送通知（冷却时间）"""
        now = time.time()
        if notification_type in self.last_notification_time:
            if now - \
                    self.last_notification_time[notification_type] < self.notification_cooldown:
                return False
        self.last_notification_time[notification_type] = now
        return True

    def send_popup_notification(self, title: str, message: str):
        """发送弹窗通知"""
        settings = self.get_notification_settings()
        if not settings['popup_enabled']:
            return

        if not self.can_notify('popup'):
            return

        try:
            from PySide6.QtWidgets import QSystemTrayIcon
            if QSystemTrayIcon.isSystemTrayAvailable():
                pass
            logger.info(f"弹窗通知: {title} - {message}")
        except Exception as e:
            logger.error(f"发送弹窗通知失败: {e}")

    def send_dingtalk_notification(self, title: str, message: str):
        """发送钉钉通知（支持加签验证）"""
        settings = self.get_notification_settings()
        if not settings['dingtalk_enabled']:
            return

        webhook = settings['dingtalk_webhook']
        secret = settings['dingtalk_secret']

        if not webhook:
            logger.warning("钉钉Webhook未配置")
            return

        if not self.can_notify('dingtalk'):
            return

        try:
            import base64
            import hashlib
            import hmac
            import urllib.parse
            from datetime import datetime
            from urllib.parse import parse_qs, urlparse

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"### {title}\n\n{message}\n\n> 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }

            final_url = webhook

            if secret:
                timestamp = str(round(time.time() * 1000))
                string_to_sign = f'{timestamp}\n{secret}'.encode('utf-8')
                hmac_code = hmac.new(
                    secret.encode('utf-8'),
                    string_to_sign,
                    digestmod=hashlib.sha256
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

                parsed_url = urlparse(webhook)
                query_params = parse_qs(parsed_url.query)
                access_token = query_params.get('access_token', [''])[0]

                new_query = f"access_token={access_token}&timestamp={timestamp}&sign={sign}"
                final_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
                logger.info(f"使用加签模式发送钉钉通知")

            response = requests.post(
                final_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                resp_json = response.json()
                if resp_json.get('errcode') == 0:
                    logger.info(f"✅ 钉钉通知发送成功: {title}")
                else:
                    errcode = resp_json.get('errcode', 'unknown')
                    errmsg = resp_json.get('errmsg', '未知错误')
                    logger.error(f"❌ 钉钉API错误 [{errcode}]: {errmsg}")
                    if errcode == 310000:
                        logger.error("⚠️ 签名验证失败！请检查：")
                        logger.error("   1. 加签密钥是否正确复制（无多余空格）")
                        logger.error("   2. 密钥是否与钉钉机器人设置页面一致")
                        logger.error("   3. 系统时间是否准确")
            else:
                logger.error(f"❌ 钉钉请求失败: HTTP {response.status_code}, 响应: {response.text}")

        except Exception as e:
            logger.error(f"❌ 发送钉钉通知异常: {e}")

    def check_and_notify(self, fund_data: Dict,
                         total_profit: float, daily_profit: float):
        """检查并发送通知"""
        settings = self.get_notification_settings()

        for code, fund in fund_data.items():
            gszzl = float(fund.get('gszzl', 0))
            name = fund.get('name', code)

            if gszzl >= settings['rise_threshold']:
                message = f"基金 {name}({code}) 涨幅达到 {gszzl:.2f}%"
                self.send_popup_notification("涨幅预警", message)
                self.send_dingtalk_notification("📈 涨幅预警", message)

            elif gszzl <= settings['fall_threshold']:
                message = f"基金 {name}({code}) 跌幅达到 {gszzl:.2f}%"
                self.send_popup_notification("跌幅预警", message)
                self.send_dingtalk_notification("📉 跌幅预警", message)

        if total_profit >= settings['profit_threshold']:
            message = f"累计盈亏达到 ¥{total_profit:.2f}"
            self.send_popup_notification("盈利预警", message)
            self.send_dingtalk_notification("💰 盈利预警", message)

        elif total_profit <= settings['loss_threshold']:
            message = f"累计亏损达到 ¥{abs(total_profit):.2f}"
            self.send_popup_notification("亏损预警", message)
            self.send_dingtalk_notification("⚠️ 亏损预警", message)
