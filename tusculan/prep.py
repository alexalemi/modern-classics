"""Build chapters/ (Latin), reference/ (Yonge crib) + manifest.json for
the Tusculan Disputations.

Latin source: The Latin Library (tusc1.html … tusc5.html), one page per
book, sections numbered with flush arabic numerals — the standard
paragraph (§) citations. English crib: C. D. Yonge's translation from
Gutenberg #14988 (tusc_yonge.txt; the file also bundles On the Nature
of the Gods, which is cut).

Unlike De Officiis' Loeb parallel text, the two sources use different
division schemes (Latin §§ vs. Yonge's Roman-numeral chapters), so
there is no per-file alignment: reference/book-N.txt holds Yonge's
ENTIRE book N, and each translation agent locates its section span in
the crib. chapters/NNN.txt groups contiguous Latin sections into
~2800-word files (Section N headings kept — they are the standard
citation numbers), never crossing book boundaries.
"""

import html as H
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 2800

TITLES = {1: "On the Contempt of Death", 2: "On Bearing Pain",
          3: "On Grief of Mind", 4: "On the Other Disorders of the Mind",
          5: "Whether Virtue Alone Is Sufficient for a Happy Life"}
ROMAN = ["I", "II", "III", "IV", "V"]

# ---- Latin books --------------------------------------------------------
books = []
for n in range(1, 6):
    raw = BOOK.joinpath(f"tusc{n}.html").read_text(encoding="latin-1")
    # Two markups: books 3-5 anchor each section as [<a name="N">N</a>];
    # books 1-2 use plain inline numerals — which carry typos in the
    # source (31 printed as "14", 39 as "9"), so boundaries are taken by
    # POSITION and renumbered, with a >=90% agreement check.
    if re.search(r'name="\d+"', raw):
        body = re.sub(r'\[<a name="(\d+)">\d+</a>\s*\]', r"\n@@\1@@ ", raw,
                      flags=re.I)
        body = H.unescape(re.sub(r"<[^>]+>", "\n", body))
        marks = list(re.finditer(r"@@(\d+)@@", body))
    else:
        body = H.unescape(re.sub(r"<[^>]+>", "\n", raw))
        marks = list(re.finditer(r"(?:^|\s|(?<=[.!?;:]))(\d+)\s", body))
    agree = sum(1 for k, m2 in enumerate(marks) if int(m2.group(1)) == k + 1)
    assert agree >= 0.9 * len(marks), \
        f"book {n}: only {agree}/{len(marks)} numerals match position"
    cleaned = []
    for k, m2 in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(body)
        text = body[m2.end():end]
        text = re.sub(r"Cicero: Tusculan[^\n]*|The Latin Library[^\n]*"
                      r"|The Classics Page[^\n]*|M\. TVLLI[^\n]*", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        # the old chapter divisions ("XVI.") precede section numerals and
        # end up dangling at section boundaries — drop multi-letter Roman
        # numerals only (single letters like "C." are praenomens: C. Marius)
        text = re.sub(r"(?<![A-Za-z])[IVXLC]{2,7}\s?\.(?=\s|$)", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if int(m2.group(1)) != k + 1:
            print(f"  book {n}: numeral {m2.group(1)} at position {k + 1} "
                  f"renumbered")
        cleaned.append((k + 1, text))
    assert [s[0] for s in cleaned] == list(range(1, len(cleaned) + 1)), \
        f"book {n}: section sequence broke"
    books.append(cleaned)
    print(f"Latin book {n}: {len(cleaned)} sections, "
          f"{sum(len(t.split()) for _, t in cleaned)} words")

# ---- Yonge crib ---------------------------------------------------------
yonge = BOOK.joinpath("tusc_yonge.txt").read_text()
m = [x.start() for x in re.finditer(r"^BOOK [IV]+\.$", yonge, flags=re.M)]
# first five BOOK headings are the Tusculans; the sixth starts De Natura Deorum
bounds = m[:5] + [m[5]]
for n in range(5):
    seg = yonge[bounds[n]:bounds[n + 1]]
    seg = seg[:seg.rfind("*       *")] if "*       *" in seg else seg
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", seg) if p.strip()]
    BOOK.joinpath("reference", f"book-{n + 1}.txt").write_text(
        "\n\n".join(paras) + "\n")
    print(f"Yonge book {n + 1}: {sum(len(p.split()) for p in paras)} words")

# ---- group Latin sections into files ------------------------------------
manifest, file_no = [], 0
for bi, secs in enumerate(books, 1):
    title = f"Book {ROMAN[bi - 1]}: {TITLES[bi]}"
    total = sum(len(t.split()) for _, t in secs)
    per = total / max(1, round(total / TARGET))
    groups, cur, curw = [], [], 0
    for num, text in secs:
        w = len(text.split())
        if cur and curw + w > per * 1.15:
            groups.append(cur); cur, curw = [], 0
        cur.append((num, text)); curw += w
        if curw >= per:
            groups.append(cur); cur, curw = [], 0
    if cur:
        groups.append(cur)
    for part, group in enumerate(groups, 1):
        out = [title]
        if len(groups) > 1:
            out.append(f"\n(Part {part} of {len(groups)})")
        for num, text in group:
            out.append(f"\nSection {num}\n\n{text}")
        content = "\n".join(out) + "\n"
        fn = f"{file_no:03d}.txt"
        BOOK.joinpath("chapters", fn).write_text(content)
        manifest.append({"file": fn, "title": title, "part": part,
                         "of": len(groups),
                         "words": len(content.split()),
                         "sections": f"{group[0][0]}-{group[-1][0]}",
                         "book": bi})
        file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"-> {file_no} files")
for m2 in manifest:
    print(f"  {m2['file']}  Book {m2['book']} part {m2['part']}/{m2['of']}"
          f"  §{m2['sections']:<8} {m2['words']:>5}")
