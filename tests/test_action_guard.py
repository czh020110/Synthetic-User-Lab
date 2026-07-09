import pytest

from backend.execution.action_guard import is_destructive_action
from backend.schemas.run_schemas import (
    ActionInput,
    ClickActionPayload,
    FillActionPayload,
    NavigateActionPayload,
    WaitActionPayload,
)
from backend.schemas.task_schemas import Task
from backend.stores import get_entity_store


def setup_function():
    """每个测试前重置 EntityStore，避免 is_destructive_action 读到被其他测试污染的护栏关键词。"""
    get_entity_store().clear()


def test_navigate_same_domain_allowed():
    """同域导航应被允许。"""
    task = Task(
        start_url="https://example.com/login",
        destructive_action_allowed=False,
    )
    action = ActionInput(
        action="navigate",
        payload=NavigateActionPayload(url="https://example.com/register"),
    )

    is_destructive, reason = is_destructive_action(action, task)
    assert not is_destructive
    assert reason == ""


def test_navigate_test_domain_allowed():
    """测试域名应被允许。"""
    task = Task(
        start_url="https://prod.example.com",
        destructive_action_allowed=False,
    )

    test_urls = [
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "https://demo.example.com",
        "https://staging.example.com",
        "https://test.example.com",
    ]

    for url in test_urls:
        action = ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=url),
        )
        is_destructive, reason = is_destructive_action(action, task)
        assert not is_destructive, f"URL {url} should be allowed"


def test_navigate_unknown_domain_blocked():
    """非白名单域名应被阻断。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )
    action = ActionInput(
        action="navigate",
        payload=NavigateActionPayload(url="https://malicious.com/phishing"),
    )

    is_destructive, reason = is_destructive_action(action, task)
    assert is_destructive
    assert "非白名单域名" in reason
    assert "malicious.com" in reason


def test_navigate_allowed_when_destructive_enabled():
    """destructive_action_allowed=True 时应放行。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=True,
    )
    action = ActionInput(
        action="navigate",
        payload=NavigateActionPayload(url="https://malicious.com"),
    )

    is_destructive, reason = is_destructive_action(action, task)
    assert not is_destructive


def test_click_safe_button_allowed():
    """安全按钮点击应被允许。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )
    action = ActionInput(
        action="click",
        payload=ClickActionPayload(selector="button[data-testid='login-button']"),
    )

    is_destructive, reason = is_destructive_action(action, task)
    assert not is_destructive


def test_click_destructive_button_blocked():
    """高风险按钮点击应被阻断。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )

    destructive_selectors = [
        "button:has-text('Delete Account')",
        "button:has-text('删除')",
        "button:has-text('Pay Now')",
        "button:has-text('确认支付')",
        "button:has-text('Publish')",
        "button:has-text('发布')",
        "a[href='/unsubscribe']",
        "button[data-action='checkout']",
    ]

    for selector in destructive_selectors:
        action = ActionInput(
            action="click",
            payload=ClickActionPayload(selector=selector),
        )
        is_destructive, reason = is_destructive_action(action, task)
        assert is_destructive, f"Selector '{selector}' should be blocked"
        assert "高风险操作" in reason


def test_fill_safe_field_allowed():
    """安全字段填写应被允许。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )
    action = ActionInput(
        action="fill",
        payload=FillActionPayload(
            selector="input[name='username']",
            value="test_user",
        ),
    )

    is_destructive, reason = is_destructive_action(action, task)
    assert not is_destructive


def test_fill_sensitive_field_blocked():
    """敏感字段填写应被阻断。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )

    sensitive_selectors = [
        "input[name='password']",
        "input[type='password']",
        "input[name='credit-card']",
        "input[name='card_number']",
        "input[name='cvv']",
        "input[placeholder='请输入密码']",
        "input[id='password-field']",
    ]

    for selector in sensitive_selectors:
        action = ActionInput(
            action="fill",
            payload=FillActionPayload(selector=selector, value="test_value"),
        )
        is_destructive, reason = is_destructive_action(action, task)
        assert is_destructive, f"Selector '{selector}' should be blocked"
        assert "敏感字段" in reason


def test_wait_action_always_allowed():
    """wait 动作应始终被允许。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )
    action = ActionInput(
        action="wait",
        payload=WaitActionPayload(duration_ms=2000),
    )

    is_destructive, reason = is_destructive_action(action, task)
    assert not is_destructive


def test_click_normal_submit_confirm_cancel_allowed():
    """普通提交/确认/取消按钮不应被误伤（避免阻断正常表单流程）。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )

    # demo 站点核心 selector，必须放行
    normal_selectors = [
        "#btn-submit-form",
        "#s2-submit",
        "#btn-confirm",
        "#modal-confirm",
        "#btn-cancel",
        "#modal-cancel",
        "button:has-text('确认完成')",
        "button:has-text('提交表单')",
        "button:has-text('取消任务')",
    ]

    for selector in normal_selectors:
        action = ActionInput(
            action="click",
            payload=ClickActionPayload(selector=selector),
        )
        is_destructive, _ = is_destructive_action(action, task)
        assert not is_destructive, f"Normal selector '{selector}' should not be blocked"


def test_navigate_substring_bypass_blocked():
    """域名白名单应使用精确匹配，不能被子字符串绕过。"""
    task = Task(
        start_url="https://app.example.com",
        destructive_action_allowed=False,
    )

    bypass_urls = [
        "https://example.com.evil.org",
        "https://not-test.com",
        "https://evil.testing.com",
        "https://example.com.attacker.io",
    ]

    for url in bypass_urls:
        action = ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=url),
        )
        is_destructive, reason = is_destructive_action(action, task)
        assert is_destructive, f"URL {url} should be blocked (substring bypass)"


def test_navigate_subdomain_of_safe_domain_allowed():
    """安全域名的子域应被放行。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )

    subdomain_urls = [
        "https://demo.example.com",
        "https://staging.example.com",
        "https://api.test.com",
    ]

    for url in subdomain_urls:
        action = ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=url),
        )
        is_destructive, _ = is_destructive_action(action, task)
        assert not is_destructive, f"Subdomain URL {url} should be allowed"


def test_navigate_localhost_allowed():
    """本地开发域名应被放行。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )

    local_urls = [
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:8000",
    ]

    for url in local_urls:
        action = ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=url),
        )
        is_destructive, _ = is_destructive_action(action, task)
        assert not is_destructive, f"Local URL {url} should be allowed"


def test_navigate_demo_run_app_base_url_allowed():
    """demo run 的 app_base_url 同域导航应被放行。"""
    task = Task(
        start_url="http://127.0.0.1:8765/demo/index.html",
        destructive_action_allowed=False,
    )

    action = ActionInput(
        action="navigate",
        payload=NavigateActionPayload(url="http://127.0.0.1:8765/demo/step2.html"),
    )
    is_destructive, _ = is_destructive_action(action, task)
    assert not is_destructive


def test_fill_demo_site_password_field_blocked():
    """demo 站点的密码字段填写应被阻断。"""
    task = Task(
        start_url="https://example.com",
        destructive_action_allowed=False,
    )

    action = ActionInput(
        action="fill",
        payload=FillActionPayload(selector="#fill-pwd", value="test_password"),
    )
    is_destructive, reason = is_destructive_action(action, task)
    assert is_destructive
    assert "敏感字段" in reason
