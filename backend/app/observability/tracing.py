from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def traced(name: str, *, run_type: str = "chain") -> Callable[[F], F]:
    """Apply LangSmith tracing when installed; otherwise preserve the function unchanged."""

    def decorator(function: F) -> F:
        try:
            from langsmith import traceable
        except ImportError:
            return function
        try:
            wrapped = traceable(name=name, run_type=run_type)(function)
        except Exception:
            return function
        return wraps(function)(wrapped)  # type: ignore[return-value]

    return decorator
