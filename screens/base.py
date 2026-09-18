"""Base class for the four screens."""
from __future__ import annotations

import tkinter as tk

import audio
from anim import Clock
from config import HEIGHT, PALETTE, WIDTH
import ui


class Screen:
    """One full-window canvas plus its own animation clock.

    The screen manager places screens with `place()` and slides them, so every
    screen must be exactly WIDTH x HEIGHT.
    """

    background_mood = "day"

    def __init__(self, app):
        self.app = app
        self.canvas = tk.Canvas(app.container, width=WIDTH, height=HEIGHT,
                                bg=PALETTE["bg"], highlightthickness=0, bd=0)
        self.clock = Clock(self.canvas)
        self.alive = True
        self.sound_btn = None

    # -- overridable hooks
    def build(self):
        """Create canvas items. Called once, before the screen is shown."""

    def on_enter(self):
        """Called once the slide-in transition has finished."""

    def on_exit(self):
        """Called just before the screen is destroyed."""

    # -- plumbing
    def start(self):
        if self.sound_btn is None:
            self.sound_btn = ui.make_button(
                self.canvas, self.clock, WIDTH - 70, 42, 122, 38,
                self._sound_label(), self._toggle_sound, font_size=11,
                fill=PALETTE["lav_soft"], hover_fill=PALETTE["lav"],
                border=PALETTE["lav_deep"], text_color=PALETTE["lav_deep"],
                lift=3, hover_scale=1.02, sparkles=False, sound=None)
        self.canvas.tag_raise(self.sound_btn.tag)
        self.clock.start()

    def _sound_label(self):
        return "SOUND: OFF" if audio.MUTED else "SOUND: ON"

    def _toggle_sound(self):
        muted = audio.toggle_muted()
        self.sound_btn.set_text(self._sound_label())
        # Restore the button's normal colour after a muted toggle.
        if not muted:
            audio.play("click")

    def destroy(self):
        self.alive = False
        try:
            self.on_exit()
        except tk.TclError:
            pass
        self.clock.stop()
        try:
            self.canvas.destroy()
        except tk.TclError:
            pass

    # -- convenience
    def text(self, x, y, content, role="pixel", size=18, color=None,
             anchor="center", tags=(), weight="normal"):
        import assets
        return self.canvas.create_text(
            x, y, text=content, anchor=anchor,
            font=assets.font(role, size, weight),
            fill=color or PALETTE["ink"], tags=tags)
