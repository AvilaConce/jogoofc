import pgzrun
from pgzero.rect import Rect
from pgzero.actor import Actor
from pgzero.keyboard import keyboard

WIDTH, HEIGHT = 800, 600

game_state = 'menu'
round_number = 1
max_rounds = 3
music_on = True

buttons = {
    'start': Rect((WIDTH // 2 - 100, 200, 200, 50)),
    'music': Rect((WIDTH // 2 - 100, 300, 200, 50)),
    'exit': Rect((WIDTH // 2 - 100, 400, 200, 50))
}

hover = {key: False for key in buttons}

background = Actor("background")

music.play('background.wav')
music.set_volume(0.5)

sound_shoot = sounds.shoot
sound_hit = sounds.hit
sound_lose = sounds.lose


class Hero:
    def __init__(self):
        self.actor = Actor("hero", (WIDTH // 2, HEIGHT // 2))
        self.speed = 3
        self.walk_count = 0
        self.frame = 0
        self.last_direction = (1, 0)
        self.lives = 3
        self.facing_left = False

    def update(self):
        dx = (keyboard.d - keyboard.a) * self.speed
        dy = (keyboard.s - keyboard.w) * self.speed

        if dx or dy:
            self.last_direction = (dx, dy)
            self.facing_left = dx < 0
            self.actor.x = max(0, min(WIDTH, self.actor.x + dx))
            self.actor.y = max(0, min(HEIGHT, self.actor.y + dy))
            self.walk_count += 1
            if self.walk_count % 10 == 0:
                self.frame = (self.frame + 1) % 2
                direction = "left" if self.facing_left else "right"
                self.actor.image = f"hero_walk_{direction}{self.frame+1}"
        else:
            self.actor.image = "hero"
            self.walk_count = 0

    def draw(self):
        self.actor.draw()
        for i in range(self.lives):
            screen.draw.text("♥", (10 + i * 20, 50), fontsize=30, color="red")

    def take_damage(self):
        self.lives -= 1
        return self.lives <= 0


class Enemy:
    def __init__(self, speed=2, pos=(100, 100)):
        self.actor = Actor("enemy_walk_right1", pos)
        self.speed = speed
        self.alive = True
        self.frame = 0
        self.walk_count = 0
        self.facing_left = False

    def update(self):
        if not self.alive:
            return
        dx = hero.actor.x - self.actor.x
        dy = hero.actor.y - self.actor.y
        dist = max(1, (dx**2 + dy**2)**0.6)
        vx, vy = self.speed * dx / dist, self.speed * dy / dist
        self.actor.x += vx
        self.actor.y += vy

        self.facing_left = vx < 0

        self.walk_count += 1
        if self.walk_count % 10 == 0:
            self.frame = (self.frame + 1) % 2
            direction = "left" if self.facing_left else "right"
            self.actor.image = f"enemy_walk_{direction}{self.frame+1}"

    def draw(self):
        if self.alive:
            self.actor.draw()

    def kill(self):
        self.alive = False


class Bullet:
    def __init__(self, x, y, dx, dy):
        self.actor = Actor("bullet", (x, y))
        self.dx = dx * 5
        self.dy = dy * 5
        self.alive = True

    def update(self):
        self.actor.x += self.dx
        self.actor.y += self.dy
        if not (0 <= self.actor.x <= WIDTH and 0 <= self.actor.y <= HEIGHT):
            self.alive = False

    def draw(self):
        if self.alive:
            self.actor.draw()


hero = None
enemies = []
bullets = []


def start_round(num):
    global enemies
    enemies = []
    positions = {
        1: [(100, 100)],
        2: [(100, 100), (700, 100)],
        3: [(100, 100), (400, 100), (700, 100)]
    }
    for pos in positions.get(num, [(100, 100)]):
        enemies.append(Enemy(speed=2 + num, pos=pos))


def draw_rounded_button(rect, text, color):
    screen.draw.filled_rect(rect.move(4, 4), (0, 0, 0, 150))
    screen.draw.filled_rect(rect, color)
    screen.draw.text(text, center=rect.center, fontsize=36,
                     color="white", owidth=2, ocolor="black")


def draw():
    screen.clear()
    background.draw()

    if game_state == 'menu':
        screen.draw.filled_rect(Rect((0, 0), (WIDTH, HEIGHT)), (0, 0, 0, 180))
        screen.draw.text("Rogue Game", center=(WIDTH // 2, 100),
                         fontsize=70, color="white", owidth=1, ocolor="black")

        for key, rect in buttons.items():
            color = {
                'start': (70, 130, 180),
                'music': (180, 130, 70),
                'exit': (180, 70, 70)
            }[key]
            if hover[key]:
                color = tuple(min(255, c + 50) for c in color)
            label = {
                'start': "Start Game",
                'music': f"Music: {'On' if music_on else 'Off'}",
                'exit': "Exit"
            }[key]
            draw_rounded_button(rect, label, color)

    elif game_state == 'playing':
        hero.draw()
        for enemy in enemies:
            enemy.draw()
        for bullet in bullets:
            bullet.draw()
        screen.draw.text(f"Round: {round_number}", center=(
            WIDTH // 2, 30), fontsize=40, color="white")

    elif game_state == 'won':
        screen.draw.text("Você venceu!", center=(
            WIDTH // 2, HEIGHT // 2), fontsize=60, color="yellow")

    elif game_state == 'lost':
        screen.draw.text("Game Over!", center=(
            WIDTH // 2, HEIGHT // 2), fontsize=60, color="red")


def update():
    global round_number, game_state
    if game_state != 'playing':
        return

    hero.update()

    for enemy in enemies:
        enemy.update()
        if enemy.alive and hero.actor.colliderect(enemy.actor):
            if hero.take_damage():
                sound_lose.play()
                game_state = 'lost'
            else:
                hero.actor.pos = (WIDTH // 2, HEIGHT // 2)

    for bullet in bullets:
        bullet.update()
        if bullet.alive:
            for enemy in enemies:
                if enemy.alive and bullet.actor.colliderect(enemy.actor):
                    bullet.alive = False
                    enemy.kill()
                    sound_hit.play()
                    break

    bullets[:] = [b for b in bullets if b.alive]

    if all(not e.alive for e in enemies):
        if round_number < max_rounds:
            round_number += 1
            start_round(round_number)
            hero.actor.pos = (WIDTH // 2, HEIGHT // 2)
        else:
            game_state = 'won'


def on_mouse_down(pos):
    global game_state, hero, music_on
    if game_state == 'menu':
        if buttons['start'].collidepoint(pos):
            hero = Hero()
            start_round(1)
            game_state = 'playing'
        elif buttons['music'].collidepoint(pos):
            music_on = not music_on
            if music_on:
                music.unpause()
            else:
                music.pause()
        elif buttons['exit'].collidepoint(pos):
            exit()


def on_mouse_move(pos):
    for key in buttons:
        hover[key] = buttons[key].collidepoint(pos)


def on_key_down(key):
    if game_state != 'playing':
        return
    if key == keys.SPACE:
        dx, dy = hero.last_direction
        if dx != 0 or dy != 0:
            bullets.append(Bullet(hero.actor.x, hero.actor.y, dx, dy))
            sound_shoot.play()


pgzrun.go()
