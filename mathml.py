"""LaTeX -> MathML, for BOTH renderers.

A restored edition prints the mathematics as the author printed it, so the
formulas are carried through chapters/ as LaTeX -- \\(...\\) inline and
\\[...\\] displayed, exactly the `data-tex` Gutenberg's transcription
stores on every formula image -- and typeset at render time. This is the
opposite of pillow-problems/tex.py, which flattens LaTeX to Unicode text:
that was a retelling, where Alex ruled to modernise the notation.

pandoc does the conversion. Every distinct formula is converted once and
cached in build/mathml-cache.json, so a rebuild costs nothing. The
<semantics>/<annotation> wrapper pandoc adds is removed: the LaTeX is not
for the reader, and `se lint` has opinions about annotation elements.

MATH is the one pattern both renderers use to find a formula in text. It
runs BEFORE emphasis, because LaTeX is full of underscores and asterisks
that assemble.EMPH would otherwise read as italics.
"""
import json
import re
import subprocess
from pathlib import Path

CACHE = Path(__file__).parent / "build" / "mathml-cache.json"
MATH = re.compile(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)

# pandoc's TeX reader refuses a few things MathJax accepts; each is
# rewritten to an equivalent it knows. Asserted nowhere because they are
# typographic only: a size change, and a quotation mark spelled as a
# code point.
PRE = [
    (re.compile(r"\\unicode\{x201c\}"), "“"),
    (re.compile(r"\\unicode\{x201d\}"), "”"),
    (re.compile(r"\\(?:tiny|Tiny|small|large|Large)\b\s*"), ""),
]

_cache = None


def _load():
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    return _cache


def _clean(tex):
    for pat, rep in PRE:
        tex = pat.sub(rep, tex)
    return tex.strip()


def _strip(m):
    m = re.sub(r"<semantics>(.*)<annotation[^>]*>.*?</annotation></semantics>",
               r"\1", m, flags=re.S)
    return m.replace(' display="inline"', "")


def convert_all(items):
    """items: iterable of (tex, display). Fills the cache in one pandoc run."""
    cache = _load()
    todo = sorted({(t, d) for t, d in items if f"{int(d)}{t}" not in cache})
    if not todo:
        return
    doc = "\n\n".join(f"MARK{i}\n\n" + (f"$${_clean(t)}$$" if d else f"${_clean(t)}$")
                      for i, (t, d) in enumerate(todo))
    r = subprocess.run(["pandoc", "-f", "latex", "-t", "html", "--mathml"],
                       input=doc, capture_output=True, text=True, timeout=600)
    if r.returncode:
        raise SystemExit(f"pandoc failed: {r.stderr[:500]}")
    parts = re.split(r"<p>MARK(\d+)</p>", r.stdout)
    got = {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    bad = []
    for i, (t, d) in enumerate(todo):
        m = re.search(r"<math.*?</math>", got.get(i, ""), re.S)
        if not m or "merror" in m.group(0):
            bad.append(t)
            continue
        cache[f"{int(d)}{t}"] = _strip(m.group(0))
    if bad:
        raise SystemExit(f"{len(bad)} formula(s) pandoc could not typeset, "
                         f"first: {bad[0][:120]!r}")
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0))


# SPOKEN READINGS for alttext, which `se lint` requires on every formula
# (s-089). A book's prep may write {book}/mathalt.json, mapping a formula's
# LaTeX (whitespace-normalised) to a reading; Gutenberg's own alt text on
# each formula image is MathSpeak ("StartFraction d y Over d x EndFraction"),
# which is exactly that. A formula with no reading gets its LaTeX.
_alt = None


def _norm(tex):
    return re.sub(r"\s+", " ", tex).strip()


def _alts():
    global _alt
    if _alt is None:
        _alt = {}
        for f in sorted(Path(__file__).parent.glob("*/mathalt.json")):
            _alt.update(json.loads(f.read_text()))
    return _alt


def to_mathml(tex, display):
    key = f"{int(display)}{tex}"
    cache = _load()
    if key not in cache:
        convert_all([(tex, display)])
    m = cache[key]
    # pandoc sets style="text-align: ..." beside every columnalign; the
    # attribute says the same thing and `se lint` rejects inline style (x-012)
    m = re.sub(r' style="[^"]*"', "", m)
    # an empty table cell (an aligned formula's blank column) is an empty
    # element to `se lint` (s-010); <mspace/> is the one filler it exempts
    m = re.sub(r"<mtd([^>]*)(?:/>|></mtd>)", r"<mtd\1><mspace/></mtd>", m)
    # likewise an empty group, which pandoc writes for LaTeX's {}; mspace
    # keeps the parent's argument count (a superscript still has two)
    m = re.sub(r"<mrow(?:/>|></mrow>)", "<mspace/>", m)
    alt = _alts().get(_norm(tex)) or _norm(tex)
    alt = alt.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    return m.replace("<math", f'<math alttext="{alt}"', 1)


def formulas(text):
    """(tex, display) for every formula in a piece of text."""
    return [(m.group(1) or m.group(2), m.group(2) is not None)
            for m in MATH.finditer(text)]


# ---- the epub form. XHTML needs MathML in its own namespace, and `se clean`
# (lxml) HOISTS a default xmlns on <math> up to <html>, where it replaced the
# XHTML namespace and every chapter with a formula failed to parse. Standard
# Ebooks writes MathML with an `m:` prefix declared on the root element, and
# `se build-manifest` gives a file the `mathml` property only when that
# declaration is on <html> -- so both halves are needed.
NS = "http://www.w3.org/1998/Math/MathML"
_BLOCK = re.compile(r"<math\b.*?</math>", re.S)
_TAG = re.compile(r"<(/?)([A-Za-z][\w-]*)")


def prefixed(xhtml):
    """Every <math>...</math> in a fragment, rewritten as <m:math>...</m:math>."""
    def one(m):
        s = se_safe(m.group(0)).replace(f' xmlns="{NS}"', "")
        return _TAG.sub(lambda t: f"<{t.group(1)}m:{t.group(2)}", s)
    return _BLOCK.sub(one, xhtml)


def declare(xhtml):
    """Add xmlns:m to the root of a document that uses it, and only then:
    a file declared MathML-bearing that carries none is its own epubcheck
    complaint."""
    if "<m:math" not in xhtml or "xmlns:m=" in xhtml:
        return xhtml
    return xhtml.replace('<html xmlns="http://www.w3.org/1999/xhtml"',
                         f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:m="{NS}"', 1)


def se_safe(mathml_str):
    """Dodge a bug in `se build`'s compatible-epub MathML replacement.

    se_epub_build._replace_mathml rewrites each msup/msub's second argument
    as <sup>/<sub>, wrapping EVERY descendant m:mrow with ONE shared element;
    with two or more nested groups (an exponent holding a fraction of two
    grouped terms) lxml refuses to move that element a second time --
    "cannot add ancestor as sibling" -- and the whole build dies. Inside
    script arguments the nested groups become <mstyle>, which groups exactly
    as <mrow> does and which that code does not look for. Epub only.
    """
    from lxml import etree
    root = etree.fromstring(mathml_str)
    q = "{%s}" % NS
    for script in root.iter(q + "msup", q + "msub", q + "msubsup"):
        for arg in list(script)[1:]:
            for mrow in arg.iter(q + "mrow"):
                if mrow is not arg:
                    mrow.tag = q + "mstyle"
    return etree.tostring(root, encoding="unicode")
