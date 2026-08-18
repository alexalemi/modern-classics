"""Standard Ebooks XHTML -> chapters/ + manifest.json for The Subjection
of Women.

The same shape as mill/prep.py, which this is adapted from, and the same
two rules that earned their keep there:

  - PARSE THE SOURCE AS XML, NOT WITH REGEX (the epictetus rule), then
    CHECK THE PARSE AGAINST A SECOND, INDEPENDENT READING of the raw
    file that shares no code with it. Two readings that agree are
    evidence; one reading is a hope. Compare CHARACTERS, not tokens: a
    raw reading replaces each tag with a space, so "<i>x</i>," tokenises
    differently from the parsed form, which is a difference in the check
    and not in the text.
  - DELETE NOTEREF ANCHORS AS ELEMENTS, giving each tail to the nearest
    preceding sibling THAT STILL EXISTS. On Liberty had three noterefs
    in one paragraph and the naive version handed note 8's tail to
    note 7, which had itself just been removed; half a sentence vanished
    with every other word present and in order.

DIFFERENCES FROM On Liberty, and both make this the easier book:
  - THERE IS NO EDITORIAL APPARATUS TO SEPARATE. On Liberty's Standard
    Ebooks edition carries a later editor's biographical introduction
    and five of its fourteen endnotes belong to it. Here there is no
    introduction, and ALL THREE endnotes are Mill's own, so all three
    are inlined as "Footnote: ..." paragraphs after the paragraph that
    cites them (the candle pattern), in Mill's voice.
  - THE CHAPTERS HAVE NO TITLES. Standard Ebooks sets a bare <h2> Roman
    numeral, which is what the 1869 printing has. Descriptive titles are
    therefore NEW WRITING, on the soap-bubbles and augustine precedent,
    and were written from each chapter's actual argument rather than
    from its reputation -- see TITLES below.
"""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "source"
OUT = BOOK / "chapters"
X = "{http://www.w3.org/1999/xhtml}"
EPUB = "{http://www.idpf.org/2007/ops}type"

MAXW = 7000                      # an agent must OUTPUT as much as it reads

# WORD-FORM NUMBERS, as in mill/. assemble.CHAP_LINE matches only
# "Chapter <digits>: Title" and nests those as h3 under a Part divider;
# this book has no Parts, so digits would leave four chapters nested
# under nothing.
TITLES = {
    1: "Chapter One: An Opinion That Has Never Been Put on Trial",
    2: "Chapter Two: What the Law Makes of a Wife",
    3: "Chapter Three: Whether Women Should Be Shut Out of Anything",
    4: "Chapter Four: What Would Be Gained",
}


def clean(s):
    """NO-BREAK SPACES ARE INVISIBLE AND BREAK EVERY ANCHOR (bunyan).
    Standard Ebooks sets one inside abbreviations and around dashes."""
    return (s.replace(" ", " ").replace(" ", " ")
             .replace("⁠", "").replace("⁡", ""))


def text_of(el):
    """All text under el, with <em>/<i> carried through as *emphasis*."""
    out = []
    tag = el.tag.split("}")[-1]
    emph = tag in ("em", "i")
    if emph:
        out.append("*")
    out.append(el.text or "")
    for kid in el:
        out.append(text_of(kid))
    if emph:
        # the marker may not enclose a space or assemble.EMPH refuses it
        inner = "".join(out[1:]).strip()
        out = ["*" + inner + "*"] if inner else [""]
    out.append(el.tail or "")
    return "".join(out)


def kill_noterefs(root):
    """Delete noteref anchors AS ELEMENTS, tail to the SURVIVING
    predecessor. See the module docstring for what the other version
    costs."""
    seen = []
    for parent in list(root.iter()):
        prev = None
        for kid in list(parent):
            if kid.tag == f"{X}a" and "noteref" in (kid.get(EPUB) or ""):
                n = int(re.search(r"\d+", kid.get("href") or
                                  kid.get("id") or "0").group())
                seen.append((parent, n))
                tail = kid.tail or ""
                if prev is None:
                    parent.text = (parent.text or "") + tail
                else:
                    prev.tail = (prev.tail or "") + tail
                parent.remove(kid)
            else:
                prev = kid
    return seen


def paragraphs(path):
    """[(text, note_numbers)] for one source file, in document order."""
    root = ET.parse(path).getroot()
    owner = {}
    for parent, n in kill_noterefs(root):
        owner.setdefault(id(parent), []).append(n)
    out = []
    for el in root.find(f"{X}body").iter():
        tag = el.tag.split("}")[-1]
        if tag == "hr":
            out.append(("* * *", []))
        if tag not in ("p", "cite"):
            continue
        s = re.sub(r"\s+", " ", clean(text_of(el))).strip()
        if s:
            out.append((s, owner.get(id(el), [])))
    return out


def notes():
    root = ET.parse(SRC / "endnotes.xhtml").getroot()
    out = {}
    for li in root.iter(f"{X}li"):
        m = re.search(r"\d+", li.get("id") or "")
        if not m:
            continue
        for a in list(li.iter(f"{X}a")):
            if "backlink" in (a.get(EPUB) or ""):
                for p in li.iter():
                    if a in list(p):
                        p.remove(a)
                        break
        s = re.sub(r"\s+", " ", clean(text_of(li))).strip().rstrip("↩").strip()
        out[int(m.group())] = s
    return out


def split_parts(pars, maxw):
    """Cut a chapter into <= maxw-word parts at paragraph boundaries."""
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

    note = notes()
    assert set(note) == {1, 2, 3}, sorted(note)

    manifest, idx = [], 0

    def emit(title, body, part, of):
        nonlocal idx
        name = f"{idx:03d}.txt"
        (OUT / name).write_text(title + "\n\n" + body.rstrip() + "\n")
        manifest.append({"file": name, "title": title, "part": part,
                         "of": of, "words": len(body.split())})
        idx += 1

    used = set()
    for c in range(1, 5):
        pars = []
        for text, ns in paragraphs(SRC / f"chapter-{c}.xhtml"):
            pars.append(text)
            for n in sorted(ns):
                used.add(n)
                pars.append("Footnote: " + note[n])
        parts = split_parts(pars, MAXW)
        for i, part in enumerate(parts, 1):
            emit(TITLES[c], "\n\n".join(part), i, len(parts))

    assert used == set(note), sorted(set(note) - used)
    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    # -- SECOND, INDEPENDENT READING. Shares no code with the parser.
    # The footnotes are compared separately, because the raw reading has
    # them at the back where the source keeps them and the parser has
    # moved them inline.
    want = []
    for c in range(1, 5):
        raw = (SRC / f"chapter-{c}.xhtml").read_text()
        raw = re.sub(r"<head>.*?</head>", " ", raw, flags=re.S)
        raw = re.sub(r"<h2[^>]*>.*?</h2>", " ", raw, flags=re.S)
        raw = re.sub(r'<a[^>]*epub:type="noteref"[^>]*>.*?</a>', " ", raw,
                     flags=re.S)
        want += re.sub(r"\s+", " ", clean(re.sub(r"<[^>]+>", " ", raw))).split()
    got = []
    for m in manifest:
        body = "\n".join((OUT / m["file"]).read_text().split("\n")[1:])
        keep = [p for p in re.split(r"\n\s*\n", body)
                if not p.strip().startswith("Footnote: ")]
        got += " ".join(keep).split()
    for n in sorted(note):
        hits = sum((OUT / m["file"]).read_text().count("Footnote: " + note[n])
                   for m in manifest)
        assert hits == 1, f"note {n} appears {hits} times inline"

    squash = lambda ws: re.sub(r"\s+", "", " ".join(ws)).replace("*", "")
    a, b = squash(want), squash(got)
    if a != b:
        i = next(k for k in range(min(len(a), len(b))) if a[k] != b[k])
        raise SystemExit(f"diverges at char {i}:\n"
                         f"  source ...{a[max(0, i-60):i+60]}\n"
                         f"  output ...{b[max(0, i-60):i+60]}")
    print(f"cross-check: {len(a):,} characters match, in order")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} files, {total:,} words; "
          f"largest {max(m['words'] for m in manifest):,}")
    print(f"{sum(1 for m in manifest if m['of'] > 1)} files are chapter parts")


if __name__ == "__main__":
    main()
