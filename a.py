import pygame
import sys
import math
import time
import numpy as np

# --- Setup ---
pygame.init()
WIDTH, HEIGHT = 480, 320
TILE_SIZE = 32
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GPTZELDA - Mouse-Controlled Open World")
clock = pygame.time.Clock()

# --- Colors ---
GRASS = (34, 139, 34)
TREE = (20, 70, 20)
PLAYER_COLOR = (255, 240, 100)
SWORD_COLOR = (240, 240, 255)
MENU_BG = (10, 20, 40)
MENU_TEXT = (255, 255, 220)

font = pygame.font.SysFont('Consolas', 32)
font_small = pygame.font.SysFont('Consolas', 18)

# --- Audio: Procedural Overworld Theme ---
SAMPLE_RATE = 22050
BPM = 120

# Ensure Pygame mixer is mono (or generate 2D array for stereo)
pygame.mixer.quit()
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)

def make_overworld_theme():
    # Chiptune Zelda 1 overworld intro (very basic)
    notes = [
        ('E5', 0.3), ('E5', 0.3), ('E5', 0.6), ('C5', 0.3), ('E5', 0.3), ('G5', 0.6),
        ('G4', 0.6), ('C5', 0.3), ('D5', 0.3), ('B4', 0.6),
    ]
    freqs = {'C5':523.25,'D5':587.33,'E5':659.25,'G5':783.99,'B4':493.88,'G4':392.00}
    song = np.zeros(int(SAMPLE_RATE*sum(t for n, t in notes)), dtype=np.float32)
    idx = 0
    for n, dur in notes:
        f = freqs.get(n, 440.0)
        t = np.linspace(0, dur, int(SAMPLE_RATE*dur), False)
        wave = 0.4 * np.sign(np.sin(2 * np.pi * f * t))  # Square wave
        song[idx:idx+len(wave)] += wave
        idx += len(wave)
    # Normalize
    song = np.clip(song, -1, 1)
    song = (song * 32767).astype(np.int16)
    # Expand to (N,2) for stereo if needed
    if pygame.mixer.get_init()[2] == 2:
        song = np.stack((song, song), axis=-1)
    return pygame.sndarray.make_sound(song)

overworld_theme = make_overworld_theme()

def play_music():
    try:
        overworld_theme.play(loops=-1)
    except Exception as e:
        print(f"Audio error: {e}")

# --- Main Menu ---
def main_menu():
    while True:
        screen.fill(MENU_BG)
        title = font.render("WELCOME TO GPTZELDA", True, MENU_TEXT)
        prompt = font_small.render("PRESS CLICK TO START", True, MENU_TEXT)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 70))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                play_music()
                return  # Start game
        pygame.display.flip()
        clock.tick(30)

# --- Player ---
player_pos = [WIDTH // 2, HEIGHT // 2]
player_speed = 2.2
player_radius = 11
target_pos = None

# --- Sword ---
sword_active = False
sword_angle = 0
sword_length = 26
sword_cooldown = 0.4 # seconds
last_swing = 0

def player_rect():
    return pygame.Rect(player_pos[0]-player_radius//2, player_pos[1]-player_radius//2, player_radius, player_radius)

# --- World Map (simple tile data for trees) ---
MAP_WIDTH, MAP_HEIGHT = 30, 20
world = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
for i in range(MAP_WIDTH):
    if i % 3 == 0:
        world[5][i] = 1
        world[10][i] = 1
for j in range(MAP_HEIGHT):
    world[j][8] = 1

# --- Camera offset ---
camera_x, camera_y = 0, 0

def draw_world():
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile_x = x * TILE_SIZE - camera_x
            tile_y = y * TILE_SIZE - camera_y
            rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, GRASS, rect)
            if world[y][x] == 1:
                pygame.draw.rect(screen, TREE, rect)

def can_move_to(nx, ny):
    px, py = int((nx) // TILE_SIZE), int((ny) // TILE_SIZE)
    if 0 <= px < MAP_WIDTH and 0 <= py < MAP_HEIGHT:
        if world[py][px] == 1:
            return False
    if nx < player_radius or ny < player_radius: return False
    if nx > MAP_WIDTH*TILE_SIZE-player_radius or ny > MAP_HEIGHT*TILE_SIZE-player_radius: return False
    return True

def move_toward_target():
    global player_pos, target_pos
    if target_pos:
        dx = target_pos[0] - player_pos[0]
        dy = target_pos[1] - player_pos[1]
        dist = math.hypot(dx, dy)
        if dist > 2:
            dx, dy = dx / dist, dy / dist
            nx = player_pos[0] + dx * player_speed
            ny = player_pos[1] + dy * player_speed
            if can_move_to(nx, ny):
                player_pos[0] = nx
                player_pos[1] = ny
            else:
                target_pos = None
        else:
            target_pos = None

def draw_player_and_sword():
    px, py = int(player_pos[0] - camera_x), int(player_pos[1] - camera_y)
    pygame.draw.circle(screen, PLAYER_COLOR, (px, py), player_radius)
    if sword_active:
        sx = px + int(math.cos(sword_angle) * (player_radius + 10))
        sy = py + int(math.sin(sword_angle) * (player_radius + 10))
        ex = px + int(math.cos(sword_angle) * (player_radius + sword_length))
        ey = py + int(math.sin(sword_angle) * (player_radius + sword_length))
        pygame.draw.line(screen, SWORD_COLOR, (sx, sy), (ex, ey), 4)

# --- MAIN GAME LOOP ---
def main_game():
    global camera_x, camera_y, target_pos, sword_active, sword_angle, last_swing

    running = True
    while running:
        clock.tick(FPS)
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    target_pos = [mx + camera_x, my + camera_y]
                elif event.button == 3:
                    now = time.time()
                    if now - last_swing > sword_cooldown:
                        sword_active = True
                        last_swing = now
                        mx, my = pygame.mouse.get_pos()
                        dx = mx + camera_x - player_pos[0]
                        dy = my + camera_y - player_pos[1]
                        sword_angle = math.atan2(dy, dx)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    sword_active = False

        move_toward_target()

        camera_x = int(player_pos[0] - WIDTH / 2)
        camera_y = int(player_pos[1] - HEIGHT / 2)
        camera_x = max(0, min(camera_x, MAP_WIDTH * TILE_SIZE - WIDTH))
        camera_y = max(0, min(camera_y, MAP_HEIGHT * TILE_SIZE - HEIGHT))

        draw_world()
        draw_player_and_sword()

        info = font_small.render("L-Click: Move  |  R-Click: Sword", True, (230,230,255))
        screen.blit(info, (8, HEIGHT-26))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# --- BOOT: MENU THEN GAME ---
main_menu()
main_game()
