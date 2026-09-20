"""Aristotle's Rhetoric: a MODERN CLASSIC, from the Greek.

    python3 rhetoric/prep.py

Both texts are Perseus' canonical-greekLit (tlg0086.tlg038):
    perseus-grc2   the Greek (Ross's Oxford text, 1959)
    perseus-eng2   J. H. Freese's Loeb English (1926), the per-chapter crib

They carry the SAME 882 sections under the same book/chapter/section
numbers, so the crib is aligned by construction; prep asserts it before
writing anything (the lucretius lesson: check for a shared reference
system before building alignment machinery).

One file per chapter: chapters/NNN.txt is the Greek, reference/NNN.txt
Freese section by section with his footnotes inline as "[Note: ...]".
Quoted verse (<lg>/<l>) becomes tab-indented lines, one per line, in
both. Sections are marked "§N" at the start of their paragraph in both
files, so a translator can keep register with the crib; the markers are
the translator's guide and are NOT carried into the translation.
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
TEI = "{http://www.tei-c.org/ns/1.0}"
WORD = ["One", "Two", "Three"]
SECTIONS = 882
SUM_TITLES = 60
CHAPTERS = {1: 15, 2: 26, 3: 19}
# Aristotle titles nothing; these are NEW WRITING (the augustine precedent),
# each a plain description of what the chapter does, checked against the
# chapter by the agent who translates it.
TITLES = {1: ["Rhetoric and Dialectic", "The Means of Persuasion", "The Three Kinds of Speech",
              "What Political Speeches Are About", "Happiness", "The Good and the Useful",
              "The Greater Good", "Constitutions", "Virtue, Vice, Praise and Blame",
              "Wrongdoing and Its Motives", "Pleasure", "Who Does Wrong, and to Whom",
              "Justice, Written and Unwritten", "Degrees of Wrong",
              "Proofs Outside the Art"],
          2: ["Character and Emotion", "Anger", "Calm", "Friendship and Enmity", "Fear and Confidence",
              "Shame", "Kindness", "Pity", "Indignation", "Envy", "Emulation", "The Young", "The Old",
              "The Prime of Life", "Good Birth", "Wealth", "Power and Good Fortune",
              "What All Speeches Share", "The Possible, the Past and the Future", "Examples", "Maxims",
              "Enthymemes", "Lines of Argument", "Sham Arguments", "Refutation",
              "What Is Not a Line of Argument"],
          3: ["Style and Delivery", "Clarity and Propriety", "Frigid Style", "Simile",
              "Correct Greek", "Dignity", "Appropriateness", "Rhythm", "The Periodic Style",
              "Wit and Metaphor", "Setting Things Before the Eyes", "Written and Spoken Style",
              "The Parts of a Speech", "The Introduction", "Answering Prejudice", "The Narrative",
              "Proofs", "Questioning", "The Conclusion"]}


def text_of(el, notes):
    """Flatten a section to paragraphs of text and verse blocks."""
    out = []

    def walk(e, buf):
        tag = e.tag.replace(TEI, "")
        if tag == "note":
            if notes:
                inner = []
                walk_children(e, inner)
                buf.append(" [Note: " + " ".join("".join(inner).split()) + "]")
            if e.tail:
                buf.append(e.tail)
            return
        if tag in ("milestone", "bibl"):
            if e.tail:
                buf.append(e.tail)
            return
        if tag == "lg":
            flush(buf)
            lines = []
            for l in e.iter(TEI + "l"):
                ln = []
                walk_children(l, ln)
                s = " ".join("".join(ln).split())
                if s:
                    lines.append("\t" + s)
            if lines:
                out.append("\n".join(lines))
            if e.tail:
                buf.append(e.tail)
            return
        if e.text:
            buf.append(e.text)
        for c in e:
            walk(c, buf)
        if tag == "p":
            flush(buf)
        if e.tail:
            buf.append(e.tail)

    def walk_children(e, buf):
        if e.text:
            buf.append(e.text)
        for c in e:
            walk(c, buf)

    def flush(buf):
        s = " ".join("".join(buf).split())
        if s:
            out.append(s)
        buf.clear()
    b = []
    walk_children(el, b)
    flush(b)
    return out


def read(path, notes):
    root = ET.parse(path).getroot()
    body = root.find(f".//{TEI}body")
    secs = {}
    for book in body.iter(TEI + "div"):
        if book.get("subtype") != "book":
            continue
        for ch in book:
            if ch.get("subtype") != "chapter":
                continue
            for sec in ch:
                if sec.get("subtype") != "section":
                    continue
                key = (int(book.get("n")), int(ch.get("n")), int(sec.get("n")))
                secs[key] = text_of(sec, notes)
    return secs


def main():
    grc = read(HERE / "_perseus_grc2.xml", notes=False)
    eng = read(HERE / "_perseus_eng2.xml", notes=True)
    # the same sections, and in the same order but for ONE editorial
    # transposition: Ross sets 2.10.7 after 2.10.10, Freese keeps the
    # manuscript order. The Greek's order governs; the crib file for that
    # chapter holds all four sections, so nothing is out of reach.
    assert len(grc) == SECTIONS and set(grc) == set(eng), (len(grc), len(eng))
    moved = [a for a, b in zip(grc, eng) if a != b]
    assert moved == [(2, 10, 8), (2, 10, 9), (2, 10, 10), (2, 10, 7)], moved
    chs = sorted({k[:2] for k in grc})
    assert all(len(TITLES[b]) == n for b, n in CHAPTERS.items())
    assert len({t for v in TITLES.values() for t in v}) == SUM_TITLES, "titles must be unique (anchors)"
    assert {b: sum(1 for c in chs if c[0] == b) for b in (1, 2, 3)} == CHAPTERS, chs
    for d in ("chapters", "reference"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    for i, (b, c) in enumerate(chs):
        title = f"Chapter {c}: {TITLES[b][c - 1]}"
        for d, src in (("chapters", grc), ("reference", eng)):
            paras = []
            for k in (k for k in src if k[:2] == (b, c)):
                ps = src[k]
                if ps and not ps[0].startswith("\t"):
                    ps = [f"§{k[2]} " + ps[0]] + ps[1:]
                else:
                    ps = [f"§{k[2]}"] + ps
                paras.extend(ps)
            (HERE / d / f"{i:03d}.txt").write_text(title + "\n\n" + "\n\n".join(paras) + "\n")
        e = {"file": f"{i:03d}.txt", "title": title, "part": 1, "of": 1, "chapter": True}
        if c == 1:
            e["part_before"] = f"Book {WORD[b - 1]}"
        manifest.append(e)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    gw = sum(len(" ".join(p for ps in grc.values() for p in ps).split()) for _ in [0])
    ew = sum(len(re.sub(r"\[Note:[^\]]*\]", "", " ".join(p for ps in eng.values() for p in ps)).split()) for _ in [0])
    print(len(chs), "chapters;", gw, "Greek words;", ew, "Freese words (notes excluded)")
    for i, (b, c) in enumerate(chs):
        n = len((HERE / "chapters" / f"{i:03d}.txt").read_text().split())
        if n > 2600:
            print("  long:", i, b, c, n)


if __name__ == "__main__":
    main()
