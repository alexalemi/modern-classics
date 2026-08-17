#!/usr/bin/env python3
"""Recover Smith's wheat-price tables into modern_chapters/023.txt.

    python3 wealth-of-nations/tables.py            # print, do not write
    python3 wealth-of-nations/tables.py --write

WHAT WAS WRONG. File 023 is the conclusion of Book I chapter XI, and
Smith appends three tables of wheat prices to it -- roughly 1,900 words
of data in 342 rows. The prose was translated; the tables were not, and
they were not flagged either, because verify.py's word ratio was the
only thing that could see the loss and 0.44 looked like ordinary
summarisation of prose. It is not: the prose is complete and runs about
0.9. What is missing is all of the DATA.

WHY IT COULD NOT BE FIXED FROM chapters/. The old splitter flattened
the tables to one cell per line, so the column structure is gone and
the year a price belongs to is only recoverable by counting. Guessing
at the columns would have put wrong numbers in a published book, which
is worse than the gap.

WHY IT CAN BE FIXED NOW. The book's source is Standard Ebooks, not
Gutenberg, and SE's XHTML keeps the tables as real tables -- colgroup,
thead, colspan and all. So the columns are recoverable exactly. Nothing
here is inferred; every figure is read out of a cell.

THE ROWS ARE NOT ALL THE SAME SHAPE, and each irregularity is Smith's,
not the transcription's:
  - a year with SEVERAL recorded prices prints the extra prices on
    their own rows with no year, under the first group of columns;
  - the twelve-year blocks close with "Total" and "Average Price" rows
    that span the first seven columns;
  - the Windsor tables close each run with a long-division row
    ("64)129 13 6") and then the quotient.
Rendering these as ordinary rows would silently turn a divisor into a
price, so each is given its own shape.
"""
import argparse
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
TARGET = BOOK / "modern_chapters" / "023.txt"
SRC_URL = ("https://raw.githubusercontent.com/standardebooks/"
           "adam-smith_the-wealth-of-nations/master/src/epub/text/"
           "chapter-1-11.xhtml")
CACHE = BOOK / "source" / "chapter-1-11.xhtml"

X = "{http://www.w3.org/1999/xhtml}"
EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"

# Smith's own column headings, kept verbatim as a lead-in rather than
# stacked over the columns: they run to sixty characters and would make
# the block far too wide to read in a monospace <pre>.
LEAD_IN = {
    1: "The three pairs of money columns give, in Smith's own words, "
       "the price of the quarter of wheat each year; the average of the "
       "different prices of the same year; and the average price of "
       "each year in money of the present times. Where a year was "
       "recorded at several prices, the further prices follow on lines "
       "of their own.",
    2: "Prices of the quarter of nine bushels of the best or highest "
       "priced wheat at Windsor Market, on Lady-Day and Michaelmas, "
       "from 1595 to 1764, both inclusive; the price of each year being "
       "the medium between the highest and lowest prices of those two "
       "market days.",
    3: "The same, for the years 1731 to 1750.",
}


# A CELL THE EDITOR IDENTIFIES AS CORRUPT, corrected with the assertion
# that keeps a correction honest (the candle/ pattern): if the garbled
# form ever leaves the source, the build stops rather than silently
# applying nothing.
#
# Standard Ebooks' endnote 668 on the last cell of the Windsor table
# reads, in full, "This should be 9/32." The transcription carries
# "6⅓⁸⁄₂", which is not a quantity at all. This is a printing defect the
# editor has identified, not a figure of Smith's, so the Verne rule does
# not protect it -- the same ground as correcting "Denionax" to Demonax
# in epictetus/. Every OTHER oddity in these tables stands: the divisor
# "64)" over 170 years is Smith's own arithmetic and is left exactly as
# he printed it.
SOURCE_FIXES = [("6⅓⁸⁄₂", "6⁹⁄₃₂")]


def apply_fixes(text):
    for bad, good in SOURCE_FIXES:
        if bad not in text:
            raise SystemExit(f"source fix no longer matches: {bad!r}")
        text = text.replace(bad, good)
    return text


def fetch():
    CACHE.parent.mkdir(exist_ok=True)
    if not CACHE.exists():
        with urllib.request.urlopen(SRC_URL, timeout=90) as r:
            CACHE.write_bytes(r.read())
    return apply_fixes(CACHE.read_text())


def strip_noterefs(root):
    """Remove noteref anchors as ELEMENTS, giving each tail to the
    element that actually preceded it. Appending the tail to the
    parent's LAST child instead relocates text, which is how a clause
    moved to the end of a paragraph in epictetus/."""
    for parent in root.iter():
        i = 0
        while i < len(parent):
            el = parent[i]
            if el.tag == X + "a" and el.get(EPUB_TYPE) == "noteref":
                tail = el.tail or ""
                del parent[i]
                if i:
                    parent[i - 1].tail = (parent[i - 1].tail or "") + tail
                else:
                    parent.text = (parent.text or "") + tail
            else:
                i += 1


def cells(tr):
    out = []
    for c in tr:
        if c.tag in (X + "td", X + "th"):
            txt = re.sub(r"\s+", " ", "".join(c.itertext())).strip()
            out.append((txt, int(c.get("colspan", 1))))
    return out


YEAR = re.compile(r"^1[2-7]\d\d$")


def classify(r, groups):
    """Every row gets a kind, and an unrecognised shape RAISES.

    Silently dropping a row it did not understand is exactly how a
    table loses a price, and a lost price is invisible to every check
    this project has -- the word ratio moves by three tokens."""
    texts = [t for t, _ in r]
    n = 1 + 3 * groups
    if r and r[0][1] > 1:                       # "Total" / "Average Price"
        return "label", texts
    if len(texts) == n and YEAR.match(texts[0]):
        return "year", texts
    if len(texts) == 3 and groups == 3:         # further price, same year
        return "more", texts
    if len(texts) == n and texts[0] == "":      # long division / quotient
        return "sum", texts
    if set(texts) <= {"", "£", "s.", "d.", "Years", "Years XII",
                      "Wheat per quarter",
                      "Price of the quarter of wheat each year",
                      "Average of the different prices of the same year",
                      "The average price of each year in money of the "
                      "present times"}:
        return "head", texts                    # carried by LEAD_IN instead
    raise SystemExit(f"unrecognised row shape: {r}")


# 14, not 12: "Average Price" is thirteen characters and at 12 it
# pushed its own money columns one place right, out of line with
# every year above it.
W_YEAR, W_L, W_S, W_D = 14, 4, 4, 6


def money_cols(vals, groups):
    out = ""
    for g in range(groups):
        l, s, d = vals[3 * g:3 * g + 3]
        out += f"{l:>{W_L}}{s:>{W_S}}{d:>{W_D}}"
        if g < groups - 1:
            out += "   "
    return out


def render(rows, groups):
    """One table -> tab-indentable lines, columns aligned for <pre>.

    The figures are never reformatted: "2 0 6\u2153" is a measured value and
    its fractions are part of it (the fleming rule about computed
    tables)."""
    lines = []
    for r in rows:
        kind, texts = classify(r, groups)
        if kind == "head":
            continue
        if kind == "label":
            lines.append(f"{texts[0]:<{W_YEAR}}"
                         + money_cols(texts[1:], 1))
        elif kind == "year":
            lines.append((f"{texts[0]:<{W_YEAR}}"
                          + money_cols(texts[1:], groups)).rstrip())
        elif kind == "more":
            lines.append((" " * W_YEAR + money_cols(texts, 1)).rstrip())
        elif kind == "sum":
            lines.append((" " * W_YEAR
                          + money_cols(texts[1:], groups)).rstrip())
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    root = ET.fromstring(fetch())
    strip_noterefs(root)
    tables = list(root.iter(X + "table"))
    assert len(tables) == 3, f"expected 3 tables, found {len(tables)}"

    blocks = []
    for n, tb in enumerate(tables, 1):
        rows = [cells(tr) for tr in tb.iter(X + "tr")]
        groups = 3 if n == 1 else 1
        label = ("Years" + " " * 9
                 + "   ".join(f"{'£':>4}{'s.':>4}{'d.':>6}"
                              for _ in range(groups)))
        data = render(rows, groups)
        # EVERY NON-HEADER ROW MUST SURVIVE. Counting them is the only
        # guard against a shape that classify() quietly skips.
        want = sum(1 for r in rows if classify(r, groups)[0] != "head")
        assert len(data) == want, f"table {n}: {want} rows in, {len(data)} out"
        lines = [label] + data
        blocks.append((n, lines))

    out = []
    for n, lines in blocks:
        out.append(LEAD_IN[n])
        out.append("\n".join("\t" + l for l in lines))
    text = "\n\n".join(out)

    if args.write:
        cur = TARGET.read_text().rstrip("\n")
        assert "Years" not in cur, "tables already present"
        TARGET.write_text(cur + "\n\n" + text + "\n")
        print(f"appended {sum(len(l) for _, l in blocks)} lines to {TARGET}")
    else:
        print(text[:1800])
        print("\n   ...\n")
        print(text[-900:])


if __name__ == "__main__":
    main()
