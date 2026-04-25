from __future__ import annotations

import asyncio
from typing import Any, cast

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate


async def try_agent_input(label: str, agent: Any, messages_value: Any) -> None:
    try:
        result = await agent.ainvoke(cast(Any, {"messages": messages_value}))
        print(f"{label}: 成功, 返回键={list(result.keys())}")
    except Exception as exc:
        print(f"{label}: 报错, {type(exc).__name__}: {exc}")


async def main() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个测试助手。"),
            ("user", "请复述这个主题：{topic}"),
        ]
    )

    prompt_value = await prompt.ainvoke({"topic": "ChatPromptTemplate"})
    converted_messages = prompt_value.to_messages()
    formatted_messages = prompt.format_messages(topic="ChatPromptTemplate")

    print("prompt.ainvoke 返回类型:", type(prompt_value).__name__)
    print("to_messages 返回类型:", type(converted_messages).__name__)
    print("format_messages 返回类型:", type(formatted_messages).__name__)

    agent = create_agent(
        model=FakeListChatModel(responses=["direct ok", "converted ok", "formatted ok"]),
        tools=[],
    )

    await try_agent_input("直接传 ChatPromptValue", agent, prompt_value)
    await try_agent_input("传 prompt_value.to_messages()", agent, converted_messages)
    await try_agent_input("传 prompt.format_messages()", agent, formatted_messages)


if __name__ == "__main__":
    asyncio.run(main())
