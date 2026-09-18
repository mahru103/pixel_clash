"""Sound effects.

Zero required dependencies. On Windows this plays short chiptune-style tones
straight from memory using the stdlib `winsound` module. On macOS/Linux it
tries `simpleaudio` if installed; if that's not available, sound is silently
skipped — the game never crashes or blocks because audio isn't available.

Drop a real .wav file into assets/sounds/<name>.wav to override any built-in
tone (see SOUND_NAMES below) — no code changes needed, same pattern as the
fonts and images.
"""
from __future__ import annotations

import io
import math
import os
import struct
import sys
import threading
import time
import wave

from config import SOUND_DIR

MUTED = False

_backend = None
if sys.platform.startswith("win"):
    try:
        import winsound  # noqa: F401  (import-checked, used lazily in play())
        _backend = "winsound"
    except Exception:
        _backend = None
if _backend is None:
    try:
        import simpleaudio  # noqa: F401
        _backend = "simpleaudio"
    except Exception:
        _backend = None

_cache: dict[str, bytes] = {}
_last_hover_at = float("-inf")
HOVER_COOLDOWN_SECONDS = 0.65

# name -> (frequencies, durations) — short, cute chiptune-ish blips.
_DEFAULT_TONES = {
    "hover":       ([1318, 1568], [0.035, 0.045]),
    "click":       ([740], [0.08]),
    "round_start": ([523, 659, 784], [0.10, 0.10, 0.14]),
    "count":       ([784], [0.06]),
    "go":          ([1046, 1318], [0.07, 0.11]),
    "choose":      ([880], [0.10]),
    "reveal":      ([392, 523], [0.08, 0.12]),
    "win":         ([523, 659, 784, 1046], [0.10, 0.10, 0.10, 0.20]),
    "lose":        ([392, 330, 261], [0.14, 0.14, 0.24]),
    "tie":         ([440, 440], [0.10, 0.18]),
    "victory":     ([523, 659, 784, 1046, 1318], [0.12, 0.12, 0.12, 0.12, 0.30]),
}
SOUND_NAMES = tuple(_DEFAULT_TONES)


def _tone_wav(freqs, durations, volume=0.55, sample_rate=22050):
    """Synthesize a short sequence of sine tones into raw WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for freq, dur in zip(freqs, durations):
            n = int(sample_rate * dur)
            for i in range(n):
                t = i / sample_rate
                fade = min(1.0, i / 80, (n - i) / 80)  # avoid clicky edges
                sample = math.sin(2 * math.pi * freq * t) * volume * fade
                frames += struct.pack("<h", int(sample * 32767))
        w.writeframes(bytes(frames))
    return buf.getvalue()


def _load(name: str) -> bytes | None:
    if name in _cache:
        return _cache[name]
    path = SOUND_DIR / f"{name}.wav"
    if path.exists():
        data = path.read_bytes()
    elif name in _DEFAULT_TONES:
        freqs, durs = _DEFAULT_TONES[name]
        data = _tone_wav(freqs, durs)
    else:
        return None
    _cache[name] = data
    return data


def set_muted(value: bool) -> None:
    global MUTED
    MUTED = value


def toggle_muted() -> bool:
    set_muted(not MUTED)
    return MUTED


def _play_winsound(data: bytes) -> None:
    """Play memory-backed audio off the Tk event thread on Windows.

    winsound does not allow SND_MEMORY and SND_ASYNC together. Running its
    synchronous memory mode in a daemon thread gives us the same responsive UI
    without triggering that Windows-only RuntimeError.
    """
    try:
        import winsound
        winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
    except Exception:
        if os.environ.get("PIXEL_CLASH_AUDIO_DEBUG"):
            import traceback
            traceback.print_exc()


def play(name: str) -> None:
    """Fire-and-forget playback. Never raises, never blocks the UI thread."""
    global _last_hover_at
    if MUTED or _backend is None:
        return
    if name == "hover":
        now = time.monotonic()
        if now - _last_hover_at < HOVER_COOLDOWN_SECONDS:
            return
        _last_hover_at = now
    data = _load(name)
    if data is None:
        return
    try:
        if _backend == "winsound":
            threading.Thread(target=_play_winsound, args=(data,), daemon=True).start()
        elif _backend == "simpleaudio":
            import simpleaudio
            simpleaudio.WaveObject.from_wave_file(io.BytesIO(data)).play()
    except Exception:
        # Sound should never take the game down with it — but if you're
        # debugging silence, set PIXEL_CLASH_AUDIO_DEBUG=1 to see why.
        if os.environ.get("PIXEL_CLASH_AUDIO_DEBUG"):
            import traceback
            traceback.print_exc()
