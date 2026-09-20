"""Widgets custom: botones redondeados (ttk no soporta border-radius)."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from gui import theme as T


class RoundedButton(tk.Frame):
    """Botón con esquinas redondas dibujado en Canvas."""

    def __init__(
        self,
        master=None,
        text: str = "",
        command: Optional[Callable] = None,
        radius: int = 14,
        bg: str = T.ACCENT,
        fg: str = T.FG_INVERT,
        hover: str = T.ACCENT_HOVER,
        disabled_bg: str = T.ACCENT_DISABLED,
        disabled_fg: str = T.ACCENT_DISABLED_FG,
        font=T.FONT_BOLD,
        padx: int = 18,
        pady: int = 8,
        state: str = "normal",
        width: Optional[int] = None,
        **_ignored,
    ):
        parent_bg = T.BG
        try:
            parent_bg = master.cget("background")
        except tk.TclError:
            pass
        if not parent_bg or parent_bg in ("SystemButtonFace",):
            parent_bg = T.BG

        super().__init__(master, bg=parent_bg, highlightthickness=0, bd=0)
        self._command = command
        self._radius = radius
        self._bg = bg
        self._fg = fg
        self._hover = hover
        self._disabled_bg = disabled_bg
        self._disabled_fg = disabled_fg
        self._font = font
        self._padx = padx
        self._pady = pady
        self._state = state
        self._text = text
        self._fixed_width = width

        self._canvas = tk.Canvas(
            self, highlightthickness=0, bd=0, bg=parent_bg, cursor="hand2"
        )
        self._canvas.pack(fill="both", expand=True)
        self._expand_x = False
        self.bind("<Configure>", self._on_resize)
        self._redraw()

        self._canvas.bind("<Button-1>", self._on_click)
        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)

    def pack(self, **kwargs):
        if kwargs.get("fill") in ("x", "both"):
            self._expand_x = True
        return super().pack(**kwargs)

    def grid(self, **kwargs):
        if kwargs.get("sticky") and ("ew" in kwargs["sticky"] or "nsew" == kwargs["sticky"]):
            self._expand_x = True
        return super().grid(**kwargs)

    def _on_resize(self, event):
        if not self._expand_x or event.width < 10:
            return
        if getattr(self, "_last_w", None) == event.width:
            return
        self._last_w = event.width
        self._redraw()

    def _measure(self):
        tmp = tk.Label(self, text=self._text, font=self._font)
        tmp.update_idletasks()
        tw = tmp.winfo_reqwidth()
        th = tmp.winfo_reqheight()
        tmp.destroy()
        w = self._fixed_width if self._fixed_width else tw + self._padx * 2
        if self._expand_x:
            avail = self.winfo_width()
            if avail > 10:
                w = max(w, avail)
        h = th + self._pady * 2
        return max(w, 36), max(h, 28)

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kwargs)

    def _redraw(self, fill: Optional[str] = None):
        self._canvas.delete("all")
        w, h = self._measure()
        self._canvas.config(width=w, height=h)
        disabled = self._state == "disabled"
        color = self._disabled_bg if disabled else (fill or self._bg)
        text_color = self._disabled_fg if disabled else self._fg
        r = min(self._radius, h // 2, w // 2)
        self._round_rect(1, 1, w - 1, h - 1, r, fill=color, outline=color)
        self._canvas.create_text(
            w // 2, h // 2, text=self._text, fill=text_color, font=self._font
        )
        self._canvas.config(cursor="arrow" if disabled else "hand2")

    def _on_click(self, _event=None):
        if self._state == "disabled":
            return
        if self._command:
            self._command()

    def _on_enter(self, _event=None):
        if self._state != "disabled":
            self._redraw(self._hover)

    def _on_leave(self, _event=None):
        self._redraw()

    def config(self, **kwargs):
        return self.configure(**kwargs)

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        if "text" in kwargs:
            self._text = kwargs.pop("text")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "state" in kwargs:
            self._state = kwargs.pop("state")
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    def __setitem__(self, key, value):
        self.configure(**{key: value})
