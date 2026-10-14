"""Invariants of jevons-logic/chapters that verify.py cannot see.

    python3 books/jevons-logic/check.py            # source chapters/
    python3 books/jevons-logic/check.py --modern   # modern_chapters/ too

Exits nonzero on any failure.
  - 33 lessons in order, each file's first line its manifest title;
  - every question set landed: each lesson carries "Questions and
    Exercises" except 20 and 28 (their sets are grouped at 21 and 29);
    the four group subheadings sit where prep put them;
  - every [Figure id] has its image, and every image is used, once;
  - no page furniture survived (running heads, page-number lines,
    "[less.", "LKSSON");
  - no prose paragraph opens in lower case (a page-turn split).
"""
import json
import re
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parent
IMG = BOOK.parent.parent / "site" / "images" / "jevons-logic"
SUBS = {10: ["Questions and Exercises", "Examples of Propositions"],
        20: [],
        21: ["Questions on Fallacies", "Miscellaneous Examples"],
        28: [],
        29: ["Questions on the Methods of Induction"]}
FURNITURE = re.compile(r"\[l\.?ess|\bLESS\b|LKSSON|QUESTIONS AND EXERCISES|^\s*\d{1,3}\s*$|"
                       r"^[IVXL]+\.\]", re.M)
FIG = re.compile(r"\[Figure ([A-Za-z0-9_-]+)")


def main():
    fails = []
    man = json.loads((BOOK / "manifest.json").read_text())
    dirs = ["chapters"] + (["modern_chapters"] if "--modern" in sys.argv else [])
    lessons = [m["lesson"] for m in man if m.get("lesson") and m["part"] == 1]
    if lessons != list(range(1, 34)):
        fails.append(f"lessons out of order or missing: {lessons}")
    for d in dirs:
        seen = []
        for m in man:
            t = (BOOK / d / m["file"]).read_text()
            if d == "chapters" and t.split("\n", 1)[0] != m["title"]:
                fails.append(f"{d}/{m['file']}: first line is not {m['title']!r}")
            if m["of"] > 1 and f"(Part {m['part']} of {m['of']})" not in t.split("\n\n")[1]:
                fails.append(f"{d}/{m['file']}: part marker missing")
            for f in FURNITURE.finditer(t):
                fails.append(f"{d}/{m['file']}: furniture {f.group(0)!r}")
            paras = t.split("\n\n")
            for prev, p in zip(paras, paras[1:]):
                # a sentence may run on after a display, a plate or a note;
                # Jevons's italic letters s, p, m, k open their own lines
                if (p[:1].islower() and not prev.startswith(("\t", "[Figure", "Footnote:", "\\["))
                        and not re.match(r"[spmk] (indicates|denotes)", p)):
                    fails.append(f"{d}/{m['file']}: lower-case paragraph {p[:40]!r}")
            seen += FIG.findall(t)
            n = m.get("lesson")
            if d == "chapters" and n:
                want = SUBS.get(n, ["Questions and Exercises"])
                have = [p for p in paras if p in ("Questions and Exercises", "Examples of Propositions",
                                                  "Questions on Fallacies", "Miscellaneous Examples",
                                                  "Questions on the Methods of Induction")]
                if have != want:
                    fails.append(f"Lesson {n}: question subheadings {have}, want {want}")
        imgs = {p.stem[3:] for p in IMG.glob("fig*.png")}
        dup = {s for s in seen if seen.count(s) > 1}
        if dup:
            fails.append(f"{d}: figure markers used twice: {sorted(dup)}")
        if set(seen) != imgs:
            fails.append(f"{d}: markers without image {sorted(set(seen) - imgs)}, "
                         f"images without marker {sorted(imgs - set(seen))}")
    for f in fails:
        print("FAIL", f)
    print(f"check.py: {len(fails)} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
