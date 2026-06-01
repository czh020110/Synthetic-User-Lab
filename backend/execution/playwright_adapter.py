from __future__ import annotations

import logging
from typing import Any

from backend.schemas.run_schemas import (
    AbandonPayload,
    ActionInput,
    AskForHelpPayload,
    CheckActionPayload,
    ClickActionPayload,
    DblclickActionPayload,
    DragActionPayload,
    ExecutionResult,
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

logger = logging.getLogger(__name__)

# ============================ 浏览器会话管理 ============================ #


async def create_browser_session(headless: bool) -> dict[str, Any]:
    """返回新的浏览器会话对象。"""

    from playwright.async_api import async_playwright

    logger.info("creating browser session, headless=%s", headless)
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        return {"playwright": playwright, "browser": browser, "page": page}
    except Exception:
        logger.exception("failed to create browser session")
        raise


async def close_browser_session(session: dict[str, Any] | None) -> None:
    """关闭浏览器会话。"""

    if not session:
        return

    browser = session.get("browser")
    playwright = session.get("playwright")

    if browser is not None:
        await browser.close()
    if playwright is not None:
        await playwright.stop()


# ============================ 受控动作执行 ============================ #

TERMINAL_ACTIONS = {"ask_for_help", "abandon"}


async def execute_action(page: Any, action: ActionInput) -> ExecutionResult:
    """执行单个受控动作并返回结果。"""

    payload = action.payload
    try:
        if action.action == "navigate":
            if not isinstance(payload, NavigateActionPayload):
                raise ValueError("navigate action requires NavigateActionPayload.")
            await page.goto(payload.url, wait_until="domcontentloaded")
        elif action.action == "click":
            if not isinstance(payload, ClickActionPayload):
                raise ValueError("click action requires ClickActionPayload.")
            await page.locator(payload.selector).click()
        elif action.action == "fill":
            if not isinstance(payload, FillActionPayload):
                raise ValueError("fill action requires FillActionPayload.")
            await page.locator(payload.selector).fill(payload.value)
        elif action.action == "wait":
            pass
        elif action.action == "press":
            if not isinstance(payload, PressActionPayload):
                raise ValueError("press action requires PressActionPayload.")
            await page.keyboard.press(payload.key)
        elif action.action == "scroll":
            if not isinstance(payload, ScrollActionPayload):
                raise ValueError("scroll action requires ScrollActionPayload.")
            delta = payload.amount if payload.direction == "down" else -payload.amount
            await page.mouse.wheel(0, delta)
        elif action.action == "upload":
            if not isinstance(payload, UploadActionPayload):
                raise ValueError("upload action requires UploadActionPayload.")
            await page.locator(payload.selector).set_input_files(payload.file_paths)
        elif action.action == "select":
            if not isinstance(payload, SelectActionPayload):
                raise ValueError("select action requires SelectActionPayload.")
            await page.locator(payload.selector).select_option(payload.values)
        elif action.action == "hover":
            if not isinstance(payload, HoverActionPayload):
                raise ValueError("hover action requires HoverActionPayload.")
            await page.locator(payload.selector).hover()
        elif action.action == "check":
            if not isinstance(payload, CheckActionPayload):
                raise ValueError("check action requires CheckActionPayload.")
            await page.locator(payload.selector).check()
        elif action.action == "uncheck":
            if not isinstance(payload, UncheckActionPayload):
                raise ValueError("uncheck action requires UncheckActionPayload.")
            await page.locator(payload.selector).uncheck()
        elif action.action == "dblclick":
            if not isinstance(payload, DblclickActionPayload):
                raise ValueError("dblclick action requires DblclickActionPayload.")
            await page.locator(payload.selector).dblclick()
        elif action.action == "drag":
            if not isinstance(payload, DragActionPayload):
                raise ValueError("drag action requires DragActionPayload.")
            start = page.locator(payload.start_selector)
            end = page.locator(payload.end_selector)
            await start.drag_to(end)
        elif action.action == "ask_for_help":
            if not isinstance(payload, AskForHelpPayload):
                raise ValueError("ask_for_help action requires AskForHelpPayload.")
        elif action.action == "abandon":
            if not isinstance(payload, AbandonPayload):
                raise ValueError("abandon action requires AbandonPayload.")
        else:
            raise ValueError(f"Unsupported action: {action.action}")

        if action.action == "wait":
            detail = "wait 动作已进入等待观察节点处理。"
        elif action.action == "ask_for_help" and isinstance(payload, AskForHelpPayload):
            detail = f"用户请求帮助：{payload.message}"
        elif action.action == "abandon" and isinstance(payload, AbandonPayload):
            detail = f"用户放弃任务：{payload.reason}"
        else:
            detail = f"动作 {action.action} 执行成功。"

        return ExecutionResult(action=action.action, success=True, detail=detail)
    except Exception as exc:
        return ExecutionResult(
            action=action.action,
            success=False,
            detail=f"动作 {action.action} 执行失败。",
            error_message=str(exc),
        )