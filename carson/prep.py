"""Rachel Carson, Conservation in Action (1947-1950): five booklets ->
chapters/ and modern_chapters/ (a RESTORED EDITION).

    python3 carson/prep.py

The words are the page readers' proofs (proof/{book}-{NN}.txt; see
page_agent_prompt.txt), checked page by page against the scan's OCR
(pagecheck.py), booklet by booklet against a second copy's OCR, and --
for Bear River, read twice from two different scans -- against each other
(4 differences in 5,000 words, all trivial). Guarding pp. 5-10 come from
the OCR plus word patches (guarding_ocr.py). Plates are cut by plates.py.

Each booklet is one section, in series order. Its title page gives the
byline line; its cover drawing opens it; the department lines, imprints,
prices and library stamps are dropped. Paragraphs broken across pages
(the readers' ⟨cont⟩ markers) are joined, a line-end hyphen at a page
break closed up. Captions: the printed caption, then -- in the modern
file only -- this edition's description (captions/plates.txt, CAPTIONS.md).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BOOKLETS = [  # (key, pages, title)
    ("chincoteague", range(1, 24), "Chincoteague: A National Wildlife Refuge"),
    ("parker", range(1, 24), "Parker River: A National Wildlife Refuge"),
    ("mattamuskeet", range(1, 13), "Mattamuskeet: A National Wildlife Refuge"),
    ("guarding", range(1, 51), "Guarding Our Wildlife Resources"),
    ("bear", range(1, 17), "Bear River: A National Wildlife Refuge"),
]
# Each booklet's title page, read off the image: author, illustrator,
# series number, imprint year (the year is asserted against the proof).
BYLINES = {
    "chincoteague": "By Rachel L. Carson · Illustrations by Shirley A. Briggs and Katherine L. Howe · Conservation in Action, Number One · 1947",
    "parker": "By Rachel L. Carson · Drawings and photographs by Katherine L. Howe · Conservation in Action, Number Two · 1947",
    "mattamuskeet": "By Rachel L. Carson · Illustrations by Katherine L. Howe · Conservation in Action, Number Four · 1947",
    "guarding": "By Rachel L. Carson · Designed by Katherine L. Howe · Conservation in Action, Number Five · 1948",
    "bear": "By Vanez T. Wilson and Rachel L. Carson · Illustrations by Bob Hines · Conservation in Action, Number Eight · 1950",
}
FRONT_KINDS = {"cover", "inside-cover", "title", "back-cover"}
# the imprint, price and job-number lines (the introduction says they go)
IMPRINT = re.compile(r"PRINTING OFFICE|FOR SALE BY|SUPERINTENDENT OF DOCUMENTS", re.I)
# A printed caption that runs across a two-page spread (Parker River pp.
# 12-13: one sentence for the panorama, then "Below, left:" and "Right:"),
# given to the plates it describes. The page reader set it on the first
# plate and the last.
CAPTION_SPLITS = {
    "pa12a": "A panoramic view of Plum Island may be had from any high dune, from the bordering "
             "ocean in the east across dunes and thickets to the marshes.",
    "pa12b": "Below, left: pot-holes dot the marshes, are favorite stopping places for ducks.",
    "pa13b": "Right: the beaches of Plum Island attract many shore birds; diving ducks often appear "
             "offshore. Surf casters like to fish for striped bass from this beach.",
}
PLATE = re.compile(r"^\[PLATE\s+([\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+)\s*\|\s*(\w+)\s*\|\s*(.*?)\]\s*$")
BYLINE = re.compile(r"\b(By|by)\b.*(Carson|Wilson)|Illustrations by|Drawings and photographs by|Designed by|Conservation in Action|NUMBER|Number")
YEAR = re.compile(r"WASHINGTON\s*:\s*(\d{4})|Washington\s*:\s*(\d{4})")
# headings that only repeat the booklet's own title
TITLE_HEADS = re.compile(r"^(Chincoteague|Parker River|Mattamuskeet|Bear River|Guarding Our Wildlife Resources)(:.*)?$|^A National Wildlife Refuge$", re.I)


def plate_ids():
    return {(r["book"], r["page"], tuple(r["box"])): r["id"] for r in json.loads((HERE / "plates.json").read_text())}


def descriptions():
    caps = {}
    for f in sorted((HERE / "captions").glob("batch-*.txt")) if (HERE / "captions").is_dir() else []:
        for line in f.read_text().splitlines():
            if "\t" in line and not line.startswith("#"):
                k, _, v = line.partition("\t")
                assert k not in caps, f"{k} captioned twice"
                caps[k.strip()] = v.strip()
    return caps


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def slugs(order):
    """Plate id -> a letters-only id, in reading order (aa, ab, ...). The
    plates are unnumbered in print, and assemble.figure_label gives a
    "Figure N" label to any id with a digit in it."""
    abc = "abcdefghijklmnopqrstuvwxyz"
    return {pid: abc[i // 26] + abc[i % 26] for i, pid in enumerate(order)}


def place_images(slug, prune=False):
    """site/images/carson/fig{slug}.jpg from plates.py's fig{id}.jpg, at
    1200px. A photograph is a halftone, and its screen is what costs bytes
    and beats against the reader's pixels: a light blur before the
    downscale takes the set from 72 MB to about 25 with no loss a reader
    can see. Drawings and maps are line work and are only resized."""
    from PIL import Image, ImageFilter
    kinds = {r["id"]: r["kind"] for r in json.loads((HERE / "plates.json").read_text())}
    d = HERE.parent / "site/images/carson"
    for pid, sl in slug.items():
        old, new = d / f"fig{pid}.jpg", d / f"fig{sl}.jpg"
        if old.exists():
            im = Image.open(old)
            if kinds[pid] == "photo":
                im = im.filter(ImageFilter.GaussianBlur(1.2))
            im.thumbnail((1200, 1200), Image.LANCZOS)
            im.save(new, "JPEG", quality=82, optimize=True)
            if prune:
                old.unlink()
        assert new.exists(), new


def titlecase(s):
    small = {"a", "an", "the", "of", "to", "in", "on", "and", "for", "at", "by"}
    if s.upper() != s:
        return s
    ws = s.lower().split()
    return " ".join(w if (w in small and i) else w.capitalize() for i, w in enumerate(ws))


def booklet(key, pages, title, ids, caps):
    blocks, byline, year, cover_caption = [], [], None, None
    for nn in pages:
        raw = (HERE / f"proof/{key}-{nn:02d}.txt").read_text()
        lines = raw.splitlines()
        kind = re.match(r"# \S+ \d+: (\S+)", lines[0]).group(1)
        items = [l.strip() for l in "\n".join(lines[1:]).split("\n") if l.strip()]
        # a map's title repeated as a line of text under it
        page_caps = [norm(m.group(3)) for m in map(PLATE.match, items) if m and m.group(3).strip()]
        for it in items:
            y = YEAR.search(it)
            if y:
                year = year or (y.group(1) or y.group(2))
            if IMPRINT.search(it):
                continue
            if not PLATE.match(it) and len(norm(it)) > 8 and any(norm(it) in c for c in page_caps):
                continue
            m = PLATE.match(it)
            if m:
                box = tuple(float(v) for v in m.group(1).split())
                if m.group(2) == "ornament":
                    continue
                pid = ids[(key, nn, box)]
                printed = CAPTION_SPLITS.get(pid, m.group(3).strip()).replace("*", "")
                assert "⟨cont⟩" not in printed, (pid, printed[-40:])
                blocks.append(("PLATE", pid, printed))
                continue
            y = YEAR.search(it)
            if y:
                year = year or (y.group(1) or y.group(2))
            if kind in FRONT_KINDS:
                plain = it.replace("*", "")
                if BYLINE.search(plain) and len(plain.split()) < 16:
                    byline.append(plain.strip())
                elif plain.startswith("Cover:"):
                    cover_caption = plain
                elif len(plain.split()) >= 15:
                    blocks.append(("P", it))
                continue
            if it.startswith("## "):
                h = it[3:].strip()
                if TITLE_HEADS.match(h.replace("*", "")):
                    continue
                blocks.append(("H", titlecase(h)))
                continue
            if it == "* * *":
                blocks.append(("HR",))
                continue
            blocks.append(("P", it))
    # join paragraphs across page breaks
    out = []
    for b in blocks:
        if b[0] == "P" and b[1].startswith("⟨cont⟩"):
            text = b[1][len("⟨cont⟩"):].strip()
            # the last paragraph left open -- a map's legend or a plate page
            # may stand between the two halves
            k = max(i for i, x in enumerate(out) if x[0] == "P" and x[1].endswith("⟨cont⟩"))
            prev = out[k][1]
            assert prev.endswith("⟨cont⟩"), (key, prev[-60:], text[:60])
            prev = prev[: -len("⟨cont⟩")].rstrip()
            joined = prev[:-1] + text if re.search(r"[A-Za-z]-$", prev) else prev + " " + text
            out[k] = ("P", joined)
            continue
        out.append(b)
    for b in out:
        assert not (b[0] == "P" and "⟨cont⟩" in b[1]), (key, b[1][-80:])
    # the byline, in the print's words
    head = []
    seen = set()
    for l in byline:
        l = re.sub(r"\s+", " ", l)
        if l.lower() not in seen:
            seen.add(l.lower())
            head.append(titlecase(l) if l.isupper() else l)
    by = BYLINES[key]          # the title page's own lines, in one order
    assert year and year in by, (key, year)
    cover = next((b[1] for b in out if b[0] == "PLATE" and re.fullmatch(r"[a-z]{2}01[a-z]", b[1])), None)
    return {"title": title, "byline": by, "blocks": out, "cover_caption": cover_caption, "cover_plate": cover}


def render(sec, caps, modern, slug):
    lines = [sec["title"], "", f"*{sec['byline']}*", ""]
    for b in sec["blocks"]:
        if b[0] == "PLATE":
            pid, printed = b[1], b[2]
            if not printed and sec["cover_caption"] and pid == sec["cover_plate"]:
                printed = sec["cover_caption"]
            desc = caps.get(pid, "")
            if modern:
                cap = " — ".join(x for x in (printed, desc) if x)
                lines.append(f"[Figure {slug[pid]}: {cap}]" if cap else f"[Figure {slug[pid]}]")
            else:
                lines.append(f"[Figure {slug[pid]}]")
        elif b[0] == "H":
            lines.append(b[1])
        elif b[0] == "HR":
            lines.append("* * *")
        else:
            lines.append(b[1])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ids, caps = plate_ids(), descriptions()
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest, nplates = [], 0
    secs = [booklet(key, pages, title, ids, caps) for key, pages, title in BOOKLETS]
    slug = slugs([b[1] for sec in secs for b in sec["blocks"] if b[0] == "PLATE"])
    place_images(slug, prune="--prune" in sys.argv)
    for i, ((key, pages, title), sec) in enumerate(zip(BOOKLETS, secs)):
        nplates += sum(b[0] == "PLATE" for b in sec["blocks"])
        (HERE / f"chapters/{i:03d}.txt").write_text(render(sec, caps, False, slug))
        (HERE / f"modern_chapters/{i:03d}.txt").write_text(render(sec, caps, True, slug))
        manifest.append({"file": f"{i:03d}.txt", "title": title, "part": 1, "of": 1})
        print(f"{title}: {sum(b[0]=='P' for b in sec['blocks'])} paragraphs; byline: {sec['byline']}")
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(nplates, "plates placed;", sum(1 for k in caps), "described")


if __name__ == "__main__":
    main()
