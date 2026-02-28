"""

   N×N TIC-TAC-TOE  –  Minimax AI + Alpha-Beta Pruning       
   Day 10 | Level 2 Improvements:                            
     • K-in-a-row win condition  (not always full row)       
     • Threat-aware heuristic   (open-end double threats)    
     • Persistent score counter across rounds                
     • Vintage warm colour palette                           

"""

import pygame
import sys
import math
import random
import os
from datetime import datetime

# CONSTANTS

SCREEN_W, SCREEN_H = 960, 540
FPS = 60

# Vintage warm palette with sepia tones and parchment textures
BG_COLOR        = (28,  22,  16)   # very dark brown
PAPER_COLOR     = (42,  34,  24)   # aged paper dark
PANEL_COLOR     = (34,  27,  18)   # sidebar
GRID_COLOR      = (90,  72,  48)   # sepia wood
GRID_LIGHT      = (120, 96,  60)   # lighter wood line

X_COLOR         = (210, 140,  50)  # amber gold
X_GLOW          = (140,  80,  10)  # dark amber
O_COLOR         = (180,  60,  55)  # brick red
O_GLOW          = (100,  25,  20)  # dark brick

WIN_LINE_COLOR  = (240, 210,  80)  # golden yellow
HOVER_COLOR     = (200, 170,  90,  35)
THREAT_COLOR    = (200,  80,  40,  55)  # warm orange tint for threat cells

TEXT_COLOR      = (230, 210, 175)  # aged parchment
TEXT_DIM        = (150, 130, 100)  # muted parchment
BTN_COLOR       = (55,  42,  26)
BTN_HOVER       = (80,  62,  36)
BTN_BORDER      = (130, 100,  55)
BTN_ACTIVE_BDR  = (210, 160,  60)

SCORE_X_COLOR   = (210, 140,  50)
SCORE_O_COLOR   = (180,  60,  55)
SCORE_TIE_COLOR = (160, 145, 110)

SEPARATOR       = (70,  54,  32)

# Win-condition K per grid size (N) 
DEFAULT_K = {3: 3, 4: 4, 5: 4, 6: 5}   # N -> K needed to win

DIFFICULTY_DEPTH = {
    "Easy":       1,
    "Medium":     3,
    "Impossible": 999,
}


# UTILITIES 

def draw_text(surface, text, font, color, cx, cy, glow=False, glow_color=None, anchor="center"):
    if glow and glow_color:
        for d in range(3, 0, -1):
            gs = font.render(text, True, glow_color)
            gr = gs.get_rect(center=(cx, cy))
            for dx in [-d, d]:
                for dy in [-d, d]:
                    surface.blit(gs, (gr.x + dx, gr.y + dy))
    surf = font.render(text, True, color)
    if anchor == "center":
        rect = surf.get_rect(center=(cx, cy))
    elif anchor == "midleft":
        rect = surf.get_rect(midleft=(cx, cy))
    else:
        rect = surf.get_rect(center=(cx, cy))
    surface.blit(surf, rect)
    return rect


def draw_rrect(surface, color, rect, radius=10, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


#  BOARD LOGIC

class Board:
    """N×N board with configurable K-in-a-row win condition."""

    def __init__(self, n: int, k: int):
        self.n = n
        self.k = k                                      # win length
        self.cells = [['' for _ in range(n)] for _ in range(n)]
        self.last_move = None

    def copy(self):
        b = Board(self.n, self.k)
        b.cells     = [row[:] for row in self.cells]
        b.last_move = self.last_move
        return b

    def place(self, row, col, player) -> bool:
        if self.cells[row][col] == '':
            self.cells[row][col] = player
            self.last_move = (row, col)
            return True
        return False

    def undo(self, row, col):
        """Make/unmake pattern – restore cell to empty."""
        self.cells[row][col] = ''
        self.last_move = None

    def is_full(self) -> bool:
        return all(self.cells[r][c] != '' for r in range(self.n) for c in range(self.n))

    def get_empty(self):
        return [(r, c) for r in range(self.n) for c in range(self.n)
                if self.cells[r][c] == '']

    # Win detection (K consecutive in any direction)

    def _all_segments(self):
        """Yield every possible K-length segment as a list of (r,c) tuples."""
        n, k = self.n, self.k
        for r in range(n):
            for c in range(n):
                if c + k <= n:
                    yield [(r, c+i) for i in range(k)]
                if r + k <= n:
                    yield [(r+i, c) for i in range(k)]
                if r + k <= n and c + k <= n:
                    yield [(r+i, c+i) for i in range(k)]
                if r + k <= n and c - k >= -1:
                    yield [(r+i, c-i) for i in range(k)]

    def check_winner(self):
        c = self.cells
        for seg in self._all_segments():
            vals = [c[r][col] for r, col in seg]
            if vals[0] != '' and all(v == vals[0] for v in vals):
                return vals[0]
        return None

    def winning_cells(self):
        c = self.cells
        for seg in self._all_segments():
            vals = [c[r][col] for r, col in seg]
            if vals[0] != '' and all(v == vals[0] for v in vals):
                return seg
        return []


# THREAT DETECTION 

def get_threats(board: Board, player: str):
    """
    Return a set of (r,c) empty cells that extend an open-ended run
    of 2+ pieces for `player`.  These are visually highlighted and
    also used by the move-ordering heuristic.
    """
    threats = set()
    n, k = board.n, board.k
    c = board.cells

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for r in range(n):
        for col in range(n):
            if c[r][col] != player:
                continue
            for dr, dc in directions:
                # Count consecutive pieces forward
                count = 1
                nr, nc = r + dr, col + dc
                while 0 <= nr < n and 0 <= nc < n and c[nr][nc] == player:
                    count += 1
                    nr += dr
                    nc += dc
                open_front = (0 <= nr < n and 0 <= nc < n and c[nr][nc] == '')
                front_cell = (nr, nc) if open_front else None

                # Count consecutive pieces backward
                nr2, nc2 = r - dr, col - dc
                while 0 <= nr2 < n and 0 <= nc2 < n and c[nr2][nc2] == player:
                    count += 1
                    nr2 -= dr
                    nc2 -= dc
                open_back = (0 <= nr2 < n and 0 <= nc2 < n and c[nr2][nc2] == '')
                back_cell = (nr2, nc2) if open_back else None

                # A run of 2+ with at least one open end is a threat
                if count >= 2 and count < k:
                    if open_front and front_cell:
                        threats.add(front_cell)
                    if open_back and back_cell:
                        threats.add(back_cell)
    return threats


# MINIMAX AI 

class Minimax:
    """
    Minimax with Alpha-Beta pruning.

    Heuristic improvements (Level 2):
      1. Scores open-ended runs (both ends free = double weight)
      2. Near-win (count == k-1 with open end) gets a large bonus
      3. Opponent threats penalised 1.3x more than own score
         (forces aggressive blocking)
    """

    def __init__(self, player: str, opponent: str, max_depth: int):
        self.player    = player
        self.opponent  = opponent
        self.max_depth = max_depth

    # Public entry 

    def get_best_move(self, board: Board):
        n = board.n
        if n >= 5 and self.max_depth > 2:
            depth = 2
        elif n == 4 and self.max_depth > 4:
            depth = 4
        else:
            depth = self.max_depth

        best_val  = -math.inf
        best_move = None
        alpha     = -math.inf
        beta      = math.inf

        for r, c in self._ordered_moves(board):
            board.place(r, c, self.player)
            val = self._minimax(board, depth - 1, False, alpha, beta)
            board.undo(r, c)
            if val > best_val:
                best_val  = val
                best_move = (r, c)
            alpha = max(alpha, best_val)

        # Easy mode: 50 % chance of random move
        if self.max_depth == 1 and random.random() < 0.5:
            empties = board.get_empty()
            return random.choice(empties) if empties else best_move

        return best_move

    # Minimax with alpha-beta pruning

    def _minimax(self, board: Board, depth: int, is_max: bool,
                 alpha: float, beta: float) -> float:
        winner = board.check_winner()
        if winner == self.player:
            return 10000 + depth
        if winner == self.opponent:
            return -(10000 + depth)
        if board.is_full() or depth == 0:
            return self._heuristic(board)

        moves = self._ordered_moves(board)

        if is_max:
            best = -math.inf
            for r, c in moves:
                board.place(r, c, self.player)
                best = max(best, self._minimax(board, depth-1, False, alpha, beta))
                board.undo(r, c)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = math.inf
            for r, c in moves:
                board.place(r, c, self.opponent)
                best = min(best, self._minimax(board, depth-1, True, alpha, beta))
                board.undo(r, c)
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    # Move ordering

    def _ordered_moves(self, board: Board):
        """
        Priority order:
          1. Winning move for AI
          2. Blocking opponent win
          3. Extending own open threat
          4. Blocking opponent open threat
          5. Centre proximity
        """
        empties = board.get_empty()
        center  = board.n / 2.0

        def priority(rc):
            r, c = rc
            board.place(r, c, self.player)
            win = board.check_winner()
            board.undo(r, c)
            if win == self.player:
                return -1000

            board.place(r, c, self.opponent)
            win = board.check_winner()
            board.undo(r, c)
            if win == self.opponent:
                return -900

            if rc in get_threats(board, self.player):
                return -50
            if rc in get_threats(board, self.opponent):
                return -40

            return (r - center)**2 + (c - center)**2

        empties.sort(key=priority)
        return empties

    # Threat-aware heuristic 

    def _heuristic(self, board: Board) -> float:
        """
        Score every K-length window.

        Window scoring:
          • Both ends open  → count² × 2
          • One end open    → count²
          • Near-win (count == k-1, open end) → +500 bonus
          • Opponent threat penalised × 1.3  (encourages blocking)
        """
        score = 0
        n, k  = board.n, board.k
        c     = board.cells

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(n):
            for col in range(n):
                for dr, dc in directions:
                    cells_in_window = []
                    valid = True
                    for i in range(k):
                        nr, nc = r + i*dr, col + i*dc
                        if not (0 <= nr < n and 0 <= nc < n):
                            valid = False
                            break
                        cells_in_window.append((nr, nc))
                    if not valid:
                        continue

                    vals  = [c[r2][c2] for r2, c2 in cells_in_window]
                    p_cnt = vals.count(self.player)
                    o_cnt = vals.count(self.opponent)

                    if p_cnt > 0 and o_cnt > 0:
                        continue  # mixed window, no value

                    # Open ends
                    br, bc = r - dr, col - dc
                    ar, ac = r + k*dr, col + k*dc
                    open_before = (0 <= br < n and 0 <= bc < n and c[br][bc] == '')
                    open_after  = (0 <= ar < n and 0 <= ac < n and c[ar][ac] == '')
                    open_ends   = int(open_before) + int(open_after)

                    if open_ends == 0:
                        continue

                    def window_score(cnt, ends):
                        base    = cnt ** 2
                        multi   = 2 if ends == 2 else 1
                        bonus   = 500 if cnt == k - 1 else 0
                        return base * multi + bonus

                    if p_cnt > 0:
                        score += window_score(p_cnt, open_ends)
                    elif o_cnt > 0:
                        score -= window_score(o_cnt, open_ends) * 1.3

        return score


# GAME RECORDER

class GameRecorder:
    def __init__(self, n: int, k: int, mode: str, difficulty: str):
        self.n          = n
        self.k          = k
        self.mode       = mode
        self.difficulty = difficulty
        self.moves      = []
        self.start_time = datetime.now()

    def record(self, player: str, row: int, col: int):
        col_letter = chr(ord('a') + col)
        row_number = self.n - row
        self.moves.append((player, f"{col_letter}{row_number}"))

    def save(self, result: str = "*") -> str:
        os.makedirs("games", exist_ok=True)
        fname = f"games/game_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        lines = [
            f"[Date \"{self.start_time.strftime('%Y.%m.%d')}\"]",
            f"[Time \"{self.start_time.strftime('%H:%M:%S')}\"]",
            f"[Grid \"{self.n}x{self.n}\"]",
            f"[Win \"{self.k} in a row\"]",
            f"[Mode \"{self.mode}\"]",
            f"[Difficulty \"{self.difficulty}\"]",
            f"[Result \"{result}\"]",
            "",
        ]
        move_str = ""
        i = 0
        while i < len(self.moves):
            num  = i // 2 + 1
            x_mv = self.moves[i][1]   if i   < len(self.moves) else "-"
            o_mv = self.moves[i+1][1] if i+1 < len(self.moves) else ""
            move_str += f"{num}. {x_mv} {o_mv}  "
            i += 2
        lines += [move_str.strip(), result]
        with open(fname, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return fname


# UI COMPONENTS 

class Button:
    def __init__(self, rect, label: str, font, active: bool = False):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.font    = font
        self.active  = active
        self.hovered = False

    def draw(self, surface):
        bg     = BTN_HOVER      if (self.hovered or self.active) else BTN_COLOR
        border = BTN_ACTIVE_BDR if self.active else BTN_BORDER
        draw_rrect(surface, bg, self.rect, 8, 2, border)
        tc = X_COLOR if self.active else TEXT_COLOR
        draw_text(surface, self.label, self.font, tc,
                  self.rect.centerx, self.rect.centery)

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos) -> bool:
        return self.rect.collidepoint(pos)


class Animation:
    def __init__(self):
        self.pulse_t    = 0.0
        self.particles  = []
        self.fade_cells = {}
        self.win_flash  = 0

    def update(self, dt: float):
        self.pulse_t += dt
        self.particles = [
            (x+vx, y+vy*0.92, vx*0.98, vy*0.92, life-1, col)
            for x, y, vx, vy, life, col in self.particles if life > 0
        ]
        for key in list(self.fade_cells):
            self.fade_cells[key] = min(255, self.fade_cells[key] + 14)
            if self.fade_cells[key] >= 255:
                del self.fade_cells[key]
        if self.win_flash > 0:
            self.win_flash -= 1

    def spawn(self, x: int, y: int, color, count: int = 20):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append((x, y, vx, vy, random.randint(18, 40), color))

    def add_fade(self, r: int, c: int):
        self.fade_cells[(r, c)] = 0

    def draw_particles(self, surface):
        for x, y, vx, vy, life, col in self.particles:
            alpha = min(255, life * 7)
            rad   = max(2, life // 6)
            s     = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (rad, rad), rad)
            surface.blit(s, (int(x) - rad, int(y) - rad))


# SCORE BOARD

class ScoreBoard:
    """Persistent score counter across rounds."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.x_wins = 0
        self.o_wins = 0
        self.draws  = 0

    def record(self, result: str):
        if result == 'X':
            self.x_wins += 1
        elif result == 'O':
            self.o_wins += 1
        else:
            self.draws += 1

    @property
    def total(self):
        return self.x_wins + self.o_wins + self.draws


# MAIN GAME CODE

class Game:
    MENU     = "menu"
    PLAYING  = "playing"
    GAMEOVER = "gameover"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tic-Tac-Toe AI – Day 10")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock  = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("georgia",    40, bold=True)
        self.font_large = pygame.font.SysFont("georgia",    26, bold=True)
        self.font_med   = pygame.font.SysFont("courier new",21, bold=True)
        self.font_small = pygame.font.SysFont("courier new",15)
        self.font_tiny  = pygame.font.SysFont("courier new",13)

        self.anim   = Animation()
        self.scores = ScoreBoard()
        self.state  = self.MENU

        self.grid_n     = 3
        self.win_k      = DEFAULT_K[3]
        self.mode       = "1P"
        self.difficulty = "Impossible"

        self.board          = None
        self.recorder       = None
        self.ai             = None
        self.current_player = 'X'
        self.winner         = None
        self.win_cells      = []
        self.ai_thinking    = False
        self.ai_timer       = 0
        self.status_msg     = ""
        self.last_saved     = ""
        self.hover_cell     = None
        self.threat_overlay: set = set()

        self._init_menu()

    # MENU 

    def _init_menu(self):
        cx = SCREEN_W // 2
        bw, bh = 170, 40

        self.btn_n = [
            Button((cx-270, 255, bw, bh), "3x3", self.font_med, True),
            Button((cx- 85, 255, bw, bh), "4x4", self.font_med),
            Button((cx+100, 255, bw, bh), "5x5", self.font_med),
        ]
        self.btn_mode = [
            Button((cx-190, 320, 180, bh), "1 Player",  self.font_med, True),
            Button((cx+ 10, 320, 180, bh), "2 Players", self.font_med),
        ]
        self.btn_diff = [
            Button((cx-270, 385, bw, bh), "Easy",       self.font_med),
            Button((cx- 85, 385, bw, bh), "Medium",     self.font_med),
            Button((cx+100, 385, bw, bh), "Impossible", self.font_med, True),
        ]
        self.btn_reset_score = Button((cx-85, 450, 170, 35), "Reset Scores", self.font_small)
        self.btn_play = Button((cx-100, 510, 200, 48), "PLAY", self.font_large)
        self.btn_play.active = True

    def _start_game(self):
        self.board    = Board(self.grid_n, self.win_k)
        self.recorder = GameRecorder(self.grid_n, self.win_k, self.mode, self.difficulty)
        self.ai       = Minimax('O', 'X', DIFFICULTY_DEPTH[self.difficulty])

        self.current_player = 'X'
        self.winner      = None
        self.win_cells   = []
        self.ai_thinking = False
        self.status_msg  = "Your turn  -  X goes first"
        self.last_saved  = ""
        self.threat_overlay = set()
        self.state = self.PLAYING

        panel_w = SCREEN_W - 300
        cs = min((panel_w - 80) // self.grid_n,
                 (SCREEN_H - 100) // self.grid_n)
        self.cell_size = cs
        total = cs * self.grid_n
        self.grid_ox = (panel_w - total) // 2
        self.grid_oy = (SCREEN_H - total) // 2

        rx = SCREEN_W - 278
        self.btn_menu    = Button((rx, 580, 240, 40), "Main Menu", self.font_med)
        self.btn_restart = Button((rx, 628, 240, 40), "Restart",   self.font_med)

    # HELPERS

    def cell_rect(self, r: int, c: int) -> pygame.Rect:
        return pygame.Rect(
            self.grid_ox + c * self.cell_size,
            self.grid_oy + r * self.cell_size,
            self.cell_size, self.cell_size
        )

    def pixel_to_cell(self, px: int, py: int):
        col = (px - self.grid_ox) // self.cell_size
        row = (py - self.grid_oy) // self.cell_size
        if 0 <= row < self.grid_n and 0 <= col < self.grid_n:
            return int(row), int(col)
        return None

    # ACTIONS

    def human_play(self, row: int, col: int):
        if self.board.cells[row][col] != '':
            return
        self.board.place(row, col, self.current_player)
        self.recorder.record(self.current_player, row, col)
        cx, cy = self.cell_rect(row, col).center
        self.anim.spawn(cx, cy, X_COLOR if self.current_player == 'X' else O_COLOR, 22)
        self.anim.add_fade(row, col)
        self._check_end()

    def ai_play(self):
        move = self.ai.get_best_move(self.board)
        if move:
            r, c = move
            self.board.place(r, c, 'O')
            self.recorder.record('O', r, c)
            cx, cy = self.cell_rect(r, c).center
            self.anim.spawn(cx, cy, O_COLOR, 28)
            self.anim.add_fade(r, c)
        self.ai_thinking = False
        self._update_threats()
        self._check_end()

    def _update_threats(self):
        if self.board and self.state == self.PLAYING:
            opp = 'O' if self.current_player == 'X' else 'X'
            self.threat_overlay = get_threats(self.board, opp)
        else:
            self.threat_overlay = set()

    def _check_end(self):
        w = self.board.check_winner()
        if w:
            self.winner    = w
            self.win_cells = self.board.winning_cells()
            self.anim.win_flash = 130
            self.scores.record(w)
            result = "1-0" if w == 'X' else "0-1"
            self.last_saved = self.recorder.save(result)
            name = "X" if w == 'X' else ("O (AI)" if self.mode == "1P" else "O")
            self.status_msg = f"{name} wins!   (saved)"
            self.threat_overlay = set()
            self.state = self.GAMEOVER
        elif self.board.is_full():
            self.winner = 'draw'
            self.scores.record('draw')
            self.last_saved = self.recorder.save("1/2-1/2")
            self.status_msg = "Draw!   (saved)"
            self.threat_overlay = set()
            self.state = self.GAMEOVER
        else:
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            if self.mode == "1P" and self.current_player == 'O':
                self.ai_thinking = True
                self.ai_timer    = pygame.time.get_ticks() + 380
                self.status_msg  = "AI is thinking..."
                self.threat_overlay = set()
            else:
                self.status_msg = f"{'X' if self.current_player == 'X' else 'O'}'s turn"
                self._update_threats()

    #DRAWING 

    def draw_menu(self):
        s  = self.screen
        cx = SCREEN_W // 2
        s.fill(BG_COLOR)

        # Crosshatch bg
        for i in range(0, SCREEN_W, 40):
            pygame.draw.line(s, (38, 30, 20), (i, 0), (i, SCREEN_H))
        for j in range(0, SCREEN_H, 40):
            pygame.draw.line(s, (38, 30, 20), (0, j), (SCREEN_W, j))

        # Title
        pygame.draw.rect(s, PAPER_COLOR, (cx-260, 50, 520, 90), border_radius=12)
        pygame.draw.rect(s, GRID_LIGHT,  (cx-260, 50, 520, 90), 2, border_radius=12)
        draw_text(s, "TIC-TAC-TOE  AI", self.font_title, X_COLOR, cx, 82,
                  glow=True, glow_color=X_GLOW)
        draw_text(s, "Minimax  .  Alpha-Beta  .  Threat Detection",
                  self.font_tiny, TEXT_DIM, cx, 122)

        # Score panel (only shown after at least one game)
        if self.scores.total > 0:
            bx, by = cx - 190, 148
            pygame.draw.rect(s, PAPER_COLOR, (bx, by, 380, 50), border_radius=8)
            pygame.draw.rect(s, SEPARATOR,   (bx, by, 380, 50), 1, border_radius=8)
            draw_text(s, f"X  {self.scores.x_wins}", self.font_med,
                      SCORE_X_COLOR, bx + 65, by + 25)
            draw_text(s, f"Ties  {self.scores.draws}", self.font_med,
                      SCORE_TIE_COLOR, cx, by + 25)
            draw_text(s, f"{self.scores.o_wins}  O", self.font_med,
                      SCORE_O_COLOR, bx + 315, by + 25)

        draw_text(s, "GRID SIZE",           self.font_small, TEXT_DIM, cx, 235)
        for b in self.btn_n:    b.draw(s)

        draw_text(s, "GAME MODE",           self.font_small, TEXT_DIM, cx, 302)
        for b in self.btn_mode: b.draw(s)

        draw_text(s, "DIFFICULTY  (vs AI)", self.font_small, TEXT_DIM, cx, 367)
        for b in self.btn_diff: b.draw(s)

        self.btn_reset_score.draw(s)
        self.btn_play.draw(s)

        draw_text(s, "Games are saved to /games/  in algebraic notation",
                  self.font_tiny, TEXT_DIM, cx, 578)
        draw_text(s,
                  f"Win condition: {self.win_k} in a row on a {self.grid_n}x{self.grid_n} board",
                  self.font_small, (160, 130, 80), cx, 600)

    def draw_board(self):
        s  = self.screen
        n  = self.grid_n
        cs = self.cell_size
        ox = self.grid_ox
        oy = self.grid_oy

        s.fill(BG_COLOR)

        # Animated vertical lines bg
        t = self.anim.pulse_t
        for i in range(0, SCREEN_W - 300, 50):
            v = int(32 + 6 * math.sin(t * 0.4 + i * 0.05))
            pygame.draw.line(s, (v, int(v*0.8), int(v*0.55)), (i, 0), (i, SCREEN_H))

        # Threat overlay
        for tr, tc in self.threat_overlay:
            rect = self.cell_rect(tr, tc)
            ov   = pygame.Surface((cs, cs), pygame.SRCALPHA)
            ov.fill(THREAT_COLOR)
            s.blit(ov, rect)

        # Grid lines
        for i in range(n + 1):
            lw = 3 if i in (0, n) else 1
            lc = GRID_LIGHT if i in (0, n) else GRID_COLOR
            pygame.draw.line(s, lc, (ox, oy + i*cs), (ox + n*cs, oy + i*cs), lw)
            pygame.draw.line(s, lc, (ox + i*cs, oy), (ox + i*cs, oy + n*cs), lw)

        # Hover highlight
        if self.hover_cell and self.state == self.PLAYING and not self.ai_thinking:
            r2, c2 = self.hover_cell
            if self.board.cells[r2][c2] == '':
                rect = self.cell_rect(r2, c2)
                hov  = pygame.Surface((cs, cs), pygame.SRCALPHA)
                hov.fill(HOVER_COLOR)
                s.blit(hov, rect)

        # Symbols
        pad = cs // 4
        for r in range(n):
            for c in range(n):
                val = self.board.cells[r][c]
                if val == '':
                    continue
                rect     = self.cell_rect(r, c)
                cx2, cy2 = rect.center
                if val == 'X':
                    for dx, dy in [(-1,-1),(1,1),(-1,1),(1,-1)]:
                        pygame.draw.line(s, X_GLOW,
                            (cx2+dx*(pad+4), cy2+dy*(pad+4)),
                            (cx2-dx*(pad+4), cy2-dy*(pad+4)), 9)
                    pygame.draw.line(s, X_COLOR,
                        (rect.left+pad,  rect.top+pad),
                        (rect.right-pad, rect.bottom-pad), 4)
                    pygame.draw.line(s, X_COLOR,
                        (rect.right-pad, rect.top+pad),
                        (rect.left+pad,  rect.bottom-pad), 4)
                else:
                    r_outer = cs // 2 - pad
                    pygame.draw.circle(s, O_GLOW,  (cx2, cy2), r_outer + 4, 12)
                    pygame.draw.circle(s, O_COLOR, (cx2, cy2), r_outer, 4)

        # Win line
        if self.win_cells and self.anim.win_flash > 0:
            pulse = abs(math.sin(self.anim.win_flash * 0.14))
            p1 = self.cell_rect(*self.win_cells[0]).center
            p2 = self.cell_rect(*self.win_cells[-1]).center
            pygame.draw.line(s, WIN_LINE_COLOR, p1, p2, int(5 + 5 * pulse))

        # Particles
        self.anim.draw_particles(s)

        # Right panel
        px = SCREEN_W - 292
        pygame.draw.rect(s, PANEL_COLOR, (px - 8, 0, 300, SCREEN_H))
        pygame.draw.line(s, SEPARATOR, (px - 8, 0), (px - 8, SCREEN_H), 2)

        draw_text(s, "TIC-TAC-TOE", self.font_large, X_COLOR, px+138, 36,
                  glow=True, glow_color=X_GLOW)
        draw_text(s, f"{n}x{n}  -  {self.win_k} in a row",
                  self.font_small, TEXT_DIM, px+138, 62)
        draw_text(s, "1 Player" if self.mode == "1P" else "2 Players",
                  self.font_small, TEXT_DIM, px+138, 82)
        if self.mode == "1P":
            draw_text(s, self.difficulty, self.font_small, (180, 140, 60), px+138, 102)

        if self.state == self.PLAYING:
            pc = X_COLOR if self.current_player == 'X' else O_COLOR
            draw_text(s, f"Turn: {self.current_player}", self.font_large, pc, px+138, 140)
        draw_text(s, self.status_msg, self.font_small, TEXT_DIM, px+138, 168)

        if self.threat_overlay and self.state == self.PLAYING:
            draw_text(s, "* Threat cells highlighted",
                      self.font_tiny, (200, 100, 60), px+138, 192)

        # Score box
        pygame.draw.line(s, SEPARATOR, (px, 210), (px+276, 210), 1)
        draw_text(s, "SCORE", self.font_small, TEXT_DIM, px+138, 228)
        pygame.draw.rect(s, BTN_COLOR, (px+2, 240, 270, 56), border_radius=8)
        pygame.draw.rect(s, SEPARATOR, (px+2, 240, 270, 56), 1, border_radius=8)
        draw_text(s, f"X  {self.scores.x_wins}", self.font_large,
                  SCORE_X_COLOR, px + 60, 268)
        draw_text(s, str(self.scores.draws), self.font_large,
                  SCORE_TIE_COLOR, px+138, 268)
        draw_text(s, f"{self.scores.o_wins}  O", self.font_large,
                  SCORE_O_COLOR, px+216, 268)
        draw_text(s, "X wins    Ties    O wins",
                  self.font_tiny, TEXT_DIM, px+138, 306)

        # Move log
        pygame.draw.line(s, SEPARATOR, (px, 320), (px+276, 320), 1)
        draw_text(s, "MOVE LOG", self.font_small, TEXT_DIM, px+138, 336)
        moves   = self.recorder.moves
        visible = moves[-16:] if len(moves) > 16 else moves
        s_idx   = len(moves) - len(visible)
        for i, (pl, nota) in enumerate(visible):
            pair_num = (s_idx + i) // 2 + 1
            is_x     = (pl == 'X')
            label    = f"{pair_num}. {nota}" if is_x else f"    {nota}"
            draw_text(s, label, self.font_tiny,
                      X_COLOR if is_x else O_COLOR,
                      px+138, 356 + i * 14)

        if self.last_saved:
            draw_text(s, "Saved", self.font_tiny, (100, 180, 80), px+138, 582)
            draw_text(s, self.last_saved[-30:], self.font_tiny, (70, 130, 60), px+138, 596)

        self.btn_menu.draw(s)
        self.btn_restart.draw(s)

    def draw_gameover_overlay(self):
        s = self.screen
        if self.winner == 'draw':
            msg, color = "DRAW", SCORE_TIE_COLOR
        elif self.winner == 'X':
            msg, color = "X  WINS!", X_COLOR
        else:
            suffix = "  (AI)" if self.mode == "1P" else ""
            msg, color = f"O  WINS!{suffix}", O_COLOR

        panel_w = SCREEN_W - 300
        ov = pygame.Surface((panel_w, 110), pygame.SRCALPHA)
        ov.fill((20, 15, 10, 185))
        s.blit(ov, (0, SCREEN_H // 2 - 55))
        draw_text(s, msg, self.font_title, color,
                  panel_w // 2, SCREEN_H // 2,
                  glow=True, glow_color=(60, 40, 10))
        draw_text(s,
                  f"X:{self.scores.x_wins}  Ties:{self.scores.draws}  O:{self.scores.o_wins}",
                  self.font_small, TEXT_DIM, panel_w // 2, SCREEN_H // 2 + 38)

    # MAIN LOOP 

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.anim.update(dt)
            mp = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.state == self.MENU:
                    self._handle_menu_event(event, mp)
                else:
                    self._handle_game_event(event, mp)

            if self.state == self.MENU:
                for b in [*self.btn_n, *self.btn_mode, *self.btn_diff,
                           self.btn_reset_score, self.btn_play]:
                    b.check_hover(mp)
            else:
                self.btn_menu.check_hover(mp)
                self.btn_restart.check_hover(mp)
                prev = self.hover_cell
                self.hover_cell = self.pixel_to_cell(*mp)
                if self.hover_cell != prev:
                    self._update_threats()

            if self.state == self.PLAYING and self.ai_thinking:
                if pygame.time.get_ticks() >= self.ai_timer:
                    self.ai_play()

            if self.state == self.MENU:
                self.draw_menu()
            else:
                self.draw_board()
                if self.state == self.GAMEOVER:
                    self.draw_gameover_overlay()

            pygame.display.flip()

    def _handle_menu_event(self, event, pos):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        n_map = {"3x3": 3, "4x4": 4, "5x5": 5}
        for b in self.btn_n:
            if b.is_clicked(pos):
                self.grid_n = n_map[b.label]
                self.win_k  = DEFAULT_K[self.grid_n]
                for bb in self.btn_n: bb.active = False
                b.active = True

        for b in self.btn_mode:
            if b.is_clicked(pos):
                self.mode = "1P" if b.label == "1 Player" else "2P"
                for bb in self.btn_mode: bb.active = False
                b.active = True

        for b in self.btn_diff:
            if b.is_clicked(pos):
                self.difficulty = b.label
                for bb in self.btn_diff: bb.active = False
                b.active = True

        if self.btn_reset_score.is_clicked(pos):
            self.scores.reset()

        if self.btn_play.is_clicked(pos):
            self._start_game()

    def _handle_game_event(self, event, pos):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.btn_menu.is_clicked(pos):
            self.state = self.MENU
            return
        if self.btn_restart.is_clicked(pos):
            self._start_game()
            return

        if self.state == self.GAMEOVER or self.ai_thinking:
            return

        cell = self.pixel_to_cell(*pos)
        if cell:
            r, c = cell
            if self.mode == "2P" or self.current_player == 'X':
                self.human_play(r, c)


# MAIN 

if __name__ == "__main__":
    game = Game()
    game.run()