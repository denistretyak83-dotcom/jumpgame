"""Entity -- базовая модель с консервативной инкапсуляцией позиции/размеров.

Свойства x, y, width, height, left, top, right, bottom, centerx, centery
делегируют во внутренний pygame.Rect (сам rect сохранён для коллизий/рендера.
Полный отказ от pygame.Rect в моделях — отдельный радикальный план).
"""
import pygame


class Entity:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    @property
    def x(self): return self.rect.x
    @x.setter
    def x(self, v): self.rect.x = v

    @property
    def y(self): return self.rect.y
    @y.setter
    def y(self, v): self.rect.y = v

    @property
    def width(self): return self.rect.width
    @width.setter
    def width(self, v): self.rect.width = v

    @property
    def height(self): return self.rect.height
    @height.setter
    def height(self, v): self.rect.height = v

    @property
    def left(self): return self.rect.left
    @left.setter
    def left(self, v): self.rect.left = v

    @property
    def top(self): return self.rect.top
    @top.setter
    def top(self, v): self.rect.top = v

    @property
    def right(self): return self.rect.right
    @right.setter
    def right(self, v): self.rect.right = v

    @property
    def bottom(self): return self.rect.bottom
    @bottom.setter
    def bottom(self, v): self.rect.bottom = v

    @property
    def centerx(self): return self.rect.centerx
    @centerx.setter
    def centerx(self, v): self.rect.centerx = v

    @property
    def centery(self): return self.rect.centery
    @centery.setter
    def centery(self, v): self.rect.centery = v