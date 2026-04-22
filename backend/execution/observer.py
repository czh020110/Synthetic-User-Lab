from __future__ import annotations

# ============================ 页面观察模块 ============================ #
# 使用技术栈: Python / Playwright
# 模块功能: 从真实页面采集 URL、标题、可点击元素、表单字段和错误信息
# 模块数据流: Page -> observe_page() -> ObservedPageState
# 模块接口说明: observe_page(page) 返回当前页面状态摘要

from typing import Any

from backend.schemas.run_schemas import FormFieldState, ObservedElement, ObservedPageState


async def observe_page(page: Any) -> ObservedPageState:
    """返回当前页面的结构化观察结果。"""

    title = await page.title()
    visible_text = await page.evaluate(
        r"() => (document.body?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600)"
    )
    clickable_elements = await page.evaluate(
        """
        () => Array.from(document.querySelectorAll('button, a, [role="button"]'))
            .filter((element) => !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length))
            .slice(0, 10)
            .map((element, index) => ({
                text: (element.innerText || element.textContent || '').trim(),
                selector: element.id
                    ? `#${element.id}`
                    : `${element.tagName.toLowerCase()}:visible-${index + 1}`,
            }))
        """
    )
    form_fields = await page.evaluate(
        """
        () => Array.from(document.querySelectorAll('input, textarea, select'))
            .slice(0, 10)
            .map((element, index) => ({
                name: element.getAttribute('name') || element.id || `field-${index + 1}`,
                selector: element.id
                    ? `#${element.id}`
                    : `[name="${element.getAttribute('name') || `field-${index + 1}`}" ]`,
                value: element.value || '',
            }))
        """
    )
    error_messages = await page.evaluate(
        """
        () => Array.from(document.querySelectorAll('.error-message, [role="alert"], [data-error="true"]'))
            .filter((element) => !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length))
            .map((element) => (element.innerText || element.textContent || '').trim())
            .filter(Boolean)
            .slice(0, 5)
        """
    )

    return ObservedPageState(
        current_url=page.url,
        title=title,
        visible_text_summary=visible_text,
        clickable_elements=[ObservedElement(**item) for item in clickable_elements],
        form_fields=[FormFieldState(**item) for item in form_fields],
        error_messages=error_messages,
    )
