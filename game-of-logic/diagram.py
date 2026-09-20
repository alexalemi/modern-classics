"""Carroll's Game of Logic diagrams, drawn from Gutenberg's ASCII.

The 1887 printing SETS its diagrams in type: boxes ruled with lines, the
counters printed as the digits 1 (red, "there is some") and 0 (grey,
"there is none"), a counter "sitting on the fence" printed on the rule
itself. Gutenberg's transcription keeps every one as ASCII art, which
carries all of that: '-' runs are horizontal rules, '|' vertical rules,
anything else is a character in its place. So the diagrams are REDRAWN,
not cut from a page scan (the calculus-made-easy rule: what was typeset
is set again, not photographed).

    render(ascii_text) -> PIL.Image (LA, ink on transparent)
"""
from PIL import Image, ImageDraw, ImageFont

CW, CH = 14, 26          # one character cell, in pixels (a monospace grid)
PAD = 10
LINE = 2
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def render(text):
    rows = text.split("\n")
    while rows and not rows[0].strip():
        rows.pop(0)
    while rows and not rows[-1].strip():
        rows.pop()
    ind = min(len(r) - len(r.lstrip()) for r in rows if r.strip())
    rows = [r[ind:].rstrip() for r in rows]
    W = max(len(r) for r in rows)
    grid = [list(r.ljust(W)) for r in rows]
    H = len(grid)
    for r in range(H):
        for c in range(W):
            # an underscore run is a rule drawn low ("|    _____|_____    |",
            # the inner square's top): set it as a rule
            if grid[r][c] == "_":
                grid[r][c] = "-"
    for r in range(H):
        for c in range(W):
            # A RED COUNTER ON A VERTICAL FENCE. The print sets it as a
            # sideways 1, a short stroke across the rule, and Gutenberg types
            # that as a lone "-" in a column of "|" -- which, drawn as a rule,
            # simply vanishes. Set it as the 1 it is.
            if (grid[r][c] == "-" and (c == 0 or grid[r][c - 1] == " ")
                    and (c == W - 1 or grid[r][c + 1] == " ")
                    and ((r > 0 and grid[r - 1][c] == "|") or (r < H - 1 and grid[r + 1][c] == "|"))):
                grid[r][c] = "1"
    grid = ["".join(r) for r in grid]
    img = Image.new("LA", (W * CW + 2 * PAD, H * CH + 2 * PAD), (0, 0))
    d = ImageDraw.Draw(img)
    ink = (0, 255)
    font = _font(19)

    def at(r, c):
        return grid[r][c] if 0 <= r < H and 0 <= c < W else " "

    def cx(c):
        return PAD + c * CW + CW // 2

    def cy(r):
        return PAD + r * CH + CH // 2

    def is_rule(ch):
        return ch in "-|"

    # THE RULES ARE LINKS BETWEEN CELL CENTRES. Two cells side by side join
    # when both are part of a horizontal rule ('-', or a '|' it meets, or a
    # label set on the rule, "-x-"); two cells one above the other join when
    # both are part of a vertical rule. ASCII leaves the CORNERS implied --
    # a border's first '-' sits one column in from the '|' below it -- so a
    # rule end with a '|' diagonally next to it is joined round the corner.
    def hpart(r, c):
        ch = at(r, c)
        return ch == "-" or (ch not in " |" and at(r, c - 1) == "-" and at(r, c + 1) == "-")

    def vpart(r, c):
        ch = at(r, c)
        return ch == "|" or (ch not in " -" and at(r - 1, c) == "|" and at(r + 1, c) == "|")

    segs = []
    for r in range(H):
        for c in range(W):
            a, b = at(r, c), at(r, c + 1)
            if (hpart(r, c) and (hpart(r, c + 1) or b == "|")) or (a == "|" and hpart(r, c + 1)):
                segs.append(((cx(c), cy(r)), (cx(c + 1), cy(r))))
            a2 = at(r + 1, c)
            if (vpart(r, c) and (vpart(r + 1, c) or a2 == "-")) or (a == "-" and vpart(r + 1, c)):
                segs.append(((cx(c), cy(r)), (cx(c), cy(r + 1))))
            # implied corners
            if a == "-":
                for dc in (-1, 1):
                    if at(r, c + dc) == " ":
                        for dr in (-1, 1):
                            if at(r + dr, c + dc) == "|":
                                segs.append(((cx(c), cy(r)), (cx(c + dc), cy(r))))
                                segs.append(((cx(c + dc), cy(r)), (cx(c + dc), cy(r + dr))))
    # each segment runs half a line-width past its nodes, so joints close
    # without a separate mark (square dots a pixel off the line read as ticks)
    e = LINE // 2
    for (x0, y0), (x1, y1) in set(segs):
        if y0 == y1:
            d.rectangle([min(x0, x1) - e, y0 - e, max(x0, x1) + e - 1, y0 + e - 1], fill=ink)
        else:
            d.rectangle([x0 - e, min(y0, y1) - e, x0 + e - 1, max(y0, y1) + e - 1], fill=ink)
    # every run of other characters is ONE WORD, set over the cells it
    # occupies ("32.", "y'", "10" would otherwise be spaced out a letter per
    # cell); a word set ON a rule gets a clear patch first, so a counter on
    # the fence reads as a counter
    for r in range(H):
        c = 0
        while c < W:
            ch = grid[r][c]
            if ch == " " or is_rule(ch):
                c += 1
                continue
            s = c
            while c < W and grid[r][c] != " " and not is_rule(grid[r][c]):
                c += 1
            word = grid[r][s:c]
            on_rule = any(is_rule(at(r, k)) for k in (s - 1, c)) or any(
                is_rule(at(rr, k)) for rr in (r - 1, r + 1) for k in range(s, c))
            box = d.textbbox((0, 0), word, font=font)
            w, h = box[2] - box[0], box[3] - box[1]
            mid = (cx(s) + cx(c - 1)) // 2
            x, y = mid - w // 2 - box[0], cy(r) - h // 2 - box[1]
            if on_rule:
                d.rectangle([x + box[0] - 3, y + box[1] - 2, x + box[2] + 3, y + box[3] + 2], fill=(0, 0))
            d.text((x, y), word, font=font, fill=ink)
    return img


if __name__ == "__main__":
    import sys
    render(open(sys.argv[1]).read()).save(sys.argv[2])
