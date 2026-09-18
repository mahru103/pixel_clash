"""Screen 1: the welcome / title screen."""
from __future__ import annotations

import math

import fx
import sprites
import ui
from config import PALETTE, WIDTH
from screens.base import Screen


class WelcomeScreen(Screen):
    def build(self):
        c = self.canvas
        self.bg = fx.Background(c, self.clock, stars=30, clouds=3, hearts=5)

        # -- title block
        self.title_a = self.text(WIDTH / 2, 150, "ROCK PAPER SCISSORS",
                                 role="title", size=44, color=PALETTE["pink_ink"])
        self.title_b = self.text(WIDTH / 2, 212, "PIXEL CLASH",
                                 role="title", size=58, color=PALETTE["pink_deep"])
        ui.pop_text(c, self.clock, self.title_a, 44)
        ui.pop_text(c, self.clock, self.title_b, 58, duration=0.55)

        for dx, dy, name, scale in ((-250, 118, "star", 3), (250, 118, "star", 3),
                                    (-215, 232, "heart", 3), (215, 232, "heart", 3)):
            sprites.draw_centered(c, name, WIDTH / 2 + dx, dy, scale)

        self.text(WIDTH / 2, 270, "Can you defeat the computer?",
                  size=17, color=PALETTE["ink_soft"])

        # -- idle move sprites
        self.icons = []
        for i, (name, x) in enumerate((("rock", 210), ("paper", 400), ("scissors", 590))):
            ids = ui.draw_icon(c, name, x, 380, 92, tags=(f"idle{i}",))
            self.icons.append({"ids": ids, "phase": i * 2.1, "kind": name,
                               "last_dy": 0.0, "last_scale": 1.0, "x": x, "y": 380})
            self.text(x, 448, name.upper(), size=14, color=PALETTE["ink_soft"])

        self.t = 0.0
        self.clock.subscribe(self._idle)

        # -- start button
        self.start_btn = ui.make_button(
            c, self.clock, WIDTH / 2, 560, 300, 78, "▶  START GAME",
            self._start, font_size=24, fill=PALETTE["pink"],
            hover_fill=PALETTE["pink_soft"], border=PALETTE["pink_deep"],
            text_color=PALETTE["pink_ink"], lift=7)

        self.text(WIDTH / 2, 660, "Choose your move.  Start the clash.",
                  size=13, color=PALETTE["ink_soft"])

        # -- footer
        self.text(WIDTH / 2, 706, "Made with  ♡  by Maha", size=12,
                  color=PALETTE["ink_soft"])
        sprites.draw_centered(c, "heart", WIDTH / 2 - 130, 706, 2)
        sprites.draw_centered(c, "heart", WIDTH / 2 + 130, 706, 2)

    def _idle(self, dt):
        self.t += dt
        c = self.canvas
        for i, icon in enumerate(self.icons):
            tag = f"idle{i}"
            if icon["kind"] == "rock":                      # gentle bob
                offset = math.sin(self.t * 1.5 + icon["phase"]) * 6
            elif icon["kind"] == "paper":                   # slower, smaller wiggle
                offset = math.sin(self.t * 2.4 + icon["phase"]) * 3
                dx = math.sin(self.t * 1.9) * 0.6
                c.move(tag, dx, 0)
            else:                                           # scissors: breathe
                offset = math.sin(self.t * 1.8 + icon["phase"]) * 4
                target = 1.0 + math.sin(self.t * 1.8) * 0.03
                factor = target / icon["last_scale"]
                icon["last_scale"] = target
                c.scale(tag, icon["x"], icon["y"] + icon["last_dy"], factor, factor)
            dy = offset - icon["last_dy"]
            icon["last_dy"] = offset
            c.move(tag, 0, dy)

    def _start(self):
        from screens.rounds import RoundSelectScreen
        self.app.go(RoundSelectScreen)
