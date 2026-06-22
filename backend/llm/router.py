from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from backend.schemas import ModelOption


@dataclass(frozen=True)
class ProviderEnv:
    provider: str
    api_key: str | None
    api_base: str
    models: list[str]
    default_model: str


_ENV_LOCK = threading.RLock()
_ENV_CONDITION = threading.Condition(_ENV_LOCK)
_ROUTED_ENV_KEYS = ("OPENAI_API_KEY", "OPENAI_API_BASE", "MODEL_NAME")
_ACTIVE_ROUTE: tuple[str, str, str] | None = None
_ACTIVE_COUNT = 0
_PREVIOUS_ENV: dict[str, str | None] | None = None


def _split_models(raw: str | None, fallback: list[str]) -> list[str]:
    if not raw:
        return fallback
    models = [item.strip() for item in raw.split(",") if item.strip()]
    return models or fallback


def get_provider_env(provider: str) -> ProviderEnv:
    if provider == "deepseek":
        models = _split_models(os.environ.get("DEEPSEEK_MODELS"), ["deepseek-chat", "deepseek-reasoner"])
        return ProviderEnv(
            provider="deepseek",
            api_key=os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            api_base=os.environ.get("DEEPSEEK_API_BASE") or os.environ.get("OPENAI_API_BASE") or "https://api.deepseek.com/v1",
            models=models,
            default_model=os.environ.get("DEEPSEEK_DEFAULT_MODEL") or models[0],
        )

    if provider == "openrouter":
        models = _split_models(
            os.environ.get("OPENROUTER_MODELS"),
            ["openai/gpt-4o", "openai/gpt-4.1", "openai/gpt-4.1-mini", "openai/o4-mini"],
        )
        return ProviderEnv(
            provider="openrouter",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            api_base=os.environ.get("OPENROUTER_API_BASE") or "https://openrouter.ai/api/v1",
            models=models,
            default_model=os.environ.get("OPENROUTER_DEFAULT_MODEL") or models[0],
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")


def list_model_options() -> list[ModelOption]:
    default_provider = os.environ.get("LLM_DEFAULT_PROVIDER", "deepseek")
    options: list[ModelOption] = []
    for provider in ["deepseek", "openrouter"]:
        provider_env = get_provider_env(provider)
        for model in provider_env.models:
            options.append(
                ModelOption(
                    provider=provider,  # type: ignore[arg-type]
                    model=model,
                    label=model,
                    configured=bool(provider_env.api_key),
                    default=provider == default_provider and model == provider_env.default_model,
                )
            )
    return options


@contextmanager
def llm_provider_context(config: dict[str, Any]) -> Iterator[None]:
    global _ACTIVE_COUNT, _ACTIVE_ROUTE, _PREVIOUS_ENV

    provider = config.get("provider") or os.environ.get("LLM_DEFAULT_PROVIDER", "deepseek")
    provider_env = get_provider_env(provider)
    model = config.get("model") or provider_env.default_model
    if not provider_env.api_key:
        raise RuntimeError(
            f"Missing API key for provider '{provider}'. "
            "Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY in the backend .env."
        )

    route = (provider_env.api_key, provider_env.api_base, model)
    with _ENV_CONDITION:
        while _ACTIVE_ROUTE is not None and _ACTIVE_ROUTE != route:
            _ENV_CONDITION.wait()
        if _ACTIVE_COUNT == 0:
            _PREVIOUS_ENV = {key: os.environ.get(key) for key in _ROUTED_ENV_KEYS}
            os.environ["OPENAI_API_KEY"] = provider_env.api_key
            os.environ["OPENAI_API_BASE"] = provider_env.api_base
            os.environ["MODEL_NAME"] = model
            _ACTIVE_ROUTE = route
        _ACTIVE_COUNT += 1

    try:
        yield
    finally:
        with _ENV_CONDITION:
            _ACTIVE_COUNT -= 1
            if _ACTIVE_COUNT == 0:
                previous = _PREVIOUS_ENV or {}
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
                _ACTIVE_ROUTE = None
                _PREVIOUS_ENV = None
                _ENV_CONDITION.notify_all()
            elif _ACTIVE_COUNT < 0:
                _ACTIVE_COUNT = 0
                _ACTIVE_ROUTE = None
                _PREVIOUS_ENV = None
                _ENV_CONDITION.notify_all()
