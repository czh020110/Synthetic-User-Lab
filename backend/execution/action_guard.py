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
# 仅匹配带有明确不可逆/财务含义的词，避免误伤普通提交/确认/取消按钮。
# submit/confirm/cancel 等通用词不在此列，否则会阻断正常表单流程。
DESTRUCTIVE_BUTTON_PATTERNS = [
    r"\bdelete\b", r"\bremove\b", r"\bunsubscribe\b",
    r"删除", r"移除", r"取消订阅",
    r"\bpublish\b", r"\bpay\b", r"\bcheckout\b", r"\bbuy\b", r"\bpurchase\b",
    r"发布", r"支付", r"结算", r"购买",
]

# 敏感字段：密码、信用卡、CVV 等，不应被随意填写。
SENSITIVE_FIELD_PATTERNS = [
    r"\bpassword\b", r"\bpwd\b", r"密码",
    r"\bcredit[_-]?card\b", r"\bcard[_-]?number\b",
    r"信用卡", r"银行卡",
    r"\bcvv\b", r"\bcvc\b", r"安全码",
]

# 测试/本地域名白名单：用于 navigate 动作的精确域名匹配。
SAFE_TEST_DOMAINS = {
    "localhost", "127.0.0.1", "0.0.0.0",
    "example.com", "test.com", "demo.com",
    "prod.example.com",  # demo run 实际 start_url 同域
}

# 允许的安全域名后缀（子域归一化匹配）。
SAFE_DOMAIN_SUFFIXES = {".test", ".local", ".example.com", ".test.com", ".demo.com"}


def is_destructive_action(action: ActionInput, task: Task) -> tuple[bool, str]:
    """检查动作是否为高风险操作。

    返回: (is_destructive, reason)
    当 task.destructive_action_allowed=True 时直接放行。
    """

    if task.destructive_action_allowed:
        return False, ""

    if action.action == "navigate":
        return _check_navigate(action, task)

    if action.action == "click":
        return _check_click(action)

    if action.action == "fill":
        return _check_fill(action)

    return False, ""


def _check_navigate(action: ActionInput, task: Task) -> tuple[bool, str]:
    """导航护栏：放行同域与测试域名，阻断其他域名。"""

    payload = action.payload
    if not isinstance(payload, NavigateActionPayload):
        return False, ""

    target_url = payload.url.lower()
    task_hostname = _extract_hostname(task.start_url)
    target_hostname = _extract_hostname(target_url)

    # 同域放行：主机名完全一致，或目标主机名是 task 主机名的子域
    if task_hostname and target_hostname:
        if target_hostname == task_hostname or target_hostname.endswith("." + task_hostname):
            return False, ""

    # 测试/本地域名放行：精确匹配或安全后缀匹配
    if target_hostname in SAFE_TEST_DOMAINS:
        return False, ""
    if any(target_hostname.endswith(suffix) for suffix in SAFE_DOMAIN_SUFFIXES):
        return False, ""

    return True, f"导航到非白名单域名 {payload.url} 可能存在风险"


def _check_click(action: ActionInput) -> tuple[bool, str]:
    """点击护栏：匹配 selector 中的高风险关键词。"""

    payload = action.payload
    if not isinstance(payload, ClickActionPayload):
        return False, ""

    selector = payload.selector.lower()
    for pattern in DESTRUCTIVE_BUTTON_PATTERNS:
        if re.search(pattern, selector, re.IGNORECASE):
            return True, f"点击目标 '{payload.selector}' 可能触发删除/支付等高风险操作"

    return False, ""


def _check_fill(action: ActionInput) -> tuple[bool, str]:
    """填写护栏：匹配 selector 中的敏感字段关键词。"""

    payload = action.payload
    if not isinstance(payload, FillActionPayload):
        return False, ""

    selector = payload.selector.lower()
    for pattern in SENSITIVE_FIELD_PATTERNS:
        if re.search(pattern, selector, re.IGNORECASE):
            return True, f"填写目标 '{payload.selector}' 可能涉及密码/支付信息等敏感字段"

    return False, ""


def _extract_hostname(url: str) -> str:
    """提取 URL 的主机名（不做子域归一化，避免多段 TLD 误判）。"""

    match = re.search(r"https?://([^/:]+)", url, re.IGNORECASE)
    return match.group(1).lower() if match else ""
