#用户前置对话
print ("\f hello")
user = input ("你是猫娘吗?\n(Y or N)")
if user == "Y": 
    print ("喵~")
else:
    print ("喵~主人你不是猫娘吗")
    test = input("真的吗?\n")
    while test == "Y":
        print ("喵~主人你不是猫娘吗(Y or N)")
        test = input ("真的吗?(Y or N)\n")
    else:
        print ("我就知道你是香香软软的小猫娘！\n")
print ("我们来玩游戏吧\n")

#主体
import random
import sys

import pygame


pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D 射击游戏")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)

PLAYER_SPEED = 300
BULLET_SPEED = 600
SHOOT_INTERVAL = 0.2
SPAWN_INTERVAL = 1.0


def new_game():
    return {
        "player": pygame.Vector2(WIDTH / 2, HEIGHT / 2),
        "bullets": [],
        "enemies": [],
        "score": 0,
        "health": 3,
        "spawn_timer": 0,
        "shoot_timer": 0,
    }


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

    return {"pos": pos, "radius": 16, "speed": random.randint(80, 140)}


game = new_game()
running = True

while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_r
            and game["health"] <= 0
        ):
            game = new_game()

    if game["health"] > 0:
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        if move.length_squared() > 0:
            move = move.normalize()
            game["player"] += move * PLAYER_SPEED * dt

        game["player"].x = max(18, min(WIDTH - 18, game["player"].x))
        game["player"].y = max(18, min(HEIGHT - 18, game["player"].y))

        game["shoot_timer"] -= dt
        mouse_buttons = pygame.mouse.get_pressed()
        aim = pygame.Vector2(pygame.mouse.get_pos()) - game["player"]

        if mouse_buttons[0] and aim.length_squared() > 0 and game["shoot_timer"] <= 0:
            aim = aim.normalize()
            game["bullets"].append({
                "pos": game["player"].copy(),
                "vel": aim * BULLET_SPEED,
            })
            game["shoot_timer"] = SHOOT_INTERVAL

        game["spawn_timer"] += dt
        if game["spawn_timer"] >= SPAWN_INTERVAL:
            game["enemies"].append(spawn_enemy())
            game["spawn_timer"] = 0

        for bullet in game["bullets"]:
            bullet["pos"] += bullet["vel"] * dt

        game["bullets"] = [
            bullet for bullet in game["bullets"]
            if -10 <= bullet["pos"].x <= WIDTH + 10
            and -10 <= bullet["pos"].y <= HEIGHT + 10
        ]

        for enemy in game["enemies"]:
            direction = game["player"] - enemy["pos"]
            if direction.length_squared() > 0:
                enemy["pos"] += direction.normalize() * enemy["speed"] * dt

        hit_bullets = set()
        hit_enemies = set()

        for bullet_index, bullet in enumerate(game["bullets"]):
            for enemy_index, enemy in enumerate(game["enemies"]):
                if bullet["pos"].distance_to(enemy["pos"]) < enemy["radius"] + 5:
                    hit_bullets.add(bullet_index)
                    hit_enemies.add(enemy_index)
                    game["score"] += 1
                    break

        game["bullets"] = [
            bullet for i, bullet in enumerate(game["bullets"])
            if i not in hit_bullets
        ]
        game["enemies"] = [
            enemy for i, enemy in enumerate(game["enemies"])
            if i not in hit_enemies
        ]

        survivors = []
        for enemy in game["enemies"]:
            if enemy["pos"].distance_to(game["player"]) < enemy["radius"] + 16:
                game["health"] -= 1
            else:
                survivors.append(enemy)
        game["enemies"] = survivors

    screen.fill((25, 28, 38))

    for bullet in game["bullets"]:
        pygame.draw.circle(screen, (255, 220, 80), bullet["pos"], 5)

    for enemy in game["enemies"]:
        pygame.draw.circle(screen, (230, 75, 75), enemy["pos"], enemy["radius"])

    pygame.draw.circle(screen, (80, 180, 255), game["player"], 16)

    hud = font.render(
        f"Score: {game['score']}    Health: {max(0, game['health'])}",
        True,
        (255, 255, 255),
    )
    screen.blit(hud, (16, 16))

    if game["health"] <= 0:
        message = font.render("Game Over - Press R to restart", True, (255, 255, 255))
        screen.blit(message, message.get_rect(center=(WIDTH / 2, HEIGHT / 2)))

    pygame.display.flip()

pygame.quit()
sys.exit()