"""Built-in pixel sprites.

Each sprite is (grid, palette) where grid is a list of equal-length strings and
palette maps a character to a colour. '.' means transparent.

These are fallbacks / defaults: drop a PNG with the same name into
assets/images/ and it will be used instead (see assets.py + ui.draw_icon).
"""
from config import PALETTE as P

# --------------------------------------------------------------- moves ------
ROCK = ([
    "....######....",
    "..##llllo##...",
    ".#llllooooo#..",
    "#lllooooooo##.",
    "#llooooooooo#.",
    "#loooooooooo#.",
    "#oooooooooo##.",
    ".############.",
    "..##########..",
    "....######....",
], {"#": "#8E7C9B", "l": "#DCD2E8", "o": "#B6A7C8"})

PAPER = ([
    "..##########..",
    "..#pppppppp#..",
    "..#pllllllp#..",
    "..#pppppppp#..",
    "..#pllllllp#..",
    "..#pppppppp#..",
    "..#pllllllp#..",
    "..#pppppppp#..",
    "..#pllllllp#..",
    "..#pppppppp#..",
    "..#pllllllp#..",
    "..#pppppppp#..",
    "..##########..",
], {"#": "#C9A9BE", "p": P["cream"], "l": P["pink_pale"]})

SCISSORS = ([
    "..#........#..",
    "..#s......s#..",
    "...#s....s#...",
    "....#s..s#....",
    ".....#ss#.....",
    "......##......",
    ".....#ss#.....",
    "....#s..s#....",
    "...#s....s#...",
    "..##......##..",
    ".#hh#....#hh#.",
    ".#hh#....#hh#.",
    ".#hh#....#hh#.",
    "..##......##..",
], {"#": "#8E7C9B", "s": "#D9D2E6", "h": P["pink"]})

# ---------------------------------------------------------------- cats ------
# 'E' is the eye colour: swap it to fur colour to make the cat blink.
CAT_HAPPY = ([
    "..##........##..",
    ".#cc#......#cc#.",
    ".#ccc######ccc#.",
    "#cccccccccccccc#",
    "#ccEEcccccEEccc#",
    "#ccEEcccccEEccc#",
    "#cccccccccccccc#",
    "#cbbcc#cc#ccbbc#",
    "#ccccc#cc#ccccc#",
    ".#cccccccccccc#.",
    "..############..",
    "...##......##...",
], {"#": "#B78FA8", "c": P["cream"], "E": P["ink"], "b": P["pink_soft"]})

CAT_SAD = ([
    "##............##",
    "#ss##......##ss#",
    ".#ssss####ssss#.",
    "#ssssssssssssss#",
    "#ssEEsssssEEsss#",
    "#ssEEsssssEEsss#",
    "#ssssssssssssss#",
    "#sbbss#ss#ssbbs#",
    "#sssss####sssss#",
    ".#ssssssssssss#.",
    "..############..",
    "...##......##...",
], {"#": "#9E93BE", "s": "#F2EEFA", "E": P["ink"], "b": P["blue_soft"]})

TROPHY = ([
    "..########..",
    "..#gggggg#..",
    "#g#gggggg#g#",
    "#g#gggggg#g#",
    "#g#gggggg#g#",
    ".##gggggg##.",
    "...#gggg#...",
    "....#gg#....",
    "....#gg#....",
    "..########..",
    "..#dddddd#..",
    "..########..",
], {"#": P["gold_deep"], "g": P["gold"], "d": "#F0C871"})

ROBOT = ([
    "...#....#...",
    "....#..#....",
    "..########..",
    ".#rrrrrrrr#.",
    "#rrEErrEErr#",
    "#rrEErrEErr#",
    "#rrrrrrrrrr#",
    "#rr######rr#",
    "#rrrrrrrrrr#",
    ".##########.",
    "..#rr##rr#..",
    "..########..",
], {"#": "#7FA8C9", "r": P["blue_soft"], "E": P["blue_deep"]})

HEART = ([
    ".##..##.",
    "########",
    "########",
    ".######.",
    "..####..",
    "...##...",
], {"#": P["pink_deep"]})

HEART_BROKEN = ([
    ".##..##.",
    "###.####",
    "####.###",
    ".###.##.",
    "..#.##..",
    "...##...",
], {"#": "#C98BAE"})

STAR = ([
    "..#..",
    "..#..",
    "#####",
    ".###.",
    "##.##",
], {"#": P["gold"]})

CLOUD = ([
    ".....####.......",
    "...##wwww##.....",
    "..#wwwwwwww#....",
    ".##wwwwwwwww##..",
    "#wwwwwwwwwwwww#.",
    "#wwwwwwwwwwwww#.",
    ".##############.",
], {"#": "#F0DDEC", "w": P["white"]})

SPRITES = {
    "rock": ROCK, "paper": PAPER, "scissors": SCISSORS,
    "cat_happy": CAT_HAPPY, "cat_sad": CAT_SAD, "trophy": TROPHY,
    "robot": ROBOT, "heart": HEART, "heart_broken": HEART_BROKEN,
    "star": STAR, "cloud": CLOUD,
}


def size_of(name, scale=1):
    grid, _ = SPRITES[name]
    return len(grid[0]) * scale, len(grid) * scale


def draw(canvas, name, x, y, scale=4, tags=(), palette_override=None):
    """Draw a sprite with its top-left corner at (x, y). Returns item ids.

    Horizontal runs of the same colour are merged into one rectangle, which
    keeps the canvas item count low enough to animate comfortably.
    """
    grid, palette = SPRITES[name]
    if palette_override:
        palette = {**palette, **palette_override}
    ids = []
    for row, line in enumerate(grid):
        col = 0
        while col < len(line):
            ch = line[col]
            if ch == "." or palette.get(ch) is None:
                col += 1
                continue
            run = 1
            while col + run < len(line) and line[col + run] == ch:
                run += 1
            ids.append(canvas.create_rectangle(
                x + col * scale, y + row * scale,
                x + (col + run) * scale, y + (row + 1) * scale,
                fill=palette[ch], outline="", tags=tags))
            col += run
    return ids


def draw_centered(canvas, name, cx, cy, scale=4, tags=(), palette_override=None):
    w, h = size_of(name, scale)
    return draw(canvas, name, cx - w / 2, cy - h / 2, scale, tags, palette_override)


def _self_check():
    bad = []
    for name, (grid, _pal) in SPRITES.items():
        widths = {len(r) for r in grid}
        if len(widths) != 1:
            bad.append((name, sorted(widths)))
    return bad


if __name__ == "__main__":
    problems = _self_check()
    print("ragged sprites:", problems if problems else "none")
