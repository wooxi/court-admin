#!/usr/bin/env python3
"""
朝廷政务管理系统 - 飞书通知工具
发送定时任务执行结果到飞书群

支持两种方式：
1. Webhook（需要群机器人）
2. Feishu API（需要用户 OAuth token）
"""

import requests
import json
import os
import subprocess
from datetime import datetime

# 飞书配置（从环境变量获取）
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "oc_9ac499d324230e5f2b22a91285ec76b0")

# 通过 OpenClaw 发送消息（推荐方式）
def send_via_openclaw(title, content):
    """通过 OpenClaw message 工具发送飞书消息"""
    try:
        message = f"{title}\n\n{content}"
        # 调用 OpenClaw message 工具
        result = subprocess.run(
            ["openclaw", "message", "send", "--target", f"chat:{FEISHU_CHAT_ID}", "--message", message],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ 通过 OpenClaw 发送成功")
            return True
        else:
            print(f"⚠️ OpenClaw 发送失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ OpenClaw 发送异常：{e}")
        return False

def send_feishu_message(title, content, msg_type="text"):
    """
    发送飞书消息
    
    Args:
        title: 消息标题
        content: 消息内容
        msg_type: 消息类型 (text/post)
    
    Returns:
        bool: 是否发送成功
    """
    # 优先尝试 OpenClaw 方式
    if send_via_openclaw(title, content):
        return True
    
    # 降级使用 Webhook
    if not FEISHU_WEBHOOK:
        print("⚠️  FEISHU_WEBHOOK 未配置，跳过发送")
        return False
    
    try:
        if msg_type == "post":
            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [
                                [{"tag": "text", "text": line}]
                                for line in content.split("\n")
                            ]
                        }
                    }
                }
            }
        else:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"{title}\n\n{content}"
                }
            }
        
        response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print(f"✅ 飞书消息发送成功")
            return True
        else:
            print(f"❌ 飞书消息发送失败：{result}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 飞书消息发送异常：{e}")
        return False

def send_task_notification(task_name, status, result, duration_ms=None):
    """
    发送定时任务执行通知
    
    Args:
        task_name: 任务名称
        status: 执行状态 (success/failed)
        result: 执行结果
        duration_ms: 执行耗时（毫秒）
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = "✅" if status == "success" else "❌"
    status_text = "成功" if status == "success" else "失败"
    
    duration_str = ""
    if duration_ms:
        duration_str = f"\n⏱️ 耗时：{duration_ms}ms"
    
    title = f"📋 定时任务执行报告"
    content = f"""{status_emoji} 任务：{task_name}
🕐 时间：{timestamp}
📊 状态：{status_text}
📝 结果：{result}{duration_str}
"""
    
    return send_feishu_message(title, content, msg_type="post")

def send_service_alert(service_name, message, action_taken=None):
    """
    发送服务告警通知
    
    Args:
        service_name: 服务名称
        message: 告警内容
        action_taken: 已采取的措施
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    title = "⚠️ 服务告警"
    content = f"""🚨 服务：{service_name}
🕐 时间：{timestamp}
📝 问题：{message}"""
    
    if action_taken:
        content += f"\n🔧 措施：{action_taken}"
    
    return send_feishu_message(title, content, msg_type="post")

if __name__ == "__main__":
    # 测试示例
    print("=== 朝廷政务系统 - 飞书通知工具 ===")
    
    # 测试任务通知
    send_task_notification(
        task_name="服务健康检查",
        status="success",
        result="所有服务正常",
        duration_ms=150
    )
    
    # 测试服务告警
    send_service_alert(
        service_name="后端服务",
        message="健康检查失败",
        action_taken="已自动重启"
    )
