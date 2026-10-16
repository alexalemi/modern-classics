"""Invariants of laws-of-thought that verify.py cannot see.

    python3 books/laws-of-thought/check.py            # chapters/
    python3 books/laws-of-thought/check.py --modern   # and modern_chapters/
    python3 books/laws-of-thought/check.py --render   # typeset every formula

Exits nonzero on any failure.

  - Chapters 1-22 in order, each file's first line its manifest title, part
    markers "(Part n of k)" on the second line of a multi-part file;
  - no TeX left in the prose (outside \\( \\) and \\[ \\]);
  - no paragraph that assemble.is_subheading would set as a heading;
  - Boole's articles: in each chapter the numbers at paragraph start climb
    1, 2, 3 ... with no gap (a page marker once ran article 18 into 17);
  - THE MATH IDENTITY CHECK (--modern): every formula in modern_chapters/NNN
    is byte-identical, and in the same order, to chapters/NNN. This is the
    book's real safety check: a retelling may rephrase every sentence around
    a formula and must not touch one character inside it. The equation
    numbers are inside the formulas, so they are covered too. Files with no
    modern counterpart are skipped (and counted).
  - --render: every formula through mathml.py (pandoc), with the cache in
    _src/ so the shared build/ cache is not touched.
"""
import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent.parent
sys.path.insert(0, str(ROOT))
import mathml  # noqa: E402
import assemble  # noqa: E402

MATH = mathml.MATH                       # the renderer's own pattern
ARTICLE = re.compile(r"(\d+)\. ")


def formulas(text):
    return [m.group(0) for m in MATH.finditer(text)]


def main():
    fails = []
    man = json.loads((BOOK / "manifest.json").read_text())
    chapters = [m["number"] for m in man if m.get("number") and m["part"] == 1]
    if chapters != list(range(1, 23)):
        fails.append(f"chapters out of order or missing: {chapters}")
    dirs = ["chapters"] + (["modern_chapters"] if "--modern" in sys.argv else [])
    skipped = 0
    for d in dirs:
        arts = {}
        for m in man:
            p = BOOK / d / m["file"]
            if not p.exists():
                if d == "modern_chapters":
                    skipped += 1
                    continue
                fails.append(f"{d}/{m['file']}: missing")
                continue
            t = p.read_text()
            lines = t.split("\n")
            want = "Dedication" if m.get("split_headings") else m["title"]
            if lines[0] != want:
                fails.append(f"{d}/{m['file']}: first line {lines[0]!r}, want {want!r}")
            if m["of"] > 1 and lines[1] != f"(Part {m['part']} of {m['of']})":
                fails.append(f"{d}/{m['file']}: part marker missing")
            if m["of"] == 1 and re.search(r"\(Part \d+ of \d+\)", t):
                fails.append(f"{d}/{m['file']}: stray part marker")
            # nor as a dialogue speaker: a lead-in word ("Therefore") opening
            # three multi-line paragraphs would be set as <b>Therefore</b>:
            sp = assemble.find_speakers([q for q in t.split("\n\n") if q.strip()])
            if sp:
                fails.append(f"{d}/{m['file']}: would render speakers {sorted(sp)}")
            # nothing in the body may read as a heading to the renderer
            # (a lead-in like "Hence we have" split from its display was)
            body = [q for q in t.split("\n\n")[1:] if q.strip() and not q.startswith("(Part ")]
            for q, nxt in zip(body, body[1:] + [None]):
                if q not in m.get("split_headings", []) and assemble.is_subheading(q.strip(), nxt):
                    fails.append(f"{d}/{m['file']}: would render as a heading: {q[:60]!r}")
            if d == "chapters":
                prose = MATH.sub(" ", t)
                for x in re.findall(r"\\[A-Za-z]+|[{}$%]|\x00|\x02|\x10", prose):
                    fails.append(f"{d}/{m['file']}: TeX left in prose {x!r}")
                if m.get("number"):
                    for par in t.split("\n\n"):
                        a = ARTICLE.match(par)
                        if a:
                            arts.setdefault(m["number"], []).append(int(a.group(1)))
        if d == "chapters":
            # Boole's own numbered lists (premises, definitions) restart at 1
            # inside an article, so the test is on the running maximum: the
            # article numbers must climb one at a time, never skip.
            for ch, ns in arts.items():
                top = 0
                for n in ns:
                    if n > top + 1:
                        fails.append(f"Chapter {ch}: article {n} follows {top}")
                    top = max(top, n)
    if "--modern" in sys.argv:
        compared = 0
        for m in man:
            src, mod = BOOK / "chapters" / m["file"], BOOK / "modern_chapters" / m["file"]
            if not mod.exists():
                continue
            a, b = formulas(src.read_text()), formulas(mod.read_text())
            compared += 1
            if a != b:
                for i, (x, y) in enumerate(zip(a, b)):
                    if x != y:
                        fails.append(f"MATH {m['file']}: formula {i + 1} differs:\n"
                                     f"    source {x[:160]!r}\n    modern {y[:160]!r}")
                        break
                else:
                    fails.append(f"MATH {m['file']}: {len(a)} formulas in source, {len(b)} in modern"
                                 f" (first {min(len(a), len(b))} agree)")
        print(f"math identity: {compared} file pair(s) compared, {skipped} without a modern file")
    if "--render" in sys.argv:
        mathml.CACHE = BOOK / "_src" / "mathml-cache.json"
        items = []
        for m in man:
            items += mathml.formulas((BOOK / "chapters" / m["file"]).read_text())
        bad = []
        for i in range(0, len(items), 200):
            try:
                mathml.convert_all(items[i:i + 200])
            except SystemExit:
                for it in items[i:i + 200]:
                    try:
                        mathml.convert_all([it])
                    except SystemExit:
                        bad.append(it[0])
        for b in bad:
            fails.append(f"RENDER: {b[:160]!r}")
        print(f"render: {len(items)} formulas, {len(set(items))} distinct, {len(bad)} failed")
    for f in fails:
        print("FAIL", f)
    print(f"check.py: {len(fails)} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
