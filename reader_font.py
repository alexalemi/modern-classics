"""The reader font offered on the About page: Emend Serif, an SD-card font for
CrossPoint e-readers (Xteink X3/X4) that carries every symbol the books use.

    python3 reader_font.py          -> site/downloads/EmendSerif-crosspoint.zip

CrossPoint's built-in fonts lack the logic and mathematics signs (∃ ∨ ⊃ ∼ ≠
∴ ...), the planet signs in Euler, Verne's runes and a few others, and its
reading text has no per-glyph fallback, so those show as boxes. An SD-card
font is merged at conversion time instead: Literata sets the text, and
Noto Serif, Noto Sans Math, Noto Sans Symbols 1 and 2, Noto Sans Runic and
Noto Music supply what it lacks, in that order. Every face is SIL OFL 1.1
with no Reserved Font Name, so the result is OFL too and ships with the
licence. (The fermat project's STIXMath, which Alex uses, is not offered:
STIX 1.x carries extra licence terms and its build draws on GPL FreeSerif.)

The converter is CrossPoint's own (tools/epdfont), vendored and patched for
a fallback chain in the sibling fermat project; .cpfont files are tied to
the firmware's format version, recorded in that directory.

Run it again whenever a book brings a sign the font lacks: it checks the
whole corpus (every standard epub in site/ebooks) and stops on a gap.
"""
import glob
import html
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent
EPDFONT = Path.home() / "projects/fermat/tools/epdfont"
LITERATA = Path.home() / "projects/fermat/build/x3/font/src/Literata-{}.ttf"
NOTO = "/usr/share/fonts/truetype/noto/{}.ttf"
NAME = "EmendSerif"
OUT = ROOT / "site" / "downloads" / f"{NAME}-crosspoint.zip"
STYLES = ["Regular", "Bold", "Italic", "BoldItalic"]
INTERVALS = ["reading", "(0x16A0-0x16FF)", "(0x2100-0x214F)", "(0x2300-0x23FF)",
             "(0x27C0-0x27EF)", "(0x2A00-0x2AFF)", "(0x20D0-0x20FF)",
             "(0x1D2C-0x1DBF)", "(0x1F00-0x1FFF)", "(0x1D133-0x1D133)"]
# what a reader never sees as a glyph
INVISIBLE = {0xAD, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF} | set(range(0xFE00, 0xFE10))


def chain(style):
    noto_style = "Regular" if style == "Regular" else style
    return str(LITERATA).format(style), [
        NOTO.format(f"NotoSerif-{noto_style}"), NOTO.format("NotoSansMath-Regular"),
        NOTO.format("NotoSansSymbols-Regular"), NOTO.format("NotoSansSymbols2-Regular"),
        NOTO.format("NotoSansRunic-Regular"), NOTO.format("NotoMusic-Regular")]


def ranges():
    sys.path.insert(0, str(EPDFONT))
    import fontconvert_sdcard as fc
    out = []
    for spec in INTERVALS:
        m = re.fullmatch(r"\(0x([0-9a-fA-F]+)-0x([0-9a-fA-F]+)\)", spec)
        out += [(int(m[1], 16), int(m[2], 16))] if m else fc.INTERVAL_PRESETS[spec]
    return out


def gaps():
    """Every character in the books that the font would not draw, in any style."""
    rs = ranges()
    styles = []
    for style in STYLES:
        primary, fb = chain(style)
        cps = set()
        for f in [primary] + fb:
            cps |= set(TTFont(f).getBestCmap())
        styles.append({c for c in cps if any(a <= c <= b for a, b in rs)})
    common = set.intersection(*styles)
    missing = {}
    for epub in sorted(glob.glob(str(ROOT / "site/ebooks/*.epub"))):
        if "_advanced" in epub:
            continue
        with zipfile.ZipFile(epub) as z:
            for n in z.namelist():
                if n.endswith(".xhtml"):
                    t = html.unescape(re.sub(r"<[^>]+>", " ", z.read(n).decode()))
                    for c in set(t) - set(" \n\t\r"):
                        if ord(c) not in common and ord(c) not in INVISIBLE:
                            missing.setdefault(c, Path(epub).stem)
    return missing


def main():
    missing = gaps()
    if missing:
        for c, book in sorted(missing.items()):
            print(f"  U+{ord(c):04X} {c}  ({book})", file=sys.stderr)
        sys.exit(f"{len(missing)} characters in the books are not in {NAME}")
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / NAME
        args = []
        for style, flag in zip(STYLES, ["regular", "bold", "italic", "bolditalic"]):
            primary, fb = chain(style)
            args += [f"--{flag}", primary, f"--fallback-{flag}", ",".join(fb)]
        subprocess.run([sys.executable, str(EPDFONT / "fontconvert_sdcard.py"), *args,
                        "--intervals", ",".join(INTERVALS), "--sizes", "12,14,16,18",
                        "--name", NAME, "--output-dir", str(dest)],
                       check=True, capture_output=True)
        shutil.copy(ROOT / "brand" / "OFL.txt", dest / "OFL.txt")
        (dest / "README.txt").write_text(README)
        OUT.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(dest.iterdir()):
                z.write(f, f"{NAME}/{f.name}")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB); every character in the books is covered")


README = f"""{NAME} -- a reading font for CrossPoint e-readers (Xteink X3, X4)
from Emend Press, https://emend.press/about.html

The built-in fonts on these readers have no logic or mathematics signs, so
books like Gödel's Proof or Boole's Laws of Thought show boxes where the
symbols should be. This font has every character used in the Emend Press
books.

To install: copy the {NAME} folder into the /fonts/ folder on the reader's
SD card (make the folder if it is not there), then choose {NAME} as the
reading font in the reader's settings. Sizes 12, 14, 16 and 18.

Made from Literata (The Literata Project Authors), with Noto Serif, Noto
Sans Math, Noto Sans Symbols, Noto Sans Symbols 2, Noto Sans Runic and
Noto Music (Google LLC) for the characters Literata lacks. Converted with
CrossPoint's own font tool. Licensed under the SIL Open Font License 1.1;
see OFL.txt.
"""

if __name__ == "__main__":
    main()
