#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理模块
提供弹窗、钉钉等多渠道通知功能
"""

import time
from typing import Any, Dict, List

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
                # 使用明确的列名查询，避免索引错误（dingtalk_secret在索引13）
                cursor.execute('''
                    SELECT id, popup_enabled, dingtalk_enabled, dingtalk_webhook,
                           email_enabled, email_smtp_server, email_sender,
                           email_password, email_receiver, rise_threshold,
                           fall_threshold, profit_threshold, loss_threshold,
                           dingtalk_secret
                    FROM notification_settings LIMIT 1
                ''')
                result = cursor.fetchone()
                if result:
                    return {
                        'popup_enabled': bool(result[1]),
                        'dingtalk_enabled': bool(result[2]),
                        'dingtalk_webhook': result[3] or '',
                        'dingtalk_secret': result[13] or '',  # ✅ 修正：索引13是dingtalk_secret
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
        """检查并发送通知（聚合预警通知）"""
        settings = self.get_notification_settings()

        # 收集涨幅预警和跌幅预警的基金
        rise_alerts = []
        fall_alerts = []

        for code, fund in fund_data.items():
            gszzl = float(fund.get('gszzl', 0))
            name = fund.get('name', code)

            if gszzl >= settings['rise_threshold']:
                rise_alerts.append({
                    'code': code,
                    'name': name,
                    'gszzl': gszzl
                })

            elif gszzl <= settings['fall_threshold']:
                fall_alerts.append({
                    'code': code,
                    'name': name,
                    'gszzl': gszzl
                })

        # 聚合发送涨幅预警通知
        if rise_alerts:
            rise_message = self._aggregate_alert_message(rise_alerts, "涨幅")
            self.send_popup_notification("涨幅预警", rise_message)
            self.send_dingtalk_notification("📈 涨幅预警", rise_message)

        # 聚合发送跌幅预警通知
        if fall_alerts:
            fall_message = self._aggregate_alert_message(fall_alerts, "跌幅")
            self.send_popup_notification("跌幅预警", fall_message)
            self.send_dingtalk_notification("📉 跌幅预警", fall_message)

        if total_profit >= settings['profit_threshold']:
            message = f"累计盈亏达到 ¥{total_profit:.2f}"
            self.send_popup_notification("盈利预警", message)
            self.send_dingtalk_notification("💰 盈利预警", message)

        elif total_profit <= settings['loss_threshold']:
            message = f"累计亏损达到 ¥{abs(total_profit):.2f}"
            self.send_popup_notification("⚠️ 亏损预警", message)
            # 累计亏损不发送钉钉通知（仅保留本地弹窗提醒）
            # self.send_dingtalk_notification("⚠️ 亏损预警", message)

    def _aggregate_alert_message(self, alerts: List[Dict], alert_type: str) -> str:
        """聚合预警消息，避免字符串过大

        Args:
            alerts: 预警基金列表，每个元素包含code, name, gszzl
            alert_type: 预警类型（"涨幅"或"跌幅"）

        Returns:
            聚合后的消息字符串
        """
        if not alerts:
            return ""

        # 钉钉消息文本内容最多支持2048字符，保守限制在500字符内
        max_length = 500

        # 构建简洁的聚合消息
        count = len(alerts)
        if count == 1:
            # 单个基金，直接返回详细信息
            alert = alerts[0]
            return f"基金 {alert['name']}({alert['code']}) {alert_type}达到 {alert['gszzl']:.2f}%"

        # 多个基金，聚合显示
        # 先显示总数
        header = f"{count}只基金触发{alert_type}预警\n"

        # 然后列出各基金的简要信息
        details = []
        for alert in alerts:
            detail = f"{alert['name']}: {alert['gszzl']:.2f}%"
            details.append(detail)

        # 检查总长度，如果超过限制则截断
        full_message = header + "\n".join(details)

        if len(full_message) > max_length:
            # 截断并添加省略提示
            truncated_details = []
            current_length = len(header)

            for detail in details:
                if current_length + len(detail) + 1 > max_length - 20:  # 留出省略提示的空间
                    remaining_count = len(details) - len(truncated_details)
                    truncated_details.append(f"...还有{remaining_count}只基金")
                    break
                truncated_details.append(detail)
                current_length += len(detail) + 1

            full_message = header + "\n".join(truncated_details)

        return full_message
