import pygame
import sys
import random

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

# Скорость прокрутки фона и препятствий
scroll_speed = 8

# Пол
floor_height = 50
floor_rect = pygame.Rect(0, HEIGHT - floor_height, WIDTH, floor_height)

# Препятствия
obstacle_gap = 200  # Фиксированный интервал между препятствиями

# Таймер
clock = pygame.time.Clock()

# Шрифт для отображения текста
font = pygame.font.Font(None, 36)


class Cube:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.vel_y = 0
        self.gravity = 1.5
        self.is_jumping = False
        self.jump_force = -25  # Увеличение высоты прыжка
        self.jump_count = 0

    def draw(self):
        pygame.draw.rect(screen, YELLOW, (self.x, self.y, self.size, self.size))

    def handle_jump(self):
        if not self.is_jumping:
            self.vel_y = self.jump_force
            self.is_jumping = True
            self.jump_count += 1

    def apply_gravity(self):
        self.vel_y += self.gravity
        self.y += self.vel_y
        if self.y + self.size > HEIGHT - floor_height:
            self.y = HEIGHT - self.size - floor_height
            self.vel_y = 0
            self.is_jumping = False
            self.jump_count = 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)


class Obstacle:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, HEIGHT - y - floor_height, width, height)
        self.passed = False

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

    def move(self):
        self.rect.x -= scroll_speed

    def get_rect(self):
        return self.rect


class Game:
    def __init__(self):
        self.is_running = True
        self.game_over = False
        self.game_win = False
        self.score = 0
        self.cube = Cube(150, HEIGHT - 30 - 50, 30)
        self.obstacles = []
        self.list_of_obstacles = [
            {"x": 600, "y": 30, "width": 30, "height": 30},
            {"x": 850, "y": 30, "width": 30, "height": 30},
            {"x": 1100, "y": 30, "width": 30, "height": 30},
            {"x": 1300, "y": 30, "width": 30, "height": 30},
            {"x": 1600, "y": 30, "width": 30, "height": 30},
            {"x": 1800, "y": 30, "width": 30, "height": 30},
        ]
        self.create_obstacles()

    def create_obstacles(self):
        self.obstacles = []
        x_pos = 0
        for obstacle_data in self.list_of_obstacles:
            obstacle = Obstacle(x_pos + obstacle_data["x"], obstacle_data["y"], obstacle_data["width"],
                                obstacle_data["height"])
            self.obstacles.append(obstacle)
            x_pos += obstacle_data["width"] + obstacle_gap

    def check_collision(self):
        cube_rect = self.cube.get_rect()
        for obstacle in self.obstacles:
            if cube_rect.colliderect(obstacle.get_rect()):
                return True
        return False

    def scroll_background(self):
        for obstacle in self.obstacles:
            obstacle.move()
            if obstacle.rect.right < self.cube.x and not obstacle.passed:
                self.score += 1
                obstacle.passed = True
        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.rect.right > 0]
        if not self.obstacles:
            self.game_win = True

    def run(self):
        while self.is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.game_over and not self.game_win:
                        if self.cube.jump_count < 2:
                            self.cube.handle_jump()

            if self.check_collision() and not self.game_over and not self.game_win:
                self.game_over = True

            screen.fill(BLACK)
            pygame.draw.rect(screen, GRAY, floor_rect)
            for obstacle in self.obstacles:
                obstacle.draw()
            self.cube.draw()

            if not self.game_over and not self.game_win:
                self.cube.apply_gravity()
                self.scroll_background()

            if self.game_over:
                self.show_game_over_text()
            elif self.game_win:
                self.show_game_win_text()

            pygame.display.flip()
            clock.tick(60)

    def show_game_over_text(self):
        text = font.render(f"Game Over. Score: {self.score}", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        button_text = font.render("New Game", True, BLACK)
        button_rect = button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        pygame.draw.rect(screen, GREEN, button_rect.inflate(20, 20))
        screen.blit(button_text, button_rect)
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and button_rect.collidepoint(mouse_pos):
            self.restart_game()

    def show_game_win_text(self):
        text = font.render(f"You Win! Score: {self.score}", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        button_text = font.render("New Game", True, BLACK)
        button_rect = button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        pygame.draw.rect(screen, GREEN, button_rect.inflate(20, 20))
        screen.blit(button_text, button_rect)
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and button_rect.collidepoint(mouse_pos):
            self.restart_game()

    def restart_game(self):
        self.game_over = False
        self.game_win = False
        self.score = 0
        self.cube = Cube(150, HEIGHT - 30 - 50, 30)
        self.create_obstacles()


if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
