"""Fonts and images, with graceful degradation.

Tk cannot load a font straight from a file path, so we register the files with
the OS first. Three strategies are tried in order:

  1. tkextrafont (cross-platform, needs a Tk root)  -> pip install tkextrafont
  2. the native OS font API (gdi32 / CoreText)
  3. copying into the user font dir (Linux) + fc-cache

If every strategy fails the game still runs: it falls back to the next family
in config.TITLE_FAMILIES / PIXEL_FAMILIES.
"""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

import tkinter.font as tkfont

from config import (FONT_DIR, IMAGE_DIR, PIXEL_FAMILIES, PIXEL_FONT_FILE,
                    TITLE_FAMILIES, TITLE_FONT_FILE)

notes: list[str] = []            # human-readable log, printed on startup
_resolved = {"title": None, "pixel": None}
_extra_font_refs = []            # keep tkextrafont objects alive
_image_cache: dict[tuple, object] = {}
_image_refs = []                 # keep PhotoImage objects alive


# ------------------------------------------------------------------ fonts ---
def _register_windows(path: Path) -> bool:
    try:
        FR_PRIVATE = 0x10
        added = ctypes.windll.gdi32.AddFontResourceExW(str(path), FR_PRIVATE, 0)
        return added > 0
    except Exception:
        return False


def _register_macos(path: Path) -> bool:
    try:
        ct = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreText.framework/CoreText")
        cf = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        raw = str(path).encode("utf-8")
        cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
        cf.CFURLCreateFromFileSystemRepresentation.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
        url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
        ct.CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
        ct.CTFontManagerRegisterFontsForURL.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        return bool(ct.CTFontManagerRegisterFontsForURL(url, 1, None))  # 1 = process scope
    except Exception:
        return False


def _register_linux(path: Path) -> bool:
    try:
        target_dir = Path.home() / ".local" / "share" / "fonts"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / path.name
        if not target.exists():
            shutil.copy2(path, target)
            notes.append(f"copied {path.name} -> {target_dir} (may need one restart)")
        if shutil.which("fc-cache"):
            subprocess.run(["fc-cache", "-f", str(target_dir)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False)
        return True
    except Exception:
        return False


def preregister_fonts() -> None:
    """Register font files with the OS. Call this BEFORE creating the Tk root."""
    for label, filename in (("title", TITLE_FONT_FILE), ("pixel", PIXEL_FONT_FILE)):
        path = FONT_DIR / filename
        if not path.exists():
            notes.append(f"font file not found: {path} (using a fallback family)")
            continue
        if sys.platform.startswith("win"):
            ok = _register_windows(path)
        elif sys.platform == "darwin":
            ok = _register_macos(path)
        else:
            ok = _register_linux(path)
        notes.append(f"{label} font {'registered' if ok else 'NOT registered'}: {filename}")


def _try_tkextrafont(root, path: Path) -> bool:
    try:
        from tkextrafont import Font as ExtraFont
    except Exception:
        return False
    try:
        f = ExtraFont(root, file=str(path))
        _extra_font_refs.append(f)
        return True
    except Exception:
        return False


def resolve_fonts(root) -> None:
    """Pick the best available family for each role. Call after the root exists."""
    for label, filename in (("title", TITLE_FONT_FILE), ("pixel", PIXEL_FONT_FILE)):
        path = FONT_DIR / filename
        if path.exists():
            _try_tkextrafont(root, path)

    available = {name.lower() for name in tkfont.families(root)}
    for label, wanted in (("title", TITLE_FAMILIES), ("pixel", PIXEL_FAMILIES)):
        pick = next((fam for fam in wanted if fam.lower() in available), None)
        _resolved[label] = pick or wanted[-1]
        notes.append(f"{label} family in use: {_resolved[label]}")


def font(role: str, size: int, weight: str = "normal"):
    """Return a Tk font spec, e.g. assets.font('title', 40, 'bold')."""
    family = _resolved.get(role) or (TITLE_FAMILIES if role == "title" else PIXEL_FAMILIES)[-1]
    return (family, size, weight)


# ----------------------------------------------------------------- images ---
def image(name: str, height: int):
    """Load assets/images/<name>.png scaled (nearest-neighbour) to `height` px.

    Returns a PhotoImage, or None if the file or Pillow is unavailable, in
    which case callers fall back to the built-in sprite grids.
    """
    key = (name, height)
    if key in _image_cache:
        return _image_cache[key]

    path = IMAGE_DIR / f"{name}.png"
    result = None
    if path.exists():
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGBA")
            factor = max(1, round(height / img.height)) if img.height else 1
            if abs(img.height * factor - height) > 2:
                img = img.resize((max(1, round(img.width * height / img.height)), height),
                                 Image.NEAREST)
            else:
                img = img.resize((img.width * factor, img.height * factor), Image.NEAREST)
            result = ImageTk.PhotoImage(img)
            _image_refs.append(result)
        except Exception as exc:  # missing Pillow, corrupt file, ...
            notes.append(f"could not load image {path.name}: {exc}")
            result = None

    _image_cache[key] = result
    return result


def report() -> str:
    return os.linesep.join(f"  - {n}" for n in notes)
