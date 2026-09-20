"""Paleta clara unificada — buen contraste, monocromo (alineada al mascote)."""

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

FONT = ("DejaVu Sans", 10)
FONT_BOLD = ("DejaVu Sans", 10, "bold")
FONT_TITLE = ("DejaVu Sans", 18, "bold")
FONT_SUB = ("DejaVu Sans", 11, "bold")
FONT_HINT = ("DejaVu Sans", 9)


def apply_ttk_theme(root, style) -> None:
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(background=BG)

    style.configure(
        ".",
        background=BG,
        foreground=FG,
        fieldbackground=SURFACE,
        font=FONT,
        bordercolor=BORDER,
        darkcolor=BORDER,
        lightcolor=SURFACE,
    )
    style.configure("TFrame", background=BG)
    style.configure("TLabelframe", background=BG, foreground=FG)
    style.configure("TLabelframe.Label", background=BG, foreground=FG)

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=SURFACE_2,
        foreground=FG,
        padding=[12, 6],
        font=FONT_BOLD,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE), ("active", SURFACE)],
        foreground=[("selected", FG)],
    )

    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("Hint.TLabel", background=BG, foreground=FG_MUTED, font=FONT_HINT)

    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=FG,
        insertcolor=FG,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        foreground=FG,
        background=SURFACE,
        arrowcolor=FG,
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
        rowheight=24,
    )
    style.configure(
        "Treeview.Heading",
        background=SURFACE_2,
        foreground=FG,
        font=FONT_BOLD,
        borderwidth=0,
    )
    style.map(
        "Treeview",
        background=[("selected", SELECT)],
        foreground=[("selected", SELECT_FG)],
    )

    style.configure("TCheckbutton", background=BG, foreground=FG, focuscolor=BG)
    style.configure("TRadiobutton", background=BG, foreground=FG, focuscolor=BG)
    style.map("TCheckbutton", background=[("active", BG)])
    style.map("TRadiobutton", background=[("active", BG)])

    style.configure(
        "TButton",
        background=ACCENT,
        foreground=FG_INVERT,
        padding=[10, 5],
        borderwidth=0,
    )
