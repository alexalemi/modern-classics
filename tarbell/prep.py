"""Harlan Tarbell, The Tarbell Course in Magic, Revised Edition, Volume II
(Lessons 20 to 33), Louis Tannen, 1942: a RESTORED EDITION.

    python3 tarbell/draft.py && python3 tarbell/apply_fixes.py \
        && python3 tarbell/plates.py && python3 tarbell/prep.py

US public domain: registered A168896 (1942), never renewed -- see
COPYRIGHT.txt for the search of the 1969-71 renewal catalogues.

Words: one open scan (Archive.org tarbellcourseinm0000unse, a later N. L.
Magic Company printing of the 1942 text), its hOCR drafted per leaf
(draft.py) and corrected by page readers against the page image as
patches (page_prompt.txt; fixes/ -> apply_fixes.py -> proof/). The same
readers boxed and described every drawing (figs/), which plates.py cuts.

Composition: a paragraph broken across a page (the readers' ⟨cont⟩) is
joined; each lesson is a section; each "[FIG n]" in a proof is matched,
in order, to that leaf's figs line (Tarbell restarts his numbering with
each trick, so a figure is known by its leaf, not its number) and given a
letters-only id in reading order. The caption is Tarbell's number, then
the reader's description. Kept: the dedication, Tarbell's introduction,
the fourteen lessons, his rabbit tailpieces. Dropped: the title and
copyright pages, the contents, and the decorative rules.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}
FIRST, LAST = 11, 413          # 414: the publisher's advertisement for Volume 1
SKIP = {11, 12, 13, 14, 15, 16}     # the dedication is set below; 13-15 the contents
FIG = re.compile(r"^\[FIG ([^\]]+)\]$")
ORNAMENT = re.compile(r"\b(rule|ornament|flourish|border|emblem|monogram|decorative line)\b", re.I)
ABC = "abcdefghijklmnopqrstuvwxyz"


def is_word(k):
    k = k.lower()
    return k in DICT or k.rstrip("s") in DICT or k[:-2] in DICT or k[:-3] in DICT or k[:-1] in DICT


def join_break(a, b):
    m = re.search(r"([A-Za-z]+)-$", a)
    if m:
        w = re.match(r"[A-Za-z]+", b)
        if w and (is_word(m.group(1) + w.group(0)) or not (is_word(m.group(1)) and is_word(w.group(0)))):
            return a[:-1] + b
        return a + b
    return a + " " + b


def figlines(leaf):
    f = HERE / f"figs/{leaf:04d}.txt"
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        p = [x.strip() for x in line.split("|")]
        if len(p) >= 3 and p[0].lower() != "none":
            out.append({"label": p[0], "desc": "|".join(p[2:]).strip()})
    return out


def norm_label(s):
    s = s.lower().replace("figs.", "").replace("fig.", "").replace("fig", "").strip()
    return re.sub(r"\s+", "", s)


def italics(t):
    """Two italic spans meeting at a page join ("on the* *receiver") are one
    span; a span longer than the renderers' 400-character emphasis limit is
    italicised sentence by sentence, so no asterisk survives on the page."""
    t = re.sub(r"\*\s+\*", " ", t)

    def split(m):
        body = m.group(1)
        if len(body) < 380:
            return m.group(0)
        parts = re.split(r"(?<=[.!?”])\s+", body)
        return " ".join(f"*{x}*" for x in parts if x)
    return re.sub(r"\*([^*]+)\*", split, t)


def stream():
    """(leaf, kind, text) over the proofs; kind H, P, FIG."""
    files = {r["file"]: r for r in json.loads((HERE / "figures.json").read_text())}
    out, problems = [], []
    for leaf in range(FIRST, LAST + 1):
        if leaf in SKIP:
            continue
        f = HERE / f"proof/{leaf:04d}.txt"
        if not f.exists():
            continue
        figs = figlines(leaf)
        k = 0
        for p in re.split(r"\n\s*\n", f.read_text()):
            p = p.strip()
            if not p or p.startswith("# leaf"):
                continue
            m = FIG.match(p)
            if m:
                if k >= len(figs):
                    problems.append(f"leaf {leaf}: [FIG {m.group(1)}] has no figs line")
                    continue
                fl = figs[k]
                if norm_label(fl["label"]) != norm_label(m.group(1)):
                    problems.append(f"leaf {leaf}: [FIG {m.group(1)}] vs figs line {fl['label']!r}")
                fname = f"p{leaf:04d}{ABC[k]}.jpg"
                assert fname in files, fname
                out.append((leaf, "FIG", {"file": fname, "label": fl["label"], "desc": fl["desc"]}))
                k += 1
                continue
            if p.startswith("## "):
                out.append((leaf, "H", p[3:].strip()))
                continue
            out.append((leaf, "P", " ".join(p.split())))
        if k != len(figs):
            problems.append(f"leaf {leaf}: {len(figs)} figs lines, {k} markers")
    return out, problems


def compose():
    items, problems = stream()
    secs = [{"title": "Dedication", "items": [("P", "*To my wife, Martha Beck Tarbell*")]}]
    cur = None
    for leaf, kind, x in items:
        if kind == "H":
            m = re.match(r"Lesson (\d+)\s*[:.—-]\s*(.+)", x)
            if m:
                cur = {"title": f"Lesson {m.group(1)}: {m.group(2).strip()}", "items": []}
                secs.append(cur)
                continue
            if x.lower() == "au revoir":
                cur = {"title": "Au Revoir", "items": []}
                secs.append(cur)
                continue
            if x.lower() == "introduction" and leaf < 25:
                cur = {"title": "Introduction", "items": []}
                secs.append(cur)
                continue
        if cur is None:
            cur = {"title": "Dedication", "items": []}
            secs.append(cur)
        it = cur["items"]
        if kind == "P" and x.startswith("⟨cont⟩"):
            text = x[len("⟨cont⟩"):].strip()
            open_ = [i for i, y in enumerate(it) if y[0] == "P" and y[1].endswith("⟨cont⟩")]
            if not open_:
                open_ = [i for i, y in enumerate(it) if y[0] == "P"]
                problems.append(f"leaf {leaf}: ⟨cont⟩ with no open paragraph")
            if open_:
                i = max(open_)
                it[i] = ("P", join_break(it[i][1].replace("⟨cont⟩", "").rstrip(), text))
                continue
        it.append((kind, x))
    for s in secs:
        s["items"] = [(k, italics(x.replace("⟨cont⟩", "").strip()) if k == "P" else x) for k, x in s["items"]]
    return secs, problems


def main():
    secs, problems = compose()
    for p in problems:
        print("  ", p, file=sys.stderr)
    order = [x["file"] for s in secs for k, x in s["items"]
             if k == "FIG" and not (x["label"].lower().startswith("unnumber") and ORNAMENT.search(x["desc"]))]
    ids = {f: ABC[i // 676] + ABC[i // 26 % 26] + ABC[i % 26] for i, f in enumerate(order)}
    out = HERE.parent / "site/images/tarbell"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("fig*.jpg"):
        f.unlink()
    import shutil
    for f, i in ids.items():
        shutil.copyfile(HERE / "plates" / f, out / f"fig{i}.jpg")
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    for n, s in enumerate(secs):
        src, mod = [s["title"], ""], [s["title"], ""]
        for k, x in s["items"]:
            if k == "FIG":
                if x["file"] not in ids:
                    continue
                i = ids[x["file"]]
                lab = x["label"]
                printed = "" if lab.lower().startswith("unnumber") else lab.rstrip(".") + "."
                cap = " — ".join(y for y in (printed, x["desc"]) if y)
                src.append(f"[Figure {i}]")
                mod.append(f"[Figure {i}: {cap}]")
            else:
                src.append(x)
                mod.append(x)
            src.append("")
            mod.append("")
        (HERE / f"chapters/{n:03d}.txt").write_text("\n".join(src).rstrip() + "\n")
        (HERE / f"modern_chapters/{n:03d}.txt").write_text("\n".join(mod).rstrip() + "\n")
        manifest.append({"file": f"{n:03d}.txt", "title": s["title"], "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(len(secs), "sections;", len(ids), "drawings;", len(problems), "problems")
    print([s["title"] for s in secs])


if __name__ == "__main__":
    main()
