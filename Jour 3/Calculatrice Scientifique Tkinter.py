import tkinter as tk
from tkinter import font as tkfont
import math

#  Themes
THEMES = {
    "dark": {
        "bg":         "#1a0e00",
        "panel":      "#2b1500",
        "display":    "#3d1f00",
        "text":       "#ffe8cc",
        "subtext":    "#c49a6c",
        "btn_num":    "#2b1500",
        "btn_num_fg": "#ffe8cc",
        "btn_op":     "#e8620a",
        "btn_op_fg":  "#ffffff",
        "btn_fn":     "#3d1f00",
        "btn_fn_fg":  "#ffaa55",
        "btn_eq":     "#e8620a",
        "btn_eq_fg":  "#ffffff",
        "btn_clear":  "#b03a00",
        "btn_clear_fg":"#ffffff",
        "hover_num":  "#4a2800",
        "hover_op":   "#c04d00",
        "hover_fn":   "#5a3000",
        "border":     "#5a3000",
    },
    "light": {
        "bg":         "#fff5eb",
        "panel":      "#ffffff",
        "display":    "#ffe8cc",
        "text":       "#2b1500",
        "subtext":    "#8b5e3c",
        "btn_num":    "#ffffff",
        "btn_num_fg": "#2b1500",
        "btn_op":     "#e8620a",
        "btn_op_fg":  "#ffffff",
        "btn_fn":     "#ffe8cc",
        "btn_fn_fg":  "#b03a00",
        "btn_eq":     "#e8620a",
        "btn_eq_fg":  "#ffffff",
        "btn_clear":  "#c04d00",
        "btn_clear_fg":"#ffffff",
        "hover_num":  "#ffd9b0",
        "hover_op":   "#c04d00",
        "hover_fn":   "#ffc999",
        "border":     "#f0c090",
    }
}

current_theme = "light"


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculatrice Scientifique Tkinter")
        self.resizable(False, False)
        self.configure(bg=THEMES[current_theme]["bg"])

        self.expression = ""
        self.history = []
        self.result_shown = False

        self._build_ui()
        self._apply_theme()

    # IU Construction
    def _build_ui(self):
        t = THEMES[current_theme]

        # Header
        header = tk.Frame(self, bg=t["bg"], pady=6)
        header.pack(fill="x", padx=12)

        tk.Label(header, text="🧮 Calculatrice Scientifique",
                 bg=t["bg"], fg=t["btn_op"], font=("Courier", 13, "bold")
                 ).pack(side="left")

        self.theme_btn = tk.Button(
            header, text="☀ Clair", bg=t["btn_fn"], fg=t["btn_fn_fg"],
            relief="flat", cursor="hand2", font=("Courier", 10),
            command=self._toggle_theme, bd=0, padx=8, pady=4
        )
        self.theme_btn.pack(side="right")

        # Display
        disp_frame = tk.Frame(self, bg=t["display"], bd=0, pady=8,
                              highlightthickness=1,
                              highlightbackground=t["border"])
        disp_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.sub_var = tk.StringVar(value="")
        tk.Label(disp_frame, textvariable=self.sub_var,
                 bg=t["display"], fg=t["subtext"],
                 font=("Courier", 11), anchor="e"
                 ).pack(fill="x", padx=10)

        self.expr_var = tk.StringVar(value="0")
        tk.Label(disp_frame, textvariable=self.expr_var,
                 bg=t["display"], fg=t["text"],
                 font=("Courier", 26, "bold"), anchor="e"
                 ).pack(fill="x", padx=10)

        # Historic
        hist_frame = tk.Frame(self, bg=t["panel"],
                              highlightthickness=1,
                              highlightbackground=t["border"])
        hist_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(hist_frame, text="Historique", bg=t["panel"],
                 fg=t["subtext"], font=("Courier", 9)).pack(anchor="w", padx=6)

        self.hist_text = tk.Text(
            hist_frame, height=4, bg=t["panel"], fg=t["subtext"],
            font=("Courier", 10), relief="flat", state="disabled",
            wrap="none"
        )
        scroll = tk.Scrollbar(hist_frame, command=self.hist_text.yview,
                              bg=t["border"])
        self.hist_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.hist_text.pack(fill="x", padx=6, pady=(0, 4))

        # Bouttons
        btn_frame = tk.Frame(self, bg=t["bg"])
        btn_frame.pack(padx=12, pady=(0, 12))

        layout = [
            # (texte, colonne, ligne, colspan, type)
            ("C",    0, 0, 1, "clear"), ("(",   1, 0, 1, "op"),
            (")",    2, 0, 1, "op"),    ("/",   3, 0, 1, "op"),
            ("sin",  4, 0, 1, "fn"),

            ("7",    0, 1, 1, "num"),   ("8",   1, 1, 1, "num"),
            ("9",    2, 1, 1, "num"),   ("*",   3, 1, 1, "op"),
            ("cos",  4, 1, 1, "fn"),

            ("4",    0, 2, 1, "num"),   ("5",   1, 2, 1, "num"),
            ("6",    2, 2, 1, "num"),   ("-",   3, 2, 1, "op"),
            ("tan",  4, 2, 1, "fn"),

            ("1",    0, 3, 1, "num"),   ("2",   1, 3, 1, "num"),
            ("3",    2, 3, 1, "num"),   ("+",   3, 3, 1, "op"),
            ("log",  4, 3, 1, "fn"),

            ("0",    0, 4, 1, "num"),   (".",   1, 4, 1, "num"),
            ("⌫",   2, 4, 1, "clear"),  ("=",   3, 4, 1, "eq"),
            ("√",    4, 4, 1, "fn"),

            ("π",    0, 5, 1, "fn"),    ("e",   1, 5, 1, "fn"),
            ("x²",   2, 5, 1, "fn"),    ("x³",  3, 5, 1, "fn"),
            ("ln",   4, 5, 1, "fn"),
        ]

        self.buttons = []
        for (text, col, row, span, btype) in layout:
            btn = self._make_button(btn_frame, text, btype)
            btn.grid(row=row, column=col, columnspan=span,
                     padx=3, pady=3, sticky="nsew", ipadx=6, ipady=10)
            self.buttons.append((btn, btype))

        for i in range(5):
            btn_frame.columnconfigure(i, weight=1, minsize=62)
        for i in range(6):
            btn_frame.rowconfigure(i, weight=1)

        # Keyboard binding
        self.bind("<Key>", self._on_key)

    def _make_button(self, parent, text, btype):
        t = THEMES[current_theme]
        colors = {
            "num":   (t["btn_num"],   t["btn_num_fg"],   t["hover_num"]),
            "op":    (t["btn_op"],    t["btn_op_fg"],    t["hover_op"]),
            "fn":    (t["btn_fn"],    t["btn_fn_fg"],    t["hover_fn"]),
            "eq":    (t["btn_eq"],    t["btn_eq_fg"],    t["hover_op"]),
            "clear": (t["btn_clear"], t["btn_clear_fg"], "#7a4aad"),
        }
        bg, fg, hover = colors.get(btype, colors["num"])

        btn = tk.Button(
            parent, text=text, bg=bg, fg=fg,
            font=("Courier", 13, "bold"),
            relief="flat", cursor="hand2", bd=0,
            activebackground=hover, activeforeground=fg,
            command=lambda t=text: self._on_click(t)
        )
        btn.bind("<Enter>", lambda e, b=btn, h=hover: b.config(bg=h))
        btn.bind("<Leave>", lambda e, b=btn, c=bg: b.config(bg=c))
        return btn

    # Logic
    def _on_click(self, text):
        t = text
        if t == "C":
            self.expression = ""
            self.expr_var.set("0")
            self.sub_var.set("")
            self.result_shown = False

        elif t == "⌫":
            if self.result_shown:
                self.expression = ""
                self.expr_var.set("0")
                self.result_shown = False
            else:
                self.expression = self.expression[:-1]
                self.expr_var.set(self.expression or "0")

        elif t == "=":
            self._calculate()

        elif t == "π":
            self._append(str(math.pi))
        elif t == "e":
            self._append(str(math.e))
        elif t == "x²":
            self._append("**2")
        elif t == "x³":
            self._append("**3")
        elif t == "√":
            self._append("math.sqrt(")
        elif t == "sin":
            self._append("math.sin(math.radians(")
        elif t == "cos":
            self._append("math.cos(math.radians(")
        elif t == "tan":
            self._append("math.tan(math.radians(")
        elif t == "log":
            self._append("math.log10(")
        elif t == "ln":
            self._append("math.log(")
        else:
            if self.result_shown and t not in "+-*/)":
                self.expression = ""
            self.result_shown = False
            self._append(t)

    def _append(self, val):
        self.expression += val
        self.expr_var.set(self.expression)

    def _calculate(self):
        expr = self.expression
        if not expr:
            return
        # Automatically close the 
        opens = expr.count("(") - expr.count(")")
        expr += ")" * max(0, opens)

        try:
            result = eval(expr, {"__builtins__": {}}, {"math": math})
            # Division by zero check
            if result == float("inf") or result == float("-inf"):
                raise ZeroDivisionError("Division par zéro")
            # Properly rounded
            if isinstance(result, float):
                display = f"{result:.10g}"
            else:
                display = str(result)

            history_entry = f"{self.expression} = {display}"
            self.history.append(history_entry)
            self._update_history()

            self.sub_var.set(self.expression)
            self.expr_var.set(display)
            self.expression = display
            self.result_shown = True

        except ZeroDivisionError:
            self.expr_var.set("Erreur: ÷ par zéro")
            self.sub_var.set(self.expression)
            self.expression = ""
            self.result_shown = True
        except Exception:
            self.expr_var.set("Expression invalide")
            self.sub_var.set(self.expression)
            self.expression = ""
            self.result_shown = True

    def _update_history(self):
        self.hist_text.config(state="normal")
        self.hist_text.delete("1.0", "end")
        for entry in reversed(self.history[-50:]):
            self.hist_text.insert("end", entry + "\n")
        self.hist_text.config(state="disabled")

    def _on_key(self, event):
        k = event.char
        mapping = {
            "\r": "=", "\x08": "⌫",
        }
        k = mapping.get(k, k)
        valid = set("0123456789.+-*/()=⌫")
        if k in valid:
            self._on_click(k)

    # Theme toggle
    def _toggle_theme(self):
        global current_theme
        current_theme = "light" if current_theme == "dark" else "dark"
        # UI Reconstruction
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg=THEMES[current_theme]["bg"])
        self._build_ui()
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[current_theme]
        label = "🌙 Sombre" if current_theme == "light" else "☀ Clair"
        self.theme_btn.config(text=label)
        self._update_history()


if __name__ == "__main__":
    app = Calculator()
    app.mainloop()
