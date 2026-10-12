"""Build chapters/ + manifest.json for Verne's Le Tour du monde en
quatre-vingts jours from the Project Gutenberg French plain text (#800).

Structure: 37 chapters, single part. In the body each chapter heading is
a centered lone Roman numeral line, then (after a blank) Verne's long
descriptive ALL-CAPS title, which may span several lines — distinct from
the table-of-contents entries. We drop the title page + TOC (everything
before the first lone-numeral chapter heading), reflow the hard-wrapped
paragraphs, strip Gutenberg's underscore-italics, and emit ~3200-French-
word part files split at paragraph boundaries (output — not input — is
the binding constraint for translation agents). Chapters here are short
(~1900 words avg), so most become single files. Manifest titles are the
FRENCH titles; the English chapter titles are decided at translation
time and specified per-agent.

Ratio note for verify: French -> modern English narrative runs near 1:1;
run verify.py with --min-ratio 0.9 --max-ratio 1.5 and tell agents NOT
to pad.
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
    """Yield (roman, french_title, body). Title = the consecutive
    non-blank lines after the lone numeral (Verne's long titles wrap)."""
    lines = text.split("\n")
    heads = [i for i, ln in enumerate(lines) if HEADING.match(ln)]
    # a chapter heading = a lone Roman numeral followed (after blanks) by
    # a non-empty title line. (Don't gate on isupper(): Verne's titles can
    # contain an italicized mixed-case proper noun, e.g. «Tankadère».)
    starts = []
    for i in heads:
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and lines[j].strip():
            starts.append((i, HEADING.match(lines[i]).group(1)))
    for k, (i, roman) in enumerate(starts):
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        title_lines = []
        while j < len(lines) and lines[j].strip():
            title_lines.append(lines[j].strip()); j += 1
        title = re.sub(r"_", "", " ".join(title_lines))
        title = " ".join(w.capitalize() if w.isupper() else w
                         for w in title.split())
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        body = reflow(lines[j:end])
        body = re.sub(r"_", "", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        yield roman, title, body


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
    manifest, fileno = [], 0
    for roman, title, body in chapters_of(raw):
        for pi, chunk in enumerate(split_body(body), 1):
            of = len(split_body(body))
            out = [title]
            if of > 1:
                out.append(f"\n(Partie {pi} sur {of})")
            out.append("\n" + chunk)
            fn = f"{fileno:03d}.txt"
            (BOOK / "chapters" / fn).write_text("\n".join(out) + "\n",
                                                encoding="utf-8")
            manifest.append({"file": fn, "title": title, "roman": roman,
                             "part": pi, "of": of,
                             "words": len(chunk.split())})
            fileno += 1
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    tot = sum(m["words"] for m in manifest)
    print(f"-> {fileno} files, {tot} French words")
    for m in manifest[:4] + manifest[-2:]:
        print(f"  {m['file']}  {m['roman']:<5} {m['title'][:44]:<44}"
              f" {m['part']}/{m['of']} {m['words']:>5}")


if __name__ == "__main__":
    main()
