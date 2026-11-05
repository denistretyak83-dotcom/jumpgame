"""SoundManager -- procedurally generated sound effects + looped background music.

Ported from the original sounds.py. Synthesis math is preserved exactly.
Uses pathlib for the music path (in place of the equivalent string join).
"""
import math
import array
import pathlib
import pygame


class SoundManager:
    SAMPLE_RATE = 22050

    def __init__(self, sounds_dir):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.mixer.init()
        self.sounds_dir = sounds_dir
        self.SAMPLE_RATE = 22050

        # Build all sound effects procedurally
        self.death_sound = self._make_death_sound()
        self.bump_sound = self._make_bump_sound()
        self.jump_sound = self._make_jump_sound()
        self.coin_sound = self._make_coin_sound()
        self.win_sound = self._make_win_sound()

    # ---------------- internal synthesis helpers ----------------
    def _make_sound(self, samples):
        data = array.array('h')
        for s in samples:
            val = int(max(-1.0, min(1.0, s)) * 32767)
            data.append(val)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _make_jump_sound(self):
        SR = self.SAMPLE_RATE
        n = int(SR * 0.15)
        samples = []
        for i in range(n):
            t = i / SR
            freq = 200 + (400 * i / n)
            amp = (1 - i / n)
            samples.append(amp * math.sin(2 * math.pi * freq * t))
        return self._make_sound(samples)

    def _make_coin_sound(self):
        SR = self.SAMPLE_RATE
        n = int(SR * 0.2)
        samples = []
        for i in range(n):
            t = i / SR
            env = math.exp(-t * 15)
            s = 0.7 * math.sin(2 * math.pi * 880 * t) + 0.3 * math.sin(2 * math.pi * 1320 * t)
            samples.append(env * s)
        return self._make_sound(samples)

    def _make_win_sound(self):
        SR = self.SAMPLE_RATE
        notes = [(523.25, 0.16), (659.25, 0.16), (783.99, 0.18)]
        samples = []
        for freq, dur in notes:
            n = int(SR * dur)
            for i in range(n):
                t = i / SR
                env = math.exp(-t * 8)
                samples.append(env * math.sin(2 * math.pi * freq * t))
        return self._make_sound(samples)

    def _make_bump_sound(self):
        SR = self.SAMPLE_RATE
        n = int(SR * 0.1)
        samples = []
        for i in range(n):
            t = i / SR
            env = math.exp(-t * 30)
            samples.append(env * math.sin(2 * math.pi * 120 * t))
        return self._make_sound(samples)

    def _make_death_sound(self):
        SR = self.SAMPLE_RATE
        n = int(SR * 0.6)
        samples = []
        for i in range(n):
            t = i / SR
            freq = 600 - (500 * i / n)
            env = math.exp(-t * 3)
            samples.append(env * math.sin(2 * math.pi * freq * t))
        return self._make_sound(samples)

    # ---------------- background music ----------------
    def play_music(self):
        try:
            path = pathlib.Path(self.sounds_dir) / "bgm_song.ogg"
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Music not found: {e}")

    def stop_music(self):
        pygame.mixer.music.stop()

    # ---------------- public play API ----------------
    def play_jump(self):
        self.jump_sound.play()

    def play_coin(self):
        self.coin_sound.play()

    def play_bump(self):
        self.bump_sound.play()

    def play_death(self):
        self.death_sound.play()

    def play_win(self):
        self.win_sound.play()
