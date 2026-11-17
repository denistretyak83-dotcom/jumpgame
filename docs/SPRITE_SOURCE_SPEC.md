# SpriteSource — контракт источника кадров

## Зачем
SpriteCache должен получать кадры ЕДИНООБРАЗНО: и из PNG-ассетов, и из
procedural-генератора. Это ключ к расширяемости графики (OCP).

## Контракт (Protocol)
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class SpriteSource(Protocol):
    def frames(self, key: str) -> list[object]:
        """Кадры анимации по ключу (idle/run/jump/walk/...)."""
        ...

    def size(self) -> tuple[int, int]:
        """Размер спрайта (ширина, высота)."""

    def supports(self, key: str) -> bool:
        """Умеет ли данный источник отдать кадры для key."""