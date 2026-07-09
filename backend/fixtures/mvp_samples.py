"""MVP 验收样例数据：3 个 persona + 3 个 task。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.core.config import get_settings
from backend.schemas.persona_schemas import Persona, PersonaCreate
from backend.schemas.task_schemas import Task, TaskCreate

if TYPE_CHECKING:
    from backend.stores.entity_store_protocol import EntityStore

# 测试站点 ShopLab 的 base_url，运行时解析为 app_base_url + /site。
_TEST_SITE_BASE = str(get_settings().app_base_url).rstrip("/") + "/site"

# ============================ Persona 样例 ============================ #

PERSONA_NEWBIE = PersonaCreate(
    name="新手用户",
    description=(
        "22岁大学生，首次使用类似产品，不熟悉行业术语。"
        "操作习惯：倾向于点击醒目按钮，不太会主动寻找帮助文档，遇到复杂表单容易放弃。"
        "期望：界面简单直观，每一步都有明确提示，错误信息友好。"
    ),
    skill_level="newbie",
    patience_level="low",
    risk_preference="low",
)

PERSONA_EXPERT = PersonaCreate(
    name="专家用户",
    description=(
        "35岁互联网从业者，熟悉各类产品，追求效率。"
        "操作习惯：优先使用快捷键和批量操作，会主动查找高级功能，不喜欢冗余提示。"
        "期望：快速完成任务，提供键盘导航和批量操作入口，避免强制引导。"
    ),
    skill_level="expert",
    patience_level="high",
    risk_preference="high",
)

PERSONA_ELDERLY = PersonaCreate(
    name="老年用户",
    description=(
        "62岁退休人员，智能手机使用经验有限，容易误触。"
        "操作习惯：反应较慢，需要多次确认，容易点错按钮，不熟悉滚动和拖拽操作。"
        "期望：按钮足够大，操作有二次确认，提供撤销功能，避免复杂交互。"
    ),
    skill_level="newbie",
    patience_level="medium",
    risk_preference="low",
)

# ============================ Task 样例 ============================ #
# 三个 task 指向自托管测试站点 ShopLab 的不同子流程，覆盖从浏览到结算的完整购物链路。
# start_url 在模块导入时由 _TEST_SITE_BASE（app_base_url + /site）解析为绝对地址，
# 因 TaskCreate.start_url 校验器要求 http(s) 前缀，故不支持相对路径。
# ShopLab 站点内故意埋入 4 个 UX 摩擦点：
#   1. 商品页优惠券输入框错误提示模糊（"操作失败，请重试"）
#   2. 结算页默认勾选加急配送，运费 ¥25 默认计入总价（隐藏费用）
#   3. 结算页表单校验失败时只显示"出错了，请检查后重试"，不指明哪个字段
#   4. 结算页验证码提示埋在页面底部，需滚动可见且远离输入框（验证码 8204）

TASK_BROWSE_PURCHASE = TaskCreate(
    name="浏览商品并完成下单",
    description="从首页进入商品详情页，点击立即购买，填写收货地址与支付信息，完成下单流程。",
    start_url=f"{_TEST_SITE_BASE}/index.html",
    success_criteria=[
        "页面显示「支付成功」提示",
        "页面显示订单号",
        "页面显示已支付金额",
    ],
    max_steps=15,
    allowed_actions=[
        "navigate", "click", "fill", "wait",
        "scroll", "press", "select",
    ],
    risk_level="medium",
    # ShopLab 是自托管测试站点，购买/支付/结算是任务本身要测的流程；
    # 护栏的 DESTRUCTIVE_BUTTON_PATTERNS 会命中"购买/支付/结算"关键词，
    # 故此处放行，让 action_guard 的"按 task 开关"设计真正生效。
    destructive_action_allowed=True,
)

TASK_USE_COUPON = TaskCreate(
    name="使用优惠券购买商品",
    description="进入商品详情页，尝试使用优惠券码 SHOP10 享受优惠，然后进入结算完成下单。",
    start_url=f"{_TEST_SITE_BASE}/product.html",
    success_criteria=[
        "优惠券提示「优惠券已应用」",
        "页面显示「支付成功」",
        "页面显示已支付金额",
    ],
    max_steps=15,
    allowed_actions=[
        "navigate", "click", "fill", "wait",
        "scroll", "press",
    ],
    risk_level="low",
    destructive_action_allowed=True,
)

TASK_CHECKOUT_FORM = TaskCreate(
    name="填写结算表单完成支付",
    description="进入结算页面，填写姓名、手机号、地址与支付账号，选择配送方式后完成支付。",
    start_url=f"{_TEST_SITE_BASE}/checkout.html",
    success_criteria=[
        "页面显示「支付成功」",
        "页面显示订单号",
        "页面显示已支付金额",
    ],
    max_steps=12,
    allowed_actions=[
        "navigate", "click", "fill", "wait",
        "scroll", "press", "select",
    ],
    risk_level="low",
    destructive_action_allowed=True,
)

# ============================ 样例数据集合 ============================ #

MVP_PERSONAS = [PERSONA_NEWBIE, PERSONA_EXPERT, PERSONA_ELDERLY]
MVP_TASKS = [TASK_BROWSE_PURCHASE, TASK_USE_COUPON, TASK_CHECKOUT_FORM]


def get_mvp_personas() -> list[PersonaCreate]:
    """获取 MVP 验收样例 persona 列表。"""
    return MVP_PERSONAS


def get_mvp_tasks() -> list[TaskCreate]:
    """获取 MVP 验收样例 task 列表。start_url 已解析为指向测试站点 ShopLab 的绝对地址。"""
    return MVP_TASKS


def seed_mvp_samples_if_absent(entity_store: EntityStore) -> tuple[int, int]:
    """幂等 seed MVP 样例 persona/task 到 entity_store，返回 (新建 persona 数, 新建 task 数)。

    PersonaCreate/TaskCreate 无 id，无法按 id 判断是否已存在，故用 list + name 匹配做幂等。
    被 main.py lifespan（启动自动 seed）与 scripts/seed_mvp_samples.py（手动 re-seed）共用。
    """

    existing_persona_names = {p.name for p in entity_store.list_personas()}
    existing_task_names = {t.name for t in entity_store.list_tasks()}

    created_personas = 0
    for persona_create in get_mvp_personas():
        if persona_create.name in existing_persona_names:
            continue
        entity_store.create_persona(Persona.model_validate(persona_create.model_dump()))
        created_personas += 1

    created_tasks = 0
    for task_create in get_mvp_tasks():
        if task_create.name in existing_task_names:
            continue
        entity_store.create_task(Task.model_validate(task_create.model_dump()))
        created_tasks += 1

    return created_personas, created_tasks
