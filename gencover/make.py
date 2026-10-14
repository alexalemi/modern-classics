"""Render generated covers into build/covers/{book}.jpg (the cache that
build_ebook.prepare_cover reads), and optionally a proof sheet.

    python3 gencover/make.py                 # every design in COVERS
    python3 gencover/make.py godel euclid-rivals
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import designs  # noqa: E402


def render(book, seed=None, scale=1.0, out=None, original=False, mark=True):
    """original: the companion edition of the source text, cached apart
    (build/covers/{book}-original.jpg) since its cover says so"""
    meta = json.load(open(ROOT / "ebook_meta.json")).get(book, {})
    seed = seed if seed is not None else meta.get("cover", {}).get("seed", 1)
    out = Path(out) if out else ROOT / "build" / "covers" / (f"{book}-original.jpg" if original else f"{book}.jpg")
    from press import Press
    import edition
    Press.SCALE = scale
    out.parent.mkdir(parents=True, exist_ok=True)
    p = designs.COVERS[book](seed)
    if mark:
        p.mark(edition.label(book, original))
    im = p.print(str(out.with_suffix(".png")))
    im.convert("RGB").save(out, quality=95)
    out.with_suffix(".png").unlink()
    Press.SCALE = 1.0
    return out


if __name__ == "__main__":
    for b in sys.argv[1:] or list(designs.COVERS):
        print("rendered", render(b))
