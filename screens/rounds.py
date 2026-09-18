"""Screen 2: choose how many rounds to play."""
from __future__ import annotations

import fx
import sprites
import ui
from config import DEFAULT_ROUNDS, PALETTE, ROUND_CHOICES, WIDTH
from screens.base import Screen


class RoundSelectScreen(Screen):
    def build(self):
        c = self.canvas
        self.bg = fx.Background(c, self.clock, stars=22, clouds=2, hearts=3)

        self.title = self.text(WIDTH / 2, 120, "GAME SETTINGS", role="title",
                               size=46, color=PALETTE["pink_ink"])
        ui.pop_text(c, self.clock, self.title, 46)
        self.text(WIDTH / 2, 178, "How many rounds do you want to play?",
                  size=16, color=PALETTE["ink_soft"])

        self.selected = DEFAULT_ROUNDS
        self.buttons = {}
        self.stars = {}
        for i, count in enumerate(ROUND_CHOICES):
            cy = 270 + i * 96
            btn = ui.make_button(
                c, self.clock, WIDTH / 2, cy, 340, 72, f"{count}  ROUNDS",
                lambda n=count: self._select(n), font_size=22,
                fill=PALETTE["pink_pale"], hover_fill=PALETTE["pink_soft"],
                border=PALETTE["pink"], text_color=PALETTE["pink_ink"],
                selected_fill=PALETTE["pink"], lift=5, hover_scale=1.03,
                selected=(count == DEFAULT_ROUNDS))
            self.buttons[count] = btn
            star_ids = sprites.draw_centered(c, "star", WIDTH / 2 + 205, cy, 4)
            self.stars[count] = star_ids
            if count != DEFAULT_ROUNDS:
                for sid in star_ids:
                    c.itemconfigure(sid, state="hidden")

        self.begin_btn = ui.make_button(
            c, self.clock, WIDTH / 2, 600, 400, 92, "⚔  BEGIN BATTLE!",
            self._begin, font_size=28, fill=PALETTE["pink"],
            hover_fill=PALETTE["pink_soft"], border=PALETTE["pink_deep"],
            text_color=PALETTE["pink_ink"], lift=8, hover_scale=1.05)

        self.back_btn = ui.make_button(
            c, self.clock, 96, 686, 150, 48, "⌂  MENU", self._menu,
            font_size=15, fill=PALETTE["lav_soft"], hover_fill=PALETTE["lav"],
            border=PALETTE["lav"], text_color=PALETTE["lav_deep"],
            lift=4, hover_scale=1.03, sparkles=False)

    def _select(self, count):
        if count == self.selected:
            return
        self.buttons[self.selected].set_selected(False)
        for sid in self.stars[self.selected]:
            self.canvas.itemconfigure(sid, state="hidden")
        self.selected = count
        self.buttons[count].set_selected(True)
        for sid in self.stars[count]:
            self.canvas.itemconfigure(sid, state="normal")

    def _begin(self):
        from screens.gameplay import GameplayScreen
        rounds = self.selected if self.selected in ROUND_CHOICES else DEFAULT_ROUNDS
        self.app.go(GameplayScreen, rounds=rounds)

    def _menu(self):
        from screens.welcome import WelcomeScreen
        self.app.go(WelcomeScreen, direction=-1)
