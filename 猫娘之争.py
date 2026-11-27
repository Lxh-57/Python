import math
import random
import sys
from dataclasses import dataclass, field

import pygame


WIDTH, HEIGHT = 800, 600
PLAYER_SPEED = 300
BULLET_SPEED = 600
SHOOT_INTERVAL = 0.2
SPAWN_INTERVAL = 1.0
INVULNERABILITY_TIME = 1.0
PLAYER_RADIUS = 16
BULLET_RADIUS = 5

WHITE = (255, 255, 255)
BLUE = (80, 180, 255)
YELLOW = (255, 220, 80)
RED = (230, 75, 75)
BACKGROUND = (25, 28, 38)

BACKGROUND_TOP = (18, 21, 42)
BACKGROUND_BOTTOM = (52, 34, 78)

PLAYER_LIGHT = (165, 225, 255)
PLAYER_DARK = (45, 110, 200)
PLAYER_OUTLINE = (30, 70, 150)
INNER_EAR = (255, 190, 210)

ENEMY_LIGHT = (255, 155, 150)
ENEMY_DARK = (150, 40, 55)
ENEMY_OUTLINE = (95, 25, 40)
ENEMY_EYE = (255, 235, 150)

HEART_FULL = (255, 100, 130)
HEART_EMPTY = (60, 60, 80)


@dataclass
class Bullet:
    pos: pygame.Vector2
    vel: pygame.Vector2


@dataclass
class Enemy:
    pos: pygame.Vector2
    radius: int
    speed: int


@dataclass
class GameState:
    player: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(WIDTH / 2, HEIGHT / 2))
    bullets: list[Bullet] = field(default_factory=list)
    enemies: list[Enemy] = field(default_factory=list)
    score: int = 0
    health: int = 3
    spawn_timer: float = 0
    shoot_timer: float = 0
    invulnerability_timer: float = 0


def ask_catgirl():
    answer = input("你是猫娘吗? (Y or N)\n").strip().upper()
    if answer == "Y":
        print("喵~")
    else:
        answer = input("真的吗? (Y or N)\n").strip().upper()
        if answer == "Y":
            print("喵~主人你不是猫娘吗")
        else:
            print("我就知道你是香香软软的小猫娘！")
        print()
    print("我们来玩游戏吧\n")


def new_game():
    return GameState()


def spawn_enemy():
    side = random.randrange(4)
    if side == 0:
        pos = pygame.Vector2(random.randrange(WIDTH), -20)
    elif side == 1:
        pos = pygame.Vector2(WIDTH + 20, random.randrange(HEIGHT))
    elif side == 2:
        pos = pygame.Vector2(random.randrange(WIDTH), HEIGHT + 20)
    else:
        pos = pygame.Vector2(-20, random.randrange(HEIGHT))

    return Enemy(pos, 16, random.randint(80, 140))


def update_game(game: GameState, dt: float) -> None:
    keys = pygame.key.get_pressed()
    move = pygame.Vector2(
        keys[pygame.K_d] - keys[pygame.K_a],
        keys[pygame.K_s] - keys[pygame.K_w],
    )
    if move.length_squared() > 0:
        game.player += move.normalize() * PLAYER_SPEED * dt

    game.player.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, game.player.x))
    game.player.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, game.player.y))

    game.shoot_timer -= dt
    game.invulnerability_timer -= dt
    mouse_buttons = pygame.mouse.get_pressed()
    aim = pygame.Vector2(pygame.mouse.get_pos()) - game.player

    if mouse_buttons[0] and aim.length_squared() > 0 and game.shoot_timer <= 0:
        game.bullets.append(Bullet(game.player.copy(), aim.normalize() * BULLET_SPEED))
        game.shoot_timer = SHOOT_INTERVAL

    game.spawn_timer += dt
    if game.spawn_timer >= SPAWN_INTERVAL:
        game.enemies.append(spawn_enemy())
        game.spawn_timer -= SPAWN_INTERVAL

    for bullet in game.bullets:
        bullet.pos += bullet.vel * dt
    game.bullets = [
        bullet
        for bullet in game.bullets
        if -10 <= bullet.pos.x <= WIDTH + 10
        and -10 <= bullet.pos.y <= HEIGHT + 10
    ]

    for enemy in game.enemies:
        direction = game.player - enemy.pos
        if direction.length_squared() > 0:
            enemy.pos += direction.normalize() * enemy.speed * dt

    hit_bullet_indices = set()
    hit_enemy_indices = set()
    for bullet_index, bullet in enumerate(game.bullets):
        for enemy_index, enemy in enumerate(game.enemies):
            if bullet.pos.distance_to(enemy.pos) < enemy.radius + BULLET_RADIUS:
                hit_bullet_indices.add(bullet_index)
                hit_enemy_indices.add(enemy_index)
                game.score += 1
                break

    game.bullets = [
        bullet
        for index, bullet in enumerate(game.bullets)
        if index not in hit_bullet_indices
    ]
    game.enemies = [
        enemy
        for index, enemy in enumerate(game.enemies)
        if index not in hit_enemy_indices
    ]

    if game.invulnerability_timer <= 0:
        for enemy in game.enemies:
            if enemy.pos.distance_to(game.player) < enemy.radius + PLAYER_RADIUS:
                game.health -= 1
                game.invulnerability_timer = INVULNERABILITY_TIME
                enemy.pos = pygame.Vector2(-100, -100)
                break
    game.enemies = [
        enemy
        for enemy in game.enemies
        if enemy.pos.x >= 0 and enemy.pos.y >= 0
    ]


# ============ 绘制辅助（仅表现层，不改游戏逻辑） ============

_glow_cache = {}
_gradient_bg = None
_heart_full = None
_heart_empty = None
_dim_overlay = None

# 星空：每条为 (x, y, 半径, 相位)，相位用于随时间闪烁
_stars = [
    (
        random.randrange(WIDTH),
        random.randrange(HEIGHT),
        random.randrange(1, 3),
        random.randrange(0, 720),
    )
    for _ in range(110)
]


def _lerp_color(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _make_gradient_bg():
    surf = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        color = _lerp_color(BACKGROUND_TOP, BACKGROUND_BOTTOM, y / (HEIGHT - 1))
        pygame.draw.line(surf, color, (0, y), (WIDTH, y))
    return surf


def _draw_stars(screen):
    ticks = pygame.time.get_ticks()
    for x, y, radius, phase in _stars:
        t = ((ticks + phase) % 720) / 720.0
        k = 0.5 + 0.5 * math.sin(t * math.tau)
        v = int(90 + 150 * k)
        pygame.draw.circle(screen, (int(v * 0.85), int(v * 0.9), v), (x, y), radius)


def _make_glow(color, radius=48):
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = radius
    steps = 20
    for i in range(1, steps + 1):
        r = int(radius * i / steps)
        t = 1.0 - i / steps
        alpha = int(150 * t * t)
        pygame.draw.circle(surf, (color[0], color[1], color[2], alpha), (center, center), r)
    return surf


def _get_glow(color, radius=48):
    key = (color, radius)
    glow = _glow_cache.get(key)
    if glow is None:
        glow = _make_glow(color, radius)
        _glow_cache[key] = glow
    return glow


def _draw_glow(screen, color, pos, radius=48):
    glow = _get_glow(color, radius)
    screen.blit(glow, glow.get_rect(center=(int(pos.x), int(pos.y))))


def _draw_gradient_ball(screen, center, radius, top_color, bottom_color):
    cx, cy = int(center.x), int(center.y)
    for dy in range(-radius, radius + 1):
        half = int((radius * radius - dy * dy) ** 0.5)
        if half <= 0:
            continue
        color = _lerp_color(top_color, bottom_color, (dy + radius) / (2 * radius))
        pygame.draw.line(screen, color, (cx - half, cy + dy), (cx + half, cy + dy))


def _draw_cat_ears(screen, center, radius, outer, inner):
    cx, cy = int(center.x), int(center.y)
    r = radius
    for sign in (-1, 1):
        pygame.draw.polygon(screen, outer, [
            (cx + sign * r, cy - r * 0.55),
            (cx + sign * r * 0.15, cy - r * 1.25),
            (cx + sign * r * 0.25, cy - r * 0.15),
        ])
        pygame.draw.polygon(screen, inner, [
            (cx + sign * r * 0.72, cy - r * 0.55),
            (cx + sign * r * 0.28, cy - r * 1.0),
            (cx + sign * r * 0.35, cy - r * 0.3),
        ])


def _draw_cat(screen, center, radius, light, dark, outline, inner_ear, eye, nose, mouth):
    _draw_cat_ears(screen, center, radius, dark, inner_ear)
    _draw_gradient_ball(screen, center, radius, light, dark)
    pygame.draw.circle(screen, outline, (int(center.x), int(center.y)), radius, 2)

    cx, cy = int(center.x), int(center.y)
    r = radius
    eye_dx = r * 0.45
    eye_dy = -r * 0.15
    eye_r = max(2, int(r * 0.22))
    pygame.draw.circle(screen, eye, (int(cx - eye_dx), int(cy + eye_dy)), eye_r)
    pygame.draw.circle(screen, eye, (int(cx + eye_dx), int(cy + eye_dy)), eye_r)
    pygame.draw.polygon(screen, nose, [
        (cx - r * 0.12, cy + r * 0.1),
        (cx + r * 0.12, cy + r * 0.1),
        (cx, cy + r * 0.25),
    ])
    pygame.draw.line(screen, mouth, (cx, cy + r * 0.25), (cx - r * 0.15, cy + r * 0.42), 2)
    pygame.draw.line(screen, mouth, (cx, cy + r * 0.25), (cx + r * 0.15, cy + r * 0.42), 2)


def _draw_player(screen, game):
    _draw_glow(screen, BLUE, game.player, 48)
    if game.invulnerability_timer > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
        return  # 无敌闪烁：本帧隐藏
    _draw_cat(
        screen,
        game.player,
        PLAYER_RADIUS,
        PLAYER_LIGHT,
        PLAYER_DARK,
        PLAYER_OUTLINE,
        INNER_EAR,
        (30, 40, 80),
        INNER_EAR,
        (255, 255, 255),
    )


def _draw_enemy(screen, enemy):
    _draw_glow(screen, RED, enemy.pos, 48)
    _draw_cat(
        screen,
        enemy.pos,
        enemy.radius,
        ENEMY_LIGHT,
        ENEMY_DARK,
        ENEMY_OUTLINE,
        ENEMY_DARK,
        ENEMY_EYE,
        ENEMY_DARK,
        ENEMY_EYE,
    )


def _draw_soft_circle(screen, color, center, radius, alpha):
    if radius <= 0 or alpha <= 0:
        return
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (color[0], color[1], color[2], alpha), (radius, radius), radius)
    screen.blit(surf, (int(center.x) - radius, int(center.y) - radius))


def _draw_bullet(screen, bullet):
    _draw_glow(screen, YELLOW, bullet.pos, 20)
    direction = bullet.vel.normalize() if bullet.vel.length_squared() > 0 else pygame.Vector2(1, 0)
    for i in range(1, 4):
        t = i / 3.0
        tail = bullet.pos - direction * (BULLET_RADIUS * 3.2 * t)
        _draw_soft_circle(screen, YELLOW, tail, max(1, int(BULLET_RADIUS * (1 - t))), int(160 * (1 - t)))
    pygame.draw.circle(screen, YELLOW, (int(bullet.pos.x), int(bullet.pos.y)), BULLET_RADIUS)
    pygame.draw.circle(screen, WHITE, (int(bullet.pos.x), int(bullet.pos.y)), max(1, BULLET_RADIUS - 2))


def _make_heart(color, size=24):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    lobe_r = int(size * 0.3)
    pygame.draw.circle(surf, color, (int(size * 0.32), int(size * 0.34)), lobe_r)
    pygame.draw.circle(surf, color, (int(size * 0.68), int(size * 0.34)), lobe_r)
    pygame.draw.polygon(surf, color, [
        (int(size * 0.08), int(size * 0.46)),
        (int(size * 0.92), int(size * 0.46)),
        (int(size * 0.5), int(size * 0.95)),
    ])
    return surf


def _get_heart(full):
    global _heart_full, _heart_empty
    if full:
        if _heart_full is None:
            _heart_full = _make_heart(HEART_FULL)
        return _heart_full
    if _heart_empty is None:
        _heart_empty = _make_heart(HEART_EMPTY)
    return _heart_empty


def _draw_hud(screen, font, game):
    score_text = f"Score: {game.score}"
    score_surface = font.render(score_text, True, WHITE)
    score_shadow = font.render(score_text, True, (0, 0, 0))
    screen.blit(score_shadow, (18, 18))
    screen.blit(score_surface, (16, 16))
    for i in range(3):
        heart = _get_heart(i < max(0, game.health))
        screen.blit(heart, (16 + i * 28, 54))


def draw_game(screen: pygame.Surface, font: pygame.font.Font, game: GameState) -> None:
    global _gradient_bg, _dim_overlay

    if _gradient_bg is None:
        _gradient_bg = _make_gradient_bg()
    screen.blit(_gradient_bg, (0, 0))
    _draw_stars(screen)

    for bullet in game.bullets:
        _draw_bullet(screen, bullet)

    for enemy in game.enemies:
        _draw_enemy(screen, enemy)

    _draw_player(screen, game)
    _draw_hud(screen, font, game)

    if game.health <= 0:
        if _dim_overlay is None:
            _dim_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            _dim_overlay.fill((0, 0, 0, 120))
        screen.blit(_dim_overlay, (0, 0))
        message = font.render("Game Over - Press R to restart", True, WHITE)
        message_shadow = font.render("Game Over - Press R to restart", True, (0, 0, 0))
        rect = message.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        screen.blit(message_shadow, rect.move(2, 2))
        screen.blit(message, rect)

    pygame.display.flip()


def main() -> None:
    ask_catgirl()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D 射击游戏")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    game = new_game()
    running = True

    while running:
        dt = min(clock.tick(60) / 1000, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
                and game.health <= 0
            ):
                game = new_game()

        if game.health > 0:
            update_game(game, dt)

        draw_game(screen, font, game)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
