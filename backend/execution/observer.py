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
        r"() => (document.body?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 1200)"
    )
    clickable_elements = await page.evaluate(
        """
        () => {
            // button/input[type=submit] 优先，a 和 role=button 靠后
            const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'));
            const links = Array.from(document.querySelectorAll('a, [role="button"]'));
            const all = [...buttons, ...links];
            const visible = all.filter((el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length));
            return visible.slice(0, 30).map((element, index) => {
                let selector;
                if (element.id) {
                    selector = `#${CSS.escape(element.id)}`;
                } else if (element.getAttribute('data-testid')) {
                    selector = `[data-testid="${CSS.escape(element.getAttribute('data-testid'))}"]`;
                } else {
                    selector = `[data-clickable-index="${index}"]`;
                    element.setAttribute('data-clickable-index', String(index));
                }
                return {
                    text: (element.innerText || element.textContent || '').trim(),
                    selector,
                };
            });
        }
        """
    )
    form_fields = await page.evaluate(
        """
        () => Array.from(document.querySelectorAll('input, textarea, select'))
            .filter((element) => !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length))
            .slice(0, 20)
            .map((element, index) => {
                // name 取语义来源：html name 属性 > id > aria-label > placeholder，便于 LLM 区分字段
                const attrName = element.getAttribute('name') || element.id || element.getAttribute('aria-label') || element.getAttribute('placeholder') || '';
                // selector 优先用稳定的全局唯一定位符；id/name 缺失时回退到主动注入的 data-form-field-index，
                // 避免 nth-of-type 在多父容器下同时匹配多个元素导致 Playwright strict mode violation。
                let selector;
                if (element.id) {
                    selector = `#${CSS.escape(element.id)}`;
                } else if (element.getAttribute('name')) {
                    const tagName = element.tagName.toLowerCase();
                    selector = `${tagName}[name="${CSS.escape(element.getAttribute('name'))}"]`;
                } else {
                    selector = `[data-form-field-index="${index}"]`;
                    element.setAttribute('data-form-field-index', String(index));
                }
                return {
                    name: attrName || `field-${element.tagName.toLowerCase()}`,
                    selector,
                    value: element.value || '',
                };
            })
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
