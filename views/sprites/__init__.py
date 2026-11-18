"""Подпакет sources: контракт SpriteSource, PNG и procedural-источники."""

from views.sprites.procedural import ProceduralSpriteSource
from views.sprites.sprite_source import PngSpriteSource, SpriteSource

__all__ = ["SpriteSource", "PngSpriteSource", "ProceduralSpriteSource"]
