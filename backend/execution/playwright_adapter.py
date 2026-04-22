from __future__ import annotations

# ============================ Playwright 执行模块 ============================ #
# 使用技术栈: Python / Playwright
# 模块功能: 创建浏览器会话并执行受控动作
# 模块数据流: ActionInput -> execute_action() -> ExecutionResult
# 模块接口说明: create_browser_session/close_browser_session/execute_action 为执行层核心入口

from pathlib import Path
from typing import Any

from backend.schemas.run_schemas import ActionInput, ExecutionResult


async def create_browser_session(headless: bool) -> dict[str, Any]:
    """返回新的浏览器会话对象。"""

    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    page = await browser.new_page()
    return {"playwright": playwright, "browser": browser, "page": page}


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


async def execute_action(page: Any, action: ActionInput, screenshot_path: Path | None = None) -> ExecutionResult:
    """执行单个受控动作并返回结果。"""

    try:
        if action.action == "navigate":
            await page.goto(action.target, wait_until="domcontentloaded")
        elif action.action == "click":
            await page.locator(action.target).click()
        elif action.action == "fill":
            await page.locator(action.target).fill(action.value or "")
        elif action.action == "wait":
            timeout_ms = int(action.value or "300")
            await page.wait_for_timeout(timeout_ms)
        else:
            raise ValueError(f"Unsupported action: {action.action}")

        screenshot_value = None
        if screenshot_path is not None:
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path), full_page=True)
            screenshot_value = str(screenshot_path)

        return ExecutionResult(
            action=action.action,
            success=True,
            detail=f"动作 {action.action} 执行成功。",
            screenshot_path=screenshot_value,
            current_url_after_action=page.url,
        )
    except Exception as exc:
        screenshot_value = None
        if screenshot_path is not None:
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path), full_page=True)
            screenshot_value = str(screenshot_path)

        return ExecutionResult(
            action=action.action,
            success=False,
            detail=f"动作 {action.action} 执行失败。",
            screenshot_path=screenshot_value,
            current_url_after_action=page.url,
            error_message=str(exc),
        )
