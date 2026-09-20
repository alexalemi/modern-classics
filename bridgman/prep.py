"""P. W. Bridgman, Dimensional Analysis (Yale, 1922): a RESTORED EDITION.

    python3 bridgman/prep.py

The text is bridgman/proof/NNN.txt, one file per leaf, READ FROM THE PAGE
IMAGE of Archive.org's dimensionalanaly00bridrich (the 1922 first printing,
University of California copy) by a proofreading pass whose instructions
are proof_instructions.txt. No transcription exists; the OCR was a word
draft only, and it destroys every formula. The formulas are typeset as
LaTeX, \\(...\\) and \\[...\\], which both renderers set (mathml.py).

Conventions the proof files carry, resolved here:
  "+ " continues the paragraph before it (a page turn); a word broken across
      the turn ("informa-" / "+ tion") is closed up.
  ^^Small Capitals^^ -> plain words (paper authors, a chapter's first word).
  "Footnote: ..." at the foot of a leaf -> set after the paragraph that
      cites it.
  CHAPTER N + its title -> one section, "Chapter N: Title".

WITNESSES, asserted: every chapter of the printed Contents, in order and
by title; the leaf's printed page runs 1-109 with no leaf missing; no markup
left over. The WORDS are then voted against two further scans
(scan_diff.py --vote), which share no keystrokes with the proofreading.

LEFT OUT, deliberately: the title page, copyright, the Contents (it is the
witness above, and the page numbers mean nothing in a reflowable edition),
and the two-page Index, which is page numbers and nothing else.
"""
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402
import mathml  # noqa: E402

PREFACE, CONTENTS = 10, 12
FIRST, LAST = 14, 122            # pp. 1-109

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def load(leaf):
    t = (HERE / "proof" / f"{leaf:03d}.txt").read_text()
    return [p.strip("\n") for p in re.split(r"\n\s*\n", t) if p.strip()]


def is_heading(p):
    letters = re.sub(r"[^A-Za-z]", "", mathml.MATH.sub("", p))
    # a heading may carry a formula ("THE \\(\\Pi\\) THEOREM"); a short line only
    return (len(letters) > 2 and letters == letters.upper() and not p.startswith(("\t", "+ ", "Footnote:"))
            and (not mathml.MATH.search(p) or len(p) < 60))


def join_broken(a, b, solid, hyph):
    head = a.split()[-1][:-1]
    tail = b.split()[0]
    w = re.sub(r"[^\w-]", "", head + tail)
    compound = f"{head}-{re.sub(r'[^A-Za-z-]', '', tail)}".lower()
    if compound in hyph and w.lower() not in solid:
        return a + b, compound
    return a[:-1] + b, None


def marks(p):
    """footnote reference marks a paragraph carries (outside formulas)"""
    t = mathml.MATH.sub(" ", p)
    return set(re.findall(r"[*†‡§]", R.assemble.EMPH.sub(" ", t)))


def main():
    leaves = [PREFACE] + list(range(FIRST, LAST + 1))
    missing = [l for l in leaves + [CONTENTS] if not (HERE / "proof" / f"{l:03d}.txt").exists()]
    assert not missing, f"no proof for leaves {missing}"
    raw = {l: load(l) for l in leaves}
    alltext = " ".join(p for ps in raw.values() for p in ps)
    solid = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", alltext))
    hyph = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]+-[A-Za-z]+\b", alltext))

    stream, kept_hyphen, notes = [], [], 0
    held = []
    for leaf in leaves:
        paras = [p for p in raw[leaf] if not p.startswith("Footnote: ")]
        pending = [p for p in raw[leaf] if p.startswith("Footnote: ")]
        notes += len(pending)
        for p in paras:
            if p.startswith("+ "):
                body = p[2:]
                prev = next(i for i in range(len(stream) - 1, -1, -1) if stream[i][0] in ("P", "BLOCK"))
                a = stream[prev][1]
                if a.endswith("-") and not a.endswith("--") and not a.endswith("\\]"):
                    joined, comp = join_broken(a, body, solid, hyph)
                    if comp:
                        kept_hyphen.append((leaf, comp))
                else:
                    joined = a + ("\n" if stream[prev][0] == "BLOCK" else " ") + body
                stream[prev] = (stream[prev][0], joined)
            else:
                stream.extend(held)
                held = []
                if p.startswith("\t"):
                    stream.append(("BLOCK", p))
                elif is_heading(p):
                    stream.append(("H", p))
                else:
                    stream.append(("P", p))
            # a footnote follows the paragraph that cites it
            for n in list(pending):
                sym = n[len("Footnote: "):][:1]
                if sym in marks(p):
                    held.append(("P", n))
                    pending.remove(n)
        assert not pending, f"leaf {leaf}: footnote with no reference mark: {pending}"
    stream.extend(held)

    # sections
    sections = [{"title": "Preface", "stream": []}]
    chapters = []
    it = iter(stream)
    first = True
    for kind, text in it:
        if first:
            assert (kind, text) == ("H", "PREFACE"), (kind, text)
            first = False
            continue
        if kind == "H":
            m = re.fullmatch(r"CHAPTER ([IVX]+)\.?", text)
            if m:
                k2, title = next(it)
                assert k2 == "H", (text, title)
                # the Pi of the Pi theorem is set as the character in a title
                t = R.titlecase(title.replace("\\(\\Pi\\)", "Π").rstrip(".").lower())
                chapters.append((m.group(1), t))
                sections.append({"title": f"Chapter {m.group(1)}: {t}", "stream": [], "chapter": True})
            elif text.rstrip(".") == "PROBLEMS":
                sections.append({"title": "Problems", "stream": []})
            else:
                h = R.titlecase(text.rstrip(".").lower())
                # titlecase lower-cases a Roman numeral's tail ("Chapter Ii")
                h = re.sub(r"\b[IVX][ivx]+\b", lambda m: m.group(0).upper(), h)
                sections[-1]["stream"].append(("P", h))
            continue
        t = re.sub(r"\^\^(.+?)\^\^", r"\1", text)
        # a reference mark keyed to the chapter's REFERENCES list is a raised
        # numeral, not mathematics: \(^{1}\) typesets a superscript on
        # nothing (an empty <mi/>, which `se lint` rejects)
        t = re.sub(r"\\\(\^\{?(\d)\}?\\\)", lambda m: "⁰¹²³⁴⁵⁶⁷⁸⁹"[int(m.group(1))], t)
        # Bridgman's "and so on" is a run of four hyphens after a list of
        # symbols; set as two em dashes OUTSIDE the formulas, or the page
        # shows hyphens and `se typogrify` turns them into dashes in the epub
        held_m = []
        t = mathml.MATH.sub(lambda m: (held_m.append(m.group(0)), f"\x00{len(held_m)-1}\x00")[1], t)
        t = t.replace("----", "\u2014\u2014")
        assert "--" not in t, t[:120]
        # inside a formula the run is \text{----}: the same two dashes; the
        # longer rules of system A (p. 39) keep their length, in dashes
        dash = lambda run: "\u2014" * max(2, len(run) // 2)
        held_m = [re.sub(r"\\text\{([^{}]*)\}",
                         lambda m: "\\text{" + re.sub(r"-{3,}", lambda d: dash(d.group(0)), m.group(1)) + "}", x)
                  for x in held_m]
        held_m = [re.sub(r"-{3,}", lambda d: "\\text{" + dash(d.group(0)) + "}", x) for x in held_m]
        assert not any("--" in x for x in held_m), [x for x in held_m if "--" in x][:1]
        t = re.sub(r"\x00(\d+)\x00", lambda m: held_m[int(m.group(1))], t)
        sections[-1]["stream"].append((kind, R.emph_safe(t) if kind == "P" else t))

    # WITNESS: the printed Contents, chapter for chapter
    ctext = (HERE / "proof" / f"{CONTENTS:03d}.txt").read_text()
    printed = re.findall(r"^\tChapter ([IVX]+)\. \| (.+?) \| \d+$", ctext, re.M)
    words = lambda s: re.findall(r"[a-z]+", mathml.MATH.sub("", s).lower())
    assert [r for r, _ in chapters] == ROMAN, chapters
    assert len(printed) == len(chapters), (printed, chapters)
    for (r1, t1), (r2, t2) in zip(printed, chapters):
        assert r1 == r2 and words(t1)[:4] == words(t2)[:4], (r1, t1, t2)

    left = [x for s in sections for x in s["stream"]
            if re.search(r"\^\^|^\+ ", x[1]) or re.search(r"[a-z]- [a-z]", mathml.MATH.sub("", x[1]))]
    assert not left, left[:3]
    nf = sum(1 for s in sections for x in s["stream"] if x[1].startswith("Footnote: "))
    assert nf == notes, (nf, notes)
    nmath = sum(len(mathml.formulas(x[1])) for s in sections for x in s["stream"])
    print(len(sections), "sections;", nmath, "formulas;", notes, "footnotes; hyphens kept at a join:", kept_hyphen)
    for s in sections:
        print(f'  {s["title"][:64]:64} {sum(len(x[1].split()) for x in s["stream"]):6}')

    book = R.Book(HERE, "dimensionalanaly00bridrich_jp2.zip", html_name="-")
    rows, described = R.compose(book, sections, plates=[])


if __name__ == "__main__":
    main()
