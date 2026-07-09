from __future__ import annotations

# ============================ 护栏默认关键词库 ============================ #
# 模块功能: 提供 action_guard 关键词库的默认值，供 GuardConfig 空库兜底与首次 seed 使用
# 模块接口说明: DEFAULT_DESTRUCTIVE_KEYWORDS / DEFAULT_SENSITIVE_KEYWORDS 被 GuardConfig 与 action_guard 引用

# click 护栏：命中这些正则的按钮点击被判定为破坏性动作（删除/支付/发布等不可逆操作）。
# 关键词以正则模式存储：英文词用 \b 词边界避免误伤（如 deleted-item），中文直接子串匹配。
DEFAULT_DESTRUCTIVE_KEYWORDS: list[str] = [
    r"\bdelete\b", r"\bremove\b", r"\bunsubscribe\b",
    r"删除", r"移除", r"取消订阅",
    r"\bpublish\b", r"\bpay\b", r"\bcheckout\b", r"\bbuy\b", r"\bpurchase\b",
    r"发布", r"支付", r"结算", r"购买",
]

# fill 护栏：命中这些正则的表单字段被判定为敏感字段（密码/支付信息等不应被随意填写）。
DEFAULT_SENSITIVE_KEYWORDS: list[str] = [
    r"\bpassword\b", r"\bpwd\b", r"密码",
    r"\bcredit[_-]?card\b", r"\bcard[_-]?number\b",
    r"信用卡", r"银行卡",
    r"\bcvv\b", r"\bcvc\b", r"安全码",
]
