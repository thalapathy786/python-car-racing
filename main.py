import asyncio
import math
import os
import random

import pygame


# ============================================================
# PYGAME INITIALIZATION
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    pass


# ============================================================
# GAME SIZE
# ============================================================

BASE_WIDTH = 600
BASE_HEIGHT = 800

WIDTH = BASE_WIDTH
HEIGHT = BASE_HEIGHT

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption("Python Car Racing")

clock = pygame.time.Clock()


# ============================================================
# COLORS
# ============================================================

GRASS = (40, 150, 40)
ROAD = (60, 60, 60)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RED = (220, 30, 30)
BLUE = (30, 100, 220)
YELLOW = (255, 180, 30)
GREEN = (30, 200, 100)

WINDOW_COLOR = (120, 200, 230)
TIRE_COLOR = (20, 20, 20)
HEADLIGHT_COLOR = (255, 255, 180)

BUTTON_COLOR = (40, 40, 40)
BUTTON_PRESSED = (90, 90, 90)

ORANGE = (255, 140, 0)


# ============================================================
# ROAD
# ============================================================

ROAD_LEFT = 100
ROAD_RIGHT = 500
ROAD_WIDTH = 400

road_line_offset = 0


# ============================================================
# PLAYER
# ============================================================

CAR_WIDTH = 50
CAR_HEIGHT = 90

car_x = 275
car_speed = 7


def get_player_y():
    return BASE_HEIGHT - 150


# ============================================================
# TRAFFIC
# ============================================================

ENEMY_WIDTH = 50
ENEMY_HEIGHT = 90

MAX_ENEMIES = 7

ENEMY_COLORS = [
    BLUE,
    YELLOW,
    GREEN
]

MIN_HORIZONTAL_GAP = 55


def get_min_enemy_x():
    return ROAD_LEFT + 5


def get_max_enemy_x():
    return ROAD_RIGHT - ENEMY_WIDTH - 5


# ============================================================
# SOUND
# ============================================================

sound_enabled = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_FOLDER = os.path.join(BASE_DIR, "sounds")


def load_sound(filename):

    path = os.path.join(SOUND_FOLDER, filename)

    if not os.path.exists(path):
        return None

    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None


crash_sound = load_sound("crash.ogg")
score_sound = load_sound("score.ogg")
click_sound = load_sound("click.ogg")
start_sound = load_sound("start.ogg")


def play_sound(sound):

    if sound_enabled and sound is not None:

        try:
            sound.play()
        except pygame.error:
            pass


# ============================================================
# SCALING
# ============================================================

scale_x = 1.0
scale_y = 1.0
scale = 1.0


def update_scale():

    global WIDTH
    global HEIGHT
    global scale_x
    global scale_y
    global scale

    WIDTH, HEIGHT = screen.get_size()

    if WIDTH <= 0:
        WIDTH = BASE_WIDTH

    if HEIGHT <= 0:
        HEIGHT = BASE_HEIGHT

    scale_x = WIDTH / BASE_WIDTH
    scale_y = HEIGHT / BASE_HEIGHT

    scale = min(scale_x, scale_y)


def sx(value):
    return int(value * scale_x)


def sy(value):
    return int(value * scale_y)


def ss(value):
    return max(1, int(value * scale))


update_scale()


# ============================================================
# FONTS
# ============================================================

def create_fonts():

    return {
        "title": pygame.font.Font(None, ss(72)),
        "large": pygame.font.Font(None, ss(58)),
        "score": pygame.font.Font(None, ss(34)),
        "button": pygame.font.Font(None, ss(28)),
        "control": pygame.font.Font(None, ss(38)),
        "countdown": pygame.font.Font(None, ss(120)),
        "small": pygame.font.Font(None, ss(26)),
    }


fonts = create_fonts()


# ============================================================
# BUTTONS
# ============================================================

start_button = pygame.Rect(0, 0, 0, 0)
pause_button = pygame.Rect(0, 0, 0, 0)
sound_button = pygame.Rect(0, 0, 0, 0)
left_button = pygame.Rect(0, 0, 0, 0)
right_button = pygame.Rect(0, 0, 0, 0)


def update_buttons():

    global start_button
    global pause_button
    global sound_button
    global left_button
    global right_button

    start_button = pygame.Rect(
        WIDTH // 2 - sx(120),
        sy(430),
        sx(240),
        sy(70)
    )

    pause_button = pygame.Rect(
        WIDTH - sx(110),
        sy(20),
        sx(90),
        sy(45)
    )

    sound_button = pygame.Rect(
        WIDTH - sx(210),
        sy(20),
        sx(90),
        sy(45)
    )

    left_button = pygame.Rect(
        sx(35),
        HEIGHT - sy(100),
        sx(220),
        sy(70)
    )

    right_button = pygame.Rect(
        WIDTH - sx(255),
        HEIGHT - sy(100),
        sx(220),
        sy(70)
    )


update_buttons()


# ============================================================
# GAME STATE
# ============================================================

game_started = False
game_over = False
paused = False

score = 0
best_score = 0
lives = 3


# ============================================================
# COUNTDOWN
# ============================================================

countdown_active = False
countdown_start_time = 0
countdown_text = ""
race_started = False


def start_countdown():

    global countdown_active
    global countdown_start_time
    global countdown_text
    global race_started

    countdown_active = True
    countdown_start_time = pygame.time.get_ticks()
    countdown_text = "3"
    race_started = False

    play_sound(start_sound)


def update_countdown():

    global countdown_active
    global countdown_text
    global race_started

    if not countdown_active:
        return

    elapsed = pygame.time.get_ticks() - countdown_start_time

    if elapsed < 1000:
        countdown_text = "3"

    elif elapsed < 2000:
        countdown_text = "2"

    elif elapsed < 3000:
        countdown_text = "1"

    elif elapsed < 4000:
        countdown_text = "GO!"

    else:
        countdown_active = False
        countdown_text = ""
        race_started = True


# ============================================================
# COLLISION
# ============================================================

collision_cooldown = 0
COLLISION_COOLDOWN_TIME = 60


# ============================================================
# EXPLOSION
# ============================================================

crash_timer = 0
CRASH_ANIMATION_TIME = 45

explosion_particles = []


def create_explosion(x, y):

    global explosion_particles

    explosion_particles = []

    for _ in range(30):

        explosion_particles.append({
            "x": x + 25,
            "y": y + 45,
            "dx": random.uniform(-5, 5),
            "dy": random.uniform(-5, 5),
            "size": random.randint(4, 9),
            "life": random.randint(20, 45),
        })


def update_explosion():

    global explosion_particles

    for particle in explosion_particles:

        particle["x"] += particle["dx"]
        particle["y"] += particle["dy"]

        particle["dy"] += 0.15

        particle["life"] -= 1
        particle["size"] -= 0.1

    explosion_particles = [
        p for p in explosion_particles
        if p["life"] > 0
    ]


def draw_explosion():

    for particle in explosion_particles:

        size = max(
            1,
            int(particle["size"] * scale)
        )

        pygame.draw.circle(
            screen,
            ORANGE,
            (
                sx(particle["x"]),
                sy(particle["y"])
            ),
            size
        )


# ============================================================
# TRAFFIC CREATION
# ============================================================

def create_enemy(x, y):

    return {
        "x": x,
        "y": y,
        "speed": random.randint(4, 6),
        "color": random.choice(ENEMY_COLORS),
        "horizontal_speed": random.uniform(-0.8, 0.8),
        "direction_timer": random.randint(40, 120)
    }


def find_spawn_x():

    for _ in range(100):

        x = random.randint(
            get_min_enemy_x(),
            get_max_enemy_x()
        )

        safe = True

        for enemy in enemies:

            if enemy["y"] < 300:

                if abs(enemy["x"] - x) < MIN_HORIZONTAL_GAP:

                    safe = False
                    break

        if safe:
            return x

    return random.randint(
        get_min_enemy_x(),
        get_max_enemy_x()
    )


def create_enemies():

    result = []

    spawn_y = [
        -150,
        -450,
        -750
    ]

    for y in spawn_y:

        x = random.randint(
            get_min_enemy_x(),
            get_max_enemy_x()
        )

        result.append(
            create_enemy(x, y)
        )

    return result


enemies = create_enemies()


# ============================================================
# DIFFICULTY
# ============================================================

def get_difficulty():

    level = 1 + score // 100

    speed_bonus = min(level - 1, 8)

    target_enemies = min(
        3 + level // 2,
        MAX_ENEMIES
    )

    return level, speed_bonus, target_enemies


def add_enemy():

    if len(enemies) >= MAX_ENEMIES:
        return

    x = find_spawn_x()

    highest_y = -100

    for enemy in enemies:

        if enemy["y"] < highest_y:
            highest_y = enemy["y"]

    spawn_y = highest_y - random.randint(180, 300)

    enemies.append(
        create_enemy(x, spawn_y)
    )


# ============================================================
# RESET GAME
# ============================================================

def reset_input():

    global mouse_left_pressed
    global mouse_right_pressed
    global touch_left
    global touch_right

    mouse_left_pressed = False
    mouse_right_pressed = False
    touch_left = False
    touch_right = False


def reset_game():

    global car_x
    global score
    global lives
    global best_score
    global game_over
    global paused
    global enemies
    global road_line_offset
    global collision_cooldown
    global crash_timer
    global explosion_particles
    global countdown_active
    global countdown_start_time
    global countdown_text
    global race_started

    car_x = 275
    score = 0
    lives = 3

    game_over = False
    paused = False

    enemies = create_enemies()

    road_line_offset = 0

    collision_cooldown = 0
    crash_timer = 0

    explosion_particles = []

    countdown_active = False
    countdown_start_time = 0
    countdown_text = ""

    race_started = False

    reset_input()


# ============================================================
# INPUT
# ============================================================

mouse_left_pressed = False
mouse_right_pressed = False

touch_left = False
touch_right = False


def set_mouse_control(position):

    global mouse_left_pressed
    global mouse_right_pressed

    mouse_left_pressed = False
    mouse_right_pressed = False

    if left_button.collidepoint(position):
        mouse_left_pressed = True

    elif right_button.collidepoint(position):
        mouse_right_pressed = True


def set_touch_control(position):

    global touch_left
    global touch_right

    touch_left = False
    touch_right = False

    if left_button.collidepoint(position):
        touch_left = True

    elif right_button.collidepoint(position):
        touch_right = True


def clear_controls():

    global mouse_left_pressed
    global mouse_right_pressed
    global touch_left
    global touch_right

    mouse_left_pressed = False
    mouse_right_pressed = False
    touch_left = False
    touch_right = False


# ============================================================
# CAR DRAWING
# ============================================================

def draw_player_car(x, y):

    x = sx(x)
    y = sy(y)

    pygame.draw.rect(
        screen,
        RED,
        (
            x + sx(5),
            y,
            sx(40),
            sy(90)
        ),
        border_radius=ss(10)
    )

    pygame.draw.rect(
        screen,
        WINDOW_COLOR,
        (
            x + sx(12),
            y + sy(12),
            sx(26),
            sy(20)
        ),
        border_radius=ss(5)
    )

    pygame.draw.rect(
        screen,
        WINDOW_COLOR,
        (
            x + sx(12),
            y + sy(55),
            sx(26),
            sy(18)
        ),
        border_radius=ss(5)
    )

    for wx, wy in [
        (0, 15),
        (42, 15),
        (0, 55),
        (42, 55)
    ]:

        pygame.draw.rect(
            screen,
            TIRE_COLOR,
            (
                x + sx(wx),
                y + sy(wy),
                sx(8),
                sy(25)
            ),
            border_radius=ss(3)
        )

    for hx in [10, 30]:

        pygame.draw.rect(
            screen,
            HEADLIGHT_COLOR,
            (
                x + sx(hx),
                y + sy(2),
                sx(10),
                sy(7)
            ),
            border_radius=ss(2)
        )


def draw_enemy_car(x, y, color):

    x = sx(x)
    y = sy(y)

    pygame.draw.rect(
        screen,
        color,
        (
            x + sx(5),
            y,
            sx(40),
            sy(90)
        ),
        border_radius=ss(10)
    )

    pygame.draw.rect(
        screen,
        WINDOW_COLOR,
        (
            x + sx(12),
            y + sy(12),
            sx(26),
            sy(20)
        ),
        border_radius=ss(5)
    )

    pygame.draw.rect(
        screen,
        WINDOW_COLOR,
        (
            x + sx(12),
            y + sy(55),
            sx(26),
            sy(18)
        ),
        border_radius=ss(5)
    )

    for wx, wy in [
        (0, 15),
        (42, 15),
        (0, 55),
        (42, 55)
    ]:

        pygame.draw.rect(
            screen,
            TIRE_COLOR,
            (
                x + sx(wx),
                y + sy(wy),
                sx(8),
                sy(25)
            ),
            border_radius=ss(3)
        )

    for lx in [10, 30]:

        pygame.draw.rect(
            screen,
            RED,
            (
                x + sx(lx),
                y + sy(81),
                sx(10),
                sy(7)
            ),
            border_radius=ss(2)
        )


# ============================================================
# TEXT HELPER
# ============================================================

def draw_centered(text, font, color, y):

    rendered = font.render(
        text,
        True,
        color
    )

    screen.blit(
        rendered,
        (
            WIDTH // 2 - rendered.get_width() // 2,
            sy(y)
        )
    )


# ============================================================
# MAIN ASYNC GAME
# ============================================================

async def main():

    global screen
    global fonts

    global game_started
    global game_over
    global paused

    global sound_enabled

    global car_x
    global score
    global best_score
    global lives

    global road_line_offset

    global collision_cooldown
    global crash_timer

    global mouse_left_pressed
    global mouse_right_pressed
    global touch_left
    global touch_right

    running = True

    while running:

        # ====================================================
        # EVENTS
        # ====================================================

        for event in pygame.event.get():

            # ------------------------------------------------
            # QUIT
            # ------------------------------------------------

            if event.type == pygame.QUIT:

                running = False

            # ------------------------------------------------
            # RESIZE
            # ------------------------------------------------

            elif event.type == pygame.VIDEORESIZE:

                new_width = max(480, event.w)
                new_height = max(640, event.h)

                screen = pygame.display.set_mode(
                    (
                        new_width,
                        new_height
                    ),
                    pygame.RESIZABLE
                )

                update_scale()

                fonts = create_fonts()

                update_buttons()

            # ------------------------------------------------
            # KEYBOARD
            # ------------------------------------------------

            elif event.type == pygame.KEYDOWN:

                # START
                if not game_started:

                    if event.key in (
                        pygame.K_RETURN,
                        pygame.K_SPACE
                    ):

                        game_started = True

                        reset_game()

                        start_countdown()

                # GAME
                elif not game_over:

                    # P = PAUSE / PLAY
                    if event.key == pygame.K_p:

                        if not countdown_active:

                            paused = not paused

                            clear_controls()

                            play_sound(click_sound)

                    # ESC = PAUSE / PLAY
                    elif event.key == pygame.K_ESCAPE:

                        if not countdown_active:

                            paused = not paused

                            clear_controls()

                            play_sound(click_sound)

                    # M = SOUND
                    elif event.key == pygame.K_m:

                        sound_enabled = not sound_enabled

                        if sound_enabled:
                            play_sound(click_sound)

                # GAME OVER
                else:

                    if event.key in (
                        pygame.K_r,
                        pygame.K_RETURN,
                        pygame.K_SPACE
                    ):

                        reset_game()

                        start_countdown()

            # ------------------------------------------------
            # MOUSE DOWN
            # ------------------------------------------------

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    pos = event.pos

                    # START
                    if not game_started:

                        if start_button.collidepoint(pos):

                            game_started = True

                            reset_game()

                            start_countdown()

                    # GAME
                    elif not game_over:

                        # PAUSE
                        if pause_button.collidepoint(pos):

                            if not countdown_active:

                                paused = not paused

                                clear_controls()

                                play_sound(click_sound)

                        # SOUND
                        elif sound_button.collidepoint(pos):

                            sound_enabled = not sound_enabled

                            if sound_enabled:
                                play_sound(click_sound)

                        # CONTROLS
                        else:

                            if not paused and not countdown_active:

                                set_mouse_control(pos)

                    # GAME OVER
                    else:

                        # Click anywhere to restart
                        reset_game()

                        start_countdown()

                        game_started = True

            # ------------------------------------------------
            # MOUSE UP
            # ------------------------------------------------

            elif event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:

                    mouse_left_pressed = False
                    mouse_right_pressed = False

            # ------------------------------------------------
            # MOUSE MOTION
            # ------------------------------------------------

            elif event.type == pygame.MOUSEMOTION:

                if pygame.mouse.get_pressed()[0]:

                    if not paused and not countdown_active:

                        set_mouse_control(event.pos)

                else:

                    mouse_left_pressed = False
                    mouse_right_pressed = False

            # ------------------------------------------------
            # TOUCH DOWN
            # ------------------------------------------------

            elif event.type == pygame.FINGERDOWN:

                pos = (
                    int(event.x * WIDTH),
                    int(event.y * HEIGHT)
                )

                if not game_started:

                    if start_button.collidepoint(pos):

                        game_started = True

                        reset_game()

                        start_countdown()

                elif not game_over:

                    if pause_button.collidepoint(pos):

                        if not countdown_active:

                            paused = not paused

                            clear_controls()

                            play_sound(click_sound)

                    elif sound_button.collidepoint(pos):

                        sound_enabled = not sound_enabled

                        if sound_enabled:
                            play_sound(click_sound)

                    elif not paused and not countdown_active:

                        set_touch_control(pos)

            # ------------------------------------------------
            # TOUCH MOTION
            # ------------------------------------------------

            elif event.type == pygame.FINGERMOTION:

                pos = (
                    int(event.x * WIDTH),
                    int(event.y * HEIGHT)
                )

                if not paused and not countdown_active:

                    set_touch_control(pos)

            # ------------------------------------------------
            # TOUCH UP
            # ------------------------------------------------

            elif event.type == pygame.FINGERUP:

                touch_left = False
                touch_right = False

        # ====================================================
        # COUNTDOWN
        # ====================================================

        if (
            game_started
            and not game_over
            and not paused
            and countdown_active
        ):

            update_countdown()

        # ====================================================
        # GAME LOGIC
        # ====================================================

        if (
            game_started
            and not game_over
            and not paused
            and race_started
        ):

            # -----------------------------------------------
            # KEYBOARD
            # -----------------------------------------------

            keys = pygame.key.get_pressed()

            if keys[pygame.K_LEFT]:
                car_x -= car_speed

            if keys[pygame.K_RIGHT]:
                car_x += car_speed

            # -----------------------------------------------
            # MOUSE
            # -----------------------------------------------

            if mouse_left_pressed:
                car_x -= car_speed

            if mouse_right_pressed:
                car_x += car_speed

            # -----------------------------------------------
            # TOUCH
            # -----------------------------------------------

            if touch_left:
                car_x -= car_speed

            if touch_right:
                car_x += car_speed

            # -----------------------------------------------
            # PLAYER LIMIT
            # -----------------------------------------------

            car_x = max(
                105,
                min(445, car_x)
            )

            # -----------------------------------------------
            # DIFFICULTY
            # -----------------------------------------------

            level, speed_bonus, target_enemies = get_difficulty()

            # -----------------------------------------------
            # ROAD
            # -----------------------------------------------

            road_line_offset += 5 + speed_bonus

            if road_line_offset >= 80:
                road_line_offset = 0

            # -----------------------------------------------
            # TRAFFIC COUNT
            # -----------------------------------------------

            while len(enemies) < target_enemies:
                add_enemy()

            # -----------------------------------------------
            # PLAYER RECT
            # -----------------------------------------------

            player_rect = pygame.Rect(
                car_x + 5,
                get_player_y(),
                40,
                90
            )

            # -----------------------------------------------
            # ENEMIES
            # -----------------------------------------------

            for enemy in enemies:

                enemy["y"] += (
                    enemy["speed"]
                    + speed_bonus
                )

                # Horizontal movement from level 3
                if level >= 3:

                    enemy["x"] += enemy["horizontal_speed"]

                    if enemy["x"] <= get_min_enemy_x():

                        enemy["x"] = get_min_enemy_x()

                        enemy["horizontal_speed"] = abs(
                            enemy["horizontal_speed"]
                        )

                    if enemy["x"] >= get_max_enemy_x():

                        enemy["x"] = get_max_enemy_x()

                        enemy["horizontal_speed"] = -abs(
                            enemy["horizontal_speed"]
                        )

                    enemy["direction_timer"] -= 1

                    if enemy["direction_timer"] <= 0:

                        enemy["horizontal_speed"] = random.uniform(
                            -1.2,
                            1.2
                        )

                        enemy["direction_timer"] = random.randint(
                            40,
                            120
                        )

                # -------------------------------------------
                # PASSED PLAYER
                # -------------------------------------------

                if enemy["y"] > BASE_HEIGHT:

                    score += 10

                    if score > best_score:
                        best_score = score

                    play_sound(score_sound)

                    enemy["x"] = find_spawn_x()

                    enemy["y"] = random.randint(
                        -600,
                        -200
                    )

                    enemy["speed"] = random.randint(
                        4,
                        7
                    )

                # -------------------------------------------
                # COLLISION
                # -------------------------------------------

                enemy_rect = pygame.Rect(
                    enemy["x"] + 5,
                    enemy["y"],
                    40,
                    90
                )

                if (
                    player_rect.colliderect(enemy_rect)
                    and collision_cooldown == 0
                ):

                    lives -= 1

                    collision_cooldown = COLLISION_COOLDOWN_TIME

                    crash_timer = CRASH_ANIMATION_TIME

                    create_explosion(
                        car_x,
                        get_player_y()
                    )

                    play_sound(crash_sound)

                    enemy["y"] = random.randint(
                        -600,
                        -250
                    )

                    enemy["x"] = find_spawn_x()

                    if lives <= 0:

                        game_over = True

                        clear_controls()

            # -----------------------------------------------
            # COLLISION TIMER
            # -----------------------------------------------

            if collision_cooldown > 0:

                collision_cooldown -= 1

            # -----------------------------------------------
            # EXPLOSION
            # -----------------------------------------------

            if crash_timer > 0:

                crash_timer -= 1

                update_explosion()

        # ====================================================
        # DRAW BACKGROUND
        # ====================================================

        screen.fill(GRASS)

        # ====================================================
        # ROAD
        # ====================================================

        pygame.draw.rect(
            screen,
            ROAD,
            (
                sx(ROAD_LEFT),
                0,
                sx(ROAD_WIDTH),
                HEIGHT
            )
        )

        # ====================================================
        # ROAD BORDERS
        # ====================================================

        pygame.draw.line(
            screen,
            WHITE,
            (
                sx(ROAD_LEFT),
                0
            ),
            (
                sx(ROAD_LEFT),
                HEIGHT
            ),
            ss(5)
        )

        pygame.draw.line(
            screen,
            WHITE,
            (
                sx(ROAD_RIGHT),
                0
            ),
            (
                sx(ROAD_RIGHT),
                HEIGHT
            ),
            ss(5)
        )

        # ====================================================
        # ROAD CENTER LINE
        # ====================================================

        for y in range(-80, BASE_HEIGHT, 80):

            line_y = y + road_line_offset

            pygame.draw.rect(
                screen,
                WHITE,
                (
                    sx(295),
                    sy(line_y),
                    sx(10),
                    sy(40)
                )
            )

        # ====================================================
        # START SCREEN
        # ====================================================

        if not game_started:

            draw_centered(
                "CAR RACING",
                fonts["title"],
                WHITE,
                250
            )

            pygame.draw.rect(
                screen,
                RED,
                start_button,
                border_radius=ss(10)
            )

            draw_centered(
                "START GAME",
                fonts["large"],
                WHITE,
                432
            )

            draw_centered(
                "CLICK START OR PRESS ENTER",
                fonts["small"],
                WHITE,
                530
            )

        # ====================================================
        # GAME
        # ====================================================

        else:

            # ------------------------------------------------
            # ENEMIES
            # ------------------------------------------------

            for enemy in enemies:

                draw_enemy_car(
                    enemy["x"],
                    enemy["y"],
                    enemy["color"]
                )

            # ------------------------------------------------
            # PLAYER
            # ------------------------------------------------

            if collision_cooldown == 0:

                draw_player_car(
                    car_x,
                    get_player_y()
                )

            elif collision_cooldown % 10 < 5:

                draw_player_car(
                    car_x,
                    get_player_y()
                )

            # ------------------------------------------------
            # EXPLOSION
            # ------------------------------------------------

            if crash_timer > 0:
                draw_explosion()

            # =================================================
            # HUD
            # =================================================

            hud_x = sx(15)
            hud_y = sy(15)

            score_surface = fonts["score"].render(
                f"Score: {score}",
                True,
                WHITE
            )

            lives_surface = fonts["score"].render(
                f"Lives: {lives}",
                True,
                WHITE
            )

            best_surface = fonts["score"].render(
                f"Best: {best_score}",
                True,
                WHITE
            )

            level, _, _ = get_difficulty()

            level_surface = fonts["score"].render(
                f"Level: {level}",
                True,
                WHITE
            )

            traffic_surface = fonts["score"].render(
                f"Traffic: {len(enemies)}",
                True,
                WHITE
            )

            screen.blit(
                score_surface,
                (
                    hud_x,
                    hud_y
                )
            )

            screen.blit(
                lives_surface,
                (
                    hud_x,
                    hud_y + sy(38)
                )
            )

            screen.blit(
                best_surface,
                (
                    hud_x,
                    hud_y + sy(76)
                )
            )

            screen.blit(
                level_surface,
                (
                    hud_x,
                    hud_y + sy(114)
                )
            )

            screen.blit(
                traffic_surface,
                (
                    hud_x,
                    hud_y + sy(152)
                )
            )


            # =================================================
            # SOUND BUTTON
            # =================================================

            pygame.draw.rect(
                screen,
                BLACK,
                sound_button,
                border_radius=ss(8)
            )

            sound_text = fonts["button"].render(
                "SOUND" if sound_enabled else "MUTE",
                True,
                WHITE
            )

            screen.blit(
                sound_text,
                (
                    sound_button.centerx
                    - sound_text.get_width() // 2,
                    sound_button.centery
                    - sound_text.get_height() // 2
                )
            )

            # =================================================
            # PAUSE BUTTON
            # =================================================

            pygame.draw.rect(
                screen,
                BLACK,
                pause_button,
                border_radius=ss(8)
            )

            pause_text = fonts["button"].render(
                "PLAY" if paused else "PAUSE",
                True,
                WHITE
            )

            screen.blit(
                pause_text,
                (
                    pause_button.centerx
                    - pause_text.get_width() // 2,
                    pause_button.centery
                    - pause_text.get_height() // 2
                )
            )

            # =================================================
            # LEFT BUTTON
            # =================================================

            left_color = (
                BUTTON_PRESSED
                if mouse_left_pressed or touch_left
                else BUTTON_COLOR
            )

            pygame.draw.rect(
                screen,
                left_color,
                left_button,
                border_radius=ss(15)
            )

            left_text = fonts["control"].render(
                "◀ LEFT",
                True,
                WHITE
            )

            screen.blit(
                left_text,
                (
                    left_button.centerx
                    - left_text.get_width() // 2,
                    left_button.centery
                    - left_text.get_height() // 2
                )
            )

            # =================================================
            # RIGHT BUTTON
            # =================================================

            right_color = (
                BUTTON_PRESSED
                if mouse_right_pressed or touch_right
                else BUTTON_COLOR
            )

            pygame.draw.rect(
                screen,
                right_color,
                right_button,
                border_radius=ss(15)
            )

            right_text = fonts["control"].render(
                "RIGHT ▶",
                True,
                WHITE
            )

            screen.blit(
                right_text,
                (
                    right_button.centerx
                    - right_text.get_width() // 2,
                    right_button.centery
                    - right_text.get_height() // 2
                )
            )

            # =================================================
            # COUNTDOWN
            # =================================================

            if countdown_active:

                overlay = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )

                overlay.fill(
                    (0, 0, 0, 130)
                )

                screen.blit(
                    overlay,
                    (0, 0)
                )

                draw_centered(
                    countdown_text,
                    fonts["countdown"],
                    WHITE,
                    280
                )

            # =================================================
            # PAUSED
            # =================================================

            if paused:

                overlay = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )

                overlay.fill(
                    (0, 0, 0, 120)
                )

                screen.blit(
                    overlay,
                    (0, 0)
                )

                draw_centered(
                    "PAUSED",
                    fonts["large"],
                    WHITE,
                    330
                )

                draw_centered(
                    "Press P or click PLAY",
                    fonts["score"],
                    WHITE,
                    400
                )

            # =================================================
            # GAME OVER
            # =================================================

            if game_over:

                overlay = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )

                overlay.fill(
                    (0, 0, 0, 170)
                )

                screen.blit(
                    overlay,
                    (0, 0)
                )

                draw_centered(
                    "GAME OVER",
                    fonts["large"],
                    WHITE,
                    280
                )

                draw_centered(
                    f"Final Score: {score}",
                    fonts["score"],
                    WHITE,
                    350
                )

                draw_centered(
                    f"Best Score: {best_score}",
                    fonts["score"],
                    WHITE,
                    350
                )

                draw_centered(
                    "Press R to Restart",
                    fonts["score"],
                    WHITE,
                    440
                )

        # ====================================================
        # DISPLAY
        # ====================================================

        pygame.display.flip()

        # ====================================================
        # IMPORTANT FOR PYGBAG / CHROME
        # ====================================================

        clock.tick(60)

        await asyncio.sleep(0)


# ============================================================
# START
# ============================================================

asyncio.run(main())
