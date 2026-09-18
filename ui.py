"""Canvas-drawn UI pieces.

Everything is drawn on a tk.Canvas rather than built from CustomTkinter
widgets: that is what makes per-pixel hover lifts, scaling, sparkles and
sprite icons possible. CustomTkinter still owns the window and frames.
"""
from __future__ import annotations

import itertools

import assets
import audio
import fx
import sprites
from anim import ease_out_back, ease_out_cubic, lighten, mix
from config import PALETTE

_uid = itertools.count(1)


def new_tag(prefix="w"):
    return f"{prefix}{next(_uid)}"


# ----------------------------------------------------------------- panels ---
def _stepped(canvas, x, y, w, h, color, step, tags):
    """A rectangle with chunky pixel-style stepped corners."""
    return [
        canvas.create_rectangle(x + step, y, x + w - step, y + h,
                                fill=color, outline="", tags=tags),
        canvas.create_rectangle(x, y + step, x + w, y + h - step,
                                fill=color, outline="", tags=tags),
    ]


def pixel_panel(canvas, x, y, w, h, fill, border=None, step=10, tags=(),
                shadow=None, shadow_offset=6, border_width=3):
    ids = []
    if shadow:
        ids += _stepped(canvas, x + shadow_offset, y + shadow_offset, w, h,
                        shadow, step, tags)
    if border:
        ids += _stepped(canvas, x - border_width, y - border_width,
                        w + border_width * 2, h + border_width * 2,
                        border, step + border_width, tags)
    ids += _stepped(canvas, x, y, w, h, fill, step, tags)
    return ids


def panel_centered(canvas, cx, cy, w, h, **kwargs):
    return pixel_panel(canvas, cx - w / 2, cy - h / 2, w, h, **kwargs)


def draw_icon(canvas, name, cx, cy, height, tags=(), scale_hint=None):
    """Use assets/images/<name>.png if present, else the built-in sprite."""
    photo = assets.image(name, height)
    if photo is not None:
        return [canvas.create_image(cx, cy, image=photo, tags=tags)]
    grid, _ = sprites.SPRITES[name]
    scale = scale_hint or max(1, round(height / len(grid)))
    return sprites.draw_centered(canvas, name, cx, cy, scale, tags=tags)


# ------------------------------------------------------------- text helper --
def pop_text(canvas, clock, item, base_size, role="title", duration=0.42,
             overshoot=True, family_weight="normal"):
    """Scale a canvas text item up with a bouncy pop (font-size tween)."""
    ease = ease_out_back if overshoot else ease_out_cubic

    def apply(value):
        canvas.itemconfigure(item, font=assets.font(role, max(1, int(value)),
                                                    family_weight))

    clock.tween(duration, apply, start=max(1, int(base_size * 0.35)),
                end=base_size, ease=ease)


def bump_text(canvas, clock, item, base_size, role="pixel", amount=1.45):
    """Quick grow-and-settle, used for score increments."""
    def apply(value):
        canvas.itemconfigure(item, font=assets.font(role, max(1, int(value))))

    clock.tween(0.14, apply, start=base_size, end=int(base_size * amount),
                ease=ease_out_cubic,
                on_done=lambda: clock.tween(0.26, apply,
                                            start=int(base_size * amount),
                                            end=base_size, ease=ease_out_back))


# ---------------------------------------------------------------- buttons ---
class PixelButton:
    """A canvas button with hover lift, colour blend, sparkles and a press dip.

    Works for plain buttons and for the big rock/paper/scissors choice cards
    (pass `icon=` and a taller height).
    """

    def __init__(self, canvas, clock, cx, cy, w, h, text, command=None, *,
                 icon=None, icon_height=76, sub=None,
                 fill=None, hover_fill=None, border=None, text_color=None,
                 font_role="pixel", font_size=20, shadow=None, sparkles=True,
                 step=12, lift=6, hover_scale=1.05, selected=False,
                 selected_fill=None, sound="click"):
        self.canvas = canvas
        self.clock = clock
        self.cx, self.cy, self.w, self.h = cx, cy, w, h
        self.command = command
        self.tag = new_tag("btn")
        self.body_tag = f"{self.tag}-body"
        self.enabled = True
        self.sparkles = sparkles
        self.lift = lift
        self.hover_scale = hover_scale
        self.selected = selected
        self.sound = sound
        self._offset = 0.0
        self._scale = 1.0
        self._hovering = False
        self._lift_tween = None
        self._scale_tween = None
        self._color_tween = None

        self.fill = fill or PALETTE["pink"]
        self.hover_fill = hover_fill or lighten(self.fill, 0.35)
        self.border = border or PALETTE["pink_deep"]
        self.text_color = text_color or PALETTE["pink_ink"]
        self.shadow = shadow if shadow is not None else PALETTE["shadow"]
        self.font_role = font_role
        self.font_size = font_size
        self.fill_current = self.fill
        self.selected_fill = selected_fill or lighten(self.fill, 0.18)

        x, y = cx - w / 2, cy - h / 2
        self.shadow_ids = []
        if self.shadow:
            self.shadow_ids = _stepped(canvas, x + 6, y + 6, w, h, self.shadow,
                                       step, (self.tag,))
        self.border_ids = _stepped(canvas, x - 3, y - 3, w + 6, h + 6,
                                   self.border, step + 3, (self.tag,))
        self.body_ids = _stepped(canvas, x, y, w, h, self.fill, step,
                                 (self.tag, self.body_tag))

        text_y = cy
        self.icon_ids = []
        if icon:
            icon_cy = cy - h / 2 + icon_height / 2 + 24
            self.icon_ids = draw_icon(canvas, icon, cx, icon_cy, icon_height,
                                      tags=(self.tag,))
            text_y = cy + h / 2 - 32

        self.text_id = canvas.create_text(
            cx, text_y - (12 if sub else 0), text=text,
            font=assets.font(font_role, font_size, "bold"),
            fill=self.text_color, tags=(self.tag,))
        self.sub_id = None
        if sub:
            self.sub_id = canvas.create_text(
                cx, text_y + 14, text=sub,
                font=assets.font("pixel", max(10, font_size - 8)),
                fill=PALETTE["ink_soft"], tags=(self.tag,))

        canvas.tag_bind(self.tag, "<Enter>", self._on_enter)
        canvas.tag_bind(self.tag, "<Leave>", self._on_leave)
        canvas.tag_bind(self.tag, "<Button-1>", self._on_press)
        canvas.tag_bind(self.tag, "<ButtonRelease-1>", self._on_release)

        if selected:
            self.set_selected(True, animate=False)

    # -- internals -------------------------------------------------------
    @property
    def _center(self):
        return self.cx, self.cy + self._offset

    def _move_to(self, offset):
        dy = offset - self._offset
        self._offset = offset
        self.canvas.move(self.tag, 0, dy)

    def _scale_to(self, scale):
        if self._scale == 0:
            return
        factor = scale / self._scale
        self._scale = scale
        cx, cy = self._center
        self.canvas.scale(self.tag, cx, cy, factor, factor)

    def _tint(self, color):
        for i in self.body_ids:
            self.canvas.itemconfigure(i, fill=color)

    def _animate_fill(self, target):
        start = self.fill_current
        if self._color_tween:
            self.clock.cancel(self._color_tween)

        def apply(t):
            self.fill_current = mix(start, target, t)
            self._tint(self.fill_current)

        self._color_tween = self.clock.tween(0.18, apply, ease=ease_out_cubic)

    # -- events ----------------------------------------------------------
    def _on_enter(self, _event=None):
        if not self.enabled or self._hovering:
            return
        self._hovering = True
        self.canvas.configure(cursor="hand2")
        if self.sound:
            audio.play("hover")
        if self._lift_tween:
            self.clock.cancel(self._lift_tween)
        self._lift_tween = self.clock.tween(0.18, self._move_to,
                                            start=self._offset, end=-self.lift)
        if self.hover_scale != 1.0:
            if self._scale_tween:
                self.clock.cancel(self._scale_tween)
            self._scale_tween = self.clock.tween(0.2, self._scale_to,
                                                 start=self._scale,
                                                 end=self.hover_scale,
                                                 ease=ease_out_back)
        self._animate_fill(self.hover_fill)
        if self.sparkles:
            cx, cy = self._center
            fx.sparkle_burst(self.canvas, self.clock, cx, cy,
                             count=7, spread=self.w * 0.55,
                             color=PALETTE["gold"])

    def _on_leave(self, _event=None):
        if not self._hovering:
            return
        self._hovering = False
        self.canvas.configure(cursor="")
        if self._lift_tween:
            self.clock.cancel(self._lift_tween)
        target = -3 if self.selected else 0
        self._lift_tween = self.clock.tween(0.22, self._move_to,
                                            start=self._offset, end=target)
        if self.hover_scale != 1.0:
            if self._scale_tween:
                self.clock.cancel(self._scale_tween)
            end = 1.04 if self.selected else 1.0
            self._scale_tween = self.clock.tween(0.22, self._scale_to,
                                                 start=self._scale, end=end)
        self._animate_fill(self.selected_fill if self.selected else self.fill)

    def _on_press(self, _event=None):
        if not self.enabled:
            return
        if self._lift_tween:
            self.clock.cancel(self._lift_tween)
        self._lift_tween = self.clock.tween(0.08, self._move_to,
                                            start=self._offset, end=3)

    def _on_release(self, _event=None):
        if not self.enabled:
            return
        if self._lift_tween:
            self.clock.cancel(self._lift_tween)
        target = -self.lift if self._hovering else 0
        self._lift_tween = self.clock.tween(0.14, self._move_to,
                                            start=self._offset, end=target,
                                            ease=ease_out_back)
        cx, cy = self._center
        fx.sparkle_burst(self.canvas, self.clock, cx, cy, count=12,
                         spread=self.w * 0.6, color=PALETTE["white"])
        if self.sound:
            audio.play(self.sound)
        if self.command:
            self.clock.after(90, self.command)

    # -- public ----------------------------------------------------------
    def set_enabled(self, value):
        self.enabled = value
        if value:
            self._tint(self.fill)
            self.fill_current = self.fill
        else:
            self._hovering = False
            self.canvas.configure(cursor="")
            self._tint(mix(self.fill, PALETTE["gray"], 0.55))
            for i in (self.text_id,):
                self.canvas.itemconfigure(i, fill=PALETTE["ink_soft"])

    def set_text(self, value):
        """Update the button label without rebuilding its canvas items."""
        self.canvas.itemconfigure(self.text_id, text=value)

    def set_selected(self, value, animate=True):
        self.selected = value
        target_fill = self.selected_fill if value else self.fill
        if animate:
            self._animate_fill(target_fill)
        else:
            self.fill_current = target_fill
            self._tint(target_fill)
        for i in self.border_ids:
            self.canvas.itemconfigure(
                i, fill=PALETTE["pink_deep"] if value else self.border)
        if not self._hovering:
            if self._lift_tween:
                self.clock.cancel(self._lift_tween)
            self._lift_tween = self.clock.tween(
                0.2, self._move_to, start=self._offset, end=-3 if value else 0)
            if self._scale_tween:
                self.clock.cancel(self._scale_tween)
            self._scale_tween = self.clock.tween(
                0.2, self._scale_to, start=self._scale,
                end=1.04 if value else 1.0, ease=ease_out_back)
        if value:
            cx, cy = self._center
            fx.sparkle_burst(self.canvas, self.clock, cx, cy, count=10,
                             spread=self.w * 0.5, color=PALETTE["pink_deep"])

    def pulse(self, amount=1.06, period=0.9):
        """Gentle looping pulse, used on the NEXT ROUND button."""
        def grow():
            if not self.canvas.winfo_exists():
                return
            self.clock.tween(period / 2, self._scale_to, start=self._scale,
                             end=amount, on_done=shrink)

        def shrink():
            self.clock.tween(period / 2, self._scale_to, start=self._scale,
                             end=1.0, on_done=grow)

        grow()

    def fade_out(self, duration=0.25, then=None):
        bg = self.canvas["background"]
        start = self.fill_current or self.fill

        def apply(t):
            faded = mix(start, bg, t)
            self._tint(faded)
            for i in self.border_ids:
                self.canvas.itemconfigure(i, fill=mix(self.border, bg, t))
            self.canvas.itemconfigure(self.text_id,
                                      fill=mix(self.text_color, bg, t))

        self.enabled = False
        self.clock.tween(duration, apply, on_done=then)

    def destroy(self):
        self.canvas.delete(self.tag)


def make_button(canvas, clock, cx, cy, w, h, text, command=None, **kwargs):
    return PixelButton(canvas, clock, cx, cy, w, h, text, command, **kwargs)
