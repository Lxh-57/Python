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


def draw_game(screen: pygame.Surface, font: pygame.font.Font, game: GameState) -> None:
    screen.fill(BACKGROUND)

    for bullet in game.bullets:
        pygame.draw.circle(screen, YELLOW, bullet.pos, BULLET_RADIUS)

    for enemy in game.enemies:
        pygame.draw.circle(screen, RED, enemy.pos, enemy.radius)

    pygame.draw.circle(screen, BLUE, game.player, PLAYER_RADIUS)

    hud = font.render(
        f"Score: {game.score}    Health: {max(0, game.health)}",
        True,
        WHITE,
    )
    screen.blit(hud, (16, 16))

    if game.health <= 0:
        message = font.render("Game Over - Press R to restart", True, WHITE)
        screen.blit(message, message.get_rect(center=(WIDTH / 2, HEIGHT / 2)))

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
