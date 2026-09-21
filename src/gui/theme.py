"""Paleta clara unificada — buen contraste, monocromo (alineada al mascote)."""

from __future__ import annotations

import tkinter.font as tkfont
from tkinter import ttk

# Superficies
BG = "#f4f4f5"           # fondo app
SURFACE = "#ffffff"      # paneles / entradas
SURFACE_2 = "#eaeaec"    # tabs inactivas, listados
BORDER = "#d0d0d4"

# Texto
FG = "#1c1c1e"           # texto principal
FG_MUTED = "#6b6b70"     # hints
FG_INVERT = "#ffffff"    # sobre botones oscuros

# Acción
ACCENT = "#2c2c30"       # botones
ACCENT_HOVER = "#1a1a1c"
ACCENT_DISABLED = "#c8c8cc"
ACCENT_DISABLED_FG = "#8a8a8e"

# Selección / estados
SELECT = "#d8d8dc"
SELECT_FG = "#1c1c1e"
OK = "#1a7f37"           # cápsula lista
WARN_BG = "#fff4e5"

# Escala tipográfica (pasos claros: hint < body < sección < página < marca)
# Los ttk Labels de título usan también font= en el widget porque en algunos Tk
# el estilo Page.TLabel no gana al font del "." raíz.
FONT = ("DejaVu Sans", 11)
FONT_BOLD = ("DejaVu Sans", 11, "bold")
FONT_HINT = ("DejaVu Sans", 9)
FONT_SUB = ("DejaVu Sans", 13, "bold")      # sección
FONT_PAGE = ("DejaVu Sans", 16, "bold")     # título de pestaña
FONT_TIMER = ("DejaVu Sans", 20, "bold")
FONT_TITLE = ("DejaVu Sans", 22, "bold")    # marca / pantalla de entrada

# Referencias vivas a Font (si se pierden, Tk deja de aplicar weight=bold)
_FONT_OBJS: dict[str, tkfont.Font] = {}
_FONT_ROOT_ID: int | None = None


def _font(root, key: str, size: int, weight: str = "normal") -> tkfont.Font:
    global _FONT_ROOT_ID
    # Nuevo Tk (unlock → app → cambiar bóveda): las Font del root muerto no sirven.
    if _FONT_ROOT_ID != id(root):
        _FONT_OBJS.clear()
        _FONT_ROOT_ID = id(root)
    obj = _FONT_OBJS.get(key)
    if obj is None:
        obj = tkfont.Font(root=root, family="DejaVu Sans", size=size, weight=weight)
        _FONT_OBJS[key] = obj
    return obj


def page_header(parent, title: str, subtitle: str | None = None, wraplength: int = 700):
    """Título de página + subtítulo opcional. Devuelve el frame del encabezado."""
    box = ttk.Frame(parent)
    ttk.Label(box, text=title, style="Page.TLabel", font=FONT_PAGE).pack(anchor="w")
    if subtitle:
        ttk.Label(
            box, text=subtitle, style="Hint.TLabel", wraplength=wraplength
        ).pack(anchor="w", pady=(4, 0))
    return box


def apply_ttk_theme(root, style) -> None:
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(background=BG)

    f_body = _font(root, "body", 11)
    f_bold = _font(root, "bold", 11, "bold")
    f_sub = _font(root, "sub", 13, "bold")
    f_page = _font(root, "page", 16, "bold")
    f_title = _font(root, "title", 22, "bold")
    f_timer = _font(root, "timer", 20, "bold")
    f_hint = _font(root, "hint", 9)

    # No poner font en ".": pisa los font= de cada Label (era el bug visual).
    style.configure(
        ".",
        background=BG,
        foreground=FG,
        fieldbackground=SURFACE,
        bordercolor=BORDER,
        darkcolor=BORDER,
        lightcolor=SURFACE,
    )
    style.configure("TFrame", background=BG)
    style.configure("TLabelframe", background=BG, foreground=FG)
    style.configure("TLabelframe.Label", background=BG, foreground=FG, font=f_sub)

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=SURFACE_2,
        foreground=FG,
        padding=[14, 7],
        font=f_bold,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE), ("active", SURFACE)],
        foreground=[("selected", FG)],
    )

    style.configure("TLabel", background=BG, foreground=FG, font=f_body)
    style.configure("Bold.TLabel", background=BG, foreground=FG, font=f_bold)
    style.configure("Heading.TLabel", background=BG, foreground=FG, font=f_sub)
    style.configure("Title.TLabel", background=BG, foreground=FG, font=f_title)
    style.configure("Page.TLabel", background=BG, foreground=FG, font=f_page)
    style.configure("Timer.TLabel", background=BG, foreground=FG, font=f_timer)
    style.configure("Hint.TLabel", background=BG, foreground=FG_MUTED, font=f_hint)

    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=FG,
        insertcolor=FG,
        borderwidth=1,
        relief="solid",
        font=f_body,
    )
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        foreground=FG,
        background=SURFACE,
        arrowcolor=FG,
        font=f_body,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE)],
        foreground=[("readonly", FG)],
    )

    style.configure(
        "Treeview",
        background=SURFACE,
        foreground=FG,
        fieldbackground=SURFACE,
        borderwidth=1,
        rowheight=28,
        font=f_body,
    )
    style.configure(
        "Treeview.Heading",
        background=SURFACE_2,
        foreground=FG,
        font=f_bold,
        borderwidth=0,
    )
    style.map(
        "Treeview",
        background=[("selected", SELECT)],
        foreground=[("selected", SELECT_FG)],
    )

    style.configure("TCheckbutton", background=BG, foreground=FG, focuscolor=BG, font=f_body)
    style.configure("TRadiobutton", background=BG, foreground=FG, focuscolor=BG, font=f_body)
    style.map("TCheckbutton", background=[("active", BG)])
    style.map("TRadiobutton", background=[("active", BG)])

    style.configure(
        "TButton",
        background=ACCENT,
        foreground=FG_INVERT,
        padding=[10, 5],
        borderwidth=0,
        font=f_bold,
    )

    style.configure("TSpinbox", fieldbackground=SURFACE, foreground=FG, font=f_body)
