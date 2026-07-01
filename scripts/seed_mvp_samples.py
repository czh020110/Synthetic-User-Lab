#!/usr/bin/env python3
"""初始化 MVP 验收样例数据到 EntityStore。

使用方式：
    python scripts/seed_mvp_samples.py

说明：
    - 会创建 3 个 persona（新手/专家/老年用户）
    - 会创建 3 个 task（注册/购物/设置）
    - 已存在的实体会跳过（基于 ID 判断）
    - 可重复运行，幂等操作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.fixtures.mvp_samples import get_mvp_personas, get_mvp_tasks
from backend.schemas.persona_schemas import Persona
from backend.schemas.task_schemas import Task
from backend.stores import get_entity_store


async def seed_mvp_samples() -> None:
    """初始化 MVP 验收样例数据。"""
    entity_store = get_entity_store()

    print("开始初始化 MVP 验收样例数据...")

    # 初始化 persona
    personas = get_mvp_personas()
    created_personas = 0

    for persona_create in personas:
        # 检查是否已存在同名 persona
        existing = entity_store.list_personas()
        if any(p.name == persona_create.name for p in existing):
            print(f"  ⏭️  Persona '{persona_create.name}' 已存在，跳过")
            continue

        # 转换为 Persona 实体
        persona = Persona(**persona_create.model_dump())
        persona = entity_store.create_persona(persona)
        print(f"  ✅ 创建 Persona: {persona.name} (ID: {persona.id})")
        created_personas += 1

    # 初始化 task
    tasks = get_mvp_tasks()
    created_tasks = 0

    for task_create in tasks:
        # 检查是否已存在同名 task
        existing = entity_store.list_tasks()
        if any(t.name == task_create.name for t in existing):
            print(f"  ⏭️  Task '{task_create.name}' 已存在，跳过")
            continue

        # 转换为 Task 实体
        task = Task(**task_create.model_dump())
        task = entity_store.create_task(task)
        print(f"  ✅ 创建 Task: {task.name} (ID: {task.id})")
        created_tasks += 1

    print(f"\n✨ 初始化完成：")
    print(f"   - 创建了 {created_personas} 个 Persona（共 {len(personas)} 个样例）")
    print(f"   - 创建了 {created_tasks} 个 Task（共 {len(tasks)} 个样例）")

    # 显示当前实体总数
    all_personas = entity_store.list_personas()
    all_tasks = entity_store.list_tasks()
    print(f"\n📊 当前实体总数：")
    print(f"   - Persona: {len(all_personas)}")
    print(f"   - Task: {len(all_tasks)}")


if __name__ == "__main__":
    asyncio.run(seed_mvp_samples())
