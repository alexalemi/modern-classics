"""Checks for the Common Law retelling. Exits nonzero on any failure.

    python3 common-law/check.py [NNN ...]

verify.py cannot see what matters here, because the retelling is meant to
DROP most footnotes: its word ratio mixes Holmes's 833 notes into the
count. So this measures:
  1. heading and part line exactly as the manifest gives them;
  2. the BODY word ratio, footnote paragraphs excluded on both sides,
     within 0.85-1.25 (silent summarising is the project's worst defect);
  3. a FLOOR on kept footnotes: at least as many "Footnote:" paragraphs as
     the source has notes prep.py scored substantive (footnotes.json), and
     never more than the source has notes at all;
  4. no citation apparatus leaked into the retelling (Y.B., fol., pl.,
     reporter volume-and-page), no "--", no ALL-CAPS line;
  5. every line the renderer would set as a heading, asked of
     assemble.is_subheading itself (the epictetus rule: mirror the renderer).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import assemble  # noqa: E402

CITATION = re.compile(r"\bY\. ?B\.|\bfol\. \d|\bpl\. \d|\b\d+ (?:Q\.B|C\.B|Exch|Mass|H\. ?L|Mod|East|Bing)\b|\bIbid\b|\bet seq\b")
HEADINGS_OK = {"Successions Inter Vivos"}


def body_words(text):
    pars = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    return sum(len(p.split()) for p in pars[1:] if not p.startswith("Footnote:") and not p.startswith("(Part "))


def main(argv):
    manifest = json.loads((HERE / "manifest.json").read_text())
    meta = json.loads((HERE / "footnotes.json").read_text())
    only = set(argv[1:])
    fails = 0
    for e in manifest:
        n = e["file"][:3]
        if only and n not in only:
            continue
        mod = HERE / "modern_chapters" / e["file"]
        if not mod.exists():
            continue
        src = (HERE / "chapters" / e["file"]).read_text()
        t = mod.read_text()
        lines = t.split("\n")
        probs = []
        if lines[0] != e["title"]:
            probs.append(f"heading {lines[0]!r} != {e['title']!r}")
        if e["of"] > 1 and lines[1] != f"(Part {e['part']} of {e['of']})":
            probs.append(f"part line {lines[1]!r}")
        r = body_words(t) / max(1, body_words(src))
        if not 0.85 <= r <= 1.25:
            probs.append(f"body ratio {r:.2f}")
        kept = sum(1 for p in re.split(r"\n\s*\n", t) if p.startswith("Footnote:"))
        floor = sum(x["substantive"] for x in meta[e["file"]])
        total = len(meta[e["file"]])
        if kept < floor or kept > total:
            probs.append(f"footnotes kept {kept}, floor {floor}, source {total}")
        for m in CITATION.finditer(t):
            probs.append(f"citation leaked: {t[max(0, m.start() - 30):m.end() + 20]!r}")
        if "--" in t:
            probs.append("double hyphen")
        pars = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
        for i, p in enumerate(pars[1:], 1):
            if p.startswith("(Part "):
                continue
            if re.fullmatch(r"[A-Z0-9 ,.;:'’—-]{6,}", p):
                probs.append(f"all-caps line {p[:50]!r}")
            nxt = pars[i + 1] if i + 1 < len(pars) else None
            if "\n" not in p and assemble.is_subheading(p, nxt) and p not in HEADINGS_OK:
                probs.append(f"renders as a heading: {p[:70]!r}")
        status = "ok" if not probs else "FAIL"
        print(f"{e['file']} ratio {r:.2f} notes {kept}/{floor}..{total} {status}")
        for pr in probs:
            print("   ", pr)
        fails += bool(probs)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main(sys.argv)
