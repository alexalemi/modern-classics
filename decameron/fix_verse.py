#!/usr/bin/env python3
"""Decameron repair (2026-10-10, from the ROADMAP audit of the MODEL=unknown
books). Repeatable: a second run changes nothing.

    python3 decameron/fix_verse.py

1. THE SONGS. Each day's canzone (and the snatches of song in 039 and 106)
   was written as a markdown "> " blockquote, which nothing in the pipeline
   reads: the page printed 394 literal "&gt; " lines run together in one
   paragraph. They are now set the way assemble.py renders verse (and
   boethius/ writes it): every line TAB-indented, stanzas separated by a
   blank line, so each stanza is its own lined block with its breaks kept.
2. THE LONG RUBRICS. Five story rubrics (053, 054, 055, 095, 108) showed
   their asterisks because assemble.EMPH caps an italic span at 400
   characters of escaped text and these run longer. Each is italicised
   sentence by sentence instead ("*One.* *Two.*"), every span under the cap, so they
   read like the other hundred-odd rubrics: all italic.
3. manifest.json, written from the files' own headings, with a divider
   before each Day and its introduction and stories grouped under it.
"""

import html
import json
import re
from pathlib import Path

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
CAP = 400          # assemble.EMPH's span limit, on ESCAPED text


def elen(s):
    """Length as EMPH sees it: it runs after html.escape, so every
    apostrophe counts six characters (&#x27;). 095's rubric is 387
    characters raw and over the cap escaped."""
    return len(html.escape(s))


DAYS = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh",
        "Eighth", "Ninth", "Tenth"]


def verse(text):
    out = []
    for line in text.split("\n"):
        if re.fullmatch(r">\s*", line):
            out.append("")                 # stanza break
        elif line.startswith("> "):
            out.append("\t" + line[2:].rstrip())
        else:
            out.append(line)
    return "\n".join(out)


SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“])")


def rubric(line):
    m = re.fullmatch(r"\*([^*]+)\*", line)
    if not m or elen(m.group(1)) < CAP:
        return line
    chunks, cur = [], ""
    for s in SENT.split(m.group(1)):
        if cur and elen(cur) + 1 + elen(s) >= CAP:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}" if cur else s
    chunks.append(cur)
    assert all(elen(c) < CAP for c in chunks), line
    return " ".join(f"*{c}*" for c in chunks)


def manifest():
    entries = []
    day = 0
    for p in sorted((BOOK / "modern_chapters").glob("[0-9][0-9][0-9].txt")):
        title = p.read_text().split("\n", 1)[0].strip()
        e = {"file": p.name, "title": title, "part": 1, "of": 1}
        m = re.match(r"Day (\d+)", title)
        if m:
            if int(m.group(1)) != day:
                day = int(m.group(1))
                e["part_before"] = f"The {DAYS[day - 1]} Day"
            e["chapter"] = True
        entries.append(e)
    return json.dumps(entries, indent=2, ensure_ascii=False) + "\n"


def main():
    changed = []
    for p in sorted((BOOK / "modern_chapters").glob("[0-9][0-9][0-9].txt")):
        old = p.read_text()
        new = verse(old)
        new = "\n".join(rubric(l) for l in new.split("\n"))
        if new != old:
            p.write_text(new)
            changed.append(p.name)
    mp = BOOK / "manifest.json"
    out = manifest()
    if not mp.exists() or mp.read_text() != out:
        mp.write_text(out)
        changed.append("manifest.json")
    print("changed: " + (", ".join(changed) if changed else "nothing"))


if __name__ == "__main__":
    main()
