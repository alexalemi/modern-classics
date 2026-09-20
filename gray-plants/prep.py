"""Asa Gray, How Plants Grow (1858): a RESTORED EDITION.

    python3 gray-plants/prep.py

The text is gray-plants/proof/NNN.txt, one file per leaf, READ FROM THE
PAGE IMAGE of Archive.org's howplantsgrowsim00gray (a later printing, by
Ivison, Blakeman, Taylor & Co., of the book entered for copyright in 1858;
it carries four inserted pages numbered 104¹-104⁴) by a proofreading pass
whose instructions are proof_instructions.txt. Each leaf's woodcuts are in
proof/NNN.plates, boxed on the page by the same pass and cut by plates.py.

Conventions the proof files carry, resolved here:
  "page: N"     first line of every file; the printed page, kept for the
                witness below and for the key's page references.
  "+ "          continues the paragraph before it (a page turn, or the text
                resuming after a woodcut set beside it); a word broken
                across the join is closed up.
  ^^Small Capitals^^ -> plain words.
  [Figure N]    a woodcut, held until the paragraph it interrupts ends.
  "Footnote: "  set after the paragraph that cites it; its further lines are
                further paragraphs.
  ⁎ † ‡         Gray's marks, kept as printed (⁎ is his star before a
                genus, written so it cannot be read as emphasis).

THE KEY'S PAGE REFERENCES ARE CONVERTED, and nothing else's. A key line
ending "^^Currant^^ F. 155" sends the reader to page 155; in a reflowable
edition it reads "Currant F., No. 40", the family's own printed number, and
prep ASSERTS that family No. 40 is the Currant Family and begins on or
before p. 155. Page references in running prose and in the Index to Part I
stay as printed (the calculus-made-easy precedent), and the introduction
says what they refer to.

WITNESSES, asserted: the printed pages run in sequence with none missing;
every family 1-105 appears once and in order; every woodcut marker has
exactly one plates line and every plates line one marker; the figure
numbers run without gaps except as logged.

LEFT OUT: the title page and copyright (the env carries them) and the
Index to the Popular Flora (leaves 237-249), which is page numbers only.
"""
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import restore_lib as R  # noqa: E402
import plates as P  # noqa: E402

FIRST, LAST = 9, 236
# "63. SAGE or MINT FAMILY." sets its "or" in small capitals
FAMILY = re.compile(r"(\d+)\. ([A-Z][A-Z'. -]+(?: or [A-Z][A-Z'. -]+)?) FAMILY\. Order (\S+?)\.?$")
MARK = re.compile(r"\[Figure ((?:\d+[a-z]?|x\d+)(?:-\d+[a-z]?)*)\]")


def load(leaf):
    t = (HERE / "proof" / f"{leaf:03d}.txt").read_text()
    head, _, body = t.partition("\n")
    m = re.fullmatch(r"page: (\S+)", head.strip())
    assert m, f"leaf {leaf}: first line {head!r}"
    return m.group(1), [p.strip("\n") for p in re.split(r"\n\s*\n", body) if p.strip()]


def plain(p):
    return re.sub(r"\^\^(.+?)\^\^", r"\1", p)


def is_heading(p):
    q = plain(p)
    letters = re.sub(r"[^A-Za-zÆŒ]", "", q.split(" Order ")[0].replace(" or ", " "))
    return (len(letters) > 2 and letters == letters.upper() and not p.startswith(("\t", "+ ", "Footnote:"))
            and len(q) < 120 and "[Figure" not in q)


def join_broken(a, b, solid, hyph):
    head = a.split()[-1][:-1]
    tail = b.split()[0]
    w = re.sub(r"[^\w-]", "", head + tail)
    compound = f"{head}-{re.sub(r'[^A-Za-z-]', '', tail)}".lower()
    if compound in hyph and w.lower() not in solid:
        return a + b, compound
    return a[:-1] + b, None


def title(s):
    t = R.titlecase(s.rstrip(".").lower())
    return re.sub(r"\b[IVX][ivx]+\b", lambda m: m.group(0).upper(), t)


def main():
    leaves = list(range(FIRST, LAST + 1))
    missing = [l for l in leaves if not (HERE / "proof" / f"{l:03d}.txt").exists()]
    assert not missing, f"no proof for leaves {missing}"
    raw = {l: load(l) for l in leaves}
    alltext = " ".join(p for _, ps in raw.values() for p in ps)
    solid = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", alltext))
    hyph = Counter(w.lower() for w in re.findall(r"\b[A-Za-z]+-[A-Za-z]+\b", alltext))

    # ---- plates: every marker has one plates line, every line one marker
    cuts = P.main(leaves)
    # a printed label that contradicts its own figure number: see proof_notes
    LABEL_FIXES = {"323": ("823.", "323."), "288": ("283.", "288."), "506": ("503.", "506.")}
    for c in cuts:
        if c["ids"] in LABEL_FIXES:
            bad, good = LABEL_FIXES[c["ids"]]
            assert c["printed"].startswith(bad), (c["ids"], c["printed"])
            c["printed"] = good + c["printed"][len(bad):]
    by_leaf = {}
    for c in cuts:
        by_leaf.setdefault(c["leaf"], {})[c["ids"]] = c
    seen_ids = []

    # ---- the stream: ("P"|"H"|"BLOCK", text, page) and ("FIG", cut)
    stream, held, kept_hyphen, notes = [], [], [], 0
    pages = []
    for leaf in leaves:
        page, paras = raw[leaf]
        pages.append((leaf, page))
        body = [p for p in paras if not p.startswith("Footnote: ")]
        pending = [p for p in paras if p.startswith("Footnote: ")]
        notes += len(pending)
        for p in body:
            m = MARK.fullmatch(p)
            if m:
                ids = m.group(1)
                c = by_leaf.get(leaf, {}).pop(ids, None)
                assert c, f"leaf {leaf}: [Figure {ids}] has no plates line"
                seen_ids.append(ids)
                held.append(("FIG", c, page))
                continue
            if p.startswith("+ "):
                text = p[2:]
                prev = next(i for i in range(len(stream) - 1, -1, -1) if stream[i][0] in ("P", "BLOCK"))
                a = stream[prev][1]
                if a.endswith("-") and not a.endswith("--"):
                    joined, comp = join_broken(a, text, solid, hyph)
                    if comp:
                        kept_hyphen.append((leaf, comp))
                else:
                    joined = a + ("\n" if stream[prev][0] == "BLOCK" else " ") + text
                stream[prev] = (stream[prev][0], joined, stream[prev][2])
            else:
                stream.extend(held)
                held = []
                kind = "BLOCK" if p.startswith("\t") else "H" if is_heading(p) else "P"
                stream.append((kind, p, page))
            for n in list(pending):
                sym = n[len("Footnote: "):][:1]
                if sym in p and not p.startswith("Footnote"):
                    lines = n.split("\n")
                    held.extend(("P", l if i == 0 else l.strip(), page) for i, l in enumerate(lines))
                    pending.remove(n)
        assert not pending, f"leaf {leaf}: footnote with no reference mark: {[x[:40] for x in pending]}"
        left = by_leaf.get(leaf, {})
        assert not left, f"leaf {leaf}: plates lines with no marker: {list(left)}"
    stream.extend(held)

    # ---- sections
    sections = [{"title": "Botany for Young People", "stream": []}]
    families, heldheads = [], []
    it = iter(stream)
    for item in it:
        kind = item[0]
        s = sections[-1]["stream"]
        if kind == "FIG":
            c = item[1]
            s.append(("PLATE", f"{c['leaf']:03d}-{c['k']}.png", c["printed"]))
            continue
        text = item[1]
        if kind == "H":
            q = plain(text)
            fm = FAMILY.fullmatch(q)
            if q in ("BOTANY FOR YOUNG PEOPLE.", "HOW PLANTS GROW.") and len(sections) == 1 and not s:
                continue                          # Part First's title page: the divider carries it
            if q in ("PART FIRST.",) or q == "Part First.":
                continue
            if re.fullmatch(r"CHAPTER ([IVX]+)\.", q):
                num = q.split()[1].rstrip(".")
                k2, t2, _ = next(it)
                assert k2 == "H", (q, t2)
                sec = {"title": f"Chapter {num}: {title(plain(t2))}", "stream": [], "chapter": True}
                if num == "I":
                    sec["part_before"] = "Part First: How Plants Grow"
                sections.append(sec)
                continue
            if fm:
                n = int(fm.group(1))
                families.append((n, fm.group(2), item[2]))
                sec = {"title": f"{n}. {title(fm.group(2))} Family. Order {title(fm.group(3))}",
                       "stream": heldheads, "chapter": True}
                heldheads = []
                sections.append(sec)
                continue
            if q == "POPULAR FLORA," or q.startswith("POPULAR FLORA"):
                if not any(x.get("part_before", "").startswith("Part Second") for x in sections):
                    # the Part Second title page: its subtitle lines follow
                    sub = []
                    while True:
                        k2, t2, _ = next(it)
                        if k2 != "H" or plain(t2).startswith("Classes"):
                            break
                        sub.append(plain(t2))
                    sections.append({"title": title(plain(t2)) if plain(t2).startswith("Classes") else "Popular Flora",
                                     "stream": [("P", " ".join(title(x) for x in sub) + ".")],
                                     "part_before": "Part Second: Popular Flora", "chapter": True})
                    if not plain(t2).startswith("Classes"):
                        sections[-1]["stream"].append((k2, t2))
                continue
            if q.startswith("KEY TO THE FAMILIES"):
                sections.append({"title": title(q), "stream": heldheads, "chapter": True})
                heldheads = []
                continue
            if q.startswith("SERIES II"):
                # the Flowerless plants follow the last family with no family
                # heading of their own: a section, not the Grass Family's tail
                k2, t2, _ = next(it)
                sections.append({"title": f"Series II: {title(plain(t2))}", "stream": [], "chapter": True})
                continue
            if q.startswith(("SERIES", "CLASS", "FLOWERING", "FLOWERLESS")):
                heldheads.append(("P", title(q)))
                continue
            if q.startswith("INDEX TO PART I"):
                rest = []
                while True:
                    k2, t2, _ = next(it)
                    if k2 != "H":
                        break
                    rest.append(plain(t2))
                sections.append({"title": "Index to Part I, and Dictionary of the Botanical Terms Used in This Book",
                                 "stream": [], "part_before": "Index and Dictionary"})
                item = (k2, t2, _)
                text, kind = t2, k2
            else:
                (heldheads if heldheads else s).append(("P", title(q)))
                continue
        if heldheads:
            sections[-1]["stream"].extend(heldheads)
            heldheads = []
        t = plain(text)
        # a range between numbers: the batches wrote " — ", " – " and "–"
        t = re.sub(r"(\d) ?[—–] ?(\d)", r"\1–\2", t)
        if t.startswith("Section ") and "—" in t:
            t = t.rstrip(".")                     # "Section I. — The Parts of a Plant": a subheading
        sections[-1]["stream"].append((kind, R.emph_safe(t) if kind == "P" else t))
    assert not heldheads, heldheads

    # ---- WITNESSES
    nums = [n for n, _, _ in families]
    assert nums == list(range(1, len(nums) + 1)), [n for i, n in enumerate(nums) if n != i + 1][:5]
    print(len(families), "families")
    figs = [i for ids in seen_ids for i in ids.split("-") if not i.startswith("x")]
    # Fig. 19 is printed twice, on p. 11 and again on p. 12
    dup = [f for f, c in Counter(figs).items() if c > (2 if f == "19" else 1)]
    assert not dup, dup

    # the key: page references to family numbers
    page_of = {}
    for n, name, page in families:
        page_of[n] = (name, page)
    def pnum(p):
        m = re.match(r"(\d+)", p)
        return int(m.group(1)) if m else None
    starts = sorted((pnum(pg), n, name) for n, (name, pg) in page_of.items() if pnum(pg))
    # MATCH ON THE NAME, THEN CHECK THE PAGE. The key's page numbers can sit a
    # page off this printing's (Moonseed F. 118 begins at the top of p. 119),
    # so the family is the one whose name the key gives, and its printed page
    # must be within two of the key's; anything further is an error.
    norm = lambda x: re.sub(r"[^a-z]", "", x.lower())
    fam_text = {}
    for sec in sections:
        m = re.match(r"(\d+)\. ", sec["title"])
        if m and sec.get("chapter"):
            fam_text[int(m.group(1))] = " ".join(plain(str(x[1])) for x in sec["stream"])
    drift = Counter()
    fallback = []
    def family_for(name, page):
        alts = lambda nm: [norm(a) for a in re.split(r" or ", nm, flags=re.I)]
        cands = [(n, pnum(pg)) for n, (nm, pg) in page_of.items()
                 if any(a.startswith(norm(name)) or norm(name).startswith(a) for a in alts(nm))]
        if not cands:
            # a subfamily ("Horsechestnut F.") or a name the family heading
            # does not use: the family whose pages hold the reference
            near = [k for k, (nm, pg) in page_of.items() if pnum(pg) and pnum(pg) <= page + 2
                    and pnum(page_of.get(k + 1, ("", "999"))[1]) >= page - 2]
            hits = [k for k in near if re.search(r"\b" + re.escape(name) + r"\b", fam_text[k], re.I)]
            assert len(hits) == 1, (name, page, near, hits)
            fallback.append((name, page, hits[0], page_of[hits[0]][0]))
            return hits[0]
        n, pg = min(cands, key=lambda c: abs(c[1] - page))
        assert abs(pg - page) <= 2, (name, page, n, pg)
        drift[pg - page] += 1
        return n
    keyed = 0
    for sec in sections:
        for i, x in enumerate(sec["stream"]):
            if x[0] != "BLOCK":
                continue
            def sub(m):
                nonlocal keyed
                keyed += 1
                return f"{m.group(1)} F., No. {family_for(m.group(1), int(m.group(2)))}"
            sec["stream"][i] = ("BLOCK", re.sub(r"((?:[A-Z][\w'.’-]* )*?[A-Z][\w'.’-]*) F\. (\d+)\b", sub, plain(x[1])))
    print(keyed, "key references converted; page drift", dict(drift))
    for f in fallback:
        print("   by page:", f)

    order = [{"src": x[1], "printed": x[2]} for s in sections for x in s["stream"] if x[0] == "PLATE"]
    caps = {f"{c['leaf']:03d}-{c['k']}.png": c["caption"] for c in cuts}
    book = R.Book(HERE, "hpg_jp2.zip", html_name="-", long_side=1600,
                  replace={f"{c['leaf']:03d}-{c['k']}.png": str(HERE / "_src" / "plates" / f"{c['leaf']:03d}-{c['k']}.png")
                           for c in cuts})
    # captions are written by the proofreading pass beside each box; they go
    # to captions/ keyed by the pinned plate ids, which compose() assigns
    L = "abcdefghijklmnopqrstuvwxyz"
    cdir = HERE / "captions"
    cdir.mkdir(exist_ok=True)
    (cdir / "all.txt").write_text("".join(f"{L[i // 26]}{L[i % 26]}\t{caps[o['src']]}\n" for i, o in enumerate(order)))
    for sec in sections:
        # A KEY THAT RUNS OVER A PAGE TURN arrives as two blocks: one block.
        merged = []
        for x in sec["stream"]:
            if x[0] == "BLOCK" and merged and merged[-1][0] == "BLOCK":
                merged[-1] = ("BLOCK", merged[-1][1] + "\n" + x[1])
            else:
                merged.append(x)
        # the key's right-hand results: the print sets them flush right with
        # white space between; " | " was the proofreading pass's separator.
        # A dot leader, the key-maker's usual sign. NOT an em dash: `se
        # typogrify` rewrites ", —" as a bare dash, deleting Gray's comma in
        # the epub while the page kept it.
        sec["stream"] = [("BLOCK", x[1].replace(" | ", " · · · ")) if x[0] == "BLOCK" else x for x in merged]
    for sec in sections:
        sec["stream"] = [(x[0], R.emph_safe(plain(x[1]))) if x[0] == "P" else
                         (x[0], plain(x[1])) if x[0] == "BLOCK" else x for x in sec["stream"]]
    left = [x for s in sections for x in s["stream"] if x[0] in ("P", "BLOCK") and re.search(r"\^\^|^\+ |\[Figure", x[1])]
    assert not left, left[:3]
    print(len(sections), "sections;", len(order), "plates;", notes, "footnotes; hyphens kept:", kept_hyphen[:10])
    rows, described = R.compose(book, sections, plates=order)
    print(len(rows), "plates;", described, "described")


if __name__ == "__main__":
    main()
