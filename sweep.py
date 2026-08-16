#!/usr/bin/env python3
"""Post-assembly sweep: the checks that only exist once a book is built.

    python3 sweep.py            # every assembled book
    python3 sweep.py grimm      # one book
    python3 sweep.py -v grimm   # also print what was inspected and passed

verify.py and a book's own check.py both compare the pipeline against
itself: source files against modern files, manifest against files. That
leaves one whole class of defect invisible, and Grimm shipped an example
of it — "The Twelve Idle Servants" is numbered 151* in the Grimms' own
sequence, prep's `\\d{1,3}` dropped the star, and the tale rode through
every stage inside its neighbour's file. The word ratio did not move (the
words were all present), and the manifest agreed with the files because
the heading was missing from both. It was found by counting headings in
the assembled HTML.

So this looks at the OUTPUT, and at the source's own evidence:

  A  section counts — manifest vs page headings vs table of contents
  B  headings that are really prose — the is_subheading failure mode
  C  markup that shipped literally — [Figure, **bold**, &lt;, _italic_
  D  epub images — present vs referenced, BOTH directions
  E  page images — every <img> resolves to a file on disk
  F  ORPHAN SOURCE HEADINGS — heading-shaped lines in chapters/ that no
     manifest section claims. This is the Grimm check, generalised: a
     section prep never recognised leaves its heading stranded in the
     source text. Runs only where the source headings and the manifest
     titles are the same strings (skipped for translated-title books like
     the Verne novels, where they cannot be compared).
  G  sections with (almost) no body

Nothing here is a hard gate — several checks are deliberately noisy in
the direction of showing you something to look at. Exit status is 1 if
anything was reported, so it can still fail a build.
"""
import argparse
import html as _html
import json
import re
import sys
import zipfile
from pathlib import Path

import assemble

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# a heading line in a source file: what assemble would call a subheading,
# plus the shapes a splitter emits ("12 The Turnip", "CHAPTER IV.")
NUM_PREFIX = re.compile(r"^\s*(\d{1,3}\*?|[IVXLC]{1,7})[.\s]\s*")
TAG = re.compile(r"<[^>]+>")


def text_of(fragment):
    return _html.unescape(TAG.sub("", fragment)).strip()


def page_headings(page, level):
    return [text_of(m) for m in
            re.findall(rf"<h{level}[^>]*>(.*?)</h{level}>", page, re.S)]


def looks_like_prose_heading(h):
    """A heading that is really a line of the book's body text.

    LENGTH AND PUNCTUATION ARE NOT ENOUGH, and calibrating this was most
    of the work. Real titles in this collection are routinely long ("Of
    the Origin and Design of Government in General, with Concise Remarks
    on the English Constitution") and routinely end in a full stop
    ("CHAPTER VIII."), so those tests alone produced 289 hits of which
    almost none were defects. What actually separates a title from a
    sentence is CASE: a heading is majority-capitalised, prose is not.
    """
    words = [w for w in re.findall(r"[A-Za-z][\w'’-]*", h)]
    if not words:
        return None
    caps = sum(1 for w in words if w[0].isupper()) / len(words)

    # narration plus speech — precise enough to stand on its own, and the
    # shape that hid from is_subheading because the terminal stop sits
    # inside the quotation marks
    if re.search(r"[,.]\s+[\"'“‘]", h) and h[-1] in "\"'”’":
        return "reported speech"
    if caps >= 0.4:
        return None
    if len(h) > 60:
        return f"long and sentence-case ({caps:.0%} capitalised)"
    if h[-1] in ".;:,":
        return f"ends in prose punctuation, sentence-case ({caps:.0%})"
    return None


def orphan_source_headings(book, manifest):
    """Heading-shaped lines in chapters/ that no manifest section claims.

    Only meaningful where the source and the manifest use the same title
    strings. Calibrated per book: if fewer than half the manifest titles
    can be found in chapters/ at all, the titles were translated and there
    is nothing to compare, so the check reports that it stood down.
    """
    src = book / "chapters"
    if not src.exists():
        return None, "no chapters/ (no source text kept)"

    wanted = set()
    for m in manifest:
        wanted.update(m.get("split_headings") or [m["title"]])
    wanted = {w for w in wanted if w}
    if not wanted:
        return None, "manifest carries no titles"

    lines = []
    for p in sorted(src.glob("*.txt")):
        lines.extend(p.read_text(errors="replace").split("\n"))
    stripped = {NUM_PREFIX.sub("", l).strip() for l in lines}
    found = {w for w in wanted if w in stripped}
    if len(found) < len(wanted) / 2:
        return None, (f"source headings do not match manifest titles "
                      f"({len(found)}/{len(wanted)} found) — translated "
                      f"titles, nothing to compare")

    # now look for heading-shaped lines that match nothing we know about
    numbered, bare_orphans = [], []
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line or line in wanted:
            continue
        bare = NUM_PREFIX.sub("", line).strip()
        if not bare or bare in wanted:
            continue
        # surrounded by blank lines, and shaped like a heading
        prev_blank = i == 0 or not lines[i - 1].strip()
        next_blank = i + 1 >= len(lines) or not lines[i + 1].strip()
        if not (prev_blank and next_blank):
            continue
        if not assemble.is_subheading(bare):
            continue
        # TWO GRADES, because they mean different things. A line that
        # carried a NUMBER and still matches no section is the Grimm
        # shape — the book numbered a section and the manifest has not
        # got it. A bare unclaimed line is far more often a legitimate
        # subheading inside a chapter (Hunt's "FIRST STORY", a recipe
        # name in soap-bubbles), so it is reported only in verbose mode.
        (numbered if bare != line else bare_orphans).append(line)
    return (numbered, bare_orphans), \
        f"{len(found)}/{len(wanted)} manifest titles found in source"


def epub_images(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    present = {n.rsplit("/", 1)[-1] for n in names
               if re.search(r"\.(jpg|jpeg|png|gif|svg)$", n, re.I)}
    used = set()
    for n in names:
        if n.endswith((".xhtml", ".opf", ".svg", ".css")):
            s = z.read(n).decode("utf8", "replace")
            for u in re.findall(
                    r'(?:src|href|xlink:href)="([^"]+\.(?:jpg|jpeg|png|gif|svg))"', s):
                used.add(u.rsplit("/", 1)[-1])
    return present, used


def sweep(book, verbose=False):
    name = book.name
    out = []
    note = []

    pages = [(SITE / f"{name}.html", False)]
    orig = SITE / f"{name}-original.html"
    if orig.exists():
        pages.append((orig, True))
    if not pages[0][0].exists():
        return [f"{name}: not assembled (no site/{name}.html)"], note

    manifest = assemble.load_manifest(book)
    sections = sum(len(m.get("split_headings") or [m["title"]])
                   for m in manifest if m["part"] == 1)

    for page_path, is_original in pages:
        tag = page_path.stem
        page = page_path.read_text()

        # A — counts
        h2 = page_headings(page, 2)
        toc = len(re.findall(r'<li><a href="#', page)) or \
            len(re.findall(r'href="#[a-z0-9-]', page))
        # the page's own <h2> title line is not a section
        body_h2 = [h for h in h2 if h]
        if abs(len(body_h2) - sections) > 1:
            out.append(f"{tag}: manifest has {sections} sections, page has "
                       f"{len(body_h2)} h2 — a section may be missing or doubled")
        if toc and abs(toc - sections) > 1:
            out.append(f"{tag}: {sections} manifest sections but {toc} "
                       f"table-of-contents links")
        note.append(f"{tag}: {sections} sections, {len(body_h2)} h2, {toc} toc links")

        # B — headings that are really prose. Only the BODY: the page's
        # own masthead carries the work's subtitle and the author line as
        # h3, and a subtitle is supposed to be a sentence.
        first = page.find('<h2 id=')
        body_only = page[first:] if first > 0 else page
        for level in (2, 3, 4):
            for h in page_headings(body_only, level):
                why = looks_like_prose_heading(h) if h else None
                if why:
                    out.append(f"{tag}: h{level} looks like body text "
                               f"({why}): {h[:72]!r}")

        # C — markup that shipped literally
        for pat, what in ((r"\[Figure\b", "unrendered figure marker"),
                          (r"\*\*\w", "markdown bold"),
                          (r"&lt;", "escaped angle bracket"),
                          (r"(?m)^\s*_[A-Z][^_\n]{2,40}_\s*$", "markdown italic line")):
            n = len(re.findall(pat, page))
            if n:
                out.append(f"{tag}: {n} x {what}")

        # E — every <img> resolves
        for src in re.findall(r'<img[^>]+src="([^"]+)"', page):
            if src.startswith(("http:", "https:", "data:")):
                continue
            if not (SITE / src).exists():
                out.append(f"{tag}: <img> points at a missing file: {src}")

        # G — near-empty sections
        for m in re.finditer(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|\Z)", page, re.S):
            head, body = text_of(m.group(1)), text_of(m.group(2))
            if head and len(body) < 40:
                out.append(f"{tag}: section {head[:50]!r} has almost no body "
                           f"({len(body)} chars)")

    # D — epub images, both directions
    for original in (False, True):
        ep = assemble.find_epub(book, ROOT, original=original)
        if not ep:
            continue
        path = SITE / "ebooks" / ep
        if not path.exists():
            out.append(f"{name}: manifest points at a missing epub: {ep}")
            continue
        present, used = epub_images(path)
        for x in sorted(present - used):
            out.append(f"{path.name}: image in the epub that nothing "
                       f"references: {x}")
        for x in sorted(used - present):
            out.append(f"{path.name}: image referenced but not present: {x}")
        note.append(f"{path.name}: {len(present)} images, all referenced"
                    if present == used else f"{path.name}: image mismatch")

    # F — orphan source headings
    orphans, why = orphan_source_headings(book, manifest)
    if orphans is None:
        note.append(f"{name}: orphan-heading check stood down — {why}")
    else:
        numbered, bare_orphans = orphans
        note.append(f"{name}: orphan-heading check ran — {why}; "
                    f"{len(numbered)} numbered, {len(bare_orphans)} bare")
        for o in numbered[:12]:
            out.append(f"{name}: NUMBERED heading in chapters/ that no "
                       f"manifest section claims: {o[:72]!r}")
        if len(numbered) > 12:
            out.append(f"{name}: ...and {len(numbered) - 12} more")
        if verbose:
            for o in bare_orphans[:12]:
                note.append(f"{name}: unclaimed heading-shaped line "
                            f"(usually a subheading): {o[:60]!r}")
    return out, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("books", nargs="*")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    if a.books:
        books = [ROOT / b.rstrip("/") for b in a.books]
    else:
        books = sorted(p for p in ROOT.iterdir()
                       if (p / "manifest.json").exists()
                       or (p / "modern_chapters").exists())

    total = 0
    for book in books:
        found, note = sweep(book, a.verbose)
        if a.verbose:
            for n in note:
                print(f"  . {n}")
        for f in found:
            print(f"  ! {f}")
        total += len(found)
    print(f"\n{len(books)} book(s) swept, {total} thing(s) to look at")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
