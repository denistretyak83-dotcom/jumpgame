"""PlayerView -- responsible for rendering the player model."""

import pygame


class PlayerView:
    """Render player state to the screen."""

    def __init__(self, player):
        """
        Args:
            player (models.player.Player): The logical player model.
        """
        self.player = player

    def render(self, screen):
        """Draws the player to the screen surface."""
        player = self.player

        # 1. Обработка состояния смерти (переворот)
        if player.is_dead:
            frame = player.animations["idle"].current()
            if frame is not None:
                # Переворачиваем спрайт
                flipped_frame = pygame.transform.flip(frame, False, True)
                screen.blit(flipped_frame, (player.rect.x, player.rect.y))
            return

        # 2. Отрисовка обычного состояния
        frame = player.current_anim.current()
        if frame is None:
            return

        # 3. Отрисовка с учетом направления (влево/вправо)
        if player.facing_left and (
            player.current_anim is player.animations["idle"]
            or player.current_anim is player.animations["jump"]
        ):
            frame = pygame.transform.flip(frame, True, False)

        # 4. Блик (blit)
        # В оригинале использовалось player.rect.bottom, здесь используем player.rect
        screen.blit(frame, (player.rect.x, player.rect.bottom - frame.get_height()))
