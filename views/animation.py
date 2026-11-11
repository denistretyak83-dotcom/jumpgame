"""Animation -- кадровая анимация, привязанная к реальному времени (dt)."""


class Animation:
    def __init__(self, frames, frame_delay_s: float, loop=True):
        self.frames = frames
        self.frame_delay_s = frame_delay_s  # секунды
        self.loop = loop
        self.index = 0
        self.timer = 0.0

    def update(self, dt: float):
        if not self.frames:
            return
        self.timer += dt
        while self.timer >= self.frame_delay_s:
            self.timer -= self.frame_delay_s
            if self.index < len(self.frames) - 1:
                self.index += 1
            elif self.loop:
                self.index = 0

    def reset(self):
        self.index = 0
        self.timer = 0.0

    def current(self):
        return self.frames[self.index] if self.frames else None
