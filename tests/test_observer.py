from __future__ import annotations

import asyncio

from backend.execution.observer import observe_page


class FakeObserverPage:
    url = "http://testserver/demo/index.html"

    async def title(self) -> str:
        return "demo"

    async def evaluate(self, script: str):
        if "document.body?.innerText" in script:
            return "开始 姓名"
        if "button" in script and "input[type=\"submit\"]" in script:
            return [
                {"text": "开始", "selector": "#btn-start"},
                {"text": "继续", "selector": "#continue-button"},
            ]
        if "input, textarea, select" in script:
            return [
                {"name": "name", "selector": 'input[name="name"]', "value": ""},
                {"name": "email", "selector": "#email", "value": ""},
            ]
        if ".error-message" in script:
            return []
        raise AssertionError(f"unexpected script: {script}")


def test_observe_page_returns_executable_selectors() -> None:
    page_state = asyncio.run(observe_page(FakeObserverPage()))

    assert [element.selector for element in page_state.clickable_elements] == [
        "#btn-start",
        "#continue-button",
    ]
    assert [field.selector for field in page_state.form_fields] == [
        'input[name="name"]',
        "#email",
    ]
    assert all(":visible-" not in element.selector for element in page_state.clickable_elements)
    assert all('" ]' not in field.selector for field in page_state.form_fields)
