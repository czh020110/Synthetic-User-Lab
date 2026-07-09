#!/usr/bin/env python3
"""初始化 MVP 验收样例数据到 EntityStore。

使用方式：
    python scripts/seed_mvp_samples.py

说明：
    - 会创建 3 个 persona（新手/专家/老年用户）
    - 会创建 3 个 task（浏览下单/优惠券/结算表单）
    - 已存在的实体会跳过（按 name 判断）
    - 可重复运行，幂等操作
    - 与 main.py lifespan 启动 seed 共用同一逻辑（seed_mvp_samples_if_absent）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.fixtures.mvp_samples import seed_mvp_samples_if_absent
from backend.stores import get_entity_store


async def seed_mvp_samples() -> None:
    """初始化 MVP 验收样例数据。"""

    print("开始初始化 MVP 验收样例数据...")
    created_personas, created_tasks = seed_mvp_samples_if_absent(get_entity_store())

    all_personas = get_entity_store().list_personas()
    all_tasks = get_entity_store().list_tasks()
    print(f"\n✨ 初始化完成：新建 {created_personas} 个 Persona、{created_tasks} 个 Task")
    print(f"📊 当前实体总数：Persona {len(all_personas)} / Task {len(all_tasks)}")


if __name__ == "__main__":
    asyncio.run(seed_mvp_samples())
