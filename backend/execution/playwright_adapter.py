from __future__ import annotations

# ============================ Playwright 执行模块 ============================ #
# 使用技术栈: Python / Playwright
# 模块功能: 创建浏览器会话并执行受控动作
# 模块数据流: ActionInput -> execute_action() -> ExecutionResult
# 模块接口说明: create_browser_session/close_browser_session/execute_action 为执行层核心入口

import logging
from typing import Any

from backend.schemas.run_schemas import ActionInput, ExecutionResult

logger = logging.getLogger(__name__)

# 创建浏览器会话
async def create_browser_session(headless: bool) -> dict[str, Any]:
    """返回新的浏览器会话对象。"""

    from playwright.async_api import async_playwright  # 延迟导入

    logger.info("creating browser session, headless=%s", headless)
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)  # 启动 Chromium 浏览器
        page = await browser.new_page()  # 创建一个新页面标签页
        return {"playwright": playwright, "browser": browser, "page": page}
    except Exception:
        logger.exception("failed to create browser session")
        raise

# 清理 Playwright 资源
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

# page: Playwright 页面对象, action: 要执行的动作
async def execute_action(page: Any, action: ActionInput) -> ExecutionResult:
    """执行单个受控动作并返回结果。"""

    try:
        if action.action == "navigate":  # 跳转到目标 URL
            if action.target is None:
                raise ValueError("navigate action requires target.")
            await page.goto(action.target, wait_until="domcontentloaded")
        elif action.action == "click":  # 找到目标元素并点击
            if action.target is None:
                raise ValueError("click action requires target.")
            await page.locator(action.target).click()
        elif action.action == "fill":  # 向输入框填写
            if action.target is None:
                raise ValueError("fill action requires target.")
            await page.locator(action.target).fill(str(action.value or ""))
        elif action.action == "wait":  # 等待动作交由 graph 等待观察节点处理
            pass
        else:  # 其他不支持动作直接报错
            raise ValueError(f"Unsupported action: {action.action}")

        detail = "wait 动作已进入等待观察节点处理。" if action.action == "wait" else f"动作 {action.action} 执行成功。"
        return ExecutionResult(
            action=action.action,
            success=True,
            detail=detail,
        )
    except Exception as exc:
        return ExecutionResult(
            action=action.action,
            success=False,
            detail=f"动作 {action.action} 执行失败。",
            error_message=str(exc),
        )
