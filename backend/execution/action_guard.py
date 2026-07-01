from __future__ import annotations

import logging
import re
from typing import Any

from backend.schemas.run_schemas import (
    ActionInput,
    ClickActionPayload,
    FillActionPayload,
    NavigateActionPayload,
)
from backend.schemas.task_schemas import Task

logger = logging.getLogger(__name__)

# ============================ 高风险动作检测 ============================ #

DESTRUCTIVE_BUTTON_PATTERNS = [
    r"\bdelete\b", r"\bremove\b", r"\bcancel\b",
    r"\b删除\b", r"\b移除\b", r"\b取消订阅\b",
    r"\bsubmit\b", r"\bpublish\b", r"\bconfirm\b",
    r"\b提交\b", r"\b发布\b", r"\b确认支付\b",
    r"\bpay\b", r"\bcheckout\b", r"\bbuy\b",
    r"\b支付\b", r"\b结算\b", r"\b购买\b",
]

SENSITIVE_FIELD_PATTERNS = [
    r"\bpassword\b", r"\bpwd\b", r"密码",
    r"\bcredit[_-]?card\b", r"\bcard[_-]?number\b",
    r"信用卡", r"银行卡",
    r"\bcvv\b", r"\bexpir\b", r"有效期",
]


def is_destructive_action(action: ActionInput, task: Task, page_state: Any | None = None) -> tuple[bool, str]:
    """检查动作是否为高风险操作。

    返回: (is_destructive, reason)
    """

    if task.destructive_action_allowed:
        return False, ""

    # navigate: 检查域名白名单
    if action.action == "navigate":
        payload = action.payload
        if not isinstance(payload, NavigateActionPayload):
            return False, ""

        target_url = payload.url.lower()

        # 允许 task.start_url 的同域导航
        task_domain = _extract_domain(task.start_url)
        target_domain = _extract_domain(target_url)

        if task_domain and target_domain and task_domain == target_domain:
            return False, ""

        # 允许常见测试域名
        safe_test_domains = [
            "localhost", "127.0.0.1", "0.0.0.0",
            "example.com", "test.com", "demo.com",
            "staging.", ".test", ".local",
        ]

        if any(domain in target_url for domain in safe_test_domains):
            return False, ""

        # 其他域名视为高风险
        return True, f"导航到非白名单域名 {payload.url} 可能存在风险"

    # click: 检查按钮文本是否含高风险关键词
    if action.action == "click":
        payload = action.payload
        if not isinstance(payload, ClickActionPayload):
            return False, ""

        selector = payload.selector.lower()

        for pattern in DESTRUCTIVE_BUTTON_PATTERNS:
            if re.search(pattern, selector, re.IGNORECASE):
                return True, f"点击目标 '{payload.selector}' 可能触发删除/提交/支付等高风险操作"

        return False, ""

    # fill: 检查字段是否涉及敏感信息
    if action.action == "fill":
        payload = action.payload
        if not isinstance(payload, FillActionPayload):
            return False, ""

        selector = payload.selector.lower()

        for pattern in SENSITIVE_FIELD_PATTERNS:
            if re.search(pattern, selector, re.IGNORECASE):
                return True, f"填写目标 '{payload.selector}' 可能涉及密码/支付信息等敏感字段"

        return False, ""

    return False, ""


def _extract_domain(url: str) -> str:
    """提取 URL 的主域名。"""
    import re

    match = re.search(r"https?://([^/:]+)", url)
    if not match:
        return ""

    domain = match.group(1)

    # 提取主域名（去掉子域）
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])

    return domain
