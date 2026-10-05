"""Office of Strategic Services, Simple Sabotage Field Manual (17 January
1944) -> chapters/ and modern_chapters/ (a RESTORED EDITION).

    python3 sabotage/prep.py

A US government work, public domain. Text: Project Gutenberg #26184
(plain text), checked word by word against the OCR of a scan of the 1944
typescript (Archive.org SimpleSabotageFieldManualStrategicServicesProvisional)
with scan_diff.py; the readings it raised are settled in FIXES from the
page images.

Kept: Donovan's covering memorandum and the five numbered sections, with
their lettered and numbered outline as printed. Dropped: the cover, the
OSS reproduction-branch stamp lines and the Contents (the renderers make
one). Gutenberg's "_word_" italics are the typescript's underlining.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SECTIONS = ["Introduction", "Possible Effects", "Motivating the Saboteur",
            "Tools, Targets, and Timing", "Specific Suggestions for Simple Sabotage"]
# readings settled on the scan's page images (old, new)
FIXES = [
    ("(3) _Production. Metals_", "(3) _Production: Metals_"),   # p. 21, under the DECLASSIFIED stamp
]


USED = set()


def main():
    t = (HERE / "_src/pg26184.txt").read_text().replace("\r\n", "\n")
    t = t[t.find("*** START"):t.find("*** END")]
    t = t.split("\n", 1)[1]
    memo_start = t.find("This Simple Sabotage Field Manual")
    memo_end = t.find("CONTENTS")
    memo = t[memo_start:memo_end]
    first = t.find("1. INTRODUCTION", memo_end)          # the Contents' entry
    body = t[t.find("1. INTRODUCTION", first + 10):]       # the section itself
    parts = re.split(r"^([1-5])\. ([A-Z ,]+)\s*$", body, flags=re.M)
    assert len(parts) == 16, len(parts)     # 1 + 5 headings x (number, title, text)
    files = []

    def paras(s):
        out = []
        for p in re.split(r"\n\s*\n", s):
            p = " ".join(l.strip() for l in p.strip().splitlines())
            p = p.replace("[Illustration]", "").strip()
            if p:
                out.append(p)
        return out
    memo_paras = paras(memo)
    assert memo_paras[-1] == "William J. Donovan", memo_paras[-1]
    # the dateline and signature end on a stop: a short unpunctuated line
    # is set as a subheading (assemble.is_subheading)
    memo_paras[-1] = "—William J. Donovan."
    files.append(("Memorandum", ["Office of Strategic Services, Washington, D. C., 17 January 1944."] + memo_paras))
    for k in range(5):
        num, title, text = parts[1 + 3 * k], parts[2 + 3 * k], parts[3 + 3 * k]
        assert int(num) == k + 1 and title.strip().lower() == SECTIONS[k].lower(), (num, title)
        files.append((f"{num}. {SECTIONS[k]}", paras(text)))
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    for i, (title, ps) in enumerate(files):
        text = title + "\n\n" + "\n\n".join(ps) + "\n"
        for old, new in FIXES:
            if old in text:
                text = text.replace(old, new)
                USED.add(old)
        for d in ("chapters", "modern_chapters"):
            (HERE / d / f"{i:03d}.txt").write_text(text)
        manifest.append({"file": f"{i:03d}.txt", "title": title, "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    assert USED == {o for o, _ in FIXES}, "a FIX matched nothing"
    print(len(files), "sections,", sum(len(" ".join(p).split()) for _, p in files), "words")


if __name__ == "__main__":
    main()
