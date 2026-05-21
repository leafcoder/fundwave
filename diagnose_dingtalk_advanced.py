#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉Webhook高级诊断工具
完整验证签名算法，定位310000错误原因
"""

import base64
import hashlib
import hmac
import json
import sqlite3
import time
import urllib.parse
from datetime import datetime

import requests


def generate_dingtalk_sign(secret: str, timestamp: str) -> tuple:
    """
    生成钉钉加签（严格按照官方文档）

    Args:
        secret: 加签密钥 (SEC开头)
        timestamp: 时间戳(毫秒)

    Returns:
        (sign, string_to_sign, hmac_code)
    """
    # 步骤1：构建签名字符串
    string_to_sign = f'{timestamp}\n{secret}'

    # 步骤2：HMAC-SHA256加密
    hmac_code = hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()

    # 步骤3：Base64编码
    base64_str = base64.b64encode(hmac_code).decode('utf-8')

    # 步骤4：URL编码
    sign = urllib.parse.quote_plus(base64_str)

    return sign, string_to_sign, hmac_code


def test_webhook_with_debug(webhook_url: str, secret: str = "") -> dict:
    """
    测试Webhook连接性（带详细调试信息）

    Returns:
        包含完整调试信息的字典
    """
    result = {
        'success': False,
        'error': None,
        'response_code': None,
        'response_body': None,
        'debug_info': {},
        'suggestions': []
    }

    try:
        print("\n" + "="*80)
        print("🔍 钉钉Webhook 高级诊断")
        print("="*80)

        # 1. 解析原始URL
        print(f"\n📌 [步骤1] 解析Webhook URL")
        parsed_url = urllib.parse.urlparse(webhook_url)

        result['debug_info']['original_url'] = webhook_url
        result['debug_info']['scheme'] = parsed_url.scheme
        result['debug_info']['netloc'] = parsed_url.netloc
        result['debug_info']['path'] = parsed_url.path

        query_params = urllib.parse.parse_qs(parsed_url.query)
        access_token = query_params.get('access_token', [''])[0]

        result['debug_info']['access_token'] = access_token
        result['debug_info']['access_token_length'] = len(access_token)

        print(f"   原始URL: {webhook_url[:60]}...")
        print(f"   协议: {parsed_url.scheme}")
        print(f"   域名: {parsed_url.netloc}")
        print(f"   路径: {parsed_url.path}")
        print(f"   Access Token: {access_token[:20]}... (长度:{len(access_token)})")

        if not access_token:
            raise ValueError("URL中未找到access_token参数")

        # 2. 检查密钥
        print(f"\n📌 [步骤2] 检查加签密钥")

        if secret:
            result['debug_info']['has_secret'] = True
            result['debug_info']['secret_prefix'] = secret[:10]
            result['debug_info']['secret_length'] = len(secret)
            result['debug_info']['secret_format_valid'] = secret.startswith('SEC')

            print(f"   密钥状态: ✅ 已配置")
            print(f"   密钥前缀: {secret[:10]}...")
            print(f"   密钥长度: {len(secret)} 字符")
            print(f"   格式检查: {'✅ 正确(SEC开头)' if secret.startswith('SEC') else '❌ 错误(非SEC开头)'}")

            # 检查常见问题
            if '\n' in secret or '\r' in secret or '\t' in secret:
                result['suggestions'].append("⚠️ 密钥包含换行符或制表符！请重新复制")
                print(f"   ⚠️ 警告: 密钥中包含特殊字符（换行/制表符）")

            if ' ' in secret:
                result['suggestions'].append("⚠️ 密钥包含空格！请删除首尾空格")
                print(f"   ⚠️ 警告: 密钥中包含空格字符")

        else:
            result['debug_info']['has_secret'] = False
            print(f"   密钥状态: ❌ 未配置（将尝试无签名发送）")
            result['suggestions'].append("建议配置加签密钥以提高安全性")

        # 3. 生成签名（如果有密钥）
        final_url = webhook_url
        timestamp = ""
        sign = ""

        if secret:
            print(f"\n📌 [步骤3] 生成签名")

            # 3.1 生成时间戳
            timestamp = str(round(time.time() * 1000))
            result['debug_info']['timestamp'] = timestamp
            result['debug_info']['timestamp_datetime'] = datetime.fromtimestamp(int(timestamp)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')

            print(f"   时间戳: {timestamp}")
            print(f"   对应时间: {result['debug_info']['timestamp_datetime']}")

            # 3.2 构建签名字符串
            sign, string_to_sign, hmac_code = generate_dingtalk_sign(secret, timestamp)

            result['debug_info']['string_to_sign'] = repr(string_to_sign)
            result['debug_info']['sign'] = sign
            result['debug_info']['hmac_hex'] = hmac_code.hex()
            result['debug_info']['hmac_base64'] = base64.b64encode(hmac_code).decode()

            print(f"\n   签名算法详情:")
            print(f"   ┌─────────────────────────────────────────────┐")
            print(f"   │ 签名字符串: {repr(string_to_sign)[:50]:<43}│")
            print(f"   │ HMAC-SHA256: {hmac_code.hex()[:40]:<44}│")
            print(f"   │ Base64编码: {base64.b64encode(hmac_code).decode()[:40]:<43}│")
            print(f"   │ URL编码后: {sign[:40]:<46}│")
            print(f"   └─────────────────────────────────────────────┘")

            # 3.3 构建最终URL
            new_query = f"access_token={access_token}&timestamp={timestamp}&sign={sign}"
            final_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"

            result['debug_info']['final_url'] = final_url
            result['debug_info']['url_with_params'] = {
                'access_token': access_token,
                'timestamp': timestamp,
                'sign': sign
            }

            print(f"\n   最终请求URL:")
            print(f"   {final_url[:80]}...")
            print(f"   参数:")
            print(f"      - access_token: {access_token[:20]}...")
            print(f"      - timestamp: {timestamp}")
            print(f"      - sign: {sign[:30]}...")

        else:
            result['debug_info']['final_url'] = webhook_url

        # 4. 发送测试请求
        print(f"\n📌 [步骤4] 发送测试请求")

        test_data = {
            "msgtype": "markdown",
            "markdown": {
                "title": "🔧 连接性测试",
                "text": (
                    f"### 🔧 基金监控系统 - 钉钉通知测试\n\n"
                    f"> **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"✅ 如果您看到此消息，说明钉钉通知配置成功！\n\n"
                    f"---\n"
                    f"*测试模式: {'加签验证' if secret else '无签名'}*\n"
                    f"*时间戳: {timestamp if timestamp else 'N/A'}*"
                )
            }
        }

        print(f"   请求体:")
        print(f"   {json.dumps(test_data, ensure_ascii=False, indent=6)}")

        response = requests.post(
            final_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )

        result['response_code'] = response.status_code
        result['response_body'] = response.text

        print(f"\n   HTTP状态码: {response.status_code}")
        print(f"   响应内容:")
        print(f"   ┌{'─'*70}┐")
        for line in response.text.split('\n'):
            print(f"   │ {line:<70}│")
        print(f"   └{'─'*70}┘")

        # 5. 解析响应结果
        print(f"\n📌 [步骤5] 分析响应结果")

        try:
            resp_json = response.json()

            if response.status_code == 200 and resp_json.get('errcode') == 0:
                result['success'] = True
                print(f"\n   ✅ 成功！消息已发送到钉钉群！")
                result['suggestions'].append("🎉 钉钉通知配置完全正确！")

            else:
                errcode = resp_json.get('errcode', 'unknown')
                errmsg = resp_json.get('errmsg', '未知错误')

                result['error'] = f"[{errcode}] {errmsg}"
                print(f"\n   ❌ 失败！错误码[{errcode}]: {errmsg}")

                # 根据错误码提供针对性建议
                if errcode == 310000:
                    print(f"\n   🚨 错误码310000 - 签名不匹配分析:")

                    # 检查可能的原因
                    issues_found = []

                    if not secret:
                        issues_found.append("未配置密钥但机器人要求签名验证")
                        result['suggestions'].append("❌ 机器人启用了加签，但您未配置密钥")

                    elif len(secret) != 44:  # SEC + 40位hex
                        issues_found.append(f"密钥长度异常({len(secret)}，应为44)")
                        result['suggestions'].append(f"❌ 密钥长度不正确: {len(secret)}字符 (应为44字符)")

                    elif not secret.startswith('SEC'):
                        issues_found.append("密钥格式错误(应以SEC开头)")
                        result['suggestions'].append("❌ 密钥格式错误: 应以'SEC'开头")

                    else:
                        issues_found.append("密钥格式正确，可能是值不匹配")
                        result['suggestions'].append("⚠️ 密钥格式正确，但可能与机器人设置不一致")
                        result['suggestions'].append("💡 请在钉钉机器人设置页面重新复制密钥")

                    print(f"   可能原因:")
                    for i, issue in enumerate(issues_found, 1):
                        print(f"      {i}. {issue}")

                    print(f"\n   解决方案:")
                    print(f"      1. 打开钉钉群 → 群设置 → 智能群助手")
                    print(f"      2. 点击你的机器人 → 安全设置")
                    print(f"      3. 选择【加签】方式 → 点击【复制】按钮")
                    print(f"      4. 回到本程序 → 【通知设置】→ 粘贴密钥 → 保存")
                    print(f"      5. 重启程序并再次测试")

                elif errcode == 310006:
                    print(f"\n   🚨 错误码310006 - 机器人不在目标群聊")
                    result['suggestions'].append("❌ 机器人已被移除或群ID无效")
                    result['suggestions'].append("💡 请重新添加机器人到当前群")

                elif errcode == 430101:
                    print(f"\n   🚨 错误码430101 - 触发频率限制")
                    result['suggestions'].append("⚠️ 发送太频繁，请稍后再试")

                else:
                    print(f"\n   🚨 未知错误码")
                    result['suggestions'].append(f"❌ 未知错误: [{errcode}] {errmsg}")

        except Exception as parse_err:
            result['error'] = f"解析响应失败: {parse_err}"
            print(f"\n   ⚠️ 无法解析响应JSON: {parse_err}")

    except requests.exceptions.Timeout:
        result['error'] = "请求超时（15秒）"
        result['suggestions'].append("❌ 网络超时，请检查网络连接")
        print(f"\n   ❌ 请求超时！网络可能不通。")

    except Exception as e:
        result['error'] = f"异常: {type(e).__name__}: {e}"
        result['suggestions'].append(f"❌ 未预期错误: {e}")
        print(f"\n   ❌ 异常: {e}")

    finally:
        print(f"\n{'='*80}")
        print("🔍 诊断完成")
        print(f"{'='*80}\n")

    return result


def main():
    """主函数"""
    db_path = 'fund_monitor.db'
    webhook_url = ""
    secret = ""

    # 从数据库读取配置
    print("📂 正在从数据库读取配置...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT dingtalk_webhook, dingtalk_secret FROM notification_settings LIMIT 1'
        )
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            webhook_url = result[0]
            secret = result[1] or ""

            print(f"✅ 数据库读取成功:")
            print(f"   Webhook: {webhook_url[:60]}...")
            print(f"   Secret: {secret[:15]}..." if secret else "   Secret: (未配置)")
        else:
            print(f"❌ 数据库中无Webhook配置")
            return False

    except Exception as e:
        print(f"❌ 数据库读取失败: {e}")
        return False

    # 执行诊断测试
    result = test_webhook_with_debug(webhook_url, secret)

    # 输出总结
    print("\n" + "="*80)
    print("📊 诊断总结")
    print("="*80)
    print(f"\n最终结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

    if result.get('error'):
        print(f"错误信息: {result['error']}")

    print(f"\n💡 建议:")
    for i, suggestion in enumerate(result.get('suggestions', []), 1):
        print(f"   {i}. {suggestion}")

    if result.get('debug_info', {}).get('has_secret'):
        print(f"\n🔐 密钥信息:")
        print(f"   前缀: {result['debug_info'].get('secret_prefix', 'N/A')}")
        print(f"   长度: {result['debug_info'].get('secret_length', 0)} 字符")
        print(f"   格式: {'✅ 有效(SEC开头)' if result['debug_info'].get('secret_format_valid') else '❌ 无效'}")

    return result['success']


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
