"""S. W. Erdnase, Artifice, Ruse and Subterfuge at the Card Table (1902),
the book everyone calls The Expert at the Card Table: a RESTORED EDITION.

    python3 erdnase/pages.py     # page drafts and plate cuts (once)
    python3 erdnase/prep.py

The text is erdnase/proof/NNN.txt, one file per leaf, READ FROM THE PAGE
IMAGE of Archive.org's bwb_S0-DTR-948 (a photographic facsimile of the
1902 first edition) by a proofreading pass whose instructions are
proof_instructions.txt. The OCR was only a draft: it dropped whole
paragraphs next to drawings (leaves 51, 74) and there is no second scan
to vote with, since every other copy is lending-restricted.

Conventions the proof files carry, resolved here:
  "+ " opens a paragraph that continues the one before it (a page turn, or
      a drawing set in the middle of the paragraph); a word broken across
      the page ("deter-" / "+ mining") is closed up.
  ^^Small Capitals^^ -> plain words (the run-in heads' small capitals; the
      italic that follows them is kept as emphasis).
  [Figure N] -> the plate, set after the paragraph it interrupted.

WITNESSES, asserted: Figs. 1-101 each exactly once and in order, each on
the leaf its plate was cut from; every section heading of the printed
Contents found as a body heading; no markup left over.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import restore_lib as R  # noqa: E402

FIRST, LAST = 15, 211            # the Introduction to the last page of text
PREFACE = 9
# a heading the Contents gives in another order ("BLIND SHUFFLES. ERDNASE
# SYSTEM OF") is matched on its words, not its order
FRONT_OUT = {7, 8, 10, 11, 12, 13, 14}   # title, copyright, blank, Contents


def norm_words(s):
    return sorted(re.findall(r"[a-z]+", s.lower().replace("one-handed", "one handed")))


def load(leaf):
    t = (HERE / "proof" / f"{leaf:03d}.txt").read_text()
    return [p.strip("\n") for p in re.split(r"\n\s*\n", t) if p.strip()]


def is_heading(p):
    letters = re.sub(r"[^A-Za-z]", "", p)
    return (len(letters) > 2 and letters == letters.upper() and not p.startswith("\t")
            and "[Figure" not in p and not p.startswith("+"))


def join_broken(a, b, solid, hyph):
    """a ends with a hyphen at a page turn or a plate; b continues it."""
    head = a.split()[-1][:-1]
    tail = b.split()[0]
    w = re.sub(r"[^\w-]", "", head + tail)
    compound = f"{head}-{re.sub(r'[^A-Za-z-]', '', tail)}".lower()
    if compound in hyph and w.lower() not in solid:
        return a + b, compound                    # a real compound: keep the hyphen
    return a[:-1] + b, None


def main():
    leaves = [PREFACE] + list(range(FIRST, LAST + 1))
    raw = {l: load(l) for l in leaves}
    alltext = " ".join(p for ps in raw.values() for p in ps)
    solid = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", alltext))
    hyph = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]+-[A-Za-z]+\b", alltext))
    plates = json.loads((HERE / "_src" / "plates.json").read_text())
    by_leaf = {}
    for p in plates:
        by_leaf.setdefault(p["leaf"], []).append(p)

    # one stream of ("P", text) / ("H", text) / ("BLOCK", text) / ("FIG", n, src)
    stream, kept_hyphen, figs = [], [], []
    held = []                                        # plates waiting for their paragraph to end
    for leaf in leaves:
        k = 0
        for p in raw[leaf]:
            m = re.fullmatch(r"\[Figure (\d+)\]", p)
            if m:
                n = int(m.group(1))
                src = by_leaf[leaf][k]
                k += 1
                figs.append(n)
                held.append(("FIG", n, f"{src['leaf']:03d}-{src['k']}.png"))
                continue
            if p.startswith("+ "):
                body = p[2:]
                prev = next(i for i in range(len(stream) - 1, -1, -1) if stream[i][0] in ("P", "BLOCK"))
                a = stream[prev][1]
                if a.endswith("-") and not a.endswith("--"):
                    joined, comp = join_broken(a, body, solid, hyph)
                    if comp:
                        kept_hyphen.append((leaf, comp))
                else:
                    joined = a + ("\n" if stream[prev][0] == "BLOCK" else " ") + body
                stream[prev] = (stream[prev][0], joined)
                continue
            stream.extend(held)
            held = []
            if p.startswith("\t"):
                stream.append(("BLOCK", p))
            elif is_heading(p):
                stream.append(("H", p))
            else:
                stream.append(("P", p))
        assert k == len(by_leaf.get(leaf, [])), f"leaf {leaf}: {k} figures for {len(by_leaf.get(leaf, []))} plates"
    stream.extend(held)
    assert figs == list(range(1, 102)), f"figures out of order: {figs}"

    # THE TRICKS ARE RUN-IN HEADS in the body ("*The Card and Hat.*—In
    # Effect: ...") and capital entries in the Contents, so each opens a
    # section of its own and keeps its run-in title as printed.
    tricks = {"The Exclusive Coterie", "The Divining Rod", "The Invisible Flight", "The Traveling Cards",
              "The Row of Ten Cards", "The Acrobatic Jacks", "Power of Concentrated Thought",
              "The Acme of Control", "The Card and Handkerchief", "The Top and Bottom Production",
              "The Three Aces", "The Card and Hat"}
    for i, it in enumerate(list(stream)):
        if it[0] == "P":
            m = re.match(r"\*([^*]+)\.\*—", it[1])
            if m and m.group(1) in tricks:
                stream.insert(stream.index(it), ("H", m.group(1).upper()))
                tricks.discard(m.group(1))
    assert not tricks, f"tricks not found: {tricks}"

    # sections: each capital heading opens one; a heading with no text of its
    # own before the next heading becomes that section's subheading instead
    sections = []
    for it in stream:
        if it[0] == "H":
            h = R.titlecase(it[1].rstrip(".").lower(), keep=("Erdnase", "S. W. E."))
            if sections and not any(x[0] != "PLATE" for x in sections[-1]["stream"]) and not sections[-1].get("sub"):
                sections[-1]["sub"] = True
                sections[-1]["stream"].append(("P", h))
            else:
                sections.append({"title": h, "stream": []})
            continue
        if not sections:
            continue
        s = sections[-1]["stream"]
        if it[0] == "FIG":
            s.append(("PLATE", it[2], f"Fig. {it[1]}."))
        elif it[0] == "BLOCK":
            s.append(("BLOCK", it[1]))
        else:
            t = re.sub(r"\^\^(.+?)\^\^", r"\1", it[1])
            # a numbered sub-heading on its own line ("II. To Retain the
            # Complete Stock.") is a subheading: no terminal stop
            # (some carry an inner stop: "V. To Retain Bottom Stock. Riffle II
            # and Cut IV.")
            if re.fullmatch(r"(?:[IVX]+|[A-E])\. [A-Z][^—*]{2,80}\.", t) and not re.search(r"[.!?] [a-z]", t):
                t = t[:-1]
            s.append(("P", R.emph_safe(t)))
    for s_ in sections:
        s_.pop("sub", None)

    # WITNESS: every capital entry of the printed Contents is a body heading
    contents = []
    for l in (11, 12, 13, 14):
        for line in (HERE / "proof" / f"{l:03d}.txt").read_text().splitlines():
            e = line.strip().split(" | ")[0].strip()
            letters = re.sub(r"[^A-Za-z]", "", e)
            # EXPLANATORY is the Contents' name for the untitled opening
            # pages of CARD TRICKS, which the body heads only "CARD TRICKS."
            if letters and letters == letters.upper() and e not in ("CONTENTS.", "EXPLANATORY"):
                contents.append(e)
    heads = [norm_words(s["title"]) for s in sections] + [
        norm_words(it[1]) for s in sections for it in s["stream"] if it[0] == "P" and len(it[1]) < 80]
    missing = [c for c in contents if norm_words(re.sub(r"ERDNASE SYSTEM OF|DEFINITIONS OF", "", c))
               and not any(set(norm_words(re.sub(r"(?i)erdnase system of|definitions of", "", c))) <= set(h) for h in heads)]
    assert not missing, f"Contents entries with no heading: {missing}"

    left = [it for s in sections for it in s["stream"] if it[0] in ("P", "BLOCK")
            and (re.search(r"\^\^|^\+ |\[Figure", it[1]) or re.search(r"\w- \w", it[1]))]
    assert not left, left[:3]
    print(len(sections), "sections;", len(figs), "figures; hyphens kept at a join:", kept_hyphen)
    for s in sections:
        print(f'  {s["title"][:60]:60} {sum(len(it[1].split()) for it in s["stream"] if it[0] == "P"):6}')

    book = R.Book(HERE, "bwb_S0-DTR-948_jp2.zip", html_name="-",
                  replace={f"{p['leaf']:03d}-{p['k']}.png": str(HERE / "_src" / "plates" / f"{p['leaf']:03d}-{p['k']}.png")
                           for p in plates})
    order = [{"src": it[1], "printed": it[2]} for s in sections for it in s["stream"] if it[0] == "PLATE"]
    rows, described = R.compose(book, sections, plates=order)
    print(len(rows), "plates;", described, "described")


if __name__ == "__main__":
    main()
