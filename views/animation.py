"""Centralized Animation class -- single shared source for Player and Enemy.

Animation objects are built from pre-loaded frame lists (list of pygame
Surface) supplied by the views/controllers/factory layer.
"""


class Animation:
    def __init__(self, frames, frame_delay, loop=True):
        self.frames = frames           # list of pre-loaded Surface
        self.frame_delay = frame_delay # ticks between frame changes
        self.loop = loop               # whether the animation repeats
        self.index = 0
        self.timer = 0

    def update(self):
        if not self.frames:
            return
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.timer = 0
            if self.index < len(self.frames) - 1:
                self.index += 1
            elif self.loop:
                self.index = 0
            # if not loop: stay on the last frame

    def reset(self):
        """Reset to the first frame (useful when starting a jump)."""
        self.index = 0
        self.timer = 0

    def current(self):
        if not self.frames:
            return None
        return self.frames[self.index]
