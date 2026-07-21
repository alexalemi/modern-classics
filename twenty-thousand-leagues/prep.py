"""Build chapters/ + manifest.json for Verne's Vingt mille lieues sous
les mers from the Project Gutenberg French plain text (#5097).

Structure: two parts (Première Partie, 24 chapters; Deuxième Partie,
23 chapters). In the body each chapter heading is a centered lone Roman
numeral line, then (after a blank) a centered ALL-CAPS title line —
distinct from the table-of-contents entries, which put the title on the
same line as the numeral. We split the source at "FIN DE LA PREMIÈRE
PARTIE", drop each part's title page + TOC (everything before its first
lone-numeral chapter heading), reflow the hard-wrapped paragraphs, strip
Gutenberg's underscore-italics, and emit ~3400-French-word part files
split at paragraph boundaries (output — not input — is the binding
constraint for translation agents). Chapter numbers restart in Part Two;
the manifest carries a "part_before" divider on the first chapter of the
Deuxième Partie. Manifest titles are the FRENCH titles; the English
chapter titles are decided at translation time and specified per-agent.

Ratio note for verify: French -> modern English runs a bit expansive;
run verify.py with --min-ratio 0.9 --max-ratio 1.6 (French is terse;
Verne's long periodic sentences unpack).
"""

import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 3400          # French words per part file
MAX = 4200             # split chapters longer than this

GUT_START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n")
GUT_END = re.compile(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG")
HEADING = re.compile(r"^[ \t]{15,}([IVXLC]+)[ \t]*$")


def reflow(lines):
    """Join hard-wrapped lines into paragraphs (blank line = break)."""
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
    """Cut a body into ~TARGET-word parts at paragraph boundaries."""
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


def chapters_of(part_text):
    """Yield (roman, french_title, body) for each chapter in a part."""
    lines = part_text.split("\n")
    heads = [(i, m.group(1)) for i, ln in enumerate(lines)
             if (m := HEADING.match(ln))]
    for k, (i, roman) in enumerate(heads):
        # title = next non-blank line after the numeral
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        title = re.sub(r"_", "", lines[j]).strip()
        title = " ".join(w.capitalize() if w.isupper() else w
                         for w in title.split())
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = reflow(lines[j + 1:end])
        body = re.sub(r"_", "", body)                 # drop italic markers
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
    part1, part2 = re.split(r"FIN DE LA PREMIÈRE PARTIE", raw, maxsplit=1)

    (BOOK / "chapters").mkdir(exist_ok=True)
    manifest, fileno = [], 0
    for pnum, ptext in enumerate((part1, part2), 1):
        first_in_part = True
        for roman, title, body in chapters_of(ptext):
            parts = split_body(body)
            for pi, chunk in enumerate(parts, 1):
                out = [title]
                if len(parts) > 1:
                    out.append(f"\n(Partie {pi} sur {len(parts)})")
                out.append("\n" + chunk)
                fn = f"{fileno:03d}.txt"
                (BOOK / "chapters" / fn).write_text("\n".join(out) + "\n",
                                                    encoding="utf-8")
                entry = {"file": fn, "title": title, "roman": roman,
                         "part": pi, "of": len(parts),
                         "words": len(chunk.split())}
                if first_in_part and pnum == 2 and pi == 1:
                    entry["part_before"] = "Part Two"
                manifest.append(entry)
                first_in_part = False
                fileno += 1
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    tot = sum(m["words"] for m in manifest)
    print(f"-> {fileno} files, {tot} French words")
    for m in manifest[:4] + manifest[-3:]:
        pb = "  <part-divider>" if m.get("part_before") else ""
        print(f"  {m['file']}  {m['roman']:<6} {m['title'][:34]:<34}"
              f" {m['part']}/{m['of']} {m['words']:>5}{pb}")


if __name__ == "__main__":
    main()
