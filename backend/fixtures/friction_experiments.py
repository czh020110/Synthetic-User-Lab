"""多 persona 摩擦实验 fixture。"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.fixtures.mvp_samples import (
    PERSONA_ELDERLY,
    PERSONA_EXPERT,
    PERSONA_NEWBIE,
    TASK_CHECKOUT_FORM,
    TASK_USE_COUPON,
)
from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    ExecutionResult,
    ObservedPageState,
    ReportConclusion,
    StepLog,
    ValidationResult,
    ValidationStatus,
)

CHECKOUT_URL = str(TASK_CHECKOUT_FORM.start_url)
PRODUCT_URL = str(TASK_USE_COUPON.start_url)
SUCCESS_URL = CHECKOUT_URL.rsplit("/", 1)[0] + "/success.html"

KNOWN_EXPERIMENT_FRICTION_SIGNALS = {
    "action_failed",
    "page_error",
    "step_limit_reached",
    "repeated_wait",
    "repeated_action_target",
    "stuck_page",
    "off_track_navigation",
    "recovery_candidate",
}


@dataclass(frozen=True)
class ScriptedExperimentStep:
    action: ActionName
    payload: dict[str, object]
    reason: str
    progress_summary: str
    before_url: str
    before_text: str
    after_url: str | None = None
    after_text: str | None = None
    status: ValidationStatus = "running"
    should_stop: bool = False
    friction_signals: tuple[str, ...] = ()
    detected_success: bool = False
    detected_error: bool = False
    execution_success: bool = True
    execution_detail: str = "动作已执行。"
    execution_error_message: str | None = None
    before_error_messages: tuple[str, ...] = ()
    after_error_messages: tuple[str, ...] = ()

    def to_step_log(self, index: int) -> StepLog:
        after_url = self.after_url or self.before_url
        after_text = self.after_text if self.after_text is not None else self.before_text
        return StepLog(
            step_index=index,
            observed_page_state=ObservedPageState(
                current_url=self.before_url,
                title="ShopLab",
                visible_text_summary=self.before_text,
                error_messages=list(self.before_error_messages),
            ),
            decided_action=ActionInput(action=self.action, payload=self.payload, reason=self.reason),
            execution_result=ExecutionResult(
                action=self.action,
                success=self.execution_success,
                detail=self.execution_detail,
                error_message=self.execution_error_message,
            ),
            validation_result=ValidationResult(
                status=self.status,
                should_stop=self.should_stop,
                progress_summary=self.progress_summary,
                friction_signals=list(self.friction_signals),
                detected_success=self.detected_success,
                detected_error=self.detected_error,
            ),
            post_action_page_state=ObservedPageState(
                current_url=after_url,
                title="ShopLab",
                visible_text_summary=after_text,
                error_messages=list(self.after_error_messages),
            ),
        )


@dataclass(frozen=True)
class FrictionExperiment:
    experiment_id: str
    persona_name: str
    task_name: str
    description: str
    expected_friction_signals: tuple[str, ...]
    expected_conclusion: ReportConclusion
    scripted_steps: tuple[ScriptedExperimentStep, ...] = field(default_factory=tuple)

    def build_steps(self) -> list[StepLog]:
        return [step.to_step_log(index) for index, step in enumerate(self.scripted_steps, start=1)]


FRICTION_EXPERIMENTS = [
    FrictionExperiment(
        experiment_id="E-001",
        persona_name=PERSONA_NEWBIE.name,
        task_name=TASK_CHECKOUT_FORM.name,
        description="新手用户在结算表单中因手机号和验证码提示不清晰而卡住并放弃。",
        expected_friction_signals=("page_error", "recovery_candidate", "stuck_page"),
        expected_conclusion="fix",
        scripted_steps=(
            ScriptedExperimentStep(
                action="fill",
                payload={"selector": "#phone", "value": "1380013"},
                reason="新手用户先填写了自己理解中的手机号。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 姓名 手机号 收货地址 支付账号 验证码 提交订单",
                after_text="结算信息 手机号已填写为 1380013，其他字段仍为空。",
                progress_summary="用户先填写了不完整手机号，继续尝试提交。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#submit-order"},
                reason="用户认为可以直接提交并查看结果。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 手机号=1380013 其余字段为空 确认支付",
                after_text="结算信息 出错了，请检查后重试",
                after_error_messages=("出错了，请检查后重试",),
                progress_summary="点击确认支付后只看到模糊错误提示，无法定位问题字段。",
                friction_signals=("page_error", "recovery_candidate"),
                detected_error=True,
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#submit-order"},
                reason="新手用户没有理解错误原因，直接再次提交。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 出错了，请检查后重试",
                before_error_messages=("出错了，请检查后重试",),
                after_text="结算信息 出错了，请检查后重试",
                after_error_messages=("出错了，请检查后重试",),
                progress_summary="重复提交后仍只看到同样的模糊错误提示，页面没有给出更明确指引。",
                friction_signals=("page_error", "stuck_page", "recovery_candidate"),
                detected_error=True,
            ),
            ScriptedExperimentStep(
                action="abandon",
                payload={"reason": "错误提示不明确，无法继续完成结算。"},
                reason="低耐心 persona 在重复失败后放弃。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 出错了，请检查后重试",
                before_error_messages=("出错了，请检查后重试",),
                progress_summary="用户因模糊错误提示和连续失败放弃结算。",
                status="failed",
                should_stop=True,
                friction_signals=("stuck_page",),
                detected_error=True,
            ),
        ),
    ),
    FrictionExperiment(
        experiment_id="E-002",
        persona_name=PERSONA_EXPERT.name,
        task_name=TASK_CHECKOUT_FORM.name,
        description="专家用户会检查配送费用、滚动查看验证码提示并一次完成结算。",
        expected_friction_signals=(),
        expected_conclusion="keep",
        scripted_steps=(
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "[data-testid=\"ship-standard\"]"},
                reason="专家用户发现默认加急配送会增加费用，改选标准配送。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 默认勾选加急配送 ¥25 标准配送 免费",
                after_text="结算信息 已切换为标准配送 免费。",
                progress_summary="用户主动检查并修正了默认配送选项。",
            ),
            ScriptedExperimentStep(
                action="scroll",
                payload={"direction": "down", "amount": 600},
                reason="专家用户滚动页面查找验证码提示。",
                before_url=CHECKOUT_URL,
                before_text="验证码提示位于页面底部，当前尚未看到具体验证码。",
                after_text="页面底部显示验证码提示：8204。",
                progress_summary="用户滚动到页面底部，找到验证码提示。",
            ),
            ScriptedExperimentStep(
                action="fill",
                payload={"selector": "#verify-code", "value": "8204"},
                reason="姓名、手机号、地址和支付账号已准备好，补充正确验证码。",
                before_url=CHECKOUT_URL,
                before_text="姓名、手机号、详细地址、支付账号均已填写，待填写验证码 8204。",
                after_text="验证码已填写为 8204。",
                progress_summary="用户根据页面提示补齐验证码，准备提交订单。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#submit-order"},
                reason="所有必填项与验证码已确认，提交订单。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 标准配送 免费 所有字段已填写 验证码 8204",
                after_url=SUCCESS_URL,
                after_text="支付成功 订单号 已支付金额",
                status="succeeded",
                should_stop=True,
                detected_success=True,
                progress_summary="页面显示支付成功、订单号和已支付金额，任务完成。",
            ),
        ),
    ),
    FrictionExperiment(
        experiment_id="E-003",
        persona_name=PERSONA_ELDERLY.name,
        task_name=TASK_USE_COUPON.name,
        description="老年用户多次尝试优惠券码才找到正确输入。",
        expected_friction_signals=("page_error", "recovery_candidate"),
        expected_conclusion="optimize",
        scripted_steps=(
            ScriptedExperimentStep(
                action="fill",
                payload={"selector": "#coupon-input", "value": "DISCOUNT"},
                reason="老年用户先输入自己猜测的优惠券码。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券 输入优惠券码 SHOP10",
                after_text="商品详情 优惠券输入框已填入 DISCOUNT。",
                progress_summary="用户先输入了一个自己猜测的优惠券码。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#coupon-apply"},
                reason="用户尝试应用优惠券。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券输入框为 DISCOUNT 应用按钮可点击。",
                after_text="商品详情 操作失败，请重试",
                after_error_messages=("操作失败，请重试",),
                progress_summary="点击应用后只看到模糊错误提示，无法判断优惠券为何失败。",
                friction_signals=("page_error", "recovery_candidate"),
                detected_error=True,
            ),
            ScriptedExperimentStep(
                action="fill",
                payload={"selector": "#coupon-input", "value": "10OFF"},
                reason="用户尝试另一个常见优惠券码。",
                before_url=PRODUCT_URL,
                before_text="商品详情 操作失败，请重试",
                before_error_messages=("操作失败，请重试",),
                after_text="商品详情 优惠券输入框已改为 10OFF。",
                progress_summary="用户尝试更换优惠券码继续排查。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#coupon-apply"},
                reason="用户再次尝试应用优惠券。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券输入框为 10OFF 应用按钮可点击。",
                after_text="商品详情 操作失败，请重试",
                after_error_messages=("操作失败，请重试",),
                progress_summary="第二次应用优惠券仍失败，错误提示仍没有说明可用码。",
                friction_signals=("page_error", "recovery_candidate"),
                detected_error=True,
            ),
            ScriptedExperimentStep(
                action="fill",
                payload={"selector": "#coupon-input", "value": "SHOP10"},
                reason="用户最终输入任务说明中的优惠券码。",
                before_url=PRODUCT_URL,
                before_text="商品详情 操作失败，请重试 优惠券码 SHOP10",
                after_text="商品详情 优惠券输入框已改为 SHOP10。",
                progress_summary="用户根据任务说明改用明确给出的优惠券码。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#coupon-apply"},
                reason="用户再次尝试应用优惠券。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券输入框为 SHOP10 应用按钮可点击。",
                after_text="商品详情 优惠券已应用：立减 ¥89.9",
                progress_summary="优惠券终于应用成功，但前序错误提示已造成多次试错。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "[data-testid=\"buy-now\"]"},
                reason="优惠券已应用，继续进入结算。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券已应用 立即购买",
                after_url=CHECKOUT_URL,
                after_text="结算信息 优惠券已应用，姓名/手机号/地址/支付账号/验证码均已准备。",
                progress_summary="用户带着已应用优惠券进入结算页。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#submit-order"},
                reason="所有信息已就绪，提交订单完成购买。",
                before_url=CHECKOUT_URL,
                before_text="结算信息 优惠券已应用 所有字段已填写 验证码 8204",
                after_url=SUCCESS_URL,
                after_text="支付成功 订单号 已支付金额 优惠券已应用",
                status="succeeded",
                should_stop=True,
                detected_success=True,
                progress_summary="页面显示优惠券已应用和支付成功，任务完成。",
            ),
        ),
    ),
    FrictionExperiment(
        experiment_id="E-004",
        persona_name=PERSONA_NEWBIE.name,
        task_name=TASK_USE_COUPON.name,
        description="新手用户看到优惠券模糊错误后因低耐心直接放弃。",
        expected_friction_signals=("page_error", "recovery_candidate"),
        expected_conclusion="fix",
        scripted_steps=(
            ScriptedExperimentStep(
                action="fill",
                payload={"selector": "#coupon-input", "value": "DISCOUNT"},
                reason="新手用户输入自己以为可用的优惠券码。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券 输入优惠券码 SHOP10",
                after_text="商品详情 优惠券输入框已填入 DISCOUNT。",
                progress_summary="用户先输入了自己猜测的优惠券码。",
            ),
            ScriptedExperimentStep(
                action="click",
                payload={"selector": "#coupon-apply"},
                reason="用户尝试应用优惠券。",
                before_url=PRODUCT_URL,
                before_text="商品详情 优惠券输入框为 DISCOUNT 应用按钮可点击。",
                after_text="商品详情 操作失败，请重试",
                after_error_messages=("操作失败，请重试",),
                progress_summary="优惠券错误提示模糊，没有说明失败原因或正确格式。",
                friction_signals=("page_error", "recovery_candidate"),
                detected_error=True,
            ),
            ScriptedExperimentStep(
                action="abandon",
                payload={"reason": "优惠券失败原因不明确，不知道如何继续。"},
                reason="低耐心新手用户遇到模糊错误后放弃。",
                before_url=PRODUCT_URL,
                before_text="商品详情 操作失败，请重试",
                before_error_messages=("操作失败，请重试",),
                progress_summary="用户因优惠券错误提示不明确放弃任务。",
                status="failed",
                should_stop=True,
                friction_signals=("page_error",),
                detected_error=True,
            ),
        ),
    ),
]


def get_friction_experiments() -> list[FrictionExperiment]:
    """获取 S-010 摩擦实验列表。"""

    return list(FRICTION_EXPERIMENTS)


def get_friction_experiment(experiment_id: str) -> FrictionExperiment:
    """按实验 ID 获取摩擦实验。"""

    for experiment in FRICTION_EXPERIMENTS:
        if experiment.experiment_id == experiment_id:
            return experiment
    raise ValueError(f"Unknown friction experiment: {experiment_id}")
