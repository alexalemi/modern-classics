"""Gutenberg Works Vol. III -> chapters/ + manifest.json for Burke's
Reflections on the Revolution in France.

TWO STRUCTURAL PROBLEMS, and the second is the interesting one.

1. THERE IS NO STANDALONE EDITION. Gutenberg has no Reflections of its
   own: searching it returns exactly two books and neither is one. The
   text lives inside #15679, "The Works of the Right Honourable Edmund
   Burke, Vol. 03 (of 12)", where it is the third and last item, after
   the Nabob of Arcot's Debts and the Army Estimates. So prep slices it
   out, and asserts both ends of the slice.

2. IT HAS NO CHAPTERS. It is one continuous letter of 94,000 words, so
   the division has to be imposed -- the bunyan problem. But it does NOT
   have to be invented: BURKE PUT TWELVE SECTION BREAKS IN IT HIMSELF,
   printed as a row of asterisks, and those are the strongest possible
   warrant for where a division goes. They give thirteen sections, and
   this edition uses them exactly as they stand, including the four that
   run under 2,000 words and the one that runs to 27,000.
   The section TITLES are new writing, on the augustine and soap-bubbles
   precedent, since Burke titled nothing. They were written from each
   section's actual argument.
   WORD-FORM NUMBERS, as in hume/ and mill/: "Section One: ..." does not
   match assemble.CHAP_LINE, so every section renders at one level and
   the contents stay flat. It also cannot match assemble.PART_LINE,
   which deletes a "Part <Roman/digits>:" line out of a file's front
   matter -- the trap that cost descartes all four of its Parts.

THE OVERSIZED SECTIONS BECOME PARTS, not new sections: a translation
agent must OUTPUT as much as it reads, so ~7,000 words is the binding
constraint. Sections ten and eleven need four parts each.

FOOTNOTES: 57 of them, numbered 77-133 because the numbering runs on
from earlier items in the volume. Every reference resolves and every
note is referenced -- checked, not assumed. They are inlined as
"Footnote: ..." paragraphs after the citing paragraph (the candle
pattern). They are Burke's own, and mostly citations of Dr Price's
sermon and of the decrees of the National Assembly.

ITALICS ARE ALREADY MARKUP. Gutenberg sets Burke's italics as _x_,
which is exactly what assemble.EMPH renders as <em>, so they ride
through untouched. They are load-bearing here: Burke italicises the
word he is about to turn against his opponent.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source" / "reflections.txt"
OUT = BOOK / "chapters"

MAXW = 7000
SEP = re.compile(r"^\s*\*[\s*]*\*\s*$")
NOTEREF = re.compile(r"\[(\d+)\]")

TITLES = [
    "Section One: The Letter, and the Club That Congratulated a Revolution",
    "Section Two: Dr Price's Sermon, and Whether We Choose Our Kings",
    "Section Three: The Right to Cashier a King for Misconduct",
    "Section Four: The Right to Frame a Government for Ourselves",
    "Section Five: What France Might Have Done Instead",
    "Section Six: Who the Men of the National Assembly Actually Are",
    "Section Seven: The Rights of Men, and What They Are Not",
    "Section Eight: The Sixth of October, and the Age of Chivalry",
    "Section Nine: Why I Feel Differently, and a Defence of Prejudice",
    "Section Ten: The Church Establishment, and the Seizure of Its Property",
    "Section Eleven: The New Constitution, and How It Was Built",
    "Section Twelve: The Finances, and the Paper Money",
    "Section Thirteen: What I Wish for My Own Country",
]


def slice_reflections(raw):
    """Cut the Reflections out of the collected Works, and prove it."""
    starts = [m.start() for m in re.finditer(
        r"REFLECTIONS\s+ON\s+THE\s+REVOLUTION\s+IN\s+FRANCE", raw)]
    assert len(starts) >= 2, f"expected a contents entry and a body, got {starts}"
    body = raw[starts[-1]:]
    end = re.search(r"\*\*\* ?END OF", body)
    assert end, "no Gutenberg end marker"
    body = body[:end.start()]
    assert body.rstrip().endswith("END OF VOL. III."), body.rstrip()[-60:]
    return body


def normalise(block):
    """One raw paragraph -> one output paragraph.

    An INDENTED block is verse or a quotation and keeps its shape: the
    lines stay separate and take a tab, which is what both renderers
    read as lined matter. Everything else is hard-wrapped prose and is
    joined into a single line. DEDENT the block rather than stripping
    each line, so relative indentation inside it survives (the fleming
    rule -- stripping slid the Morse alphabet out of register).
    """
    lines = [l for l in block.split("\n") if l.strip()]
    if block.startswith((" ", "\t")) and len(lines) > 1:
        pad = min(len(l) - len(l.lstrip()) for l in lines)
        return "\n".join("\t" + l[pad:].rstrip() for l in lines)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def load_notes(tail):
    notes = {}
    for m in re.finditer(r"^\[(\d+)\](.*?)(?=^\[\d+\]|\Z)", tail, re.M | re.S):
        notes[int(m.group(1))] = re.sub(r"\s+", " ", m.group(2)).strip()
    return notes


def split_parts(pars, maxw):
    total = sum(len(p.split()) for p in pars)
    k = max(1, -(-total // maxw))
    target = total / k
    parts, cur, run = [], [], 0
    for p in pars:
        w = len(p.split())
        if cur and run + w / 2 > target and len(parts) < k - 1:
            parts.append(cur)
            cur, run = [], 0
        cur.append(p)
        run += w
    parts.append(cur)
    return parts


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    body = slice_reflections(SRC.read_text(encoding="utf-8", errors="replace"))
    cut = body.find("FOOTNOTES:")
    assert cut > 0, "no FOOTNOTES section"
    notes = load_notes(body[cut:])
    text = body[:cut]

    raw = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    # the title block at the top is furniture, not text
    while raw and (raw[0].strip().isupper() or raw[0].strip() in {"ON"}):
        raw.pop(0)

    # -- carve into Burke's own sections
    sections, cur = [], []
    for p in raw:
        if SEP.match(p):
            sections.append(cur)
            cur = []
        else:
            cur.append(p)
    sections.append(cur)
    assert len(sections) == len(TITLES), \
        f"{len(sections)} sections but {len(TITLES)} titles"

    refs = [int(n) for n in NOTEREF.findall(text)]
    assert sorted(refs) == sorted(notes), \
        f"refs {len(refs)} vs notes {len(notes)}"

    manifest, idx, used = [], 0, []
    for title, blocks in zip(TITLES, sections):
        pars = []
        for block in blocks:
            here = [int(n) for n in NOTEREF.findall(block)]
            pars.append(NOTEREF.sub("", normalise(block)))
            for n in here:
                used.append(n)
                pars.append("Footnote: " + notes[n])
        pars = [re.sub(r" +", " ", p).strip() if not p.startswith("\t") else p
                for p in pars if p.strip()]
        parts = split_parts(pars, MAXW)
        for i, part in enumerate(parts, 1):
            name = f"{idx:03d}.txt"
            body_txt = "\n\n".join(part)
            (OUT / name).write_text(title + "\n\n" + body_txt.rstrip() + "\n")
            manifest.append({"file": name, "title": title, "part": i,
                             "of": len(parts),
                             "words": len(body_txt.split())})
            idx += 1
    assert sorted(used) == sorted(notes), "a footnote was lost or doubled"
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    # -- SECOND, INDEPENDENT READING (the epictetus rule). Compares
    # CHARACTERS, not tokens, and excludes the inlined footnotes, which
    # the raw reading has at the back where the source keeps them.
    want = NOTEREF.sub("", text)
    want = re.sub(r"^\s*\*[\s*]*\*\s*$", " ", want, flags=re.M)
    want = re.sub(r"^\s*(REFLECTIONS|ON|THE REVOLUTION IN FRANCE\.)\s*$", " ",
                  want, flags=re.M)
    got = []
    for m in manifest:
        lines = (OUT / m["file"]).read_text().split("\n")
        keep = [p for p in re.split(r"\n\s*\n", "\n".join(lines[1:]))
                if not p.strip().startswith("Footnote: ")]
        got.append(" ".join(keep))
    squash = lambda s: re.sub(r"\s+", "", s)
    a, b = squash(want), squash(" ".join(got))
    if a != b:
        i = next(k for k in range(min(len(a), len(b))) if a[k] != b[k])
        raise SystemExit(f"diverges at char {i}:\n"
                         f"  source ...{a[max(0, i-70):i+70]}\n"
                         f"  output ...{b[max(0, i-70):i+70]}")
    print(f"cross-check: {len(a):,} characters match, in order")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words; "
          f"largest {max(m['words'] for m in manifest):,}")
    print(f"{sum(1 for m in manifest if m['of'] > 1)} files are section parts")
    print(f"{len(notes)} footnotes inlined")


if __name__ == "__main__":
    main()
