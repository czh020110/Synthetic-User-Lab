from __future__ import annotations

import logging
import re
from typing import Any

from backend.schemas.guard_config_schemas import GuardConfig
from backend.schemas.run_schemas import (
    ActionInput,
    ClickActionPayload,
    FillActionPayload,
    NavigateActionPayload,
)
from backend.schemas.task_schemas import Task

logger = logging.getLogger(__name__)

# ============================ 高风险动作检测 ============================ #
# 破坏性/敏感关键词库由 GuardConfig（DB 持久化）提供，默认值见
# backend/fixtures/guard_defaults.py。submit/confirm/cancel 等通用词不在默认库，
# 避免阻断正常表单流程。

# 测试/本地域名白名单：用于 navigate 动作的精确域名匹配。
SAFE_TEST_DOMAINS = {
    "localhost", "127.0.0.1", "0.0.0.0",
    "example.com", "test.com", "demo.com",
    "prod.example.com",  # demo run 实际 start_url 同域
}

# 允许的安全域名后缀（子域归一化匹配）。
SAFE_DOMAIN_SUFFIXES = {".test", ".local", ".example.com", ".test.com", ".demo.com"}


def is_destructive_action(
    action: ActionInput,
    task: Task,
    guard_config: GuardConfig | None = None,
) -> tuple[bool, str]:
    """检查动作是否为高风险操作。

    返回: (is_destructive, reason)
    当 task.destructive_action_allowed=True 时直接放行。
    guard_config 为 None 时从全局 EntityStore 读取当前关键词库（默认词库兜底）。
    """

    if task.destructive_action_allowed:
        return False, ""

    # navigate 护栏只依赖域名白名单，不需要关键词库，故在其之前不触发 DB 读
    if action.action == "navigate":
        return _check_navigate(action, task)

    if guard_config is None:
        guard_config = _load_guard_config()

    if action.action == "click":
        return _check_click(action, guard_config.destructive_keywords)

    if action.action == "fill":
        return _check_fill(action, guard_config.sensitive_keywords)

    return False, ""


def _load_guard_config() -> GuardConfig:
    """从全局 EntityStore 读取护栏关键词库。

    放在函数内导入以避免 action_guard -> stores -> ... 的模块级循环导入；
    生产与 acceptance 调用方不传 guard_config 时走此路径，读取 DB 持久化配置（空库回退默认词库）。
    """
    from backend.stores import get_entity_store

    return get_entity_store().get_guard_config()


def _pattern_matches(pattern: str, text: str) -> bool:
    """关键词正则匹配；空模式不匹配任何内容（避免 re.search('', text) 命中全部）；非法正则退回字面子串匹配。"""
    if not pattern:
        return False
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in text.lower()


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


def _check_click(action: ActionInput, destructive_keywords: list[str]) -> tuple[bool, str]:
    """点击护栏：匹配 selector 中的高风险关键词。"""

    payload = action.payload
    if not isinstance(payload, ClickActionPayload):
        return False, ""

    selector = payload.selector.lower()
    for keyword in destructive_keywords:
        if _pattern_matches(keyword, selector):
            return True, f"点击目标 '{payload.selector}' 可能触发删除/支付等高风险操作"

    return False, ""


def _check_fill(action: ActionInput, sensitive_keywords: list[str]) -> tuple[bool, str]:
    """填写护栏：匹配 selector 中的敏感字段关键词。"""

    payload = action.payload
    if not isinstance(payload, FillActionPayload):
        return False, ""

    selector = payload.selector.lower()
    for keyword in sensitive_keywords:
        if _pattern_matches(keyword, selector):
            return True, f"填写目标 '{payload.selector}' 可能涉及密码/支付信息等敏感字段"

    return False, ""


def _extract_hostname(url: str) -> str:
    """提取 URL 的主机名（不做子域归一化，避免多段 TLD 误判）。"""

    match = re.search(r"https?://([^/:]+)", url, re.IGNORECASE)
    return match.group(1).lower() if match else ""
