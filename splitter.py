"""Split a source text into chapter files plus a manifest.

Two modes:

  Heading regex (preferred):
      python3 splitter.py book/source.txt --headings '^CHAPTER [IVXL]+\\..*$'
  Each regex match (multiline) starts a new chapter; the matched line(s)
  become the chapter title.

  Splits file (legacy):
      python3 splitter.py book/source.txt book/splits.txt
  Each line of the splits file is a literal string that starts a new chapter.

In both modes the tool:
  - strips the Project Gutenberg header/footer if present
  - saves any text before the first heading to preamble.txt (it is NOT
    silently written as chapter 0 — decide explicitly what to do with it)
  - splits chapters longer than --max-words into parts of roughly
    --target-words each, cut at paragraph boundaries
  - writes chapters/NNN.txt (first line = title, then "(PART n OF k)" for
    split chapters) and manifest.json

manifest.json entries: {"file", "title", "part", "of", "words"}. The
manifest drives both translation orchestration and assemble.py. Optional
fields you can add by hand afterward:
  - "part_before": a part/book divider heading to emit before this chapter
    (e.g. "Part II: Of Commonwealth")
  - "split_headings": list of standalone heading lines that divide this
    file into multiple sections (e.g. a front-matter file holding both a
    dedication and an introduction)
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

GUTENBERG_START = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*\n")
GUTENBERG_END = re.compile(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG")


def strip_gutenberg(text):
    m = GUTENBERG_START.search(text)
    if m:
        text = text[m.end():]
    m = GUTENBERG_END.search(text)
    if m:
        text = text[:m.start()]
    return text


def split_paragraphs(body, nparts):
    """Cut body into nparts roughly equal pieces at paragraph boundaries."""
    paras = body.split("\n\n")
    total = sum(len(p.split()) for p in paras)
    target = total / nparts
    parts, cur, curw = [], [], 0
    for p in paras:
        cur.append(p)
        curw += len(p.split())
        if curw >= target and len(parts) < nparts - 1:
            parts.append("\n\n".join(cur))
            cur, curw = [], 0
    parts.append("\n\n".join(cur))
    return parts


def sections_from_headings(text, pattern):
    pat = re.compile(pattern, re.M)
    matches = list(pat.finditer(text))
    if not matches:
        sys.exit(f"ERROR: heading pattern matched nothing: {pattern}")
    preamble = text[:matches[0].start()].strip()
    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = " ".join(m.group(0).split())
        sections.append((title, text[m.end():end].strip()))
    return preamble, sections


def sections_from_splits(text, splits):
    idx = text.find(splits[0])
    if idx < 0:
        sys.exit(f"ERROR: split string not found: {splits[0]!r}")
    preamble = text[:idx].strip()
    sections = []
    for i, s in enumerate(splits):
        start = text.find(s)
        if start < 0:
            sys.exit(f"ERROR: split string not found: {s!r}")
        end = text.find(splits[i + 1]) if i + 1 < len(splits) else len(text)
        title = " ".join(s.split())
        sections.append((title, text[start + len(s):end].strip()))
    return preamble, sections


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="source text file; output goes next to it")
    ap.add_argument("splits_file", nargs="?",
                    help="legacy mode: file of literal split strings, one per line")
    ap.add_argument("--headings", help="regex (multiline) matching chapter heading lines")
    ap.add_argument("--max-words", type=int, default=7000,
                    help="chapters above this are split into parts (default 7000)")
    ap.add_argument("--target-words", type=int, default=6000,
                    help="approximate words per part when splitting (default 6000)")
    ap.add_argument("--keep-gutenberg", action="store_true",
                    help="do not strip the Project Gutenberg header/footer")
    args = ap.parse_args()

    if bool(args.headings) == bool(args.splits_file):
        sys.exit("ERROR: provide exactly one of --headings or a splits file.")

    src = Path(args.source)
    book_dir = src.parent
    out_dir = book_dir / "chapters"
    out_dir.mkdir(parents=True, exist_ok=True)

    text = src.read_text()
    if not args.keep_gutenberg:
        text = strip_gutenberg(text)

    if args.headings:
        preamble, sections = sections_from_headings(text, args.headings)
    else:
        splits = [l.rstrip("\n") for l in Path(args.splits_file).read_text().splitlines()
                  if l.strip()]
        preamble, sections = sections_from_splits(text, splits)

    if preamble:
        (book_dir / "preamble.txt").write_text(preamble + "\n")
        print(f"NOTE: {len(preamble.split())} words before the first heading "
              f"saved to preamble.txt — fold them into a chapter or drop them.")

    manifest = []
    n = 0
    for title, body in sections:
        words = len(body.split())
        if words > args.max_words:
            k = math.ceil(words / args.target_words)
            for j, part in enumerate(split_paragraphs(body, k), 1):
                fn = f"{n:03d}.txt"
                (out_dir / fn).write_text(f"{title}\n(PART {j} OF {k})\n\n{part}\n")
                manifest.append({"file": fn, "title": title, "part": j, "of": k,
                                 "words": len(part.split())})
                n += 1
        else:
            fn = f"{n:03d}.txt"
            (out_dir / fn).write_text(f"{title}\n\n{body}\n")
            manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                             "words": words})
            n += 1

    (book_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{n} chapter files written to {out_dir}/")
    for m in manifest:
        tag = f" [{m['part']}/{m['of']}]" if m["of"] > 1 else ""
        print(f"{m['file']} {m['words']:6d}w  {m['title'][:60]}{tag}")


if __name__ == "__main__":
    main()
