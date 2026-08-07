"""Read the ABBYY FineReader XML of the 1885 scan into page structure.

The djvu.txt that Archive also offers is a flat dump: it has lost the page
boundaries, the block types, and -- the thing that matters most here --
which text was ITALIC. This book is a play. Its stage directions and its
speaker tags are set in italic, and italic is exactly what the 1885 scan
recognises worst ("a College dudy. Time, midvigJtf"). Working from the
flat text means finding the play's structure by pattern, in the text that
is least trustworthy.

The ABBYY XML records italic="true" on 3,994 runs, bold on 402 and
smallcaps on 292, along with per-block types (653 Text, 29 Picture, 19
Table) and coordinates for everything. So the STRUCTURE can be read off
the markup even where the CHARACTERS are wrong, and the characters can
then be repaired against the 1879 scan, whose italics came out clean.

Nothing here interprets the book; it just turns the XML into something a
prep can reason about.
"""

import gzip
import re
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

NS = "{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}"


@dataclass
class Run:
    text: str
    italic: bool = False
    bold: bool = False
    smallcaps: bool = False
    size: str = ""
    confidence: float = 100.0


@dataclass
class Line:
    runs: list = field(default_factory=list)
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0

    @property
    def text(self):
        return "".join(r.text for r in self.runs)

    @property
    def italic_share(self):
        n = sum(len(r.text.strip()) for r in self.runs)
        i = sum(len(r.text.strip()) for r in self.runs if r.italic)
        return i / n if n else 0.0


@dataclass
class Block:
    kind: str
    left: int
    top: int
    right: int
    bottom: int
    paragraphs: list = field(default_factory=list)   # list[list[Line]]

    @property
    def lines(self):
        return [l for p in self.paragraphs for l in p]

    @property
    def text(self):
        return " ".join(l.text for l in self.lines)


@dataclass
class Page:
    number: int
    width: int
    height: int
    blocks: list = field(default_factory=list)


def _line(el):
    ln = Line(top=int(el.get("t", 0)), bottom=int(el.get("b", 0)),
              left=int(el.get("l", 0)), right=int(el.get("r", 0)))
    for fmt in el.findall(f"{NS}formatting"):
        chars = fmt.findall(f"{NS}charParams")
        text = "".join(c.text or " " for c in chars)
        conf = [int(c.get("charConfidence", 100)) for c in chars
                if (c.text or " ").strip()]
        ln.runs.append(Run(
            text=text,
            italic=fmt.get("italic") == "true",
            bold=fmt.get("bold") == "true",
            smallcaps=fmt.get("smallcaps") == "true",
            size=fmt.get("fs", ""),
            confidence=sum(conf) / len(conf) if conf else 100.0))
    return ln


def pages(path):
    """Stream the document a page at a time; the file is 100 MB unpacked."""
    with gzip.open(path, "rb") as fh:
        num = 0
        for event, el in ET.iterparse(fh, events=("end",)):
            if el.tag != f"{NS}page":
                continue
            num += 1
            pg = Page(number=num, width=int(el.get("width", 0)),
                      height=int(el.get("height", 0)))
            for b in el.findall(f"{NS}block"):
                blk = Block(kind=b.get("blockType", "?"),
                            left=int(b.get("l", 0)), top=int(b.get("t", 0)),
                            right=int(b.get("r", 0)), bottom=int(b.get("b", 0)))
                for par in b.iter(f"{NS}par"):
                    lines = [_line(l) for l in par.findall(f"{NS}line")]
                    if lines:
                        blk.paragraphs.append(lines)
                pg.blocks.append(blk)
            yield pg
            el.clear()


def clean(s):
    """Whitespace only. Character repair belongs to prep, not here."""
    return re.sub(r"[ \t]+", " ", s.replace("­", "")).strip()
