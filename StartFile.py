import csv
import random
import pygame
import sys
from pygame.math import Vector2  # Импортируем Vector2 из pygame

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
floor_height = 124
floor_rect = pygame.Rect(0, HEIGHT - floor_height, WIDTH, floor_height)

# Таймер
clock = pygame.time.Clock()

# Шрифт для отображения текста
font = pygame.font.Font(None, 36)

# Загрузка изображений
cube_image = pygame.image.load("images/cube.png").convert_alpha()
standard_spike_image = pygame.image.load("images/standard_spike.png").convert_alpha()
little_spike_image = pygame.image.load('images/little_spike.png').convert_alpha()
block_image = pygame.image.load("images/block_1.png").convert_alpha()
spikes_image = pygame.image.load('images/spikes.png').convert_alpha()
background_image = pygame.image.load("images/fon.png").convert()


def blitrotate(surf, image, pos, originpos: tuple, angle: float):
    # Рассчитываем ограничивающий прямоугольник повернутого изображения
    w, h = image.get_size()  # Получаем ширину и высоту исходного изображения
    box = [Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]

    # Получаем минимальный и максимальный углы повернутого прямоугольника, чтобы учесть сдвиг и обрезку
    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
    # calculate the translation of the pivot
    pivot = Vector2(originpos[0], -originpos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    # Рассчитываем сдвиг точки вращения
    origin = (pos[0] - originpos[0] + min_box[0] - pivot_move[0], pos[1] - originpos[1] - max_box[1] + pivot_move[1])

    # Поворачиваем изображение
    rotated_image = pygame.transform.rotozoom(image, angle, 1)

    # Отрисовываем повернутое изображение
    surf.blit(rotated_image, origin)


class CubeFragment:
    def __init__(self, image, x, y, vel_x, vel_y, angle, rotation_speed):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.angle = angle
        self.rotation_speed = rotation_speed
        self.alpha = 255  # Прозрачность
        self.gravity = 0.75

    def update(self):
        """
        Обновляет состояние осколка.
        """
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.vel_y += self.gravity  # применяем гравитацию
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle -= 360
        self.alpha -= 10
        if self.alpha < 0:
            self.alpha = 0

    def draw(self):
        """
        Отрисовывает осколок на экране.
        """
        if self.alpha > 0:
            blitrotate(screen, self.image, self.rect.center, (self.image.get_width() / 2, self.image.get_height() / 2),
                       self.angle)
            self.image.set_alpha(self.alpha)


def split_image(image, parts_x, parts_y):
    """
    Разбивает изображение на несколько частей.
    """
    width = image.get_width()
    height = image.get_height()
    part_width = width // parts_x
    part_height = height // parts_y
    fragments = []
    for y in range(parts_y):
        for x in range(parts_x):
            rect = pygame.Rect(x * part_width, y * part_height, part_width, part_height)
            fragment_image = pygame.Surface(rect.size, pygame.SRCALPHA)
            fragment_image.blit(image, (0, 0), rect)
            fragments.append(fragment_image)

    return fragments


class AttemptText:
    def __init__(self, text, x, y):
        self.text = font.render(text, True, WHITE)
        self.rect = self.text.get_rect(topleft=(x, y))

    def draw(self):
        screen.blit(self.text, self.rect)

    def move(self):
        self.rect.x -= scroll_speed


class Cube:  # Класс куба
    def __init__(self, x, y):
        self.image = cube_image  # Загрузка изображения куба
        self.rect = self.image.get_rect(topleft=(x, y))  # Создание прямоугольника для куба на основе изображения

        self.vel_y = 0  # Вертикальная скорость куба

        self.gravity = 0.75  # Гравитация
        self.is_jumping = False  # Флаг, указывающий, находится ли куб в прыжке
        self.jump_force = -12  # Сила прыжка
        self.jump_count = 0  # Счетчик прыжков.
        self.rotation_angle = 0  # Угол поворота куба
        self.rotation_speed = 12  # скорость вращения
        self.is_active = True  # Флаг, определяющий, нужно ли рисовать куб
        self.particles = []  # Добавляем список для хранения частиц

    def draw(self):
        # Вызываем blitRotate для отрисовки куба, задавая центр изображения, центр поворота и угол поворота
        blitrotate(screen, self.image, self.rect.center, (self.image.get_width() / 2, self.image.get_height() / 2),
                   self.rotation_angle)
        self.draw_particle_trail(screen)

    def handle_jump(self):  # Обрабатывает прыжок куба
        # Если куб не в прыжке
        if not self.is_jumping:
            # Устанавливаем вертикальную скорость для прыжка
            self.vel_y = self.jump_force
            self.is_jumping = True
            self.jump_count += 1
            self.rotation_angle = 0

    def apply_gravity(self):  # Применяет гравитацию к кубу и обрабатывает его падение
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        if self.rect.bottom > HEIGHT - floor_height:
            self.rect.bottom = HEIGHT - floor_height
            self.vel_y = 0
            self.is_jumping = False
            self.jump_count = 0
            self.rotation_angle = 0
        if self.is_jumping:
            self.rotation_angle -= self.rotation_speed

    def get_mask(self):
        # Возвращаем маску на основе изображения куба
        return pygame.mask.from_surface(self.image)

    def draw_particle_trail(self, surface):
        # Создаём частицы
        self.particles.append([
            [self.rect.left - 9, self.rect.bottom - 7],  # Смещение слева и снизу
            [random.randint(0, 15) / 10 - 0.5, 0],  # Горизонтальная скорость
            random.randint(5, 8)  # Размер частиц
        ])

        for particle in self.particles:
            particle[0][0] += particle[1][0]
            particle[0][1] += particle[1][1]
            particle[2] -= 0.2
            particle[1][0] -= 0.1
            pygame.draw.rect(surface, WHITE,
                             ([int(particle[0][0]), int(particle[0][1])], [int(particle[2]) for _ in range(2)]))
            if particle[2] <= 0:
                self.particles.remove(particle)


class Obstacle:  # Класс препятствий
    def __init__(self, x, y, obstacle_type):
        # В зависимости от типа препятствия загружаем соответствующее изображение
        if obstacle_type == "standard_spike":
            self.image = standard_spike_image
        elif obstacle_type == "little_spike":
            self.image = little_spike_image
        elif obstacle_type == "spikes":
            self.image = spikes_image
        elif obstacle_type == 'block':
            self.image = block_image
        else:
            raise ValueError("Invalid obstacle type")
        self.rect = self.image.get_rect(topleft=(x, y))  # Создаем прямоугольник для препятствия на основе изображения
        self.passed = False

        self.type = obstacle_type

    def draw(self):  # Отрисовывает препятствие на экране
        screen.blit(self.image, self.rect)

    def move(self):  # Перемещает препятствие влево
        self.rect.x -= scroll_speed

    def get_mask(self):  # Возвращаем маску изображения препятствия
        return pygame.mask.from_surface(self.image)


class Game:
    def __init__(self):
        self.is_running = True  # Флаг, указывающий, работает ли игра
        self.game_over = False  # Флаг, указывающий, проиграна ли игра
        self.game_win = False  # Флаг, указывающий, выиграна ли игра
        self.score = 0  # Счет игрока
        self.cube = Cube(150, HEIGHT - 80)  # Создаем экземпляр куба, задавая начальные координаты
        self.obstacles = []  # Список для хранения препятствий
        self.level_data = self.load_level_from_csv()  # Загружаем данные уровня из CSV
        self.create_obstacles()  # Создаем препятствия на основе загруженных данных
        self.space_pressed = False  # Флаг, указывающий, зажата ли клавиша пробел
        self.cube_fragments = []  # Список для осколков куба
        self.attempt_count = 1  # Счетчик попыток
        self.attempt_text = None  # Для отображения текста попытки
        self.high_score = 0  # Переменная для хранения рекорда
        self.total_path_length = 8566  # Общая длина пути в пикселях
        self.new_high_score = False  # Флаг для отображения текста рекорда

    def load_level_from_csv(self):  # Загружает данные уровня из CSV-файла
        lvl = []
        with open('level_1.csv', newline='') as csvfile:
            trash = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in trash:
                lvl.append(row)
        return lvl

    def create_obstacles(self):  # Создает препятствия на основе данных уровня
        self.obstacles = []
        x_pos = 0
        y_pos = 0
        for row in self.level_data:
            for item in row:
                if item == '00':
                    obstacle = Obstacle(x_pos, y_pos, 'block')
                elif item == 's1':
                    obstacle = Obstacle(x_pos, y_pos, 'standard_spike')
                elif item == 's2':
                    obstacle = Obstacle(x_pos, y_pos, 'little_spike')
                elif item == 's3':
                    obstacle = Obstacle(x_pos, y_pos, 'spikes')
                else:
                    obstacle = ''
                if obstacle:
                    self.obstacles.append(obstacle)
                x_pos += 34
            y_pos += 34
            x_pos = 0

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
                        self.cube.rotation_angle = 0
                        return False  # Не Game Over, просто столкновение сверху

                    # Проверка столкновения слева или справа
                    else:
                        self.cube_fragments = self.create_cube_fragments(self.cube)
                        self.cube.is_active = False
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.new_high_score = True  # Устанавливаем флаг
                        return True  # Game Over

                else:  # Если столкновение с шипом
                    self.cube_fragments = self.create_cube_fragments(self.cube)
                    self.cube.is_active = False
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.new_high_score = True  # Устанавливаем флаг
                    return True  # Game Over
        return False  # Нет столкновений

    def show_new_high_score_text(self):
        text = font.render(f"Новый рекорд: {self.score}%", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(1500)  # Задержка 2 секунды (2000 миллисекунд)

    def create_cube_fragments(self, cube):  # Создает осколки куба
        fragments = []
        fragment_images = split_image(cube.image, 3, 3)  # Разбиваем изображение куба на 9 частей
        count = 0
        for y in range(3):
            for x in range(3):
                fragment_image = fragment_images[count]
                # Вычисляем случайные направления и скорости для осколков
                vel_x = random.uniform(-5, 5)
                vel_y = random.uniform(-10, 5)
                angle = random.uniform(0, 360)
                rotation_speed = random.uniform(-10, 10)
                # Создаем осколки
                fragment = CubeFragment(fragment_image, cube.rect.x + x * fragment_image.get_width(),
                                        cube.rect.y + y * fragment_image.get_height(), vel_x, vel_y, angle,
                                        rotation_speed)
                fragments.append(fragment)
                count += 1
        return fragments

    def scroll_background(self):
        for obstacle in self.obstacles:
            obstacle.move()
            if obstacle.rect.right < self.cube.rect.left and not obstacle.passed:
                obstacle.passed = True

        # Проверяем, все ли препятствия за границей экрана
        furthest_obstacle_x = max(obstacle.rect.right for obstacle in self.obstacles) if self.obstacles else 0
        if furthest_obstacle_x < 0:  # Если самое правое препятствие находится за левым краем экрана
            self.game_win = True  # Игра выйграна

        # Рассчитываем пройденное расстояние
        self.score = int((self.total_path_length - furthest_obstacle_x) / self.total_path_length * 100)

    def run(self):  # Основной игровой цикл
        while self.is_running:  # Пока игра запущена
            for event in pygame.event.get():  # Обрабатываем события
                if event.type == pygame.QUIT:  # Если нажали на закрытие окна
                    self.is_running = False  # Останавливаем игру
                if event.type == pygame.KEYDOWN:  # Если нажали на клавишу
                    if event.key == pygame.K_SPACE:  # Если нажали на пробел
                        self.space_pressed = True
                if event.type == pygame.KEYUP:  # Если отпустили клавишу
                    if event.key == pygame.K_SPACE:  # Если отпустили пробел
                        self.space_pressed = False

            if self.space_pressed and not self.game_over and not self.game_win:  # прыгаем если зажат пробел
                self.cube.handle_jump()
            screen.blit(background_image, (0, 0))  # Отрисовываем фоновое изображение
            pygame.draw.rect(screen, BLACK, floor_rect)  # Рисуем пол
            # Рисуем линию пола
            pygame.draw.line(screen, WHITE, (0, HEIGHT - floor_height), (4000, HEIGHT - floor_height), 1)
            for obstacle in self.obstacles:  # Отрисовываем все препятствия
                obstacle.draw()
            if self.cube.is_active:
                self.cube.draw()  # Рисуем куб, если он активен
            for fragment in self.cube_fragments:
                fragment.draw()  # Отрисовываем осколки
                fragment.update()  # Обновляем положение осколков
            if self.attempt_text:  # Если текст есть, отрисовываем
                self.attempt_text.draw()
                self.attempt_text.move()
            self.cube_fragments = [fragment for fragment in self.cube_fragments if fragment.alpha > 0]

            if not self.game_over and not self.game_win:  # Если игра не проиграна и не выиграна
                if self.cube.is_active:
                    self.cube.apply_gravity()
                    if not self.check_collision():
                        self.scroll_background()
                elif not self.cube_fragments:  # Проверяем, что нет осколков
                    if self.new_high_score:  # Если установлен флаг рекорда
                        self.show_new_high_score_text()  # показываем текст
                        self.new_high_score = False  # Сбрасываем флаг
                    self.restart_game()
            elif self.game_win:  # Если игра выиграна
                self.show_game_win_text()  # Показываем текст выигрыша

            pygame.display.flip()
            clock.tick(60)

    def show_game_win_text(self):
        text = font.render(f"Вы выиграли! Прогресс: {self.score}%", True, WHITE)
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
        self.cube = Cube(150, HEIGHT - 80)
        self.create_obstacles()
        self.cube_fragments = []
        if self.game_win:
            self.attempt_count = 1
            self.attempt_text = None
        else:
            self.attempt_count += 1
            self.attempt_text = AttemptText(f'Попытка: {self.attempt_count}', 200, 200)


if __name__ == '__main__':
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
