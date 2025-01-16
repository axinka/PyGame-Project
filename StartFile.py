import pygame
import sys
import random
import math

# Инициализация Pygame
pygame.init()

# Размеры окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Geometry Dash")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

# Персонаж (куб)
cube_size = 30
cube_x = 50
cube_y = HEIGHT - cube_size - 50  # От земли
cube_vel_y = 0
cube_gravity = 1.5
cube_is_jumping = False
jump_force = -20  # Скорость прыжка
jump_count = 0  # Счётчик прыжков

# Скорость прокрутки фона и препятствий
scroll_speed = 5

# Пол
floor_height = 50
floor_rect = pygame.Rect(0, HEIGHT - floor_height, WIDTH, floor_height)

# препятствия
obstacle_width = 30
obstacle_height = 50
obstacle_gap = 200
obstacle_min_height = 30
obstacle_max_height = 70
obstacle_min_gap = 250
obstacles = []


def generate_obstacle():
    # Генерация препятствий (пока генерация, потом список препятствий будет)
    y_pos = random.randint(obstacle_min_height, obstacle_max_height)

    if len(obstacles) == 0:
        x_pos = WIDTH + random.randint(100, 200)
    else:
        x_pos = obstacles[-1].right + random.randint(obstacle_min_gap, obstacle_min_gap + 100)

    obstacle_rect = pygame.Rect(x_pos, HEIGHT - y_pos - floor_height, obstacle_width, y_pos)
    obstacles.append(obstacle_rect)


# Генерация начальных препятствий
for _ in range(3):
    generate_obstacle()

# Таймер
clock = pygame.time.Clock()

# Переменная для отслеживания игры (запущена или нет)
is_running = True
game_over = False
score = 0

# Текст для отображения
font = pygame.font.Font(None, 36)


def draw_cube():
    # рисует куб-персонажа
    pygame.draw.rect(screen, YELLOW, (cube_x, cube_y, cube_size, cube_size))


def draw_floor():
    """Рисует пол."""
    pygame.draw.rect(screen, GRAY, floor_rect)


def draw_obstacles():
    # рисует препятствие
    for obstacle in obstacles:
        pygame.draw.rect(screen, WHITE, obstacle)


def check_collision():
    # Проверяет столкновение куба с препятствием
    cube_rect = pygame.Rect(cube_x, cube_y, cube_size, cube_size)
    for obstacle in obstacles:
        if cube_rect.colliderect(obstacle):
            return True
    return False


# Прокручивает препятствия и увеличивает счёт
def scroll_background():
    global obstacles, score
    for obstacle in obstacles:
        obstacle.move_ip(-scroll_speed, 0)

    # Увеличить счёт, если препятствие прошло
    for obstacle in obstacles:
        if obstacle.right < cube_x and obstacle.right > cube_x - scroll_speed:
            score += 1

    # Удаление препятствий, которые вышли за экран
    obstacles = [obstacle for obstacle in obstacles if obstacle.right > 0]

    # Генерация новых препятствий, если их меньше 3
    if len(obstacles) < 3 and len(obstacles) > 0 and obstacles[-1].right < WIDTH - obstacle_gap:
        generate_obstacle()
    elif len(obstacles) == 0:
        generate_obstacle()


# Управляет прыжком куба
def handle_jump():
    global cube_vel_y, cube_is_jumping, jump_count

    if not cube_is_jumping:
        cube_vel_y = jump_force
        cube_is_jumping = True
        jump_count += 1  # Увеличиваем счётчик прыжков


def apply_gravity():
    """Применяет гравитацию к кубу."""
    global cube_vel_y, cube_y, cube_is_jumping, jump_count
    cube_vel_y += cube_gravity
    cube_y += cube_vel_y

    # Ограничение высоты прыжка
    if cube_y + cube_size > HEIGHT - floor_height:
        cube_y = HEIGHT - cube_size - floor_height
        cube_vel_y = 0
        cube_is_jumping = False
        jump_count = 0  # Сбрасываем счётчик прыжков на земле


def show_game_over_text():
    """Показывает надпись Game Over и кнопку перезапуска."""
    text = font.render(f"Game Over. Score: {score}", True, WHITE)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(text, text_rect)

    # New game button
    button_text = font.render("New Game", True, BLACK)
    button_rect = button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    pygame.draw.rect(screen, GREEN, button_rect.inflate(20, 20))  # draw the green rectangle
    screen.blit(button_text, button_rect)

    mouse_pos = pygame.mouse.get_pos()
    if pygame.mouse.get_pressed()[0] and button_rect.collidepoint(mouse_pos):
        restart_game()


def restart_game():
    """Resets game variables"""
    global game_over, obstacles, cube_x, cube_y, cube_vel_y, score

    game_over = False
    obstacles = []
    for _ in range(3):
        generate_obstacle()
    cube_x = 50
    cube_y = HEIGHT - cube_size - 50
    cube_vel_y = 0
    score = 0


# Основной игровой цикл
while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                if jump_count < 2:
                    handle_jump()

    # Проверка столкновений
    if check_collision() and not game_over:
        game_over = True

    # Обновление экрана
    screen.fill(BLACK)
    draw_floor()
    draw_obstacles()
    draw_cube()

    # Применение гравитации
    if not game_over:
        apply_gravity()
        scroll_background()

    if game_over:
        show_game_over_text()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()
