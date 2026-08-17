#!/usr/bin/env python3
"""Hume's Enquiry Concerning Human Understanding -> chapters/ + manifest

    ./fetch.sh && python3 hume/prep.py

Source: Standard Ebooks' david-hume_an-enquiry-concerning-human-
understanding, the 1748 text. Twelve sections, ~48k words.

WHY THIS BOOK. It is the purest instance in the collection of the class
named at epictetus/: near-zero archaism (0.47 per 1,000 words) and the
highest abstraction score measured anywhere in the screening pass
(49.1). Nothing in it is old-sounding; it is blocked by eighteenth-
century philosophical vocabulary used with total consistency —
"subserviency to the easy and humane", "the operations of the
understanding", "matter of fact and real existence".

AND THE NUMBER OVERSTATES IT, which the translation has to know. Hume
is a great stylist and his famous sentences are lucid: "Custom, then,
is the great guide of human life." The obstruction is in the apparatus
around the argument, not the argument. The job is to clear the
apparatus WITHOUT flattening the prose, which is the opposite of the
usual danger.

THE SAME XML DISCIPLINE AS epictetus/. ElementTree, not regex; noterefs
removed as ELEMENTS with each tail going to its own predecessor, not to
the parent's last child; and every section's word SEQUENCE compared
against a second reading of the raw XML that shares no code with the
parser.

EMPHASIS RIDES THROUGH AS MARKERS. Hume italicises constantly — 38
spans in Section VII alone — and it is doing real work: he italicises
the terms he is defining and the words a sentence turns on. Since
2026-08-17 the pipeline renders *x* as <em> in both renderers, so the
italics survive as markers rather than being thrown away. This is the
first book prepped that depends on that.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source"
OUT = BOOK / "chapters"

X = "{http://www.w3.org/1999/xhtml}"
EPUB_TYPE = "{http://www.idpf.org/2007/ops}type"

TARGET, MAX = 3600, 4300

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII"]
WORD = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
        "Nine", "Ten", "Eleven", "Twelve"]


def clean(t):
    for a, b in [(" ", " "), (" ", " "), ("﻿", ""),
                 ("⁠", "")]:
        t = t.replace(a, b)
    return t


def load(n):
    root = ET.fromstring(clean((SRC / f"chapter-{n}.xhtml").read_text()))
    body = root.find(f"{X}body")
    A = X + "a"
    for parent in body.iter():
        i = 0
        while i < len(parent):
            el = parent[i]
            if el.tag == A and el.get(EPUB_TYPE) == "noteref":
                tail = el.tail or ""
                del parent[i]
                if i:
                    parent[i - 1].tail = (parent[i - 1].tail or "") + tail
                else:
                    parent.text = (parent.text or "") + tail
            else:
                i += 1
    return body


def text_of(el):
    """Element text, with <em> carried through as *markers*.

    Built by hand rather than with itertext() so the marker can be put
    around the emphasised run; itertext() would flatten it away."""
    out = [el.text or ""]
    for child in el:
        inner = text_of(child)
        if child.tag == X + "em" and inner.strip():
            out.append(f"*{inner.strip()}*")
        else:
            out.append(inner)
        out.append(child.tail or "")
    return "".join(out)


def para(el):
    return re.sub(r"\s+", " ", text_of(el)).strip()


def sections():
    """[(roman, title, [paragraphs])] in document order."""
    out = []
    for n in range(1, 13):
        body = load(n)
        sec = body.find(f"{X}section")
        hg = sec.find(f"{X}hgroup")
        roman = para(hg.find(f"{X}h2"))
        title = para(hg.find(f"{X}p[@epub:type='title']",
                             {"epub": "http://www.idpf.org/2007/ops"}))
        pars = []

        def walk(node):
            for el in node:
                tag = el.tag.split("}")[-1]
                if tag == "hgroup":
                    continue
                if tag == "section":
                    walk(el)
                elif tag == "h3":
                    # Hume's own "Part I" / "Part II" divisions. WORD form,
                    # not "Part I:", because assemble.strip_front deletes a
                    # line matching ^Part [IVXLC0-9]+: while reading a
                    # file's front matter -- the descartes trap.
                    label = para(el)
                    m = re.match(r"Part ([IVX]+)$", label)
                    pars.append(f"Part {WORD[ROMAN.index(m.group(1))]}"
                                if m else label)
                elif tag == "p":
                    t = para(el)
                    if t:
                        pars.append(t)
                elif tag == "blockquote":
                    walk(el)
                else:
                    raise SystemExit(f"unhandled <{tag}> in section {n}")
        walk(sec)
        out.append((roman, title, pars))
    return out


WORDRE = re.compile(r"[^\W\d_]+")


def raw_words(n):
    """The section's words by a different route: strip noteref anchors
    and every other tag from the RAW XML with regexes, sharing no code
    with the ElementTree path above."""
    t = clean((SRC / f"chapter-{n}.xhtml").read_text())
    t = re.sub(r'<a [^>]*epub:type="noteref"[^>]*>.*?</a>', "", t, flags=re.S)
    t = t[t.find("<body"):]
    t = re.sub(r"<hgroup>.*?</hgroup>", "", t, flags=re.S)
    return WORDRE.findall(re.sub(r"<[^>]+>", " ", t))


def wc(ps):
    return sum(len(p.split()) for p in ps)


def split_oversize(pars, n):
    total, out, cur, run = wc(pars), [], [], 0
    for p in pars:
        cur.append(p)
        run += len(p.split())
        if run >= total / n and len(out) < n - 1:
            out.append(cur)
            cur, run = [], 0
    if cur:
        out.append(cur)
    return out


def main():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    secs = sections()
    assert [r for r, _, _ in secs] == ROMAN, "section numbering is not I..XII"

    for i, (roman, title, pars) in enumerate(secs, 1):
        want = raw_words(i)
        # "Part One" is this edition's rewrite of the source's "Part I"
        # (word form, so assemble.strip_front cannot mistake it for a
        # divider). Map it back before comparing rather than loosening
        # the check: everything else must still match exactly.
        flat = " ".join(pars).replace("*", " ")
        for w, r in zip(WORD, ROMAN):
            flat = flat.replace(f"Part {w}", f"Part {r}")
        got = WORDRE.findall(flat)
        if got != want:
            bad = next(k for k, (a, b) in enumerate(zip(got + [None], want))
                       if a != b)
            raise SystemExit(
                f"section {roman}: text differs from source at word {bad}\n"
                f"  parsed: ...{' '.join(got[max(0, bad-8):bad+8])}...\n"
                f"  source: ...{' '.join(want[max(0, bad-8):bad+8])}...")

    manifest, idx = [], 0
    for i, (roman, title, pars) in enumerate(secs):
        head = f"Section {WORD[i]}: {title}"
        n = wc(pars)
        chunks = [pars] if n <= MAX else split_oversize(pars, -(-n // TARGET))
        for part, chunk in enumerate(chunks, 1):
            name = f"{idx:03d}.txt"
            lines = [head] + ([f"(Part {part} of {len(chunks)})"]
                              if len(chunks) > 1 else [])
            (OUT / name).write_text("\n\n".join(lines + chunk) + "\n")
            manifest.append({"file": name, "title": head, "part": part,
                             "of": len(chunks), "words": wc(chunk)})
            idx += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(manifest)} files, 12 sections, "
          f"{sum(m['words'] for m in manifest):,} words")
    ems = sum(f.read_text().count("*") for f in OUT.glob("*.txt")) // 2
    print(f"emphasis spans carried through: {ems}")
    for m in manifest:
        if m["part"] == 1:
            of = f"  ({m['of']} parts)" if m["of"] > 1 else ""
            print(f"  {m['file']}  {m['title'][:62]}{of}")


if __name__ == "__main__":
    main()
