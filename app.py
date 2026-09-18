"""Window shell and screen manager."""
from __future__ import annotations

import tkinter as tk
import traceback

import customtkinter as ctk

import assets
from anim import Clock, ease_in_out
from config import HEIGHT, PALETTE, TITLE, WIDTH

TRANSITION_MS = 420


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        super().__init__(fg_color=PALETTE["bg"])

        # The game itself is a standard Tk canvas with fixed 800 × 900 pixel
        # artwork. On high-DPI Windows displays, CTk otherwise scales only the
        # window dimensions to 125–150%, making the game appear too wide.
        # Counteract just that window scaling; the canvas stays pixel-perfect.
        dpi_scale = ctk.ScalingTracker.get_window_scaling(self)
        if dpi_scale != 1:
            ctk.set_window_scaling(1 / dpi_scale)

        self.title(TITLE)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.minsize(WIDTH, HEIGHT)
        self.resizable(False, False)
        self._center_on_screen()

        self.container = ctk.CTkFrame(self, width=WIDTH, height=HEIGHT,
                                      fg_color=PALETTE["bg"], corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.pack_propagate(False)

        assets.resolve_fonts(self)
        print("Pixel Clash asset report:")
        print(assets.report() or "  - nothing to report")

        self.transition_clock = Clock(self)
        self.transition_clock.start()
        self.current = None
        self._busy = False

        self.bind("<Escape>", lambda _e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self._quit)

    def _center_on_screen(self):
        self.update_idletasks()
        x = max(0, (self.winfo_screenwidth() - WIDTH) // 2)
        y = max(0, (self.winfo_screenheight() - HEIGHT) // 3)
        self.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

    # ------------------------------------------------------------ screens --
    def show_first(self, screen_class, **kwargs):
        screen = self._make(screen_class, kwargs)
        if screen is None:
            return
        self.current = screen
        screen.canvas.place(x=0, y=0)
        screen.start()
        screen.on_enter()

    def go(self, screen_class, direction=1, **kwargs):
        """Slide to a new screen. direction 1 = forward (right to left)."""
        if self._busy:
            return
        incoming = self._make(screen_class, kwargs)
        if incoming is None:
            return
        outgoing = self.current
        self._busy = True

        start_x = WIDTH * direction
        incoming.canvas.place(x=start_x, y=0)
        incoming.start()

        def step(t):
            offset = int(start_x * (1 - t))
            try:
                incoming.canvas.place_configure(x=offset)
                if outgoing is not None:
                    outgoing.canvas.place_configure(x=offset - start_x)
            except tk.TclError:
                pass

        def done():
            if outgoing is not None:
                outgoing.destroy()
            self.current = incoming
            self._busy = False
            try:
                incoming.canvas.place_configure(x=0)
                incoming.on_enter()
            except tk.TclError:
                pass

        self.transition_clock.tween(TRANSITION_MS / 1000, step,
                                    ease=ease_in_out, on_done=done)

    def _make(self, screen_class, kwargs):
        """Build a screen, surviving a bad frame rather than killing the app."""
        try:
            screen = screen_class(self, **kwargs)
            screen.build()
            return screen
        except Exception:
            traceback.print_exc()
            self._show_error(screen_class.__name__)
            return None

    def _show_error(self, where):
        banner = ctk.CTkLabel(
            self.container,
            text=f"Something went wrong in {where}.\nCheck the terminal for details.",
            text_color=PALETTE["ink"], fg_color=PALETTE["pink_pale"],
            corner_radius=12, padx=20, pady=14)
        banner.place(relx=0.5, rely=0.06, anchor="center")
        self.after(4000, banner.destroy)

    def _quit(self):
        if self.current:
            self.current.destroy()
        self.transition_clock.stop()
        self.destroy()


def main():
    from screens.welcome import WelcomeScreen
    app = App()
    app.show_first(WelcomeScreen)
    app.mainloop()
