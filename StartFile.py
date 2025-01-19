import pygame
import sys

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
VIOLET = (139, 0, 255)

# Скорость прокрутки фона и препятствий
scroll_speed = 5

# Пол
floor_height = 150
floor_rect = pygame.Rect(0, HEIGHT - floor_height, WIDTH, floor_height)

# Таймер
clock = pygame.time.Clock()

# Шрифт для отображения текста
font = pygame.font.Font(None, 36)

# Загрузка изображений
cube_image = pygame.image.load("cube.png").convert_alpha()
standard_spike_image = pygame.image.load("standard_spike.png").convert_alpha()
little_spike_image = pygame.image.load('little_spike.png').convert_alpha()
block_image = pygame.image.load("block.png").convert_alpha()


class Cube:
    def __init__(self, x, y):
        self.image = cube_image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.gravity = 0.75
        self.is_jumping = False
        self.jump_force = -12
        self.jump_count = 0

    def draw(self):
        screen.blit(self.image, self.rect)

    def handle_jump(self):
        if not self.is_jumping:
            self.vel_y = self.jump_force
            self.is_jumping = True
            self.jump_count += 1

    def apply_gravity(self):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        if self.rect.bottom > HEIGHT - floor_height:
            self.rect.bottom = HEIGHT - floor_height
            self.vel_y = 0
            self.is_jumping = False
            self.jump_count = 0

    def get_mask(self):
        return pygame.mask.from_surface(self.image)


class Obstacle:
    def __init__(self, x, y, obstacle_type):
        if obstacle_type == "standard_spike":
            self.image = standard_spike_image
        elif obstacle_type == "little_spike":
            self.image = little_spike_image
        elif obstacle_type == 'block':
            self.image = block_image
        else:
            raise ValueError("Invalid obstacle type")
        self.rect = self.image.get_rect(topleft=(x, HEIGHT - y - floor_height))
        self.passed = False

        self.type = obstacle_type

    def draw(self):
        screen.blit(self.image, self.rect)

    def move(self):
        self.rect.x -= scroll_speed

    def get_mask(self):
        return pygame.mask.from_surface(self.image)


class Game:
    def __init__(self):
        self.is_running = True
        self.game_over = False
        self.game_win = False
        self.score = 0
        self.cube = Cube(150, HEIGHT - 30 - 50)
        self.obstacles = []
        self.list_of_obstacles = [
            {"x": 700, "y": 30, 'type': 'standard_spike'},
            {"x": 950, "y": 30, 'type': 'little_spike'},
            {"x": 980, "y": 30, 'type': 'standard_spike'},
            {"x": 1200, "y": 30, 'type': 'standard_spike'},
            {"x": 1230, "y": 30, 'type': 'standard_spike'},
            {"x": 1400, "y": 30, 'type': 'standard_spike'},
            {"x": 1750, "y": 30, 'type': 'little_spike'},
            {"x": 1780, "y": 30, 'type': 'standard_spike'},
            {"x": 1810, "y": 30, 'type': 'little_spike'},

            {"x": 2000, "y": 30, 'type': 'block'},
            {"x": 2030, "y": 30, 'type': 'block'},
            {"x": 2060, "y": 30, 'type': 'block'},
            {"x": 2090, "y": 30, 'type': 'standard_spike'},
            {"x": 2120, "y": 30, 'type': 'standard_spike'},
            {"x": 2150, "y": 30, 'type': 'standard_spike'},
            {"x": 2180, "y": 30, 'type': 'standard_spike'},
            {"x": 2210, "y": 30, 'type': 'block'},
            {"x": 2240, "y": 30, 'type': 'block'},
            {"x": 2270, "y": 30, 'type': 'block'},

            {"x": 2550, "y": 30, 'type': 'block'},
            {"x": 2550, "y": 60, 'type': 'block'},
            {"x": 2710, "y": 30, 'type': 'block'},
            {"x": 2710, "y": 60, 'type': 'block'},
            {"x": 2710, "y": 90, 'type': 'block'},
        ]
        self.create_obstacles()
        self.space_pressed = False

    def create_obstacles(self):
        self.obstacles = []
        for obstacle_data in self.list_of_obstacles:
            obstacle = Obstacle(obstacle_data["x"], obstacle_data["y"], obstacle_data["type"])
            self.obstacles.append(obstacle)

    def check_collision(self):
        cube_rect = self.cube.rect
        cube_mask = self.cube.get_mask()

        for obstacle in self.obstacles:
            obstacle_mask = obstacle.get_mask()
            offset = (obstacle.rect.x - cube_rect.x, obstacle.rect.y - cube_rect.y)
            if cube_mask.overlap(obstacle_mask, offset):
                if obstacle.type == "block":
                    # Проверка столкновения сверху
                    if cube_rect.bottom <= obstacle.rect.top + 15 and self.cube.vel_y >= 0:
                        cube_rect.bottom = obstacle.rect.top
                        self.cube.vel_y = 0
                        self.cube.is_jumping = False
                        return False  # не Game Over

                    # Проверка столкновения слева
                    elif cube_rect.right > obstacle.rect.left and self.cube.rect.centery > obstacle.rect.top:
                        return True  # Game Over

                else:  # стандартное столкновение
                    return True
        return False

    def scroll_background(self):
        for obstacle in self.obstacles:
            obstacle.move()
            if obstacle.rect.right < self.cube.rect.left and not obstacle.passed:
                self.score += 1
                obstacle.passed = True

        self.obstacles = [obstacle for obstacle in self.obstacles if obstacle.rect.right > -100]
        if not self.obstacles:
            self.game_win = True

    def run(self):
        while self.is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.space_pressed = True  # ставим значение True при зажатии пробела
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        self.space_pressed = False  # ставим значение False при отпускании пробела

            if self.space_pressed and not self.game_over and not self.game_win:  # прыгаем если зажат пробел
                self.cube.handle_jump()
            screen.fill(VIOLET)
            pygame.draw.rect(screen, BLACK, floor_rect)
            pygame.draw.line(screen, WHITE, (0, HEIGHT - floor_height), (4000, HEIGHT - floor_height), 1)
            for obstacle in self.obstacles:
                obstacle.draw()
            self.cube.draw()

            if not self.game_over and not self.game_win:
                self.cube.apply_gravity()
                if not self.check_collision():
                    self.scroll_background()
                elif self.check_collision():
                    self.game_over = True

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
        self.cube = Cube(150, HEIGHT - 30 - 50)
        self.create_obstacles()


if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
