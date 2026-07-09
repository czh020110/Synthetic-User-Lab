from __future__ import annotations

"""model_resolver 优先级测试：persona 预设 -> 默认预设 -> env 兜底。"""

from backend.ai_api.model_resolver import resolve_runtime_model
from backend.core.config import get_settings
from backend.schemas.model_preset_schemas import ModelPreset
from backend.schemas.persona_schemas import Persona
from backend.stores import get_entity_store


def setup_function():
    get_entity_store().clear()


def _make_preset(name: str, model_name: str = "gpt-4o", is_default: bool = False, fast_model_name: str = "") -> ModelPreset:
    return ModelPreset(
        name=name,
        provider="openai",
        api_key="sk-test",
        base_url="https://api.test/v1",
        model_name=model_name,
        fast_model_name=fast_model_name,
        is_default=is_default,
    )


def test_resolver_uses_persona_preset():
    store = get_entity_store()
    preset = store.create_model_preset(_make_preset("P1", model_name="persona-model"))
    persona = Persona(name="X", model_preset_id=preset.id)

    cfg = resolve_runtime_model(persona, store)
    assert cfg.model_name == "persona-model"
    assert cfg.api_key == "sk-test"


def test_resolver_falls_back_to_default_preset():
    store = get_entity_store()
    store.create_model_preset(_make_preset("Default", model_name="default-model", is_default=True))
    persona = Persona(name="X", model_preset_id=None)

    cfg = resolve_runtime_model(persona, store)
    assert cfg.model_name == "default-model"


def test_resolver_falls_back_to_first_preset_when_no_default():
    store = get_entity_store()
    store.create_model_preset(_make_preset("P1", model_name="first-model"))  # 无默认
    persona = Persona(name="X", model_preset_id=None)

    cfg = resolve_runtime_model(persona, store)
    assert cfg.model_name == "first-model"


def test_resolver_env_fallback_when_no_preset():
    store = get_entity_store()
    persona = Persona(name="X", model_preset_id=None)

    cfg = resolve_runtime_model(persona, store)
    # 无任何预设，回退 env（get_settings）
    s = get_settings()
    assert cfg.model_name == s.model_name
    assert cfg.provider == s.model_provider


def test_resolver_persona_preset_not_found_falls_back():
    store = get_entity_store()
    store.create_model_preset(_make_preset("Default", model_name="default-model", is_default=True))
    persona = Persona(name="X", model_preset_id="nonexistent")  # 预设不存在

    cfg = resolve_runtime_model(persona, store)
    assert cfg.model_name == "default-model"


def test_resolver_none_persona_uses_default():
    store = get_entity_store()
    store.create_model_preset(_make_preset("Default", model_name="default-model", is_default=True))

    cfg = resolve_runtime_model(None, store)
    assert cfg.model_name == "default-model"


def test_resolver_fast_model_falls_back_to_main():
    store = get_entity_store()
    store.create_model_preset(_make_preset("P1", model_name="main-model", fast_model_name="", is_default=True))
    persona = Persona(name="X")

    cfg = resolve_runtime_model(persona, store)
    assert cfg.fast_model_name == "main-model"  # fast 为空回退 main
