import tkinter as tk
import random
import pygame
import numpy as np
import time

# Initialize Pygame mixer for GameBoy-style sound (stereo)
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)
pygame.mixer.init()

# Game constants
WIDTH, HEIGHT = 600, 400
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 10
BALL_RADIUS = 8
BALL_SPEED = 4
BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_WIDTH = WIDTH // BRICK_COLS
BRICK_HEIGHT = 20
FPS = 60
FRAME_DELAY = 1 / FPS
LIVES = 3

class BreakoutGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Breakout Vibe")
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#222")
        self.canvas.pack()
        self.canvas.focus_set()  # Bug 15: Ensure canvas has focus
        # Initialize sound
        self.frequency = 880  # Hz
        self.duration = 0.1  # seconds
        self.sr = 44100
        t = np.linspace(0, self.duration, int(self.sr * self.duration), False)
        square = 0.5 * np.sign(np.sin(2 * np.pi * self.frequency * t))
        mono = np.int16(square * 32767)
        stereo = np.column_stack((mono, mono))
        self.sound = pygame.sndarray.make_sound(stereo)  # Bug 19: Sound in class
        self.sound_channel = pygame.mixer.Channel(0)  # Bug 4: Use channel to prevent overlap
        # Game state
        self.state = 'menu'
        self.running = False
        self.paused = False  # Bug 7: Pause mechanism
        self.bricks = []
        self.score = 0
        self.high_score = 0  # Bug 17: High score
        self.lives = LIVES  # Bug 11: Lives system
        self.ball_speed = BALL_SPEED  # Bug 10: Dynamic ball speed
        self._setup_menu()
        self.root.bind('<Motion>', self._on_mouse)
        self.root.bind('<Button-1>', self._on_click)
        self.root.bind('<KeyPress>', self._on_key)  # Bug 20: Keyboard controls
        self.last_frame_time = time.time()
        self.root.after(int(FRAME_DELAY * 1000), self._game_loop)
        self.root.protocol("WM_DELETE_WINDOW", self._exit)  # Bug 13: Handle window close
        self.root.mainloop()

    def _setup_menu(self):
        self.canvas.delete('all')
        self.canvas.create_text(WIDTH/2, HEIGHT/2 - 40, text="BREAKOUT VIBE", fill="white", font=("Courier", 32))
        self.canvas.create_rectangle(WIDTH/2-80, HEIGHT/2, WIDTH/2+80, HEIGHT/2+40, fill="#006400", outline="")  # Bug 12: Larger click area
        self.canvas.create_text(WIDTH/2, HEIGHT/2+20, text="PLAY", fill="white", font=("Courier", 18))
        self.canvas.create_text(WIDTH-80, HEIGHT-20, text=f"High Score: {self.high_score}", fill="white", font=("Courier", 12))

    def _start_game(self):
        self.state = 'playing'
        self.running = True
        self.paused = False
        self.score = 0  # Bug 8: Reset score
        self.lives = LIVES
        self.ball_speed = BALL_SPEED
        self.bricks.clear()
        self.canvas.delete('all')
        self._create_bricks()
        self._create_paddle()
        self._create_ball()
        self.hud = self.canvas.create_text(80, 20, text=f"Score: 0  Lives: {self.lives}", fill="white", font=("Courier", 12))

    def _create_paddle(self):
        x = (WIDTH - PADDLE_WIDTH) / 2
        y = HEIGHT - 30
        self.paddle = self.canvas.create_rectangle(x, y, x+PADDLE_WIDTH, y+PADDLE_HEIGHT, fill="#fff", outline="")

    def _create_ball(self):
        # Bug 3: Create ball at correct position
        self.ball = self.canvas.create_oval(WIDTH/2 - BALL_RADIUS, HEIGHT/2 - BALL_RADIUS,
                                           WIDTH/2 + BALL_RADIUS, HEIGHT/2 + BALL_RADIUS, fill="red", outline="")
        self.vx = self.ball_speed * random.choice([-1, 1])
        self.vy = -self.ball_speed

    def _create_bricks(self):
        colors = ["#ff6666", "#ffcc66", "#66ff66", "#66ccff", "#cc66ff"]
        random.shuffle(colors)  # Bug 16: Randomize colors
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x0 = col * BRICK_WIDTH + 2
                y0 = row * BRICK_HEIGHT + 50
                brick = self.canvas.create_rectangle(x0, y0, x0+BRICK_WIDTH-4, y0+BRICK_HEIGHT-4,
                                                    fill=colors[row % len(colors)], outline="")
                self.bricks.append(brick)

    def _update(self):
        if not self.running or self.paused:
            return
        # Move ball
        self.canvas.move(self.ball, self.vx, self.vy)
        x0, y0, x1, y1 = self.canvas.coords(self.ball)
        # Wall collision with boundary fix
        if x0 <= 0:
            self.vx = abs(self.vx); self.canvas.move(self.ball, -x0, 0); self._play_sound()  # Bug 18
        elif x1 >= WIDTH:
            self.vx = -abs(self.vx); self.canvas.move(self.ball, WIDTH-x1, 0); self._play_sound()
        if y0 <= 0:
            self.vy = abs(self.vy); self.canvas.move(self.ball, 0, -y0); self._play_sound()
        # Paddle collision
        px0, py0, px1, py1 = self.canvas.coords(self.paddle)
        if y1 >= py0 and y0 < py0 and x1 >= px0 and x0 <= px1 and self.vy > 0:  # Bug 2: Check downward motion
            self.vy = -abs(self.vy); self._play_sound()
            # Bug 10: Slightly increase speed
            self.ball_speed *= 1.02
            self.vx *= 1.02
            self.vy *= 1.02
        # Brick collision
        hit_bricks = []
        for brick in self.bricks:
            bx0, by0, bx1, by1 = self.canvas.coords(brick)
            if x1 >= bx0 and x0 <= bx1 and y1 >= by0 and y0 <= by1:
                hit_bricks.append(brick)
                self.score += 10
                self.canvas.itemconfig(self.hud, text=f"Score: {self.score}  Lives: {self.lives}")
                if y0 <= by0 and self.vy > 0 or y1 >= by1 and self.vy < 0:
                    self.vy = -self.vy
                else:
                    self.vx = -self.vx
                self._play_sound()
        for brick in hit_bricks:  # Bug 9: Handle all collisions
            self.bricks.remove(brick)
            self.canvas.delete(brick)
        # Check win or lose
        if not self.bricks:
            self.running = False
            self.state = 'win'
            self._update_high_score()
            self._show_end("YOU WIN!")
        elif y1 >= HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                self._reset_ball()  # Bug 5: Reset ball
                self.canvas.itemconfig(self.hud, text=f"Score: {self.score}  Lives: {self.lives}")
            else:
                self.running = False
                self.state = 'game_over'
                self._update_high_score()
                self._show_end("GAME OVER")

    def _play_sound(self):
        if not self.sound_channel.get_busy():  # Bug 4: Prevent sound overlap
            self.sound_channel.play(self.sound)

    def _reset_ball(self):
        self.canvas.coords(self.ball, WIDTH/2 - BALL_RADIUS, HEIGHT/2 - BALL_RADIUS,
                          WIDTH/2 + BALL_RADIUS, HEIGHT/2 + BALL_RADIUS)
        self.vx = self.ball_speed * random.choice([-1, 1])
        self.vy = -self.ball_speed

    def _update_high_score(self):
        self.high_score = max(self.high_score, self.score)  # Bug 17

    def _show_end(self, msg):
        self.canvas.create_text(WIDTH/2, HEIGHT/2, text=msg, fill="yellow", font=("Courier", 32))
        self.canvas.create_rectangle(WIDTH/2-100, HEIGHT/2+20, WIDTH/2+100, HEIGHT/2+60, fill="#006400", outline="")
        self.canvas.create_text(WIDTH/2, HEIGHT/2+40, text="Restart", fill="white", font=("Courier", 16))

    def _game_loop(self):
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        if delta_time >= FRAME_DELAY:  # Bug 14: Consistent frame timing
            self._update()
            self.last_frame_time = current_time
        self.root.after(int(FRAME_DELAY * 1000), self._game_loop)

    def _on_mouse(self, event):
        if self.state != 'playing' or self.paused:
            return
        # Bug 6: Smooth paddle movement
        x = max(PADDLE_WIDTH/2, min(WIDTH - PADDLE_WIDTH/2, event.x))
        self.canvas.coords(self.paddle,
                           x - PADDLE_WIDTH/2, HEIGHT - 30,
                           x + PADDLE_WIDTH/2, HEIGHT - 30 + PADDLE_HEIGHT)

    def _on_key(self, event):
        if event.keysym == 'p':  # Bug 7: Pause with 'P' key
            if self.state == 'playing' and self.running:
                self.paused = not self.paused
                if self.paused:
                    self.canvas.create_text(WIDTH/2, HEIGHT/2, text="PAUSED", fill="white", font=("Courier", 32), tag="pause")
                else:
                    self.canvas.delete("pause")
        elif event.keysym == 'Left' and self.state == 'playing' and not self.paused:  # Bug 20: Keyboard controls
            x0, _, x1, _ = self.canvas.coords(self.paddle)
            x = max(PADDLE_WIDTH/2, x0 - 20)
            self.canvas.coords(self.paddle, x - PADDLE_WIDTH/2, HEIGHT - 30, x + PADDLE_WIDTH/2, HEIGHT - 30 + PADDLE_HEIGHT)
        elif event.keysym == 'Right' and self.state == 'playing' and not self.paused:
            x0, _, x1, _ = self.canvas.coords(self.paddle)
            x = min(WIDTH - PADDLE_WIDTH/2, x1 + 20)
            self.canvas.coords(self.paddle, x - PADDLE_WIDTH/2, HEIGHT - 30, x + PADDLE_WIDTH/2, HEIGHT - 30 + PADDLE_HEIGHT)
        elif event.keysym == 'Escape':  # Bug 13: Exit with Escape
            self._exit()

    def _on_click(self, event):
        if self.state == 'menu':
            if WIDTH/2-80 <= event.x <= WIDTH/2+80 and HEIGHT/2 <= event.y <= HEIGHT/2+40:  # Bug 12
                self._start_game()
        elif self.state in ('win', 'game_over'):
            if WIDTH/2-100 <= event.x <= WIDTH/2+100 and HEIGHT/2+20 <= event.y <= HEIGHT/2+60:  # Bug 21: Specific click area
                self.state = 'menu'
                self._setup_menu()

    def _exit(self):
        self.root.destroy()  # Bug 13: Proper exit

if __name__ == '__main__':
    BreakoutGame()
