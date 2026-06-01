from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.execution.playwright_adapter import execute_action, TERMINAL_ACTIONS
from backend.schemas.run_schemas import (
    AbandonPayload,
    ActionInput,
    AskForHelpPayload,
    CheckActionPayload,
    ClickActionPayload,
    DblclickActionPayload,
    DragActionPayload,
    FillActionPayload,
    HoverActionPayload,
    NavigateActionPayload,
    PressActionPayload,
    ScrollActionPayload,
    SelectActionPayload,
    UncheckActionPayload,
    UploadActionPayload,
    WaitActionPayload,
)


def _make_fake_page() -> AsyncMock:
    page = AsyncMock()
    locator = AsyncMock()
    locator.click = AsyncMock()
    locator.fill = AsyncMock()
    locator.hover = AsyncMock()
    locator.check = AsyncMock()
    locator.uncheck = AsyncMock()
    locator.dblclick = AsyncMock()
    locator.set_input_files = AsyncMock()
    locator.select_option = AsyncMock()
    locator.drag_to = AsyncMock()
    page.locator = MagicMock(return_value=locator)
    page.goto = AsyncMock()
    page.keyboard = AsyncMock()
    page.keyboard.press = AsyncMock()
    page.mouse = AsyncMock()
    page.mouse.wheel = AsyncMock()
    return page


@pytest.mark.asyncio
async def test_execute_navigate_reads_payload_url() -> None:
    page = _make_fake_page()
    action = ActionInput(action="navigate", payload=NavigateActionPayload(url="https://example.com/target"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.goto.assert_awaited_once_with("https://example.com/target", wait_until="domcontentloaded")


@pytest.mark.asyncio
async def test_execute_click_reads_payload_selector() -> None:
    page = _make_fake_page()
    action = ActionInput(action="click", payload=ClickActionPayload(selector="#submit-btn"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#submit-btn")
    page.locator.return_value.click.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_fill_reads_payload_selector_and_value() -> None:
    page = _make_fake_page()
    action = ActionInput(action="fill", payload=FillActionPayload(selector="#name-input", value="Alice"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#name-input")
    page.locator.return_value.fill.assert_awaited_once_with("Alice")


@pytest.mark.asyncio
async def test_execute_wait_returns_success_without_page_interaction() -> None:
    page = _make_fake_page()
    action = ActionInput(action="wait", payload=WaitActionPayload(duration_ms=3000), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    assert result.detail == "wait 动作已进入等待观察节点处理。"
    page.goto.assert_not_awaited()
    page.locator.assert_not_called()


@pytest.mark.asyncio
async def test_execute_press_calls_keyboard_press() -> None:
    page = _make_fake_page()
    action = ActionInput(action="press", payload=PressActionPayload(key="Enter"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.keyboard.press.assert_awaited_once_with("Enter")


@pytest.mark.asyncio
async def test_execute_scroll_down_calls_mouse_wheel() -> None:
    page = _make_fake_page()
    action = ActionInput(action="scroll", payload=ScrollActionPayload(direction="down", amount=500), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.mouse.wheel.assert_awaited_once_with(0, 500)


@pytest.mark.asyncio
async def test_execute_scroll_up_calls_mouse_wheel_negative() -> None:
    page = _make_fake_page()
    action = ActionInput(action="scroll", payload=ScrollActionPayload(direction="up", amount=300), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.mouse.wheel.assert_awaited_once_with(0, -300)


@pytest.mark.asyncio
async def test_execute_upload_calls_set_input_files() -> None:
    page = _make_fake_page()
    action = ActionInput(action="upload", payload=UploadActionPayload(selector="#file-input", file_paths=["/tmp/test.pdf"]), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#file-input")
    page.locator.return_value.set_input_files.assert_awaited_once_with(["/tmp/test.pdf"])


@pytest.mark.asyncio
async def test_execute_select_calls_select_option() -> None:
    page = _make_fake_page()
    action = ActionInput(action="select", payload=SelectActionPayload(selector="#country", values=["CN"]), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#country")
    page.locator.return_value.select_option.assert_awaited_once_with(["CN"])


@pytest.mark.asyncio
async def test_execute_hover_calls_locator_hover() -> None:
    page = _make_fake_page()
    action = ActionInput(action="hover", payload=HoverActionPayload(selector="#menu-item"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#menu-item")
    page.locator.return_value.hover.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_check_calls_locator_check() -> None:
    page = _make_fake_page()
    action = ActionInput(action="check", payload=CheckActionPayload(selector="#agree-checkbox"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#agree-checkbox")
    page.locator.return_value.check.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_uncheck_calls_locator_uncheck() -> None:
    page = _make_fake_page()
    action = ActionInput(action="uncheck", payload=UncheckActionPayload(selector="#agree-checkbox"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#agree-checkbox")
    page.locator.return_value.uncheck.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_dblclick_calls_locator_dblclick() -> None:
    page = _make_fake_page()
    action = ActionInput(action="dblclick", payload=DblclickActionPayload(selector="#item"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    page.locator.assert_called_once_with("#item")
    page.locator.return_value.dblclick.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_drag_calls_drag_to() -> None:
    page = _make_fake_page()
    action = ActionInput(action="drag", payload=DragActionPayload(start_selector="#source", end_selector="#target"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    assert page.locator.call_count == 2
    page.locator.return_value.drag_to.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_ask_for_help_returns_terminal_detail() -> None:
    page = _make_fake_page()
    action = ActionInput(action="ask_for_help", payload=AskForHelpPayload(message="找不到提交按钮"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    assert "找不到提交按钮" in result.detail
    assert result.action == "ask_for_help"
    page.locator.assert_not_called()


@pytest.mark.asyncio
async def test_execute_abandon_returns_terminal_detail() -> None:
    page = _make_fake_page()
    action = ActionInput(action="abandon", payload=AbandonPayload(reason="任务太难"), reason="test")
    result = await execute_action(page, action)
    assert result.success is True
    assert "任务太难" in result.detail
    assert result.action == "abandon"
    page.locator.assert_not_called()


def test_terminal_actions_contains_ask_for_help_and_abandon() -> None:
    assert "ask_for_help" in TERMINAL_ACTIONS
    assert "abandon" in TERMINAL_ACTIONS
    assert "navigate" not in TERMINAL_ACTIONS