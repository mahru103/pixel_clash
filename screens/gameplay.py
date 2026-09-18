"""Screen 3: the match itself."""
from __future__ import annotations

import math

import audio
import fx
import ui
from anim import ease_out_back
from config import PALETTE, WIDTH
from game import LOSE, TIE, WIN, GameState
from screens.base import Screen

CARD_W, CARD_H, CARD_Y = 178, 222, 432
CARD_X = (196, 400, 604)
SCORE_SIZE = 34


class GameplayScreen(Screen):
    """Round flow:

    intro (ROUND n -> READY? -> 3 2 1 -> CHOOSE!) -> pick -> computer thinks
    -> reveal -> result -> next round or results screen.
    """

    def __init__(self, app, rounds=5):
        super().__init__(app)
        self.state = GameState(rounds=rounds)
        self.cards = {}
        self.next_btn = None
        self.phase = "intro"
        self.t = 0.0

    # ------------------------------------------------------------ build --
    def build(self):
        c = self.canvas
        self.bg = fx.Background(c, self.clock, stars=18, clouds=2, hearts=2)

        self.round_label = self.text(WIDTH / 2, 44, "", size=20,
                                     color=PALETTE["ink"])

        ui.panel_centered(c, WIDTH / 2, 124, 540, 104, fill=PALETTE["cream"],
                          border=PALETTE["pink_soft"], step=14,
                          shadow=PALETTE["shadow"])
        self.text(WIDTH / 2 - 160, 100, "YOU", size=16, color=PALETTE["pink_ink"])
        self.text(WIDTH / 2 + 160, 100, "COMPUTER", size=16,
                  color=PALETTE["blue_deep"])
        self.vs_label = self.text(WIDTH / 2, 124, "VS", role="title", size=26,
                                  color=PALETTE["lav_deep"])
        self.you_score = self.text(WIDTH / 2 - 160, 146, "0", role="title",
                                   size=SCORE_SIZE, color=PALETTE["pink_deep"])
        self.cpu_score = self.text(WIDTH / 2 + 160, 146, "0", role="title",
                                   size=SCORE_SIZE, color=PALETTE["blue_deep"])

        self.center_label = self.text(WIDTH / 2, 380, "", role="title", size=56,
                                      color=PALETTE["pink_deep"])
        self.status_label = self.text(WIDTH / 2, 626, "", size=16,
                                      color=PALETTE["ink_soft"])

        self.clock.subscribe(self._ambient)

    def on_enter(self):
        self.start_round()

    def _ambient(self, dt):
        """Sparkle behind the VS label."""
        self.t += dt
        if int(self.t * 1.2) != int((self.t - dt) * 1.2):
            fx.sparkle_burst(self.canvas, self.clock, WIDTH / 2, 124, count=3,
                             spread=26, color=PALETTE["lav"], lifetime=0.6)

    # ------------------------------------------------------- round intro --
    def start_round(self):
        self.phase = "intro"
        self.canvas.delete("stage")
        self.cards = {}
        self.next_btn = None
        self.state.start_round()
        self.canvas.itemconfigure(
            self.round_label,
            text=f"ROUND {self.state.round_no} / {self.state.rounds}")
        self.canvas.itemconfigure(self.status_label, text="Get ready...")
        audio.play("round_start")

        self.clock.sequence([
            (0,    lambda: self._flash(f"ROUND {self.state.round_no}", 54)),
            (700,  lambda: self._flash("READY?", 48, PALETTE["lav_deep"])),
            (1350, lambda: self._countdown_flash("3", 72)),
            (1850, lambda: self._countdown_flash("2", 72)),
            (2350, lambda: self._countdown_flash("1", 72)),
            (2850, lambda: self._countdown_flash(
                "CHOOSE!", 56, PALETTE["pink_deep"], sound="go")),
            (3350, self.show_cards),
        ])

    def _flash(self, text, size, color=None):
        c = self.canvas
        c.itemconfigure(self.center_label, text=text,
                        fill=color or PALETTE["pink_deep"])
        ui.pop_text(c, self.clock, self.center_label, size, duration=0.34)
        fx.sparkle_burst(c, self.clock, WIDTH / 2, 380, count=6, spread=90,
                         color=PALETTE["gold"])

    def _countdown_flash(self, text, size, color=None, sound="count"):
        audio.play(sound)
        self._flash(text, size, color)

    # -------------------------------------------------------- pick phase --
    def show_cards(self):
        self.phase = "choose"
        c = self.canvas
        c.itemconfigure(self.center_label, text="")
        c.itemconfigure(self.status_label, text="Pick a move — good luck!")
        self.prompt = self.text(WIDTH / 2, 268, "CHOOSE YOUR MOVE", size=22,
                                color=PALETTE["ink"], tags=("stage",))
        ui.pop_text(c, self.clock, self.prompt, 22, role="pixel")

        palettes = {
            "rock":     (PALETTE["lav_soft"], PALETTE["lav"]),
            "paper":    (PALETTE["cream"], PALETTE["pink_soft"]),
            "scissors": (PALETTE["pink_pale"], PALETTE["pink"]),
        }
        for name, x in zip(("rock", "paper", "scissors"), CARD_X):
            fill, border = palettes[name]
            btn = ui.PixelButton(
                c, self.clock, x, CARD_Y, CARD_W, CARD_H, name.upper(),
                command=lambda n=name: self.on_choice(n),
                icon=name, icon_height=96, fill=fill, border=border,
                text_color=PALETTE["ink"], font_size=20, step=16, lift=8,
                hover_scale=1.07, shadow=PALETTE["shadow"])
            # cards live under the "stage" tag so a round reset clears them
            c.addtag_withtag("stage", btn.tag)
            self.cards[name] = btn
            btn._move_to(40)
            self.clock.tween(0.35, btn._move_to, start=40, end=0,
                             ease=ease_out_back,
                             delay=0.06 * CARD_X.index(x))

    def on_choice(self, name):
        if self.phase != "choose":
            return
        self.phase = "thinking"
        audio.play("choose")
        for move, btn in self.cards.items():
            btn.set_enabled(False)
            if move != name:
                btn.fade_out(0.3)
        chosen = self.cards[name]
        self.clock.tween(0.18, chosen._scale_to, start=chosen._scale, end=1.14,
                         ease=ease_out_back)
        fx.sparkle_burst(self.canvas, self.clock, chosen.cx, CARD_Y, count=16,
                         spread=120, color=PALETTE["pink_deep"])
        self.clock.after(520, lambda: self.computer_thinks(name))

    # ---------------------------------------------------- computer turn ---
    def computer_thinks(self, player_choice):
        c = self.canvas
        c.delete("stage")
        self.cards = {}

        c.itemconfigure(self.status_label, text="")
        self.think_label = self.text(WIDTH / 2, 300, "COMPUTER IS THINKING",
                                     size=22, color=PALETTE["blue_deep"],
                                     tags=("stage",))
        self.dots_label = self.text(WIDTH / 2, 342, "", role="title", size=30,
                                    color=PALETTE["blue_deep"], tags=("stage",))
        ui.draw_icon(c, "robot", WIDTH / 2, 448, 108, tags=("stage", "robot"))

        self._think_t = 0.0

        def animate(dt):
            self._think_t += dt
            dots = "." * (1 + int(self._think_t * 4) % 3)
            c.itemconfigure(self.dots_label, text=dots)
        self._think_anim = self.clock.subscribe(animate)

        self._bob = 0.0

        def bob(dt):
            offset = math.sin(self._think_t * 6) * 4
            c.move("robot", 0, offset - self._bob)
            self._bob = offset
        self._bob_anim = self.clock.subscribe(bob)

        self.clock.after(1400, lambda: self.reveal(player_choice))

    # ---------------------------------------------------------- reveal ----
    def reveal(self, player_choice):
        self.clock.unsubscribe(self._think_anim)
        self.clock.unsubscribe(self._bob_anim)
        c = self.canvas
        c.delete("stage")

        outcome = self.state.play(player_choice)
        audio.play("reveal")
        cpu_choice = self.state.computer_choice

        self.text(230, 268, "YOU", size=18, color=PALETTE["pink_ink"],
                  tags=("stage",))
        self.text(570, 268, "COMPUTER", size=18, color=PALETTE["blue_deep"],
                  tags=("stage",))
        vs = self.text(WIDTH / 2, 350, "VS", role="title", size=34,
                       color=PALETTE["lav_deep"], tags=("stage",))
        ui.pop_text(c, self.clock, vs, 34, duration=0.5)

        ui.draw_icon(c, player_choice, 230, 350, 120, tags=("stage", "youpick"))
        ui.draw_icon(c, cpu_choice, 570, 350, 120, tags=("stage", "cpupick"))
        self.text(230, 440, player_choice.upper(), size=18,
                  color=PALETTE["ink"], tags=("stage",))
        self.text(570, 440, cpu_choice.upper(), size=18,
                  color=PALETTE["ink"], tags=("stage",))

        self._slide("youpick", -160)
        self._slide("cpupick", 160)

        self.clock.after(700, lambda: self.show_result(outcome))

    def _slide(self, tag, dx):
        state = {"last": dx}
        self.canvas.move(tag, dx, 0)

        def apply(value):
            self.canvas.move(tag, value - state["last"], 0)
            state["last"] = value

        self.clock.tween(0.45, apply, start=dx, end=0.0, ease=ease_out_back)

    # ---------------------------------------------------------- result ----
    def show_result(self, outcome):
        c = self.canvas
        audio.play({WIN: "win", LOSE: "lose", TIE: "tie"}[outcome])
        if outcome == WIN:
            text, color = "YOU WIN!", PALETTE["pink_deep"]
            self.canvas.itemconfigure(self.you_score, text=str(self.state.player_score))
            ui.bump_text(c, self.clock, self.you_score, SCORE_SIZE, role="title")
            fx.sparkle_burst(c, self.clock, WIDTH / 2 - 160, 146, count=14,
                             spread=70, color=PALETTE["pink"])
            sub = "Nice one!"
        elif outcome == LOSE:
            text, color = "COMPUTER WINS", PALETTE["lav_deep"]
            self.canvas.itemconfigure(self.cpu_score, text=str(self.state.computer_score))
            ui.bump_text(c, self.clock, self.cpu_score, SCORE_SIZE, role="title")
            sub = "Shake it off."
        else:
            text, color = "IT'S A TIE!", PALETTE["blue_deep"]
            sub = "Nobody scores this round."

        self.result_label = self.text(WIDTH / 2, 530, text, role="title",
                                      size=46, color=color, tags=("stage",))
        ui.pop_text(c, self.clock, self.result_label, 46, duration=0.45)
        c.itemconfigure(self.status_label, text=sub)

        if outcome == WIN:
            fx.sparkle_burst(c, self.clock, WIDTH / 2, 530, count=18,
                             spread=200, color=PALETTE["gold"])
        elif outcome == TIE:
            fx.sparkle_burst(c, self.clock, WIDTH / 2, 530, count=10,
                             spread=160, color=PALETTE["lav"])

        self.phase = "result"
        if self.state.finished:
            self.clock.after(1500, self._finish)
        else:
            self.clock.after(700, self._show_next_button)
            self.clock.after(4200, self._auto_advance)

    def _show_next_button(self):
        if self.phase != "result":
            return
        self.next_btn = ui.make_button(
            self.canvas, self.clock, WIDTH / 2, 672, 260, 62, "NEXT ROUND  →",
            self._advance, font_size=18, fill=PALETTE["pink_soft"],
            hover_fill=PALETTE["pink"], border=PALETTE["pink_deep"],
            text_color=PALETTE["pink_ink"], lift=5, hover_scale=1.04)
        self.canvas.addtag_withtag("stage", self.next_btn.tag)
        self.next_btn.pulse()

    def _auto_advance(self):
        if self.phase == "result":
            self._advance()

    def _advance(self):
        if self.phase != "result":
            return
        self.phase = "intro"
        self.start_round()

    def _finish(self):
        from screens.results import ResultsScreen
        self.app.go(ResultsScreen, state=self.state)
