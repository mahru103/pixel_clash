"""Global configuration: paths, window size, palette, font identities."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets"
FONT_DIR = ASSET_DIR / "fonts"
IMAGE_DIR = ASSET_DIR / "images"
SOUND_DIR = ASSET_DIR / "sounds"

# ---------------------------------------------------------------- window ----
TITLE = "Rock Paper Scissors: Pixel Clash"
WIDTH, HEIGHT = 800, 900
FPS = 60
FRAME_MS = int(1000 / FPS)

# --------------------------------------------------------- card / chrome ----
CARD_MARGIN = 8      # outer "sticker card" frame inset from the window edge
CARD_RADIUS = 30

# ----------------------------------------------------------------- fonts ----
# Drop these two files into assets/fonts/.
TITLE_FONT_FILE = "Miracle History.ttf"
PIXEL_FONT_FILE = "Pixel Digivolve.otf"

# The family name embedded in the font file (may differ from the file name).
# If Tk reports a different family, add it to the front of the fallback list.
TITLE_FAMILIES = ["Miracle History", "MiracleHistory", "Press Start 2P", "Silkscreen",
                  "Impact", "Georgia", "TkHeadingFont"]
PIXEL_FAMILIES = ["Pixel Digivolve", "PixelDigivolve", "Press Start 2P", "Silkscreen",
                  "Consolas", "Courier New", "TkFixedFont"]

# ---------------------------------------------------------------- palette ---
PALETTE = {
    "bg":         "#FDF2F8",
    "bg_soft":    "#F7EEFB",
    "bg_gloom":   "#EDEAF7",

    "pink":       "#FFB7D5",
    "pink_soft":  "#FFD6E8",
    "pink_pale":  "#FFEAF3",
    "pink_deep":  "#F57FB6",
    "pink_ink":   "#B24A7C",

    "lav":        "#CDB9F2",
    "lav_soft":   "#E6DBFB",
    "lav_deep":   "#9A79D8",

    "blue":       "#AFD7F5",
    "blue_soft":  "#DBEDFC",
    "blue_deep":  "#5F9AD0",

    "cream":      "#FFFBF5",
    "white":      "#FFFFFF",
    "gold":       "#FFD98E",
    "gold_deep":  "#E0A73E",

    "ink":        "#6B4A63",
    "ink_soft":   "#A4899E",
    "gray":       "#CFC6D6",
    "shadow":     "#E8D3E2",
    "shadow_cool": "#D8D2EC",
}

CONFETTI_COLORS = [PALETTE["pink"], PALETTE["pink_deep"], PALETTE["lav"],
                   PALETTE["blue"], PALETTE["gold"], PALETTE["white"],
                   PALETTE["lav_deep"]]

ROUND_CHOICES = (3, 5, 7)
DEFAULT_ROUNDS = 5
