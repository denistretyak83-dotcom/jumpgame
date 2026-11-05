"""Collision helpers -- pure functions operating on pygame.Rects."""


def check_coin_collision(coins, coin_collected, player_rect):
    """Return the list of coin indices the player just collected."""
    hits = []
    for i, coin in enumerate(coins):
        if not coin_collected[i] and player_rect.colliderect(coin):
            hits.append(i)
    return hits


def check_enemy_collision(player_rect, enemies):
    """Return the first enemy whose rect collides with the player, else None."""
    for enemy in enemies:
        if player_rect.colliderect(enemy.rect):
            return enemy
    return None


def check_flag_collision(player_rect, flag_rect):
    """Return True if the player touches the flag."""
    if player_rect is None or flag_rect is None:
        return False
    return player_rect.colliderect(flag_rect)


def check_fell_out(player_rect, height):
    """Возвращает True, если игрок упал ниже экрана + буфер."""
    # Используем rect.bottom (ноги) для проверки падения
    return player_rect.bottom > height + 30
