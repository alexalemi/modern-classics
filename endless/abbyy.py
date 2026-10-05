"""Read the 1945 scan's ABBYY layout (_src/a1945_abbyy.gz) into pages of
paragraphs, keeping what the plain OCR text throws away: each paragraph's
first-line indent (a page that opens unindented is continuing the last
page's paragraph), its alignment, its position, and italic runs.

    python3 endless/abbyy.py LEAF          # dump one leaf's paragraphs
"""
import gzip
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
NS = "{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"


def _tag(e):
    return e.tag.split("}")[-1]


def merge_marks(text):
    """Internal marks -> *italic* and **bold**, closing up runs that the
    OCR split at every formatting change or line end."""
    for a, b in (("⟨i⟩", "⟨/i⟩"), ("⟨b⟩", "⟨/b⟩")):
        text = re.sub(re.escape(b) + r"(\s*|\u00ad)" + re.escape(a), r"\1", text)
    # a mark round nothing but punctuation is noise
    text = re.sub(r"⟨([ib])⟩([^A-Za-z⟨]*)⟨/\1⟩", r"\2", text)
    # bold wins where both apply: the print's bold findings carry no italics
    text = text.replace("⟨i⟩", "*").replace("⟨/i⟩", "*")
    text = text.replace("⟨b⟩", "**").replace("⟨/b⟩", "**")
    return text


def pages():
    """Yield (leaf, [para]) with para = dict(text, indent, left, align, t, b, size)."""
    with gzip.open(HERE / "_src/a1945_abbyy.gz") as f:
        leaf = -1
        for ev, el in ET.iterparse(f, events=("end",)):
            if _tag(el) != "page":
                continue
            leaf += 1
            paras = []
            for block in el.iter():
                if _tag(block) != "block" or block.get("blockType") != "Text":
                    continue
                for par in block.iter():
                    if _tag(par) != "par":
                        continue
                    lines, t, b, size, heavy = [], None, None, [], []
                    for line in par:
                        if _tag(line) != "line":
                            continue
                        t = int(line.get("t")) if t is None else t
                        b = int(line.get("b"))
                        s = ""
                        for fm in line:
                            if _tag(fm) != "formatting":
                                continue
                            txt = "".join(c.text or "" for c in fm)
                            size.append(float(fm.get("fs", "0").rstrip(".") or 0))
                            for flag, op, cl in (("italic", "⟨i⟩", "⟨/i⟩"),):
                                if fm.get(flag) == "true" and txt.strip() and re.search(r"[A-Za-z]{2}", txt):
                                    lead = txt[: len(txt) - len(txt.lstrip())]
                                    trail = txt[len(txt.rstrip()):]
                                    txt = f"{lead}{op}{txt.strip()}{cl}{trail}"
                            s += txt
                        # bold type has the heavier stroke: about 96 against
                        # 58 for the roman at this scan's resolution
                        sw = sorted(int(c.get("meanStrokeWidth")) for c in line.iter()
                                    if _tag(c) == "charParams" and c.get("meanStrokeWidth") and (c.text or "").isalpha())
                        heavy.append(bool(sw) and sw[len(sw) // 2] >= 80)
                        lines.append((int(line.get("l")), s.strip()))
                    if not lines:
                        continue
                    text = ""
                    for _, s in lines:
                        # a line-end hyphen joins with a soft hyphen (U+00AD); the
                        # caller decides between a closed word and a compound
                        if re.search(r"[A-Za-z]-(⟨/[ib]⟩)*$", text):
                            text = re.sub(r"-((⟨/[ib]⟩)*)$", "\u00ad\\1", text) + s
                        elif text.endswith("—") or s.startswith("—"):
                            text = text + s          # a dash at the line end
                        else:
                            text = (text + " " + s).strip()
                    text = merge_marks(text)
                    paras.append({"text": re.sub(r"\s+", " ", text), "indent": int(par.get("startIndent", "0")),
                                  "left": int(par.get("leftIndent", "0")), "align": par.get("align", ""),
                                  "x": lines[0][0], "t": t, "b": b, "size": max(size) if size else 0,
                                  "bold": sum(heavy) / len(heavy)})
            for q in paras:
                q["pw"], q["ph"] = int(el.get("width")), int(el.get("height"))
            yield leaf, paras
            el.clear()


if __name__ == "__main__":
    want = {int(a) for a in sys.argv[1:]}
    for leaf, ps in pages():
        if leaf in want:
            print(f"=== leaf {leaf}")
            for p in ps:
                print(f"[ind={p['indent']} left={p['left']} {p['align']} t={p['t']} fs={p['size']}] {p['text'][:110]}")
        if want and leaf > max(want):
            break
