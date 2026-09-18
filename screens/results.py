"""Screen 4: victory, defeat or a draw."""
from __future__ import annotations

import math
import random

import audio
import fx
import sprites
import ui
from anim import ease_out_bounce, ease_out_cubic
from config import PALETTE, WIDTH
from screens.base import Screen


class ResultsScreen(Screen):
    def __init__(self, app, state):
        super().__init__(app)
        self.state = state
        self.won = state.player_won
        self.drew = state.drawn
        self.confetti = None
        self.rain = None
        self.blink_t = 0.0
        self.bob_t = 0.0
        self._bob_last = 0.0

    # ------------------------------------------------------------ build --
    def build(self):
        mood = "day" if self.won or self.drew else "gloom"
        c = self.canvas
        self.bg = fx.Background(c, self.clock, mood=mood,
                                stars=28 if self.won else 14,
                                clouds=2, hearts=4 if self.won else 1)
        if self.won:
            self._build_victory()
        elif self.drew:
            self._build_draw()
        else:
            self._build_defeat()
        self._build_scorecard()
        self._build_buttons()

    def on_enter(self):
        if self.won:
            audio.play("victory")
            self.confetti = fx.Confetti(self.canvas, self.clock, count=80,
                                        duration=7.0)
            self.canvas.tag_raise("confetti")
        elif not self.drew:
            self.rain = fx.Rain(self.canvas, self.clock, count=44)
            self.canvas.tag_lower("rain")
            self.canvas.tag_lower("bglayer")
        self.clock.subscribe(self._animate_cat)

    def on_exit(self):
        if self.confetti:
            self.confetti.stop()
        if self.rain:
            self.rain.stop()

    # ---------------------------------------------------------- variants --
    def _build_victory(self):
        c = self.canvas
        self.headline = self.text(WIDTH / 2, 108, "VICTORY!", role="title",
                                  size=68, color=PALETTE["pink_deep"])
        ui.pop_text(c, self.clock, self.headline, 68, duration=0.6)
        self.text(WIDTH / 2, 166, "Congratulations!", size=20,
                  color=PALETTE["pink_ink"])
        self.text(WIDTH / 2, 198, "You defeated the computer!", size=15,
                  color=PALETTE["ink_soft"])

        self.cat_tag = "cat"
        self.cat_ids = sprites.draw_centered(c, "cat_happy", WIDTH / 2 - 40, 300,
                                             8, tags=(self.cat_tag,))
        sprites.draw_centered(c, "trophy", WIDTH / 2 + 92, 318, 6,
                              tags=(self.cat_tag,))
        self.eye_ids = [i for i in self.cat_ids
                        if c.itemcget(i, "fill") == PALETTE["ink"]]
        self.fur_color = PALETTE["cream"]

        self.hearts = []
        for dx, dy in ((-140, 250), (130, 232), (-100, 200)):
            ids = sprites.draw_centered(c, "heart", WIDTH / 2 + dx, dy, 3)
            self.hearts.append({"ids": ids, "phase": random.uniform(0, 6.2),
                                "last": 0.0})

    def _build_draw(self):
        c = self.canvas
        self.headline = self.text(WIDTH / 2, 108, "DEAD HEAT!", role="title",
                                  size=62, color=PALETTE["lav_deep"])
        ui.pop_text(c, self.clock, self.headline, 62, duration=0.6)
        self.text(WIDTH / 2, 166, "Perfectly matched.", size=20,
                  color=PALETTE["lav_deep"])
        self.text(WIDTH / 2, 198, "Nobody wins this clash — rematch?",
                  size=15, color=PALETTE["ink_soft"])
        self.cat_tag = "cat"
        self.cat_ids = sprites.draw_centered(c, "cat_happy", WIDTH / 2, 300, 8,
                                             tags=(self.cat_tag,))
        self.eye_ids = [i for i in self.cat_ids
                        if c.itemcget(i, "fill") == PALETTE["ink"]]
        self.fur_color = PALETTE["cream"]
        self.hearts = []

    def _build_defeat(self):
        c = self.canvas
        self.headline = self.text(WIDTH / 2, 108, "DEFEAT", role="title",
                                  size=64, color=PALETTE["lav_deep"])
        self.text(WIDTH / 2, 166, "Better luck next time...", size=20,
                  color=PALETTE["lav_deep"])
        self.text(WIDTH / 2, 198, "The computer got you this time!",
                  size=15, color=PALETTE["ink_soft"])

        self.cat_tag = "cat"
        self.cat_ids = sprites.draw_centered(c, "cat_sad", WIDTH / 2, 302, 8,
                                             tags=(self.cat_tag,))
        self.eye_ids = [i for i in self.cat_ids
                        if c.itemcget(i, "fill") == PALETTE["ink"]]
        self.fur_color = "#F2EEFA"
        self.hearts = []

        # entrance: fade the headline in, drop a broken heart, start the tears
        c.itemconfigure(self.headline, fill=PALETTE["bg_gloom"])
        self.clock.after(300, lambda: self._soft_pop())
        self.broken_ids = sprites.draw_centered(c, "heart_broken",
                                                WIDTH / 2 + 130, 190, 5,
                                                tags=("broken",))
        self._broken_last = 0.0
        self.clock.after(700, self._drop_broken_heart)
        self.clock.after(1200, self._start_tears)

    def _soft_pop(self):
        c = self.canvas
        c.itemconfigure(self.headline, fill=PALETTE["lav_deep"])
        ui.pop_text(c, self.clock, self.headline, 64, duration=0.5)

    def _drop_broken_heart(self):
        def apply(value):
            self.canvas.move("broken", 0, value - self._broken_last)
            self._broken_last = value

        self.clock.tween(0.9, apply, start=0, end=150, ease=ease_out_bounce)

    def _start_tears(self):
        c = self.canvas
        cx, cy = WIDTH / 2, 302

        def tear():
            if not self.alive:
                return
            for dx in (-46, 46):
                item = c.create_oval(cx + dx - 4, cy - 4, cx + dx + 4, cy + 6,
                                     fill=PALETTE["blue"], outline="",
                                     tags=("tear",))
                state = {"y": 0.0}

                def fall(value, it=item, st=state):
                    c.move(it, 0, value - st["y"])
                    st["y"] = value

                self.clock.tween(1.0, fall, start=0, end=110,
                                 ease=ease_out_cubic,
                                 on_done=lambda it=item: c.delete(it))
            self.clock.after(2200, tear)

        tear()

    # -------------------------------------------------------- score card --
    def _build_scorecard(self):
        c = self.canvas
        accent = PALETTE["pink"] if self.won else PALETTE["lav"]
        ui.panel_centered(c, WIDTH / 2, 494, 420, 150, fill=PALETTE["cream"],
                          border=accent, step=18, shadow=PALETTE["shadow"]
                          if self.won else PALETTE["shadow_cool"])
        self.text(WIDTH / 2, 444, "FINAL SCORE", size=17, color=PALETTE["ink"])
        self.text(WIDTH / 2 - 110, 496, "YOU", size=15,
                  color=PALETTE["pink_ink"])
        self.text(WIDTH / 2 + 110, 496, "COMPUTER", size=15,
                  color=PALETTE["blue_deep"])
        you = self.text(WIDTH / 2 - 110, 538, str(self.state.player_score),
                        role="title", size=40, color=PALETTE["pink_deep"])
        cpu = self.text(WIDTH / 2 + 110, 538, str(self.state.computer_score),
                        role="title", size=40, color=PALETTE["blue_deep"])
        self.text(WIDTH / 2, 528, "—", role="title", size=26,
                  color=PALETTE["ink_soft"])
        ui.pop_text(c, self.clock, you, 40, duration=0.5)
        ui.pop_text(c, self.clock, cpu, 40, duration=0.5)

    def _build_buttons(self):
        c = self.canvas
        again_text = "↻  PLAY AGAIN" if self.won or self.drew else "↻  TRY AGAIN"
        self.again_btn = ui.make_button(
            c, self.clock, WIDTH / 2 - 130, 652, 240, 68, again_text,
            self._again, font_size=18, fill=PALETTE["pink"],
            hover_fill=PALETTE["pink_soft"], border=PALETTE["pink_deep"],
            text_color=PALETTE["pink_ink"], lift=6)
        self.menu_btn = ui.make_button(
            c, self.clock, WIDTH / 2 + 130, 652, 240, 68, "⌂  MAIN MENU",
            self._menu, font_size=18, fill=PALETTE["lav_soft"],
            hover_fill=PALETTE["lav"], border=PALETTE["lav_deep"],
            text_color=PALETTE["lav_deep"], lift=6)

    # ---------------------------------------------------------- animation --
    def _animate_cat(self, dt):
        c = self.canvas
        self.bob_t += dt
        amplitude = 6 if self.won else 2.5
        speed = 3.2 if self.won else 1.4
        offset = abs(math.sin(self.bob_t * speed)) * -amplitude if self.won \
            else math.sin(self.bob_t * speed) * amplitude
        c.move(self.cat_tag, 0, offset - self._bob_last)
        self._bob_last = offset

        # blink roughly every three seconds
        self.blink_t += dt
        cycle = self.blink_t % 3.4
        closed = cycle > 3.25
        color = self.fur_color if closed else PALETTE["ink"]
        for eye in self.eye_ids:
            c.itemconfigure(eye, fill=color)

        for h in self.hearts:
            value = math.sin(self.bob_t * 1.4 + h["phase"]) * 7
            for i in h["ids"]:
                c.move(i, 0, value - h["last"])
            h["last"] = value

    # ------------------------------------------------------------ actions --
    def _again(self):
        from screens.rounds import RoundSelectScreen
        self.app.go(RoundSelectScreen)

    def _menu(self):
        from screens.welcome import WelcomeScreen
        self.app.go(WelcomeScreen, direction=-1)
