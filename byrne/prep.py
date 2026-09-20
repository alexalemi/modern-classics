"""Oliver Byrne, The First Six Books of the Elements of Euclid (1847), in
Sergey Slyusarev's LaTeX + MetaPost recreation: a RESTORED EDITION that is
CC BY-SA 4.0, not public domain (Alex's ruling, 2026-09-20; see NOTES.txt).

    python3 byrne/prep.py        # after capture/run.sh

THE TEXT IS NOT CONVERTED FROM LATEX. LuaTeX typesets the recreation and a
pre_linebreak_filter (capture/capture.lua) serialises every paragraph as TeX
built it: characters with their fonts, spaces, fractions and brace stacks,
and each MetaPost picture box tagged with its capture number. The same
macros ship every picture out as a page of its own, cropped to the picture
(capture/hooks.tex), so picture n is the n-th small page of cap.pdf and
becomes an SVG. What TeX typeset is exactly what this edition prints; the
only reading done here is of TeX's own output.

  - a paragraph that is ONE picture and nothing else is a diagram (Byrne's
    margin figure, or a plate): a [Figure] block;
  - every other picture is inline, ⟦g:ID⟧, with alt text from the picture's
    own name in the recreation (ulineAB, angleACB) and its colours;
  - a TeX fraction of pictures is ⟪NUM‖DEN⟫, a brace group ⟬{A‖B}⟭;
  - identical SVGs are one file (6,115 pictures, 1,782 distinct).

WITNESSES, asserted: every captured picture is placed exactly once (margin
diagrams, which \\marginpar typesets twice, are deduplicated by content);
every Book and every Proposition of the recreation's own numbering is found
in order; no legacy font slot survives unmapped.
"""
import collections
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
BUILD = HERE / "_src" / "build"
IMG = ROOT / "site" / "images" / "byrne"

BODY = 655360          # 10pt in sp: body text
H1 = 943718            # 14.4pt: Introduction, Book I, Definitions, Propositions
H2 = 786432            # 12pt: I.1, I.1 Prop. I. Prob.

# legacy TeX math fonts: slot -> text
SLOTS = {
    "cmr10": {40: "(", 41: ")", 43: "+", 58: ":", 59: ";", 61: "=", **{48 + i: str(i) for i in range(10)}},
    "cmr7": {48 + i: "⁰¹²³⁴⁵⁶⁷⁸⁹"[i] for i in range(10)},
    "cmsy10": {0: "−", 1: "·", 2: "×", 54: "̸", 63: "⊥", 102: "{", 103: "}", 107: "∥"},
    "cmsy7": {48: "′", 2: "×"},
    "msam10": {41: "∴", 42: "∵"},
    "msbm10": {4: "≮", 5: "≯", 44: "∦"},
    "cmex10": {40: "(", 41: ")", 9: "}", 8: "{", 26: "{", 27: "}", 110: "{", 111: "}",
               56: "{", 58: "{", 60: "{", 62: "", 57: "}", 59: "}", 61: "}", 63: ""},
}
OML = "EBGaramond-Italic--oml-ebgaramond"


def slot(m):
    font, n = m.group(1), int(m.group(2))
    if font == OML:
        if 65 <= n <= 90 or 97 <= n <= 122:
            return chr(n)
        return {58: ".", 59: ",", 60: "<", 62: ">"}[n]
    return SLOTS[font][n]


PALETTE = {"red": (217, 77, 26), "blue": (38, 89, 153), "yellow": (242, 179, 26), "black": (0, 0, 0)}


def colours(svg):
    seen = []
    for h in re.findall(r'(?:fill|stroke)="#([0-9a-fA-F]{6})"', svg):
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        if rgb == (255, 255, 255):
            continue
        name = min(PALETTE, key=lambda k: sum((a - b) ** 2 for a, b in zip(PALETTE[k], rgb)))
        if name not in seen:
            seen.append(name)
    return seen


KINDS = [("tworightangles", "two right angles"), ("onerightangle", "right angle"),
         ("anglewithsides", "angle"), ("angle", "angle"), ("uline", "line"), ("pline", "line"),
         ("sline", "line"), ("line", "line"), ("triangle", "triangle"), ("polygon", "figure"),
         ("circle", "circle"), ("arc", "arc"), ("square", "square"),
         ("parallelogram", "parallelogram"), ("magnitude", "magnitude"), ("pointl", "point"),
         ("point", "point"), ("fig", "figure"), ("lastPicture", "figure")]


def alt_text(name, svg):
    n = re.sub(r"^instanceOffspringPicture", "", name)
    if name == "instanceMainPicture":
        kind, rest = "diagram", ""
    else:
        kind, rest = "figure", n
        for k, v in KINDS:
            if n.startswith(k):
                kind, rest = v, n[len(k):]
                break
    letters = re.sub(r"\.\d*cm$|[^A-Za-z']", "", rest) if kind not in ("magnitude", "figure") else ""
    cs = colours(svg)
    col = " and ".join(cs) if len(cs) <= 2 else ", ".join(cs[:-1]) + " and " + cs[-1]
    words = [w for w in (col, kind, letters) if w]
    return " ".join(words)


def main():
    rows = [json.loads(l) for l in (BUILD / "paragraphs.jsonl").open()]
    pics = [l.rstrip("\n").split("\t") for l in (BUILD / "pictures.tsv").open()]
    pages = [int(x) for x in (BUILD / "picpages.txt").read_text().split()]
    assert len(pics) == len(pages), (len(pics), len(pages))

    # ---- pictures: dedupe by content
    IMG.mkdir(parents=True, exist_ok=True)
    for f in IMG.iterdir():
        if f.is_file():
            f.unlink()
    gid, meta, svgs = {}, {}, {}
    byhash = {}
    for (n, name, w, h, d), pg in zip(pics, pages):
        svg = (BUILD / "svg" / f"p{pg}.svg").read_text()
        k = hashlib.sha1(svg.encode()).hexdigest()
        if k not in byhash:
            i = f"{len(byhash):04x}"
            byhash[k] = i
            alt = alt_text(name, svg)
            alt = alt[0].upper() + alt[1:] + "." if alt else "Figure."
            # every SVG carries its description as <title> (se lint s-027)
            svg = re.sub(r"(<svg[^>]*>)", lambda m: m.group(1) + f"\n<title>{alt}</title>", svg, count=1)
            (IMG / f"g{i}.svg").write_text(svg)
            m = re.search(r'width="([\d.]+)pt" height="([\d.]+)pt"', svg)
            meta[i] = {"w": max(1, round(float(m.group(1)) * 4 / 3)), "h": max(1, round(float(m.group(2)) * 4 / 3)),
                       "alt": alt}
        gid[int(n)] = byhash[k]
        svgs[int(n)] = name
    (HERE / "glyphs.json").write_text(json.dumps(meta, indent=0, ensure_ascii=False))
    print(len(pics), "pictures,", len(byhash), "distinct")

    # ---- paragraphs -> markup
    unmapped = collections.Counter()

    def text_of(items, top=True):
        # ITALIC RUNS: TeX sets each word as its own glyph run, with the
        # spaces between in no font at all. A space between two italic runs
        # is italic, so a phrase is ONE span, not a span per word.
        runs = []
        for it in items:
            if it[0] == "t":
                s = re.sub(r"⟨([^:⟩]+):(\d+)⟩", lambda m: slot(m) if (m.group(1) in SLOTS or m.group(1) == OML)
                           else unmapped.update([m.group(0)]) or "?", it[1])
                runs.append(["t", s, ("Italic" in it[2] and it[2] != OML) if s.strip() else None])
            else:
                runs.append(["x", it, None if it[0] == "p" else False])
        for i, r in enumerate(runs):
            # a bare space, or an inline picture, takes its neighbours' style
            if r[2] is None:
                prev = next((x[2] for x in reversed(runs[:i]) if x[2] is not None), False)
                nxt = next((x[2] for x in runs[i + 1:] if x[2] is not None), False)
                r[2] = bool(prev and nxt)
        out, cur = [], []

        def close():
            if cur:
                body = "".join(cur)
                lead, core, trail = re.match(r"(\s*)(.*?)(\s*)$", body, re.S).groups()
                out.append(f"{lead}*{core}*{trail}" if core else body)
                cur.clear()
        for r in runs:
            if r[0] == "t":
                if r[2]:
                    cur.append(r[1])
                else:
                    close()
                    out.append(r[1])
                continue
            it = r[1]
            if it[0] == "p" and r[2]:
                cur.append(f"⟦g:{gid[it[1]]}⟧")
                used[it[1]] += 1
                continue
            close()
            if it[0] == "p":
                out.append(f"⟦g:{gid[it[1]]}⟧")
                used[it[1]] += 1
            elif it[0] == "frac":
                out.append(f"⟪{text_of(it[1], False).strip()}‖{text_of(it[2], False).strip()}⟫")
            elif it[0] == "stack":
                parts = [text_of(r, False).strip() for r in it[1]]
                parts = [p for p in parts if p]
                if len(parts) == 1:
                    out.append(parts[0])          # a one-row stack is just its row
                elif parts:
                    out.append("⟬" + "‖".join(parts) + "⟭")
            elif it[0] == "br":
                out.append("\n")
        close()
        s = "".join(out)
        # a stack between brace characters is a brace group
        s = re.sub(r"\{\s*⟬([^⟬⟭]*)⟭\s*\}?", r"⟬{\1}⟭", s)
        s = s.replace("≠", "≠").replace("̸=", "≠")
        return s

    used = collections.Counter()
    paras = []
    for r in rows:
        if r.get("event") == "sect":
            counter, num, title = r["text"].split("|", 2)
            paras.append(("SECT", (counter, num, title), r["page"]))
            continue
        its = r.get("items") or []
        if not its:
            continue
        sizes = [i[3] for i in its if i[0] == "t" and i[1].strip() and i[3]]
        size = max(sizes) if sizes else 0
        only_pic = [i for i in its if not (i[0] == "t" and not i[1].strip())]
        if len(only_pic) == 1 and only_pic[0][0] == "p":
            paras.append(("FIG", only_pic[0][1], r["page"]))
            continue
        raw = text_of(its)
        # a drop cap is set apart from its word by the lettrine box ("F   rom");
        # "A line" has one space and is not touched
        raw = re.sub(r"^\s*([A-Z])\s{2,}(?=[a-z])", r"\1", raw)
        t = re.sub(r"[ \t ]+", " ", raw).strip()
        t = re.sub(r" *\n *", "\n", t)
        if not t:
            continue
        paras.append(("H1" if size >= H1 else "H2" if size >= H2 else "SMALL" if size and size < BODY else "P", t, r["page"]))
    assert not unmapped, unmapped.most_common(10)

    # A BOXED ARRAY IN THE MARGIN (Book V's letter tables) arrives three
    # times: its rows as paragraphs of their own, then the box as a stack,
    # and all of it again because \marginpar sets it twice. Keep one stack.
    cleaned = []
    for p_ in paras:
        if p_[0] == "P" and p_[1].startswith("⟬") and p_[1].endswith("⟭"):
            rows_ = p_[1][1:-1].strip("{}").split("‖")
            while cleaned and cleaned[-1][0] in ("P", "SMALL") and cleaned[-1][1] in rows_:
                cleaned.pop()
            if cleaned and cleaned[-1][:2] == p_[:2]:
                continue
        cleaned.append(p_)
    paras = cleaned

    # title page and the recreation's credits (page 1-2) are not the book
    start = next(i for i, p in enumerate(paras) if p[0] == "H1" and p[1] == "Introduction")
    credits = [p[1] for p in paras[:start] if p[0] in ("P", "SMALL")]
    for p in paras[:start]:
        if p[0] == "FIG":
            used[p[1]] += 1          # the title page's ornament: the page is not reproduced
    paras = paras[start:]

    # ---- sections
    sections, part, lettrine = [], None, None
    props_seen = []
    last_fig_hash = None
    fig_order = []
    for kind, t, page in paras:
        if kind == "FIG":
            g = gid[t]
            if last_fig_hash == g:          # \marginpar sets the diagram twice
                used[t] += 1
                continue
            last_fig_hash = g
            used[t] += 1
            sections[-1]["stream"].append(("FIG", g))
            fig_order.append(g)
            continue
        last_fig_hash = None
        if kind == "H1":
            if re.fullmatch(r"Book [IVX]+", t):
                part = t
                continue
            if t in ("Propositions",):
                continue
            if t == "Contents":
                break                  # the recreation's list of page numbers: the end of the book
            title = f"{part}: {t}" if part and t in ("Definitions", "Postulates", "Axioms") else t
            sec = {"title": title, "stream": [], "chapter": bool(part), "book": part}
            if part and not any(s.get("_part") == part for s in sections):
                sec["part_before"] = part
                sec["_part"] = part
            sections.append(sec)
            continue
        if kind == "H2":
            continue                  # the visible heading; the SECT event carries it
        if kind == "SECT":
            counter, num, title = t
            if counter in ("proposition", "propositionAZ"):
                pk = "Problem" if re.search(r"prob", title, re.I) else "Theorem" if re.search(r"theor", title, re.I) else None
                ttl = f"Proposition {num}" + (f" ({pk})" if pk else "")
                sec = {"title": ttl, "stream": [], "chapter": True, "book": part}
                if not any(s_.get("_part") == part for s_ in sections):
                    sec["part_before"] = part
                    sec["_part"] = part
                sections.append(sec)
                props_seen.append(num)
            else:
                # a Book that opens straight on its definitions, with no
                # "Definitions" heading (Book II): the section opens here
                cur = sections[-1]
                if cur.get("book") != part and part and part != "__contents__":
                    kind_name = {"definition": "Definitions", "definitionAZ": "Definitions",
                                 "axiom": "Axioms", "postulate": "Postulates"}.get(counter, "Definitions")
                    sec = {"title": f"{part}: {kind_name}", "stream": [], "chapter": True, "book": part}
                    if not any(s_.get("_part") == part for s_ in sections):
                        sec["part_before"] = part
                        sec["_part"] = part
                    sections.append(sec)
                label = num + (f" {title}" if title.strip() else "")
                sections[-1]["stream"].append(("P", label))    # I.1, a definition's number
            continue
        # a drop cap: the letter alone, then the paragraph without it
        if kind == "P" and re.fullmatch(r"[A-Z]", t):
            lettrine = t
            continue
        # the drop cap set apart from its word: "F   rom a given point"
        t = re.sub(r"^([A-Z]) {2,}(?=[a-z])", r"\1", t)
        if lettrine:
            t2 = re.sub(r"^\s*" + lettrine + r"\s+(?=[a-z])", lettrine, t, count=1)
            if t2 == t and not t.startswith(lettrine):
                t2 = lettrine + t
            t, lettrine = t2, None
        sections[-1]["stream"].append(("P" if kind != "SMALL" else "SMALL", t))

    missing = [n for n in range(1, len(pics) + 1) if not used[n]]
    assert not missing, f"{len(missing)} pictures never placed, first {missing[:10]}"
    props = [s["title"] for s in sections if s["title"].startswith("Proposition")]
    # WITNESS: the recreation's own numbering, Book by Book, with no gap
    books = collections.OrderedDict()
    for n in props_seen:
        b, k = n.split(".")
        books.setdefault(b, []).append(k)
    for b, ks in books.items():
        nums = [int(k) for k in ks if k.isdigit()]
        assert nums == list(range(1, len(nums) + 1)), (b, nums[:5])
    print(len(sections), "sections;", len(props), "propositions;", {b: len(v) for b, v in books.items()})

    # ---- compose
    L = "abcdefghijklmnopqrstuvwxyz"
    figs = []
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    plate_of = {}
    for k, sec in enumerate(sections):
        src, mod = [sec["title"], ""], [sec["title"], ""]
        for kind, v in sec["stream"]:
            if kind == "FIG":
                # one plate per PLACEMENT: a diagram reprinted in a later
                # proposition would otherwise give two figures one id
                i = len(plate_of)
                pid = L[i // 676] + L[(i // 26) % 26] + L[i % 26]
                plate_of[(v, i)] = pid
                svg = (IMG / f"g{v}.svg").read_text()
                cap = f"The diagram for {sec['title'].split(' (')[0]}, in Byrne\u2019s colours."
                svg = re.sub(r"<title>.*?</title>", f"<title>{cap}</title>", svg, count=1)   # = its alt (s-022)
                (IMG / f"fig{pid}.svg").write_text(svg)
                src.append(f"[Figure {pid}]")
                mod.append(f"[Figure {pid}: {cap}]")
            else:
                src.append(v)
                mod.append(v)
            src.append("")
            mod.append("")
        (HERE / "chapters" / f"{k:03d}.txt").write_text("\n".join(src).rstrip() + "\n")
        (HERE / "modern_chapters" / f"{k:03d}.txt").write_text("\n".join(mod).rstrip() + "\n")
        e = {"file": f"{k:03d}.txt", "title": sec["title"], "part": 1, "of": 1}
        if sec.get("chapter"):
            e["chapter"] = True
        if sec.get("part_before"):
            e["part_before"] = sec["part_before"]
        manifest.append(e)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    # a picture used only as a block diagram ships as its fig*.svg plate; its
    # glyph copy would sit in the epub referenced by nothing
    inline = set()
    for f in (HERE / "chapters").glob("*.txt"):
        inline |= set(re.findall(r"⟦g:([0-9a-f]+)⟧", f.read_text()))
    for i in list(meta):
        if i not in inline:
            (IMG / f"g{i}.svg").unlink()
            del meta[i]
    (HERE / "glyphs.json").write_text(json.dumps(meta, indent=0, ensure_ascii=False))
    print(len(meta), "inline pictures kept")
    (HERE / "plates.json").write_text(json.dumps([{"id": p, "source": f"g{g[0]}.svg", "printed": ""}
                                                  for g, p in plate_of.items()], indent=1) + "\n")
    (HERE / "_src" / "credits.txt").write_text("\n".join(credits) + "\n")
    print(len(plate_of), "diagrams;", len(manifest), "files")


if __name__ == "__main__":
    main()
