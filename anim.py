"""A tiny tween/scheduler engine on top of Tk's `after` loop.

Nothing here ever calls time.sleep(): every animation is driven from one
per-screen Clock so the UI stays responsive and a screen can cancel all of its
pending work in one call when it is destroyed.
"""
from __future__ import annotations

import math
import time
import tkinter as tk

from config import FRAME_MS


# ----------------------------------------------------------------- easing ---
def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def linear(t):
    return t


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    return t ** 3


def ease_in_out(t):
    return 4 * t ** 3 if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2


def ease_out_back(t, s=1.9):
    u = t - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2


def ease_out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- colours ---
def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(color_a, color_b, t):
    t = clamp(t)
    a, b = hex_to_rgb(color_a), hex_to_rgb(color_b)
    return rgb_to_hex(tuple(lerp(a[i], b[i], t) for i in range(3)))


def lighten(color, amount=0.3):
    return mix(color, "#FFFFFF", amount)


def darken(color, amount=0.2):
    return mix(color, "#000000", amount)


# ------------------------------------------------------------------ tween ---
class Tween:
    def __init__(self, duration, on_update, start=0.0, end=1.0,
                 ease=ease_out_cubic, delay=0.0, on_done=None):
        self.duration = max(0.0001, duration)
        self.on_update = on_update
        self.start, self.end = start, end
        self.ease = ease
        self.delay = delay
        self.on_done = on_done
        self.elapsed = 0.0
        self.dead = False

    def update(self, dt):
        if self.dead:
            return True
        if self.delay > 0:
            self.delay -= dt
            if self.delay > 0:
                return False
            dt = -self.delay
        self.elapsed += dt
        t = clamp(self.elapsed / self.duration)
        try:
            self.on_update(lerp(self.start, self.end, self.ease(t)))
        except tk.TclError:
            self.dead = True
            return True
        if t >= 1.0:
            if self.on_done:
                try:
                    self.on_done()
                except tk.TclError:
                    pass
            return True
        return False


# ------------------------------------------------------------------ clock ---
class Clock:
    """Per-screen frame loop, tween list and cancellable timer registry."""

    def __init__(self, widget, interval=FRAME_MS):
        self.widget = widget
        self.interval = interval
        self._tweens: list[Tween] = []
        self._subs: list = []
        self._timers: set[str] = set()
        self._loop_id = None
        self._running = False
        self._last = 0.0

    # -- lifecycle
    def start(self):
        if self._running:
            return
        self._running = True
        self._last = time.perf_counter()
        self._tick()

    def stop(self):
        self._running = False
        for token in (self._loop_id, *self._timers):
            if token:
                try:
                    self.widget.after_cancel(token)
                except Exception:
                    pass
        self._loop_id = None
        self._timers.clear()
        self._tweens.clear()
        self._subs.clear()

    def _tick(self):
        if not self._running:
            return
        now = time.perf_counter()
        dt = min(now - self._last, 0.05)
        self._last = now

        for tw in list(self._tweens):
            if tw.update(dt):
                if tw in self._tweens:
                    self._tweens.remove(tw)
        for fn in list(self._subs):
            try:
                fn(dt)
            except tk.TclError:
                self.unsubscribe(fn)
        try:
            self._loop_id = self.widget.after(self.interval, self._tick)
        except tk.TclError:
            self._running = False

    # -- api
    def tween(self, duration, on_update, start=0.0, end=1.0,
              ease=ease_out_cubic, delay=0.0, on_done=None):
        tw = Tween(duration, on_update, start, end, ease, delay, on_done)
        self._tweens.append(tw)
        return tw

    def cancel(self, tween):
        if tween in self._tweens:
            tween.dead = True
            self._tweens.remove(tween)

    def subscribe(self, fn):
        if fn not in self._subs:
            self._subs.append(fn)
        return fn

    def unsubscribe(self, fn):
        if fn in self._subs:
            self._subs.remove(fn)

    def after(self, ms, fn):
        """Like widget.after, but cancelled automatically when the clock stops."""
        token = {}

        def run():
            self._timers.discard(token.get("id"))
            if not self._running:
                return
            try:
                fn()
            except tk.TclError:
                pass

        try:
            token["id"] = self.widget.after(ms, run)
        except tk.TclError:
            return None
        self._timers.add(token["id"])
        return token["id"]

    def sequence(self, steps):
        """steps: iterable of (delay_ms_from_now, callable)."""
        for delay, fn in steps:
            self.after(delay, fn)


def wobble(t, cycles=2, amount=1.0):
    """Handy decaying sine for idle animations."""
    return math.sin(t * math.tau * cycles) * amount
