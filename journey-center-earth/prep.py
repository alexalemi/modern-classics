"""Build chapters/ + manifest.json for Verne's Voyage au centre de la
Terre from the Project Gutenberg French plain text (#4791).

Structure: 45 chapters, single part. Each chapter heading in the body is
a lone centered Roman numeral (I, II, ... XLV) with NO descriptive title
(Verne's original just numbers them). We drop the title page (everything
before the first lone-numeral heading), reflow the hard-wrapped
paragraphs, strip Gutenberg's underscore-italics, and emit ~3200-French-
word part files split at paragraph boundaries. Chapters are short
(~1,550 words avg), so most become single files. Manifest titles are
generated as "Chapter N" (the modern edition numbers them in English).

Ratio note for verify: French -> modern English narrative runs near 1:1;
run verify.py with --min-ratio 0.9 --max-ratio 1.5; tell agents NOT to pad.
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 3200
MAX = 4200

GUT_START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n")
GUT_END = re.compile(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG")
HEADING = re.compile(r"^[ \t]*([IVXLC]+)[ \t]*$")


def reflow(lines):
    paras, cur = [], []
    for ln in lines:
        s = ln.strip()
        if s:
            cur.append(s)
        elif cur:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(paras)


def split_body(body):
    paras = body.split("\n\n")
    total = sum(len(p.split()) for p in paras)
    if total <= MAX:
        return [body]
    nparts = max(2, round(total / TARGET))
    per = total / nparts
    parts, cur, curw = [], [], 0
    for p in paras:
        cur.append(p); curw += len(p.split())
        if curw >= per and len(parts) < nparts - 1:
            parts.append("\n\n".join(cur)); cur, curw = [], 0
    if cur:
        parts.append("\n\n".join(cur))
    return parts


def chapters_of(text):
    """Yield (roman, body) per chapter — a lone Roman numeral, then the
    body up to the next lone numeral. No titles in the source."""
    lines = text.split("\n")
    heads = [(i, HEADING.match(ln).group(1)) for i, ln in enumerate(lines)
             if HEADING.match(ln)]
    for k, (i, roman) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = reflow(lines[i + 1:end])
        body = re.sub(r"_", "", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        yield roman, body


def main():
    raw = BOOK.joinpath("source.txt").read_text(encoding="utf-8")
    raw = raw.replace("\r\n", "\n")
    m = GUT_START.search(raw)
    if m:
        raw = raw[m.end():]
    m = GUT_END.search(raw)
    if m:
        raw = raw[:m.start()]

    (BOOK / "chapters").mkdir(exist_ok=True)
    manifest, fileno, chap = [], 0, 0
    for roman, body in chapters_of(raw):
        chap += 1
        title = f"Chapter {chap}"
        parts = split_body(body)
        for pi, chunk in enumerate(parts, 1):
            out = [title]
            if len(parts) > 1:
                out.append(f"\n(Partie {pi} sur {len(parts)})")
            out.append("\n" + chunk)
            fn = f"{fileno:03d}.txt"
            (BOOK / "chapters" / fn).write_text("\n".join(out) + "\n",
                                                encoding="utf-8")
            manifest.append({"file": fn, "title": title, "roman": roman,
                             "part": pi, "of": len(parts),
                             "words": len(chunk.split())})
            fileno += 1
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    tot = sum(m["words"] for m in manifest)
    print(f"-> {fileno} files ({chap} chapters), {tot} French words")
    for m in manifest[:3] + manifest[-2:]:
        print(f"  {m['file']}  {m['roman']:<5} {m['title']:<12} "
              f"{m['part']}/{m['of']} {m['words']:>5}")


if __name__ == "__main__":
    main()
