"""
ui.py — Tkinter interface
Retro CRT theme · QWERTY keyboard · countdown timer · leaderboard
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

import db
import game as gm
from theme import Theme, ALL_THEMES, RETRO

# Timer constants
TIMER_START = 90          # seconds per round
TIMER_WARN  = 30          # goes orange below this
TIMER_CRIT  = 10          # goes red below this

# QWERTY layout
QWERTY_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]



# HangmanCanvas


class HangmanCanvas(tk.Canvas):
    """Progressive vector drawing of the hangman."""

    _STEPS = [
        "_base", "_pole", "_beam", "_rope",
        "_head", "_body",
        "_left_arm", "_right_arm",
        "_left_leg", "_right_leg",
    ]

    def __init__(self, parent, theme: Theme, **kw):
        super().__init__(
            parent, width=220, height=270,
            bg=theme.canvas_bg, highlightthickness=1,
            highlightbackground=theme.fg_dim, **kw,
        )
        self.theme  = theme
        self.errors = 0
        self._redraw()

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.config(bg=theme.canvas_bg, highlightbackground=theme.fg_dim)
        self._redraw()

    def reset(self) -> None:
        self.errors = 0
        self._redraw()

    def add_error(self) -> None:
        if self.errors < len(self._STEPS):
            self.errors += 1
            self._redraw()

    def set_errors(self, n: int) -> None:
        self.errors = min(n, len(self._STEPS))
        self._redraw()

    #  Drawing

    def _redraw(self) -> None:
        self.delete("all")
        # Ground line (always visible)
        self.create_line(15, 255, 205, 255, width=3,
                         fill=self.theme.scaffold, capstyle=tk.ROUND)
        for step in self._STEPS[:self.errors]:
            getattr(self, step)()

    def _ln(self, x1, y1, x2, y2, color=None, w=3):
        self.create_line(x1, y1, x2, y2, width=w,
                         fill=color or self.theme.scaffold,
                         capstyle=tk.ROUND)

    def _base(self):   self._ln(55, 255, 55, 30, w=5)
    def _pole(self):   self._ln(55, 30, 145, 30)
    def _beam(self):   self._ln(55, 55, 75, 30, w=2)
    def _rope(self):   self._ln(145, 30, 145, 68, color=self.theme.fg_warn, w=2)

    def _head(self):
        t = self.theme
        self.create_oval(125, 68, 165, 108, outline=t.head, width=3)
        if self.errors >= len(self._STEPS):
            for ox in (133, 151):
                self.create_line(ox, 77, ox+6, 83, fill=t.fg_error, width=2)
                self.create_line(ox+6, 77, ox, 83, fill=t.fg_error, width=2)
            self.create_arc(133, 92, 157, 107,
                            start=0, extent=180,
                            outline=t.fg_error, width=2, style=tk.ARC)
        else:
            self.create_oval(133, 78, 139, 84, fill=t.head, outline="")
            self.create_oval(151, 78, 157, 84, fill=t.head, outline="")

    def _body(self):
        self._ln(145, 108, 145, 172, color=self.theme.body)

    def _left_arm(self):
        self._ln(145, 122, 115, 152, color=self.theme.fg_accent)

    def _right_arm(self):
        self._ln(145, 122, 175, 152, color=self.theme.fg_accent)

    def _left_leg(self):
        self._ln(145, 172, 115, 212, color=self.theme.fg_success)

    def _right_leg(self):
        self._ln(145, 172, 175, 212, color=self.theme.fg_success)



# Main Application


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        db.init()

        self.theme      : Theme       = RETRO
        self.player     : dict | None = None
        self.state      : gm.GameState | None = None
        self._timer_id  : str | None  = None
        self._time_left : int         = TIMER_START

        self.title("HANGMAN — ELO EDITION")
        self.resizable(False, False)
        self._apply_theme_to_root()
        self._ttk_style()

        self._screen_login()

    # Theme helpers 

    def _apply_theme_to_root(self) -> None:
        self.configure(bg=self.theme.bg)

    def _ttk_style(self) -> None:
        s = ttk.Style(self)
        t = self.theme
        s.theme_use("clam")
        s.configure("TCombobox",
                     fieldbackground=t.bg_input, background=t.bg_panel,
                     foreground=t.fg, selectbackground=t.btn_active,
                     font=(t.font_mono, 10))
        s.map("TCombobox", fieldbackground=[("readonly", t.bg_input)])

    def _toggle_theme(self) -> None:
        names = list(ALL_THEMES.keys())
        idx   = names.index(self.theme.name)
        self.theme = ALL_THEMES[names[(idx + 1) % len(names)]]
        self._apply_theme_to_root()
        self._ttk_style()
        # Rebuild current screen
        if self.player is None:
            self._screen_login()
        else:
            self._screen_game()

    #  Screens 

    def _clear(self) -> None:
        for w in self.winfo_children():
            w.destroy()

    def _screen_login(self) -> None:
        self._stop_timer()
        self._clear()
        t = self.theme

        wrap = tk.Frame(self, bg=t.bg)
        wrap.pack(expand=True, padx=50, pady=50)

        tk.Label(wrap, text="H A N G M A N", font=(t.font_title, 30, "bold"),
                 fg=t.fg_accent, bg=t.bg).pack(pady=(0, 4))
        tk.Label(wrap, text="ELO EDITION", font=(t.font_mono, 12),
                 fg=t.fg_dim, bg=t.bg).pack(pady=(0, 24))

        self._name_var = tk.StringVar()
        entry = tk.Entry(wrap, textvariable=self._name_var,
                         font=(t.font_mono, 14), bg=t.bg_input,
                         fg=t.fg, insertbackground=t.fg_accent,
                         relief=tk.FLAT, width=20)
        entry.pack(ipady=8, pady=(0, 16))
        entry.focus()

        self._btn(wrap, "PLAY →",   self._login,            color=t.fg_success).pack(pady=4)
        self._btn(wrap, "LEADERBOARD", self._screen_leaderboard).pack(pady=4)
        self._btn(wrap, f"THEME: {self.theme.name.upper()}", self._toggle_theme).pack(pady=4)

        entry.bind("<Return>", lambda _: self._login())

    def _login(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a username.")
            return
        self.player = db.get_or_create(name)
        self._screen_game()

    def _screen_game(self) -> None:
        self._stop_timer()
        self._clear()
        t = self.theme

        # Top bar 
        top = tk.Frame(self, bg=t.bg)
        top.pack(fill="x", padx=16, pady=(12, 4))

        self._lbl_player = tk.Label(top,
            text=f"▶ {self.player['name']}",
            font=(t.font_mono, 10), fg=t.fg_dim, bg=t.bg)
        self._lbl_player.pack(side="left")

        self._lbl_elo = tk.Label(top,
            text=f"ELO {self.player['elo']}",
            font=(t.font_mono, 11, "bold"), fg=t.fg_warn, bg=t.bg)
        self._lbl_elo.pack(side="left", padx=12)

        for txt, cmd in [
            (f"[{self.theme.name.upper()}]", self._toggle_theme),
            ("[BOARD]",                       self._screen_leaderboard),
            ("[QUIT]",                        self._screen_login),
        ]:
            self._btn(top, txt, cmd, font_size=9).pack(side="right", padx=2)

        #  Settings 
        cfg = tk.Frame(self, bg=t.bg)
        cfg.pack(fill="x", padx=16, pady=4)

        self._cat_var  = tk.StringVar(value="programming")
        self._diff_var = tk.StringVar(value="medium")

        for label, var, values in [
            ("CAT:",  self._cat_var,  gm.CATEGORIES),
            ("DIFF:", self._diff_var, gm.DIFFICULTIES),
        ]:
            tk.Label(cfg, text=label, font=(t.font_mono, 9),
                     fg=t.fg_dim, bg=t.bg).pack(side="left")
            cb = ttk.Combobox(cfg, textvariable=var, values=values,
                              width=14, state="readonly",
                              font=(t.font_mono, 9))
            cb.pack(side="left", padx=(2, 12))

        # Main layout 
        body = tk.Frame(self, bg=t.bg)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        # Left: canvas + errors
        left = tk.Frame(body, bg=t.bg)
        left.pack(side="left", padx=(0, 16))

        self._canvas = HangmanCanvas(left, self.theme)
        self._canvas.pack()

        self._lbl_errors = tk.Label(left, text="",
            font=(t.font_mono, 9), fg=t.fg_error, bg=t.bg)
        self._lbl_errors.pack(pady=4)

        # Timer
        self._lbl_timer = tk.Label(left, text="",
            font=(t.font_mono, 22, "bold"), fg=t.fg_accent, bg=t.bg)
        self._lbl_timer.pack(pady=4)

        # Right: word + keyboard + actions
        right = tk.Frame(body, bg=t.bg)
        right.pack(side="left", fill="both", expand=True)

        self._lbl_word = tk.Label(right, text="",
            font=(t.font_mono, 26, "bold"), fg=t.fg, bg=t.bg,
            letter_spacing=6)
        self._lbl_word.pack(pady=(12, 4))

        self._lbl_badge = tk.Label(right, text="",
            font=(t.font_mono, 9), fg=t.fg_success, bg=t.bg_panel,
            padx=8, pady=3)
        self._lbl_badge.pack(pady=(0, 8))

        self._lbl_hint = tk.Label(right, text="",
            font=(t.font_mono, 9), fg=t.fg_warn, bg=t.bg,
            wraplength=300, justify="left")
        self._lbl_hint.pack(pady=(0, 6))

        self._lbl_used = tk.Label(right, text="",
            font=(t.font_mono, 9), fg=t.fg_dim, bg=t.bg)
        self._lbl_used.pack(pady=(0, 10))

        # QWERTY keyboard
        self._key_frame = tk.Frame(right, bg=t.bg)
        self._key_frame.pack()
        self._key_btns: dict[str, tk.Button] = {}
        self._build_keyboard()

        # Action buttons
        acts = tk.Frame(right, bg=t.bg)
        acts.pack(pady=10)
        self._btn_hint = self._btn(acts, f"HINT  ({db.HINT_PENALTY} ELO)",
                                   self._use_hint, color=t.fg_warn)
        self._btn_hint.pack(side="left", padx=4)
        self._btn(acts, "NEW WORD", self._new_game).pack(side="left", padx=4)

        self._new_game()

    def _screen_leaderboard(self) -> None:
        win = tk.Toplevel(self)
        win.title("LEADERBOARD")
        win.configure(bg=self.theme.bg)
        win.geometry("440x380")
        t = self.theme

        tk.Label(win, text="LEADERBOARD", font=(t.font_title, 18, "bold"),
                 fg=t.fg_accent, bg=t.bg).pack(pady=(20, 4))

        frame = tk.Frame(win, bg=t.bg_panel, padx=16, pady=12)
        frame.pack(fill="both", expand=True, padx=20, pady=(8, 16))

        headers = ["#", "PLAYER", "ELO", "W", "G"]
        widths  = [3, 14, 6, 5, 5]
        for c, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(frame, text=h, font=(t.font_mono, 9, "bold"),
                     fg=t.fg_accent, bg=t.bg_panel, width=w,
                     anchor="w").grid(row=0, column=c, pady=4)

        medals = ["01", "02", "03"]
        rows   = db.leaderboard()
        for row in rows:
            i    = row["rank"] - 1
            rank = medals[i] if i < 3 else str(row["rank"])
            fg   = t.fg_warn if i == 0 else t.fg
            vals = [rank, row["name"], str(row["elo"]),
                    str(row["games_won"]), str(row["games_played"])]
            for c, (v, w) in enumerate(zip(vals, widths)):
                tk.Label(frame, text=v, font=(t.font_mono, 9),
                         fg=fg, bg=t.bg_panel, width=w,
                         anchor="w").grid(row=i+1, column=c, pady=2)

        if not rows:
            tk.Label(frame, text="No players yet.",
                     font=(t.font_mono, 10), fg=t.fg_dim,
                     bg=t.bg_panel).grid(row=1, columnspan=5, pady=20)

        self._btn(win, "CLOSE", win.destroy).pack(pady=(0, 16))

    # Game actions 

    def _new_game(self) -> None:
        self._stop_timer()
        cat  = self._cat_var.get()
        diff = self._diff_var.get()
        self.state = gm.new_game(cat, diff)
        self._canvas.apply_theme(self.theme)
        self._canvas.reset()
        self._build_keyboard()
        self._lbl_hint.config(text="")
        self._btn_hint.config(state="normal")
        self._lbl_badge.config(
            text=f"  {cat}  ·  {diff}  "
        )
        self._time_left = TIMER_START
        self._update_display()
        self._tick()
        self.bind("<Key>", self._on_key)

    def _tick(self) -> None:
        if self.state and self.state.is_over:
            return
        self._update_timer_label()
        if self._time_left <= 0:
            self._timeout()
            return
        self._time_left -= 1
        self._timer_id = self.after(1000, self._tick)

    def _stop_timer(self) -> None:
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    def _timeout(self) -> None:
        if self.state and not self.state.is_over:
            self.state.errors = gm.MAX_ERRORS
            self.state.end_time = time.time()
            self._canvas.set_errors(gm.MAX_ERRORS)
            self._end_game()

    def _guess(self, letter: str) -> None:
        if not self.state or self.state.is_over:
            return
        hit = self.state.guess(letter)
        btn = self._key_btns.get(letter)
        if btn:
            btn.config(
                bg=self.theme.btn_active if hit else "#3d0000",
                fg=self.theme.fg if hit else self.theme.fg_error,
                state="disabled",
            )
        if not hit:
            self._canvas.add_error()
        self._update_display()
        if self.state.is_over:
            self._stop_timer()
            self._end_game()

    def _on_key(self, event) -> None:
        k = event.char.upper()
        if k.isalpha() and k in self._key_btns:
            self._guess(k)

    def _use_hint(self) -> None:
        if not self.state or self.state.hint_used:
            return
        reveal = self.state.use_hint()
        if reveal:
            btn = self._key_btns.get(reveal)
            if btn:
                btn.config(bg=self.theme.btn_active, state="disabled")
            hint_text = f"HINT  ▶  letter « {reveal} » revealed"
        elif self.state.definition:
            hint_text = f"DEF  ▶  {self.state.definition}"
        else:
            hint_text = "No hint available."
        self._lbl_hint.config(text=hint_text)
        self._btn_hint.config(state="disabled")
        self._update_display()
        if self.state.is_over:
            self._stop_timer()
            self._end_game()

    def _end_game(self) -> None:
        s = self.state
        # Fill remaining errors on canvas
        self._canvas.set_errors(s.errors)
        delta = db.record_game(
            player     = self.player["name"],
            word       = s.word,
            category   = s.category,
            difficulty = s.difficulty,
            won        = s.won,
            hint_used  = s.hint_used,
            duration_s = s.duration,
        )
        self.player = db.fetch_player(self.player["name"])
        self._lbl_elo.config(text=f"ELO {self.player['elo']}")

        sign = "+" if delta >= 0 else ""
        if s.won:
            msg = (f"✓ Word found: {s.word}\n\n"
                   f"Time: {s.duration}s    ELO: {sign}{delta} → {self.player['elo']}")
            messagebox.showinfo("WIN", msg)
        else:
            msg = (f"✗ The word was: {s.word}\n\n"
                   f"ELO: {sign}{delta} → {self.player['elo']}")
            messagebox.showinfo("GAME OVER", msg)

        self._new_game()

    #  Display helpers ─

    def _update_display(self) -> None:
        if not self.state:
            return
        s = self.state
        t = self.theme
        self._lbl_word.config(text=s.display)
        self._lbl_errors.config(text=f"errors  {s.errors} / {gm.MAX_ERRORS}")
        wrong = "  ".join(s.wrong_letters) or "—"
        self._lbl_used.config(text=f"wrong:  {wrong}")

    def _update_timer_label(self) -> None:
        t = self.theme
        secs = self._time_left
        mm   = secs // 60
        ss   = secs % 60
        txt  = f"{mm:01d}:{ss:02d}"
        if secs <= TIMER_CRIT:
            color = t.fg_error
        elif secs <= TIMER_WARN:
            color = t.fg_warn
        else:
            color = t.fg_accent
        self._lbl_timer.config(text=txt, fg=color)

    def _build_keyboard(self) -> None:
        for w in self._key_frame.winfo_children():
            w.destroy()
        self._key_btns.clear()
        t = self.theme
        for row in QWERTY_ROWS:
            rf = tk.Frame(self._key_frame, bg=t.bg)
            rf.pack(pady=2)
            for letter in row:
                btn = tk.Button(
                    rf, text=letter, width=3,
                    font=(t.font_mono, 10, "bold"),
                    bg=t.btn_bg, fg=t.btn_fg,
                    activebackground=t.btn_active,
                    relief=tk.FLAT, cursor="hand2",
                    command=lambda l=letter: self._guess(l),
                )
                btn.pack(side="left", padx=2)
                self._key_btns[letter] = btn

    #  Reusable button factory 

    def _btn(self, parent, text, cmd, color=None, font_size=10) -> tk.Button:
        t = self.theme
        return tk.Button(
            parent, text=text, command=cmd,
            font=(t.font_mono, font_size),
            bg=t.btn_bg, fg=color or t.btn_fg,
            activebackground=t.btn_active,
            relief=tk.FLAT, cursor="hand2",
            padx=10, pady=4,
        )
