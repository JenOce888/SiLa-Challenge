import pygame
import json
import math
import random
import os
import sys

# Settings 
SCREEN_W, SCREEN_H = 1024, 576
FPS        = 60
TILE       = 48
SAVE_FILE  = "highscore.txt"

# Physics
GRAVITY      = 0.7
FRICTION     = 0.85   # ground friction
AIR_FRICTION = 0.76   # air friction
BOUNCE       = 0.21   # rebound factor
PLAYER_SPEED = 5.0
JUMP_FORCE   = -11.0
ENEMY_SPEED  = 1.9
BULLET_SPEED = 12.0

# Colors
C_SKY    = (18, 22, 48)
C_TILE   = (55, 75, 130)
C_TILE_T = (80, 110, 170)
C_PLAYER = (70, 190, 255)
C_ENEMY  = (255, 75, 75)
C_COIN   = (255, 210, 50)
C_BULLET = (180, 255, 100)
C_DUST   = (180, 155, 120)
C_WHITE  = (255, 255, 255)

# Helpers
def aabb(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

def load_hs():
    try:
        with open(SAVE_FILE) as f:
            return int(f.read())
    except:
        return 0

def save_hs(score):
    with open(SAVE_FILE, "w") as f:
        f.write(str(score))

# Particle
class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=4):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life = self.max_life = life
        self.size = size

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.12
        self.vx *= 0.95
        self.life -= 1

    def draw(self, surf, cx, cy):
        a = self.life / self.max_life
        r = max(1, int(self.size * a))
        col = tuple(int(c * a) for c in self.color)
        pygame.draw.circle(surf, col, (int(self.x - cx), int(self.y - cy)), r)

def spawn_dust(particles, x, y, n=5):
    for _ in range(n):
        angle = random.uniform(0, math.pi)
        spd   = random.uniform(1, 3)
        particles.append(Particle(x, y,
            math.cos(angle) * spd, -abs(math.sin(angle)) * spd,
            C_DUST, random.randint(14, 24), random.randint(3, 6)))

def spawn_explosion(particles, x, y, n=20):
    colors = [(255,200,50), (255,120,30), (255,60,20)]
    for _ in range(n):
        angle = random.uniform(0, 2 * math.pi)
        spd   = random.uniform(2, 7)
        particles.append(Particle(x, y,
            math.cos(angle) * spd, math.sin(angle) * spd,
            random.choice(colors), random.randint(18, 40), random.randint(4, 9)))

# Bullet
class Bullet:
    W, H = 12, 5

    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.vx    = BULLET_SPEED * direction
        self.alive = True

    def update(self, tilemap):
        self.x += self.vx
        col = int(self.x // TILE)
        row = int(self.y // TILE)
        if 0 <= row < len(tilemap) and 0 <= col < len(tilemap[0]):
            if tilemap[row][col] == 1:
                self.alive = False
        if not (0 < self.x < len(tilemap[0]) * TILE):
            self.alive = False

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        pygame.draw.ellipse(surf, C_BULLET,
            (sx - self.W//2, sy - self.H//2, self.W, self.H))

    def get_rect(self):
        return (self.x - self.W//2, self.y - self.H//2, self.W, self.H)

# Enemy
class Enemy:
    W, H       = 34, 40
    CHASE_DIST = 240

    def __init__(self, tile_x, tile_y, pl, pr):
        self.x  = tile_x * TILE
        self.y  = tile_y * TILE - self.H
        self.vx = -ENEMY_SPEED
        self.vy = 0.0
        self.patrol_l  = pl * TILE
        self.patrol_r  = pr * TILE
        self.on_ground = False
        self.alive     = True
        self.facing    = -1
        self.step      = 0

    def update(self, tilemap, px, py, particles):
        my_cx = self.x + self.W // 2
        px_cx = px + 16
        if abs(px_cx - my_cx) < self.CHASE_DIST:
            self.vx = ENEMY_SPEED * (1 if px_cx > my_cx else -1)
        else:
            if self.x <= self.patrol_l:
                self.vx = ENEMY_SPEED
            elif self.x + self.W >= self.patrol_r:
                self.vx = -ENEMY_SPEED

        self.facing = 1 if self.vx > 0 else -1
        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        self.on_ground = False
        self._resolve_tiles(tilemap)

        if self.on_ground and abs(self.vx) > 0.3:
            self.step += 1
            if self.step % 12 == 0:
                spawn_dust(particles, self.x + self.W // 2, self.y + self.H, 3)

    def _resolve_tiles(self, tilemap):
        rows, cols = len(tilemap), len(tilemap[0])
        for r in range(max(0, int(self.y//TILE)-1), min(rows, int((self.y+self.H)//TILE)+2)):
            for c in range(max(0, int(self.x//TILE)-1), min(cols, int((self.x+self.W)//TILE)+2)):
                if tilemap[r][c] != 1:
                    continue
                tx, ty = c * TILE, r * TILE
                if not aabb(self.x, self.y, self.W, self.H, tx, ty, TILE, TILE):
                    continue
                ol = [(tx+TILE)-self.x, (self.x+self.W)-tx,
                      (ty+TILE)-self.y, (self.y+self.H)-ty]
                mi = ol.index(min(ol))
                if   mi == 0: self.x  = tx + TILE;   self.vx =  abs(self.vx)
                elif mi == 1: self.x  = tx - self.W; self.vx = -abs(self.vx)
                elif mi == 2: self.y  = ty + TILE;   self.vy = abs(self.vy) * BOUNCE
                else:
                    self.y = ty - self.H
                    self.vy = 0 if self.vy < 8 else -self.vy * BOUNCE
                    self.on_ground = True

    def draw(self, surf, cx, cy):
        sx, sy = int(self.x - cx), int(self.y - cy)
        pygame.draw.rect(surf, C_ENEMY, (sx, sy+10, self.W, self.H-10), border_radius=6)
        pygame.draw.ellipse(surf, C_ENEMY, (sx+3, sy, self.W-6, 22))
        ex = sx + (22 if self.facing > 0 else 8)
        pygame.draw.circle(surf, C_WHITE, (ex, sy+8), 5)
        pygame.draw.circle(surf, (20,20,20), (ex + self.facing, sy+9), 3)
        leg = int(math.sin(self.step * 0.28) * 6)
        pygame.draw.rect(surf, (180,40,40), (sx+4, sy+self.H-8, 10, 8+leg), border_radius=3)
        pygame.draw.rect(surf, (180,40,40), (sx+self.W-14, sy+self.H-8, 10, 8-leg), border_radius=3)

    def get_rect(self):
        return (self.x, self.y, self.W, self.H)

# Player
class Player:
    W, H = 30, 42

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.facing    = 1
        self.step      = 0
        self.shoot_cd  = 0
        self.coyote    = 0
        self.jump_buf  = 0

    def handle_input(self, keys, bullets, particles):
        if keys[pygame.K_LEFT]:
            self.vx = max(self.vx - PLAYER_SPEED, -PLAYER_SPEED * 1.4)
            self.facing = -1
        if keys[pygame.K_RIGHT]:
            self.vx = min(self.vx + PLAYER_SPEED, PLAYER_SPEED * 1.4)
            self.facing = 1

        if keys[pygame.K_SPACE]:
            self.jump_buf = 8
        if self.jump_buf > 0 and self.coyote > 0:
            self.vy       = JUMP_FORCE
            self.coyote   = 0
            self.jump_buf = 0

        if keys[pygame.K_LCTRL] and self.shoot_cd <= 0:
            bx = self.x + (self.W if self.facing > 0 else 0)
            by = self.y + self.H // 2
            bullets.append(Bullet(bx, by, self.facing))
            self.shoot_cd = 18
            for _ in range(4):
                particles.append(Particle(bx, by,
                    self.facing * random.uniform(3, 7),
                    random.uniform(-1.5, 1.5),
                    (255, 230, 80), random.randint(5, 10), 4))

    def update(self, tilemap, particles):
        if self.coyote  > 0: self.coyote  -= 1
        if self.jump_buf > 0: self.jump_buf -= 1
        if self.shoot_cd > 0: self.shoot_cd -= 1

        self.vy += GRAVITY
        fric = FRICTION if self.on_ground else AIR_FRICTION
        self.vx *= fric

        prev_on = self.on_ground
        self.on_ground = False
        self.x += self.vx
        self.y += self.vy
        self._resolve_tiles(tilemap, particles)

        if self.on_ground:
            self.coyote = 6
            if not prev_on:
                spawn_dust(particles, self.x + self.W//2, self.y + self.H, 7)
            if abs(self.vx) > 0.4:
                self.step += 1
                if self.step % 14 == 0:
                    spawn_dust(particles, self.x + self.W//2, self.y + self.H, 2)
        else:
            self.step = 0

    def _resolve_tiles(self, tilemap, particles):
        rows, cols = len(tilemap), len(tilemap[0])
        for r in range(max(0, int(self.y//TILE)-1), min(rows, int((self.y+self.H)//TILE)+2)):
            for c in range(max(0, int(self.x//TILE)-1), min(cols, int((self.x+self.W)//TILE)+2)):
                if tilemap[r][c] != 1:
                    continue
                tx, ty = c * TILE, r * TILE
                if not aabb(self.x, self.y, self.W, self.H, tx, ty, TILE, TILE):
                    continue
                ol = [(tx+TILE)-self.x, (self.x+self.W)-tx,
                      (ty+TILE)-self.y, (self.y+self.H)-ty]
                mi = ol.index(min(ol))
                if   mi == 0: self.x  = tx + TILE;   self.vx *= -BOUNCE
                elif mi == 1: self.x  = tx - self.W; self.vx *= -BOUNCE
                elif mi == 2: self.y  = ty + TILE;   self.vy = abs(self.vy) * BOUNCE
                else:
                    self.y = ty - self.H
                    self.vy = 0 if self.vy < 9 else -self.vy * BOUNCE
                    self.on_ground = True

    def draw(self, surf, cx, cy):
        sx, sy = int(self.x - cx), int(self.y - cy)
        shad = pygame.Surface((self.W, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shad, (0, 0, 0, 70), (0, 0, self.W, 6))
        surf.blit(shad, (sx, sy + self.H - 3))
        pygame.draw.rect(surf, C_PLAYER, (sx+4, sy+14, self.W-8, self.H-14), border_radius=7)
        pygame.draw.ellipse(surf, C_PLAYER, (sx+2, sy, self.W-4, 22))
        ex = sx + (20 if self.facing > 0 else 8)
        pygame.draw.circle(surf, C_WHITE, (ex, sy+9), 5)
        pygame.draw.circle(surf, (10, 10, 70), (ex + self.facing, sy+10), 3)
        leg = int(math.sin(self.step * 0.32) * 7) if self.on_ground else -6
        pygame.draw.rect(surf, (35, 110, 190), (sx+4, sy+self.H-10, 10, 10+leg), border_radius=3)
        pygame.draw.rect(surf, (35, 110, 190), (sx+self.W-14, sy+self.H-10, 10, 10-leg), border_radius=3)
        gx = sx + self.W if self.facing > 0 else sx - 12
        pygame.draw.rect(surf, (90, 90, 110), (gx, sy+22, 14, 7), border_radius=3)

    def get_rect(self):
        return (self.x, self.y, self.W, self.H)

# Coin
class Coin:
    R = 9

    def __init__(self, tx, ty):
        self.x = tx * TILE + TILE // 2
        self.y = ty * TILE + TILE // 2
        self.alive = True
        self.t = random.uniform(0, 2 * math.pi)

    def update(self):
        self.t += 0.05

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy + math.sin(self.t) * 4)
        pygame.draw.circle(surf, C_COIN, (sx, sy), self.R)
        pygame.draw.circle(surf, (255, 240, 130), (sx-2, sy-2), self.R-3)
        pygame.draw.circle(surf, (200, 160, 30), (sx, sy), self.R, 2)

    def get_rect(self):
        return (self.x - self.R, self.y - self.R, self.R*2, self.R*2)

# HUD
def draw_hud(surf, font, font_big, score, high_score, lives):
    pygame.draw.rect(surf, (10,14,38), (10, 10, 180, 50), border_radius=8)
    pygame.draw.rect(surf, (70,100,190), (10, 10, 180, 50), 2, border_radius=8)
    surf.blit(font.render("SCORE", True, (130,155,240)), (20, 14))
    surf.blit(font_big.render(f"{score:05d}", True, C_COIN), (20, 30))

    pygame.draw.rect(surf, (10,14,38), (200, 10, 200, 50), border_radius=8)
    pygame.draw.rect(surf, (70,100,190), (200, 10, 200, 50), 2, border_radius=8)
    surf.blit(font.render("BEST", True, (130,155,240)), (210, 14))
    surf.blit(font_big.render(f"{high_score:05d}", True, (255,200,80)), (210, 30))

    for i in range(lives):
        pygame.draw.circle(surf, C_PLAYER, (SCREEN_W - 25 - i*26, 30), 10)

# Main
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("2D Platformer")
    clock = pygame.time.Clock()

    font     = pygame.font.SysFont("monospace", 15, bold=True)
    font_big = pygame.font.SysFont("monospace", 20, bold=True)
    font_hug = pygame.font.SysFont("monospace", 56, bold=True)
    font_med = pygame.font.SysFont("monospace", 28, bold=True)

    path = os.path.join(os.path.dirname(__file__), "tilemap.json")
    with open(path) as f:
        data = json.load(f)

    tilemap  = data["tiles"]
    MAP_COLS = len(tilemap[0])
    MAP_ROWS = len(tilemap)
    MAP_W    = MAP_COLS * TILE
    MAP_H    = MAP_ROWS * TILE

    high_score = load_hs()

    def reset():
        player  = Player(2 * TILE, 12 * TILE)
        enemies = [Enemy(e["x"], e["y"], e["patrol_left"], e["patrol_right"]) for e in data["enemies"]]
        coins   = [Coin(c["x"], c["y"]) for c in data["coins"]]
        return player, enemies, coins, [], [], 3, 0, "play"

    player, enemies, coins, bullets, particles, lives, score, state = reset()
    cam_x = cam_y = 0.0
    shake = 0

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if state in ("dead", "win") and event.key == pygame.K_r:
                    player, enemies, coins, bullets, particles, lives, score, state = reset()
                    cam_x = cam_y = 0.0

        # Update
        if state == "play":
            player.handle_input(keys, bullets, particles)
            player.update(tilemap, particles)

            for e in enemies:
                e.update(tilemap, player.x, player.y, particles)
            for b in bullets:
                b.update(tilemap)
            for c in coins:
                c.update()

            # Bullet hits enemy
            for b in [b for b in bullets if b.alive]:
                for e in [e for e in enemies if e.alive]:
                    if aabb(*b.get_rect(), *e.get_rect()):
                        e.alive = False
                        b.alive = False
                        score  += 200
                        shake   = 10
                        spawn_explosion(particles, e.x + e.W//2, e.y + e.H//2)

            # Player touches enemy
            for e in [e for e in enemies if e.alive]:
                if aabb(*player.get_rect(), *e.get_rect()):
                    stomp = player.vy > 1 and player.y + player.H < e.y + e.H * 0.55
                    if stomp:
                        e.alive   = False
                        player.vy = JUMP_FORCE * 0.55
                        score    += 150
                        shake     = 8
                        spawn_explosion(particles, e.x + e.W//2, e.y + e.H//2, 12)
                    else:
                        lives -= 1
                        shake  = 18
                        spawn_explosion(particles, player.x + player.W//2, player.y + player.H//2, 15)
                        if lives <= 0:
                            state = "dead"
                            if score > high_score:
                                high_score = score; save_hs(high_score)
                        else:
                            player.x, player.y = 2*TILE, 12*TILE
                            player.vx = player.vy = 0

            # Player collects coin
            for c in [c for c in coins if c.alive]:
                if aabb(*player.get_rect(), *c.get_rect()):
                    c.alive = False
                    score  += 50
                    for _ in range(7):
                        a = random.uniform(0, 2 * math.pi)
                        s = random.uniform(2, 5)
                        particles.append(Particle(c.x, c.y,
                            math.cos(a)*s, math.sin(a)*s, C_COIN, random.randint(18, 32), 5))

            # Fall below map
            if player.y > MAP_H + 60:
                lives -= 1
                shake  = 14
                if lives <= 0:
                    state = "dead"
                    if score > high_score:
                        high_score = score; save_hs(high_score)
                else:
                    player.x, player.y = 2*TILE, 12*TILE
                    player.vx = player.vy = 0

            # All coins collected = win
            if all(not c.alive for c in coins):
                state = "win"
                if score > high_score:
                    high_score = score; save_hs(high_score)

            bullets   = [b for b in bullets   if b.alive]
            enemies   = [e for e in enemies   if e.alive]
            particles = [p for p in particles if p.life > 0]
            for p in particles:
                p.update()

            # Smooth camera follow
            tx = player.x + player.W//2 - SCREEN_W//2
            ty = player.y + player.H//2 - SCREEN_H//2
            cam_x += (tx - cam_x) * 0.12
            cam_y += (ty - cam_y) * 0.12
            cam_x  = max(0, min(MAP_W - SCREEN_W, cam_x))
            cam_y  = max(0, min(MAP_H - SCREEN_H, cam_y))

        else:
            for p in particles:
                p.update()
            particles = [p for p in particles if p.life > 0]

        if shake > 0:
            shake -= 1

        # Draw 
        ox = random.randint(-shake, shake) if shake else 0
        oy = random.randint(-shake, shake) if shake else 0
        dcx, dcy = cam_x + ox, cam_y + oy

        screen.fill(C_SKY)

        # Tiles
        for r in range(max(0, int(dcy//TILE)-1), min(MAP_ROWS, int((dcy+SCREEN_H)//TILE)+2)):
            for c in range(max(0, int(dcx//TILE)-1), min(MAP_COLS, int((dcx+SCREEN_W)//TILE)+2)):
                if tilemap[r][c] == 1:
                    tx = c*TILE - int(dcx)
                    ty = r*TILE - int(dcy)
                    pygame.draw.rect(screen, C_TILE, (tx, ty, TILE, TILE))
                    pygame.draw.rect(screen, C_TILE_T, (tx+1, ty+1, TILE-2, 7), border_radius=2)
                    pygame.draw.rect(screen, (35, 55, 100), (tx, ty, TILE, TILE), 1)

        for c in coins:
            if c.alive:
                c.draw(screen, dcx, dcy)

        for p in particles:
            p.draw(screen, dcx, dcy)

        for e in enemies:
            e.draw(screen, dcx, dcy)

        if state != "dead":
            player.draw(screen, dcx, dcy)

        for b in bullets:
            b.draw(screen, dcx, dcy)

        draw_hud(screen, font, font_big, score, high_score, lives)

        hint = font.render(
            "Left/Right: move  |  Space: jump  |  Ctrl: shoot  |  Stomp enemies from above",
            True, (60, 85, 150))
        screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 24))

        # End screen overlay
        if state in ("dead", "win"):
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((10, 5, 30, 170))
            screen.blit(overlay, (0, 0))
            title_text = "GAME OVER" if state == "dead" else "YOU WIN!"
            title_color = (255, 80, 80) if state == "dead" else (100, 255, 120)
            t1 = font_hug.render(title_text, True, title_color)
            t2 = font_med.render(f"Score: {score}   Best: {high_score}", True, C_COIN)
            t3 = font.render("Press R to restart", True, (180, 180, 220))
            screen.blit(t1, (SCREEN_W//2 - t1.get_width()//2, SCREEN_H//2 - 90))
            screen.blit(t2, (SCREEN_W//2 - t2.get_width()//2, SCREEN_H//2 + 10))
            screen.blit(t3, (SCREEN_W//2 - t3.get_width()//2, SCREEN_H//2 + 60))

        pygame.display.flip()

if __name__ == "__main__":
    main()