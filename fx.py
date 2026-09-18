"""Particle effects and the animated background layer."""
from __future__ import annotations

import math
import random

import sprites
from anim import clamp, mix
from config import CONFETTI_COLORS, HEIGHT, PALETTE, WIDTH


def star_points(cx, cy, r):
    k = r * 0.3
    return [cx, cy - r, cx + k, cy - k, cx + r, cy, cx + k, cy + k,
            cx, cy + r, cx - k, cy + k, cx - r, cy, cx - k, cy - k]


# --------------------------------------------------------------- sparkles ---
def sparkle_burst(canvas, clock, cx, cy, count=8, spread=46, color=None,
                  lifetime=0.75, tags="fx"):
    """A small puff of pixel sparkles that rise, shrink and vanish."""
    base = color or PALETTE["gold"]
    bg = canvas["background"]
    parts = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        dist = random.uniform(spread * 0.35, spread)
        x = cx + math.cos(angle) * dist * 0.9
        y = cy + math.sin(angle) * dist * 0.5
        r = random.uniform(3, 6)
        item = canvas.create_polygon(star_points(x, y, r), fill=base,
                                     outline="", tags=tags)
        parts.append({"id": item, "x": x, "y": y, "r": r,
                      "vy": random.uniform(-38, -14), "age": 0.0,
                      "life": lifetime * random.uniform(0.7, 1.2)})

    def update(dt):
        alive = False
        for p in parts:
            if p["id"] is None:
                continue
            p["age"] += dt
            t = p["age"] / p["life"]
            if t >= 1.0:
                canvas.delete(p["id"])
                p["id"] = None
                continue
            alive = True
            p["y"] += p["vy"] * dt
            r = p["r"] * (1.0 - t)
            canvas.coords(p["id"], *star_points(p["x"], p["y"], max(0.5, r)))
            canvas.itemconfigure(p["id"], fill=mix(base, bg, t * 0.85))
        if not alive:
            clock.unsubscribe(update)

    clock.subscribe(update)


# --------------------------------------------------------------- confetti ---
class Confetti:
    """Falling pastel confetti: rectangles that spin, plus stars and hearts."""

    def __init__(self, canvas, clock, count=70, duration=None, tags="confetti"):
        self.canvas = canvas
        self.clock = clock
        self.tags = tags
        self.pieces = []
        self.elapsed = 0.0
        self.duration = duration
        for i in range(count):
            self.pieces.append(self._make(delay=i * 0.035))
        clock.subscribe(self.update)

    def _make(self, delay=0.0):
        canvas = self.canvas
        kind = random.choices(("rect", "star", "heart"), weights=(6, 3, 2))[0]
        color = random.choice(CONFETTI_COLORS)
        x = random.uniform(20, WIDTH - 20)
        y = random.uniform(-260, -10)
        if kind == "star":
            item = canvas.create_polygon(star_points(x, y, 6), fill=color,
                                         outline="", tags=self.tags)
        elif kind == "heart":
            item = canvas.create_polygon(self._heart_points(x, y, 6), fill=color,
                                         outline="", tags=self.tags)
        else:
            item = canvas.create_polygon([x, y, x, y, x, y, x, y], fill=color,
                                         outline="", tags=self.tags)
        return {"id": item, "kind": kind, "x": x, "y": y,
                "w": random.uniform(6, 12), "h": random.uniform(8, 16),
                "vy": random.uniform(90, 210), "vx": random.uniform(-26, 26),
                "spin": random.uniform(-4.5, 4.5), "angle": random.uniform(0, math.tau),
                "sway": random.uniform(0.6, 1.8), "phase": random.uniform(0, math.tau),
                "delay": delay}

    @staticmethod
    def _heart_points(x, y, r):
        pts = []
        for i in range(12):
            a = math.tau * i / 12
            rr = r * (1.0 + 0.25 * math.sin(2 * a))
            pts += [x + math.cos(a) * rr, y + math.sin(a) * rr * 0.95 - r * 0.15]
        return pts

    def _rect_points(self, p):
        ca, sa = math.cos(p["angle"]), math.sin(p["angle"])
        hw, hh = p["w"] / 2, p["h"] / 2
        pts = []
        for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            pts += [p["x"] + dx * ca - dy * sa, p["y"] + dx * sa + dy * ca]
        return pts

    def update(self, dt):
        self.elapsed += dt
        for p in self.pieces:
            if p["delay"] > 0:
                p["delay"] -= dt
                continue
            p["y"] += p["vy"] * dt
            p["phase"] += dt * p["sway"] * 3
            p["x"] += (p["vx"] + math.sin(p["phase"]) * 26) * dt
            p["angle"] += p["spin"] * dt
            if p["y"] > HEIGHT + 30:
                if self.duration and self.elapsed > self.duration:
                    self.canvas.itemconfigure(p["id"], state="hidden")
                    continue
                p["y"] = random.uniform(-160, -20)
                p["x"] = random.uniform(20, WIDTH - 20)
            if p["kind"] == "rect":
                self.canvas.coords(p["id"], *self._rect_points(p))
            elif p["kind"] == "star":
                self.canvas.coords(p["id"], *star_points(p["x"], p["y"], 6))
            else:
                self.canvas.coords(p["id"], *self._heart_points(p["x"], p["y"], 6))

    def stop(self):
        self.clock.unsubscribe(self.update)
        self.canvas.delete(self.tags)


# ------------------------------------------------------------------- rain ---
class Rain:
    """Soft pastel-blue rain for the defeat screen."""

    def __init__(self, canvas, clock, count=48, tags="rain"):
        self.canvas = canvas
        self.clock = clock
        self.tags = tags
        self.drops = []
        for _ in range(count):
            x = random.uniform(0, WIDTH)
            y = random.uniform(-HEIGHT, HEIGHT)
            length = random.uniform(8, 18)
            item = canvas.create_line(x, y, x - 2, y + length,
                                      fill=random.choice([PALETTE["blue"],
                                                          PALETTE["blue_soft"],
                                                          PALETTE["lav_soft"]]),
                                      width=2, tags=tags)
            self.drops.append({"id": item, "x": x, "y": y, "len": length,
                               "v": random.uniform(210, 380)})
        clock.subscribe(self.update)

    def update(self, dt):
        for d in self.drops:
            d["y"] += d["v"] * dt
            d["x"] -= d["v"] * dt * 0.12
            if d["y"] > HEIGHT + 20:
                d["y"] = random.uniform(-160, -10)
                d["x"] = random.uniform(0, WIDTH + 80)
            self.canvas.coords(d["id"], d["x"], d["y"], d["x"] - 2, d["y"] + d["len"])

    def stop(self):
        self.clock.unsubscribe(self.update)
        self.canvas.delete(self.tags)


# ------------------------------------------------------------- background ---
class Background:
    """Twinkling stars, drifting clouds and slow floating hearts."""

    def __init__(self, canvas, clock, mood="day", stars=26, clouds=3, hearts=4):
        self.canvas = canvas
        self.clock = clock
        self.bg = PALETTE["bg_gloom"] if mood == "gloom" else PALETTE["bg"]
        canvas.configure(background=self.bg)
        self.time = 0.0

        band = PALETTE["bg_soft"] if mood != "gloom" else "#E6E2F5"
        canvas.create_oval(-220, HEIGHT - 260, WIDTH + 220, HEIGHT + 220,
                           fill=band, outline="", tags="bglayer")

        star_color = PALETTE["gold"] if mood != "gloom" else PALETTE["lav"]
        self.stars = []
        for _ in range(stars):
            x, y = random.uniform(16, WIDTH - 16), random.uniform(16, HEIGHT - 16)
            r = random.uniform(3, 6)
            item = canvas.create_polygon(star_points(x, y, r), fill=star_color,
                                         outline="", tags="bglayer")
            self.stars.append({"id": item, "phase": random.uniform(0, math.tau),
                               "speed": random.uniform(0.5, 1.4), "color": star_color})

        self.clouds = []
        for _ in range(clouds):
            x, y = random.uniform(0, WIDTH), random.uniform(40, HEIGHT * 0.55)
            scale = random.choice((3, 4, 5))
            ids = sprites.draw(canvas, "cloud", x, y, scale, tags="bglayer")
            self.clouds.append({"ids": ids, "x": x, "speed": random.uniform(4, 11),
                                "width": sprites.size_of("cloud", scale)[0]})

        self.hearts = []
        for _ in range(hearts):
            x, y = random.uniform(40, WIDTH - 40), random.uniform(80, HEIGHT - 80)
            ids = sprites.draw(canvas, "heart", x, y, 3, tags="bglayer",
                               palette_override={"#": PALETTE["pink_soft"]})
            self.hearts.append({"ids": ids, "phase": random.uniform(0, math.tau),
                                "amp": random.uniform(4, 10), "last": 0.0})

        canvas.tag_lower("bglayer")
        clock.subscribe(self.update)

    def update(self, dt):
        self.time += dt
        for s in self.stars:
            k = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self.time * s["speed"] * 2 + s["phase"]))
            self.canvas.itemconfigure(s["id"], fill=mix(self.bg, s["color"], clamp(k)))
        for c in self.clouds:
            dx = c["speed"] * dt
            c["x"] += dx
            for i in c["ids"]:
                self.canvas.move(i, dx, 0)
            if c["x"] > WIDTH + 10:
                shift = -(WIDTH + c["width"] + 20)
                c["x"] += shift
                for i in c["ids"]:
                    self.canvas.move(i, shift, 0)
        for h in self.hearts:
            offset = math.sin(self.time * 0.9 + h["phase"]) * h["amp"]
            dy = offset - h["last"]
            h["last"] = offset
            for i in h["ids"]:
                self.canvas.move(i, 0, dy)

    def stop(self):
        self.clock.unsubscribe(self.update)
