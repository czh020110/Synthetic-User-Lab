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
        assert task_create.start_url.startswith("http://") or task_create.start_url.startswith("https://")
        assert "/site/" in task_create.start_url
        assert len(task_create.success_criteria) > 0
        assert task_create.max_steps >= 1
        assert len(task_create.allowed_actions) > 0
        assert task_create.risk_level in ["low", "medium", "high"]
        # ShopLab 是自托管测试站点，购买/支付/结算是任务本身要测的流程，
        # 护栏会误拦这些关键词，故 MVP task 放行高风险动作。
        assert task_create.destructive_action_allowed is True


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
    assert "浏览商品并完成下单" in names
    assert "使用优惠券购买商品" in names
    assert "填写结算表单完成支付" in names

    # 验证风险等级差异
    risk_levels = [t.risk_level for t in tasks]
    assert "low" in risk_levels
    assert "medium" in risk_levels
