"""MVP 验收样例数据：3 个 persona + 3 个 task。"""

from backend.schemas.persona_schemas import Persona, PersonaCreate
from backend.schemas.task_schemas import Task, TaskCreate

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

TASK_REGISTRATION = TaskCreate(
    name="注册新账号",
    description="访问注册页面，填写必填信息（用户名、邮箱、密码），完成注册流程。",
    start_url="https://example.com/register",
    success_criteria=[
        "页面显示「注册成功」或「欢迎」提示",
        "页面跳转到个人中心或首页",
        "能看到已登录状态标识",
    ],
    max_steps=10,
    allowed_actions=[
        "navigate", "click", "fill", "wait",
        "scroll", "press", "check",
    ],
    risk_level="low",
    destructive_action_allowed=False,
)

TASK_SHOPPING = TaskCreate(
    name="添加商品到购物车",
    description="浏览商品列表，选择一个商品，点击加入购物车，确认购物车中有该商品。",
    start_url="https://example.com/products",
    success_criteria=[
        "购物车图标显示数量增加",
        "页面提示「已加入购物车」",
        "点击购物车可以看到刚添加的商品",
    ],
    max_steps=12,
    allowed_actions=[
        "navigate", "click", "fill", "wait",
        "scroll", "hover", "press",
    ],
    risk_level="medium",
    destructive_action_allowed=False,
)

TASK_SETTINGS = TaskCreate(
    name="修改个人设置",
    description="进入个人设置页面，修改昵称或头像，保存设置。",
    start_url="https://example.com/settings",
    success_criteria=[
        "页面提示「保存成功」或「设置已更新」",
        "返回设置页面可以看到修改后的内容",
        "没有报错提示",
    ],
    max_steps=15,
    allowed_actions=[
        "navigate", "click", "fill", "wait",
        "scroll", "press", "upload", "select",
    ],
    risk_level="low",
    destructive_action_allowed=False,
)

# ============================ 样例数据集合 ============================ #

MVP_PERSONAS = [PERSONA_NEWBIE, PERSONA_EXPERT, PERSONA_ELDERLY]
MVP_TASKS = [TASK_REGISTRATION, TASK_SHOPPING, TASK_SETTINGS]


def get_mvp_personas() -> list[PersonaCreate]:
    """获取 MVP 验收样例 persona 列表。"""
    return MVP_PERSONAS


def get_mvp_tasks() -> list[TaskCreate]:
    """获取 MVP 验收样例 task 列表。"""
    return MVP_TASKS
