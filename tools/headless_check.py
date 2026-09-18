"""Run the whole game without a display.

Stubs out tkinter's Canvas with a recording fake and drives the animation
clock with a virtual timeline, so every screen builds, every tween runs and a
full match is played. Useful in CI or over SSH:

    python tools/headless_check.py
"""
from __future__ import annotations

import heapq
import itertools
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ------------------------------------------------------------ fake tkinter --
class TclError(Exception):
    pass


class FakeTime:
    def __init__(self):
        self.now = 0.0

    def perf_counter(self):
        return self.now


CLOCK = FakeTime()
TIMERS = []          # heap of (due, seq, fn, token)
CANCELLED = set()
_seq = itertools.count()


class FakeCanvas:
    def __init__(self, master=None, **kw):
        self.opts = dict(kw)
        self.items = {}
        self.tags = {}
        self._ids = itertools.count(1)
        self.destroyed = False

    # -- item creation
    def _create(self, kind, coords, kw):
        item_id = next(self._ids)
        tags = kw.pop("tags", ())
        if isinstance(tags, str):
            tags = (tags,)
        self.items[item_id] = {"kind": kind, "coords": list(coords),
                               "opts": dict(kw), "tags": set(tags),
                               "state": "normal"}
        for t in tags:
            self.tags.setdefault(t, set()).add(item_id)
        return item_id

    def create_rectangle(self, *c, **kw): return self._create("rect", c, kw)
    def create_oval(self, *c, **kw): return self._create("oval", c, kw)
    def create_line(self, *c, **kw): return self._create("line", c, kw)
    def create_text(self, *c, **kw): return self._create("text", c, kw)
    def create_image(self, *c, **kw): return self._create("image", c, kw)

    def create_polygon(self, *c, **kw):
        coords = c[0] if len(c) == 1 and isinstance(c[0], (list, tuple)) else c
        return self._create("poly", coords, kw)

    # -- lookups
    def _resolve(self, spec):
        if isinstance(spec, int):
            return [spec] if spec in self.items else []
        return sorted(self.tags.get(spec, ()))

    def coords(self, spec, *args):
        ids = self._resolve(spec)
        if not args:
            return self.items[ids[0]]["coords"] if ids else []
        values = args[0] if len(args) == 1 and isinstance(args[0], (list, tuple)) else args
        for i in ids:
            self.items[i]["coords"] = list(values)

    def move(self, spec, dx, dy):
        for i in self._resolve(spec):
            c = self.items[i]["coords"]
            self.items[i]["coords"] = [v + (dx if n % 2 == 0 else dy)
                                       for n, v in enumerate(c)]

    def scale(self, spec, ox, oy, fx, fy):
        for i in self._resolve(spec):
            c = self.items[i]["coords"]
            self.items[i]["coords"] = [
                ox + (v - ox) * fx if n % 2 == 0 else oy + (v - oy) * fy
                for n, v in enumerate(c)]

    def delete(self, spec):
        for i in self._resolve(spec):
            item = self.items.pop(i, None)
            if item:
                for t in item["tags"]:
                    self.tags.get(t, set()).discard(i)

    def itemconfigure(self, spec, **kw):
        for i in self._resolve(spec):
            if "state" in kw:
                self.items[i]["state"] = kw["state"]
            self.items[i]["opts"].update(kw)

    itemconfig = itemconfigure

    def itemcget(self, spec, key):
        ids = self._resolve(spec)
        return self.items[ids[0]]["opts"].get(key, "") if ids else ""

    def addtag_withtag(self, newtag, spec):
        for i in self._resolve(spec):
            self.items[i]["tags"].add(newtag)
            self.tags.setdefault(newtag, set()).add(i)

    def tag_bind(self, tag, event, fn): pass
    def tag_lower(self, *a): pass
    def tag_raise(self, *a): pass
    def configure(self, **kw): self.opts.update(kw)
    config = configure

    def __getitem__(self, key): return self.opts.get(key, "#FFFFFF")
    def winfo_exists(self): return not self.destroyed
    def place(self, **kw): pass
    def place_configure(self, **kw): pass
    def destroy(self): self.destroyed = True

    # -- timers
    def after(self, ms, fn=None):
        token = f"t{next(_seq)}"
        heapq.heappush(TIMERS, (CLOCK.now + ms / 1000.0, next(_seq), fn, token))
        return token

    def after_cancel(self, token):
        CANCELLED.add(token)


fake_tk = types.ModuleType("tkinter")
fake_tk.Canvas = FakeCanvas
fake_tk.TclError = TclError
fake_font = types.ModuleType("tkinter.font")
fake_font.families = lambda root=None: ("Consolas", "Courier New")
fake_tk.font = fake_font
sys.modules.setdefault("tkinter", fake_tk)
sys.modules.setdefault("tkinter.font", fake_font)

import anim  # noqa: E402
anim.time = CLOCK

import assets  # noqa: E402
assets._resolved = {"title": "Consolas", "pixel": "Consolas"}
assets.image = lambda name, height: None  # always use the built-in sprites

from screens.gameplay import GameplayScreen  # noqa: E402
from screens.results import ResultsScreen  # noqa: E402
from screens.rounds import RoundSelectScreen  # noqa: E402
from screens.welcome import WelcomeScreen  # noqa: E402


# ----------------------------------------------------------------- driver --
class FakeApp:
    def __init__(self):
        self.container = None
        self.transitions = []

    def go(self, screen_class, direction=1, **kwargs):
        self.transitions.append((screen_class.__name__, kwargs))


def pump(seconds, step=1 / 60):
    """Advance the virtual clock, firing due timers."""
    end = CLOCK.now + seconds
    while CLOCK.now < end:
        CLOCK.now = round(CLOCK.now + step, 6)
        while TIMERS and TIMERS[0][0] <= CLOCK.now:
            _due, _n, fn, token = heapq.heappop(TIMERS)
            if token in CANCELLED or fn is None:
                continue
            fn()


def pump_until(predicate, limit=15.0, step=1 / 60):
    """Advance until predicate() is true (or give up after `limit` seconds)."""
    spent = 0.0
    while spent < limit:
        pump(step, step)
        spent += step
        if predicate():
            return True
    return False


def run_screen(screen_class, seconds=3.0, **kwargs):
    app = FakeApp()
    screen = screen_class(app, **kwargs)
    screen.build()
    screen.start()
    screen.on_enter()
    pump(seconds)
    return app, screen


def main():
    checks = []

    app, welcome = run_screen(WelcomeScreen, 2.0)
    welcome.start_btn._on_enter()
    pump(0.5)
    welcome.start_btn._on_release()
    pump(0.5)
    checks.append(("welcome -> rounds", app.transitions[:1] ==
                   [("RoundSelectScreen", {})]))
    welcome.destroy()

    app, rounds = run_screen(RoundSelectScreen, 1.5)
    rounds._select(7)
    pump(0.6)
    rounds.begin_btn._on_release()
    pump(0.5)
    checks.append(("rounds -> gameplay with 7",
                   app.transitions[:1] == [("GameplayScreen", {"rounds": 7})]))
    rounds.destroy()

    app, play = run_screen(GameplayScreen, 0.1, rounds=3)
    moves = ("rock", "paper", "scissors")
    for i in range(3):
        got_cards = pump_until(lambda: play.phase == "choose")
        checks.append((f"round {i + 1} cards appear", got_cards))
        play.cards[moves[i]]._on_release()
        pump_until(lambda: play.phase == "result" or app.transitions)
        if play.next_btn is not None:   # click through instead of auto-advancing
            pump(0.8)
            play.next_btn._on_release()
    pump_until(lambda: bool(app.transitions), limit=6.0)
    checks.append(("3 rounds played", play.state.round_no == 3))
    checks.append(("gameplay -> results",
                   bool(app.transitions) and
                   app.transitions[-1][0] == "ResultsScreen"))
    final_state = app.transitions[-1][1]["state"]
    play.destroy()

    for label, forced in (("victory", "win"), ("defeat", "lose"), ("draw", "tie")):
        from game import GameState
        st = GameState(rounds=3)
        st.player_score, st.computer_score = {
            "win": (3, 0), "lose": (0, 3), "tie": (1, 1)}[forced]
        app2, res = run_screen(ResultsScreen, 4.0, state=st)
        checks.append((f"results {label}", len(res.canvas.items) > 50))
        res._again()
        pump(0.3)
        checks.append((f"results {label} -> rounds",
                       app2.transitions[-1][0] == "RoundSelectScreen"))
        res.destroy()

    width = max(len(name) for name, _ in checks)
    ok = True
    for name, passed in checks:
        ok &= bool(passed)
        print(f"  {name.ljust(width)}  {'PASS' if passed else 'FAIL'}")
    print("\nfinal score of the simulated match:",
          final_state.player_score, "-", final_state.computer_score)
    print("ALL GOOD" if ok else "SOMETHING FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
