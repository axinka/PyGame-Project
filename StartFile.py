import csv
import random
import pygame
import sys
import sqlite3
import os

from pygame.draw import rect
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

add_color = 0

# Скорость прокрутки фона и препятствий
scroll_speed = 5

level = 0
levels = ['level_1.csv', 'level_2.csv', 'level_3.csv']

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
background1_image = pygame.image.load("images/background1.png").convert()
background2_image = pygame.image.load("images/background2.png").convert()
background3_image = pygame.image.load("images/background3.png").convert()
backgrounds = [background1_image, background2_image, background3_image]

# Загрузка мелодий
pygame.mixer.init()
music1 = pygame.mixer.Sound(os.path.join("music", "music_1.mp3"))
music2 = pygame.mixer.Sound(os.path.join("music", "music_2.mp3"))
music3 = pygame.mixer.Sound(os.path.join("music", "music_3.mp3"))
music_win = pygame.mixer.Sound(os.path.join("music", "win_music.mp3"))
music_lose = pygame.mixer.Sound(os.path.join("music", "lose_music.mp3"))

music_win_flag = True
musics = [music1, music2, music3]

username = ''


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

    def update(self):  # Обновляет состояние осколка.
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.vel_y += self.gravity  # применяем гравитацию
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle -= 360
        self.alpha -= 10
        if self.alpha < 0:
            self.alpha = 0

    def draw(self):  # Отрисовывает осколок на экране.
        if self.alpha > 0:
            blitrotate(screen, self.image, self.rect.center, (self.image.get_width() / 2, self.image.get_height() / 2),
                       self.angle)
            self.image.set_alpha(self.alpha)

    def split_image(self, image, parts_x, parts_y):  # Разбивает изображение на несколько частей.
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

    def blitrotate(self, surf, image, pos, originpos: tuple, angle: float):
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
        origin = (
            pos[0] - originpos[0] + min_box[0] - pivot_move[0], pos[1] - originpos[1] - max_box[1] + pivot_move[1])

        # Поворачиваем изображение
        rotated_image = pygame.transform.rotozoom(image, angle, 1)

        # Отрисовываем повернутое изображение
        surf.blit(rotated_image, origin)

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


class Login:
    def check_password(self, password):
        count = 0
        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]:
            if str(i) in password:
                count += 1
        if count >= 1 and len(password) >= 6:
            return 'Done!'
        elif len(password) < 6:
            return 'Password must have at least 6 symbols!'
        else:
            return 'Password must have at least 1 digit!'

    def draw_login_screen(self):
        username = ""
        password = ""
        input_active = [True, False]  # [username_active, password_active]
        error_message1 = ""
        success_message = ''

        while True:
            screen.fill(BLACK)

            button_text = font.render("Add user", True, BLACK)
            button_rect = button_text.get_rect(center=(WIDTH // 2 - 75, HEIGHT // 2 + 75))
            pygame.draw.rect(screen, GREEN, button_rect.inflate(20, 20))
            button2_text = font.render("Log in", True, BLACK)
            text_x = WIDTH // 2 + 65 - button2_text.get_width() // 2
            text_y = HEIGHT // 2 + 75 - button2_text.get_height() // 2
            text_w = button2_text.get_width()
            text_h = button2_text.get_height()
            button_2_rect = pygame.Rect(text_x - 10, text_y - 10, text_w + 20, text_h + 20)
            pygame.draw.rect(screen, (0, 255, 0), button_2_rect)
            screen.blit(button_text, button_rect)
            screen.blit(button2_text, (text_x, text_y))

            button3_text = font.render("Try another user", True, BLACK)
            text_x = WIDTH // 2 - 13 - button3_text.get_width() // 2
            text_y = HEIGHT // 2 + 135 - button3_text.get_height() // 2
            text_w = button3_text.get_width()
            text_h = button3_text.get_height()
            button_3_rect = pygame.Rect(text_x - 10, text_y - 10, text_w + 20, text_h + 20)
            pygame.draw.rect(screen, (0, 255, 0), button_3_rect)
            screen.blit(button3_text, (text_x, text_y))

            title_text = font.render("Login", True, WHITE)
            username_text = font.render("Username: " + username, True, WHITE)
            password_text = font.render("Password: " + "*" * len(password), True, WHITE)
            error_text1 = font.render(error_message1, True, YELLOW)
            success_text = font.render(success_message, True, WHITE)

            screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(username_text, (WIDTH // 2 - username_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(password_text, (WIDTH // 2 - password_text.get_width() // 2, HEIGHT // 2))
            screen.blit(error_text1, (WIDTH // 2 - error_text1.get_width() // 2, HEIGHT // 2 - 200))
            screen.blit(success_text, (WIDTH // 2 - error_text1.get_width() // 2, HEIGHT // 2 + 50))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                con = sqlite3.connect('Game Users.db')
                cur = con.cursor()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    else:
                        if input_active[0]:  # Username input
                            if event.key == pygame.K_RETURN:
                                input_active[0] = False
                                input_active[1] = True
                            elif event.key == pygame.K_BACKSPACE:
                                username = username[:-1]
                            else:
                                username += event.unicode
                        elif input_active[1]:  # Password input
                            if event.key == pygame.K_BACKSPACE:
                                password = password[:-1]
                            else:
                                password += event.unicode

                mouse_pos = pygame.mouse.get_pos()
                if pygame.mouse.get_pressed()[0] == 1 and button_2_rect.collidepoint(mouse_pos):
                    if username and password:
                        logins = [login[0] for login in cur.execute("SELECT login FROM users").fetchall()]
                        if username in logins:
                            if password == cur.execute("SELECT password FROM users WHERE login = ?",
                                                       (username,)).fetchone()[0]:

                                con.commit()
                                con.close()
                                return username  # Successful login
                            else:
                                error_message1 = 'Invalid password'
                                input_active = [False, False]
                        else:
                            error_message1 = f"No user with login: {username}"
                            input_active = [False, False]
                    else:
                        error_message1 = 'Fields "Username" and "Password" can not be empty!'


                elif pygame.mouse.get_pressed()[0] == 1 and button_3_rect.collidepoint(mouse_pos):
                    username = ''
                    password = ''
                    error_message1 = ''
                    input_active = [True, False]
                elif pygame.mouse.get_pressed()[0] == 1 and button_rect.collidepoint(mouse_pos):
                    logins = [login[0] for login in cur.execute("SELECT login FROM users").fetchall()]
                    if username in logins:
                        if password == cur.execute("SELECT password FROM users WHERE login = ?",
                                                   (username,)).fetchone()[0]:
                            error_message1 = 'User is already exist!'
                    else:
                        if username and password:
                            if self.check_password(password) == 'Done!':
                                cur.execute(
                                    'INSERT INTO users(login, password, record1, record2, record3) VALUES(?, ?, ?, ?, ?)',
                                    (username, password, 0, 0, 0))
                                con.commit()
                                con.close()
                                return username
                            else:
                                error_message1 = self.check_password(password)
                                password = ''
                                input_active = [False, True]
                        else:
                            error_message1 = 'Fields "Username" and "Password" can not be empty!'


class Game:
    global level, music_win, music1, music2, music3, music_lose

    def __init__(self):
        self.record = list(get_record())
        self.start = False
        self.is_running = True  # Флаг, указывающий, работает ли игра
        self.game_over = False  # Флаг, указывающий, проиграна ли игра
        self.game_win = False  # Флаг, указывающий, выиграна ли игра
        self.score = 0  # Счет игрока
        self.cube = Cube(150, HEIGHT - 80)  # Создаем экземпляр куба, задавая начальные координаты
        self.obstacles = []  # Список для хранения препятствий
        self.level_data = self.load_level_from_csv(level)  # Загружаем данные уровня из CSV
        self.create_obstacles()  # Создаем препятствия на основе загруженных данных
        self.space_pressed = False  # Флаг, указывающий, зажата ли клавиша пробел
        self.cube_fragments = []  # Список для осколков куба
        self.attempt_count = 1  # Счетчик попыток
        self.attempt_text = None  # Для отображения текста попытки
        self.high_score = 0  # Переменная для хранения рекорда
        self.total_path_length = [8566, 6460, 6290]  # Общая длина пути в пикселях
        self.new_high_score = False  # Флаг для отображения текста рекорда

    def load_level_from_csv(self, level):  # Загружает данные уровня из CSV-файла
        name = levels[level]
        lvl = []
        with open(name, newline='') as csvfile:
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
        global music_lose
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
                        if self.score > self.record[level]:
                            self.high_score = self.score
                            self.new_high_score = True  # Устанавливаем флаг
                        music_lose.play()
                        self.is_record()
                        return True  # Game Over

                else:  # Если столкновение с шипом
                    self.cube_fragments = self.create_cube_fragments(self.cube)
                    self.cube.is_active = False
                    if self.score > self.record[level]:
                        self.high_score = self.score
                        self.new_high_score = True  # Устанавливаем флаг
                    musics[level].stop()
                    self.is_record()
                    music_lose.play()
                    return True  # Game Over
        return False  # Нет столкновений

    def show_new_high_score_text(self):
        text = font.render(f"New record: {self.score}%", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(1500)  # Задержка 2 секунды (2000 миллисекунд)

    def create_cube_fragments(self, cube):  # Создает осколки куба
        fragments = []
        fragment_images = CubeFragment.split_image(self, cube.image, 3, 3)  # Разбиваем изображение куба на 9 частей
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
        self.draw_stats()
        for obstacle in self.obstacles:
            obstacle.move()
            if obstacle.rect.right < self.cube.rect.left and not obstacle.passed:
                obstacle.passed = True

        # Проверяем, все ли препятствия за границей экрана
        furthest_obstacle_x = max(obstacle.rect.right for obstacle in self.obstacles) if self.obstacles else 0
        if furthest_obstacle_x < 0:  # Если самое правое препятствие находится за левым краем экрана
            self.game_win = True  # Игра выйграна

        # Рассчитываем пройденное расстояние
        self.score = int((self.total_path_length[level] - furthest_obstacle_x) / self.total_path_length[level] * 100)

    def draw_stats(self):
        global level, add_color
        lenghts = [0.39, 0.63, 0.62]
        lenght = lenghts[level]
        progress_colors = [pygame.Color("red"), pygame.Color("orange"), pygame.Color("yellow"),
                           pygame.Color("darkolivegreen2"), pygame.Color("lightgreen"),
                           pygame.Color("green"), pygame.Color("aquamarine4"), pygame.Color("darkgreen")]

        BAR_LENGTH = 790
        BAR_HEIGHT = 15
        add_color += lenght
        outline_rect = pygame.Rect(5, 5, BAR_LENGTH, BAR_HEIGHT)
        add_color_rect = pygame.Rect(5, 5, add_color, BAR_HEIGHT)
        col = progress_colors[int(add_color / 100)]
        rect(screen, col, add_color_rect, 0, 4)
        rect(screen, WHITE, outline_rect, 3, 4)

    def run(self):  # Основной игровой цикл
        global add_color, musics, level, username
        pygame.init()
        musics[level].play()
        button_text = font.render("Menu", True, WHITE)
        button_rect = pygame.Rect(690, 25, 720, 45)
        while self.is_running:  # Пока игра запущена
            for event in pygame.event.get():  # Обрабатываем события
                if event.type == pygame.QUIT:  # Если нажали на закрытие окна
                    self.is_running = False  # Останавливаем игру
                if event.type == pygame.KEYDOWN:  # Если нажали на клавишу
                    if event.type == pygame.K_ESCAPE:
                        self.is_running = False
                    if event.key == pygame.K_SPACE:  # Если нажали на пробел
                        self.space_pressed = True
                if event.type == pygame.KEYUP:  # Если отпустили клавишу
                    if event.key == pygame.K_SPACE:  # Если отпустили пробел
                        self.space_pressed = False

                mouse_pos = pygame.mouse.get_pos()
                if pygame.mouse.get_pressed()[0] and button_rect.collidepoint(mouse_pos):
                    self.game_win = False
                    self.is_running = False
                    self.start = True
                    musics[level].stop()
                    music_win.stop()
                    start_settings()
            if self.is_running:
                if self.space_pressed and not self.game_over and not self.game_win:  # прыгаем если зажат пробел
                    self.cube.handle_jump()
                screen.blit(backgrounds[level], (0, 0))  # Отрисовываем фоновое изображение
                pygame.draw.rect(screen, BLACK, floor_rect)  # Рисуем пол

                # Рисуем линию пола
                pygame.draw.line(screen, WHITE, (0, HEIGHT - floor_height), (4000, HEIGHT - floor_height), 1)
                screen.blit(button_text, (700, 35))
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

                if not self.game_over and not self.game_win and not self.start:  # Если игра не проиграна и не выиграна
                    if self.cube.is_active:
                        self.cube.apply_gravity()
                        if not self.check_collision():
                            self.scroll_background()
                    elif not self.cube_fragments:  # Проверяем, что нет осколков
                        if self.new_high_score:  # Если установлен флаг рекорда
                            self.show_new_high_score_text()  # показываем текст
                            self.new_high_score = False  # Сбрасываем флаг
                        self.restart_game()
                        add_color = 0
                elif self.start:
                    self.start_screen()
                    add_color = 0
                elif self.game_win:  # Если игра выиграна
                    self.is_record()
                    self.show_game_win_text()  # Показываем текст выигрыша
                    add_color = 0
                pygame.display.flip()
                clock.tick(60)

    def is_record(self):
        if self.score > self.record[level]:
            self.record[level] = self.score
            con = sqlite3.connect('Game Users.db')
            cur = con.cursor()
            if level == 0:
                cur.execute("UPDATE users SET record1 = ? WHERE login = ?", (self.score, username))
            elif level == 1:
                cur.execute("UPDATE users SET record2 = ? WHERE login = ?", (self.score, username))
            elif level == 2:
                cur.execute("UPDATE users SET record3 = ? WHERE login = ?", (self.score, username))
            con.commit()
            con.close()

    def show_game_win_text(self):
        global music_win_flag, music_win, musics, level, username
        musics[level].stop()
        music_win.play()
        screen.fill(BLACK)
        text = font.render(f"You win! Progress: {self.score}%", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)
        button_text = font.render("New Game", True, BLACK)
        button_rect = button_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        pygame.draw.rect(screen, GREEN, button_rect.inflate(20, 20))
        screen.blit(button_text, button_rect)
        button2_text = font.render("Choose Level", True, BLACK)
        text_x = WIDTH // 2 + 13 - button2_text.get_width() // 2
        text_y = HEIGHT // 2 + 10 - button2_text.get_height() // 2
        text_w = button2_text.get_width()
        text_h = button2_text.get_height()
        button2_rect = pygame.Rect(text_x - 17, text_y - 15, text_w + 10, text_h + 10)
        pygame.draw.rect(screen, GREEN, button2_rect)
        screen.blit(button2_text, button2_rect)
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and button_rect.collidepoint(mouse_pos):
            self.restart_game()
            self.start = False
            music_win.stop()
            musics[level].play()
        elif pygame.mouse.get_pressed()[0] and button2_rect.collidepoint(mouse_pos):
            self.game_win = False
            self.start = True
            music_win.stop()
            start_settings()

    def start_screen(self):
        global username
        record = get_record()
        screen.fill(BLACK)

        button_4_text = font.render("Log out", True, BLACK)
        text_x = WIDTH - 50 - button_4_text.get_width() // 2
        text_y = HEIGHT - 30 - button_4_text.get_height() // 2
        text_w = button_4_text.get_width()
        text_h = button_4_text.get_height()
        button_4_rect = pygame.Rect(text_x - 20, text_y - 20, text_w + 10, text_h + 10)
        pygame.draw.rect(screen, (0, 255, 0), button_4_rect)
        screen.blit(button_4_text, button_4_rect)

        welcome = font.render(f'Welcome to Pygame Geometry Lite!'.upper(), True, GREEN)
        choose = font.render(f'Choose level by keypad:'.upper(), True, WHITE)
        username_text = font.render(username, True, WHITE)
        record_text = font.render(f"Best score: {record[level]}".upper(), True, WHITE)
        controls = font.render('Instruction:'.upper(), True, GREEN)
        jump = font.render('start/jump: Space'.upper(), True, GREEN)
        exit_text = font.render('exit: Esc'.upper(), True, GREEN)
        chosen_level = font.render(f"Level {level + 1}".upper(), True, WHITE)
        screen.blits([(welcome, (180, 100)), [choose, (100, 150)], [record_text, (100, 275)], [controls, (100, 400)],
                      [jump, (100, 450)], [exit_text, (100, 500)], [chosen_level, (100, 200)],
                      [username_text, (750 - username_text.get_width(), 35)]])
        pygame.display.flip()
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and button_4_rect.collidepoint(mouse_pos):
            starting()

    def restart_game(self):
        musics[level].stop()
        musics[level].play()
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
            self.attempt_text = AttemptText(f'Attempt: {self.attempt_count}', 200, 200)


def start_settings():
    pygame.init()
    global level
    waiting = True
    flag = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
                flag = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    waiting = False
                    flag = False
                if event.key == pygame.K_1:
                    level = 0
                if event.key == pygame.K_2:
                    level = 1
                if event.key == pygame.K_3:
                    level = 2
        Game().start_screen()
        pygame.display.flip()
    if flag:
        Game().run()
    pygame.quit()


def get_record():
    global username
    con = sqlite3.connect("Game Users.db")
    cur = con.cursor()
    record = \
        cur.execute("SELECT record1, record2, record3 FROM users WHERE login = ?", (username,)).fetchall()[
            0]
    con.commit()
    con.close()
    return record


def starting():
    global username
    pygame.init()
    username = Login().draw_login_screen()
    start_settings()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    starting()
