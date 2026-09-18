# 🪨 Rock Paper Scissors — ✨ Pixel Clash ✨

A cozy pastel pixel-art desktop game in Python. CustomTkinter owns the window;
everything inside is drawn and animated on a `tk.Canvas`, which is what makes
the hover lifts, sparkles, confetti and sprite animation possible.

Created by **Maha**.

---

## Run it

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Press `Esc` to quit. On startup the terminal prints a short asset report
telling you which fonts were registered and which families Tk actually used —
check it if the type looks wrong.

Linux also needs Tk itself: `sudo apt install python3-tk`.

---

## Fonts

Tk cannot load a font from a file path, so the game registers the files with
the OS before the window opens (`assets.py`). Put your two files here:

```
assets/fonts/Miracle History.ttf     ← titles, VICTORY, DEFEAT
assets/fonts/Pixel Digivolve.otf     ← buttons, scores, labels
```

If a font does not appear, the *family name inside the file* probably differs
from the file name. Find it, then put it first in `TITLE_FAMILIES` or
`PIXEL_FAMILIES` in `config.py`. To list what Tk can see:

```python
import tkinter, tkinter.font
root = tkinter.Tk(); print(sorted(tkinter.font.families()))
```

`tkextrafont` (in requirements) is the most reliable loader on macOS/Linux.
On Linux the fallback copies the file into `~/.local/share/fonts` and runs
`fc-cache`, which sometimes needs one restart to take effect. Missing fonts
never crash the game — it falls back to the next family in the list.

## Your own pixel art

Drop PNGs into `assets/images/` and they replace the built-in sprites
automatically — no code change. Transparent background, small source size
(16–32 px) so nearest-neighbour upscaling stays crisp:

```
rock.png  paper.png  scissors.png
cat_happy.png  cat_sad.png  trophy.png  robot.png
heart.png  heart_broken.png  star.png  cloud.png
```

Until then, the fallbacks in `sprites.py` are drawn from character grids —
edit a grid string and the sprite changes. Every row of a grid must be the
same length; `python sprites.py` checks that for you.

---

## File map

| File | What lives there |
| --- | --- |
| `main.py` | entry point; registers fonts *before* Tk starts |
| `app.py` | window, screen manager, sliding transitions |
| `config.py` | palette, window size, font families, round options |
| `game.py` | pure game rules and state (no UI — easy to test) |
| `anim.py` | easing, tweens, per-screen frame clock |
| `fx.py` | sparkles, confetti, rain, animated background |
| `ui.py` | pixel panels, buttons, choice cards, text pops |
| `sprites.py` | built-in pixel sprites + renderer |
| `screens/welcome.py` | title screen with idle-animated moves |
| `screens/rounds.py` | 3 / 5 / 7 round picker |
| `screens/gameplay.py` | countdown, choice, computer turn, reveal, result |
| `screens/results.py` | victory (confetti + cat) and defeat (rain + sad cat) |
| `tools/headless_check.py` | plays a whole match with no display, for testing |

## Things you will probably want to tweak

- **Timings** — the round intro is one `clock.sequence([...])` block at the top
  of `GameplayScreen.start_round`. The computer's thinking delay is the
  `clock.after(1400, ...)` in `computer_thinks`.
- **Colours** — all of them are in `config.PALETTE`; nothing hardcodes a hex
  outside `sprites.py`.
- **Confetti** — `fx.Confetti(count=80, duration=7.0)` in `results.py`.
- **Screen transition** — `TRANSITION_MS` in `app.py`.

## How the animation works

There is no `time.sleep` anywhere. Each screen owns a `Clock` that ticks at
~60 fps via `after()`, holds its tweens, and cancels every pending timer when
the screen is destroyed — that is what stops a half-finished round from firing
callbacks into a dead canvas.

Buttons are canvas items, not widgets, so hover can lift them a few pixels,
scale them slightly, blend the fill colour and emit sparkles at the same time.

## Testing without a display

```bash
python tools/headless_check.py
```

Stubs out Tk, drives a virtual clock, builds all four screens and plays a full
three-round match. Handy before you commit.

## Sound

Pixel Clash includes short chiptune-style effects for buttons, round starts,
move selection, reveals, and results. Use the `SOUND: ON/OFF` button in the
top-right corner on any screen to mute or restore them. On Windows they play
without extra dependencies; on macOS/Linux install `simpleaudio` if you want
sound. You can replace any built-in tone by adding a `.wav` file with the same
name to `assets/sounds/` (for example, `win.wav` or `victory.wav`).
