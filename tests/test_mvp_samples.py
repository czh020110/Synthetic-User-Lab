import pytest

from backend.fixtures.mvp_samples import get_mvp_personas, get_mvp_tasks


def test_mvp_personas_count():
    """验证 MVP persona 样例数量。"""
    personas = get_mvp_personas()
    assert len(personas) == 3


def test_mvp_personas_have_required_fields():
    """验证 MVP persona 样例包含必填字段。"""
    personas = get_mvp_personas()

    for persona_create in personas:
        assert persona_create.name
        assert persona_create.description
        assert persona_create.skill_level in ["newbie", "intermediate", "expert"]
        assert persona_create.patience_level in ["low", "medium", "high"]
        assert persona_create.risk_preference in ["low", "medium", "high"]


def test_mvp_tasks_count():
    """验证 MVP task 样例数量。"""
    tasks = get_mvp_tasks()
    assert len(tasks) == 3


def test_mvp_tasks_have_required_fields():
    """验证 MVP task 样例包含必填字段。"""
    tasks = get_mvp_tasks()

    for task_create in tasks:
        assert task_create.name
        assert task_create.description
        assert task_create.start_url.startswith("https://")
        assert len(task_create.success_criteria) > 0
        assert task_create.max_steps >= 1
        assert len(task_create.allowed_actions) > 0
        assert task_create.risk_level in ["low", "medium", "high"]
        assert task_create.destructive_action_allowed is False


def test_mvp_personas_diversity():
    """验证 MVP persona 样例覆盖不同用户群体。"""
    personas = get_mvp_personas()

    names = [p.name for p in personas]
    assert "新手用户" in names
    assert "专家用户" in names
    assert "老年用户" in names

    # 验证技能水平差异
    skill_levels = [p.skill_level for p in personas]
    assert "newbie" in skill_levels
    assert "expert" in skill_levels


def test_mvp_tasks_diversity():
    """验证 MVP task 样例覆盖不同场景。"""
    tasks = get_mvp_tasks()

    names = [t.name for t in tasks]
    assert "注册新账号" in names
    assert "添加商品到购物车" in names
    assert "修改个人设置" in names

    # 验证风险等级差异
    risk_levels = [t.risk_level for t in tasks]
    assert "low" in risk_levels
    assert "medium" in risk_levels
