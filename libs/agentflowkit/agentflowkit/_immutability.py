from types import MappingProxyType
from typing import Mapping, TypeVar

T = TypeVar("T")


def freeze_mapping(value: Mapping[str, object] | None = None) -> Mapping[str, object]:
    """Return a shallow immutable copy for public model fields."""
    return MappingProxyType(dict(value or {}))


def freeze_tuple(value: tuple[T, ...] | list[T]) -> tuple[T, ...]:
    return tuple(value)
