"""Helmholtz, On the Sensations of Tone: a first draft of each page, in this
edition's markup, made mechanically from Archive.org's OCR.

    python3 helmholtz/preproof.py            # writes helmholtz/preproof/NNN.txt

WHY: the page-reading pass that retyped every page kept being stopped by the
API's output filter (the 1885 text is public domain, but it is also a
reprint still in print). So the proofreading pass now CORRECTS this draft
instead of retyping it: an agent writes only fixes (fixes/NNN.fix, applied
by apply_fixes.py), which is how OCR proofreading is normally done anyway.

What the draft does, and no more:
  - paragraphs are the OCR's own (ocr_par), joined into one line each, with a
    line-end hyphen closed up (the proofreader restores real compounds);
  - the first paragraph is dropped when it is the running head, and its
    number becomes the "page:" line;
  - a paragraph set smaller than the body is a footnote: "Footnote: ";
  - a page whose first body paragraph starts in lower case opens "+ ".
Everything else (italics, small capitals, note names, formulas, tables, ¶
marks, figures, footnote continuations) is left for the proofreader.
"""
import gzip
import html
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "_src"


def pages():
    t = gzip.open(SRC / "chocr.html.gz").read().decode()
    return re.split(r'<div class="ocr_page"', t)[1:]


def chars_of(line):
    """[(char, x0, x1)] for a line, spaces restored from the word breaks."""
    out = []
    for w in re.split(r'class="ocrx_word"', line)[1:]:
        cs = re.findall(r'class="ocrx_cinfo" title="x_bboxes (\d+) \d+ (\d+) \d+[^"]*">([^<]*)<', w)
        if not cs:
            continue
        if out:
            out.append((" ", out[-1][2], int(cs[0][0])))
        for x0, x1, c in cs:
            out.append((html.unescape(c), int(x0), int(x1)))
    return out


# Systematic OCR errors that are safe to correct mechanically; everything
# else is left for the proofreader. (Found by the correction pilot.)
CHAR_FIXES = [
    (r"\btlie\b", "the"), (r"\bTlie\b", "The"), (r"\btliat\b", "that"), (r"\bwliich\b", "which"),
    (r"\bAc,", "&c.,"), (r"\bAc\.", "&c."),
    # the printer's space before : ; ? ! -- after a LETTER only, because
    # Ellis writes ratios "1 : 2" and those spaces are his
    (r"(?<=[A-Za-z)]) ([;:?!])", r"\1"),
]


def fix_chars(text):
    for a, b in CHAR_FIXES:
        text = re.sub(a, b, text)
    return text


def text_of(chars):
    return re.sub(r"\s+", " ", "".join(c for c, _, _ in chars)).strip()


def lines_of(par, width=2169):
    """[(text, x_size, y0, chars)] per line; a small-type line that runs
    across BOTH footnote columns (the OCR reads straight across) is split at
    the widest gap near the middle of the page, left column first."""
    out = []
    for ln in re.split(r'class="ocr_line"', par)[1:]:
        m = re.search(r'bbox (\d+) (\d+) (\d+) (\d+); x_size ([\d.]+)', ln)
        chars = chars_of(ln)
        if not (m and chars):
            continue
        out.append((text_of(chars), float(m.group(5)), int(m.group(2)), chars))
    return out


def split_columns(chars, width):
    """(left, right) at a gap of 12px or more between 40% and 60% of the
    page, else None."""
    best = None
    for i in range(1, len(chars)):
        gap = chars[i][1] - chars[i - 1][2]
        mid = (chars[i][1] + chars[i - 1][2]) / 2
        if 0.40 * width < mid < 0.60 * width and gap >= 12 and (not best or gap > best[0]):
            best = (gap, i)
    if not best:
        return None
    i = best[1]
    return text_of(chars[:i]), text_of(chars[i:])


def join(lines):
    s = ""
    for t in lines:
        if s.endswith("-") and not s.endswith("--"):
            s = s[:-1] + t
        else:
            s = (s + " " + t) if s else t
    return re.sub(r"\s+", " ", s).strip()


def main():
    out = HERE / "preproof"
    out.mkdir(exist_ok=True)
    for i, pg in enumerate(pages()):
        pars = [lines_of(p) for p in re.split(r'class="ocr_par"', pg)[1:]]
        pars = [p for p in pars if p]
        if not pars:
            (out / f"{i:03d}.txt").write_text("page: none\n")
            continue
        # BODY SIZE FROM THE TOP OF THE PAGE: on a page with long footnotes
        # the footnote lines outnumber the body lines, and a page-wide median
        # is the footnote size (leaf 103: 41 against a body of 48)
        top = [x for p in pars for _, x, y, _ in p if 200 < y < 1800]
        body = statistics.median(top or [x for p in pars for _, x, _, _ in p])
        left = statistics.median(l[3][0][1] for p in pars for l in p if l[1] >= 0.92 * body) if pars else 0
        right = statistics.median(l[3][-1][2] for p in pars for l in p if l[1] >= 0.92 * body) if pars else 0
        page = "none"
        # THE RUNNING HEAD may come as several paragraphs ("CHAP. V.", the
        # title, the folio): every paragraph in the top band goes, and the
        # folio is read from whichever carries a number
        heads = [p for p in pars if len(p) == 1 and p[0][2] < 200]
        for h in heads:
            m = re.search(r"(?:^|\s)(\d{1,3})(?:\s|$)", h[0][0])
            if m:
                page = m.group(1)
        pars = [p for p in pars if p not in heads]
        paras = []
        for p in pars:
            size = statistics.median(x for _, x, _, _ in p)
            small = size < 0.92 * body
            texts = []
            for t, x, y, chars in p:
                # ELLIS'S ¶ IN THE MARGIN: the OCR reads it as H, U, II, 11,
                # K, ^ ... a token well left of the text column (or right of
                # it) is the pilcrow, set at the start of its line
                if chars and chars[0][1] < left - 25 and not small:
                    k = next((i for i, c in enumerate(chars) if c[0] == " "), len(chars))
                    t = "¶ " + text_of(chars[k:])
                # ... or in the RIGHT margin (odd pages), where it arrives as
                # the line's last token, standing clear of the text edge
                elif chars and not small and chars[-1][2] > right + 25:
                    k = max((i for i, c in enumerate(chars) if c[0] == " "), default=0)
                    tail = text_of(chars[k:])
                    if k and len(tail) <= 3 and not re.fullmatch(r"[a-z]+|\d+\.?", tail):
                        t = "¶ " + text_of(chars[:k])
                texts.append((t, chars))
            if small:
                lefts, rights = [], []
                for t, chars in texts:
                    sp = split_columns(chars, 2169)
                    if sp:
                        lefts.append(sp[0]); rights.append(sp[1])
                    else:
                        (rights if chars and chars[0][1] > 0.5 * 2169 else lefts).append(t)
                chunks = [c for c in (join(lefts), join(rights)) if c]
            else:
                chunks = [join(t for t, _ in texts)]
            for text in chunks:
                text = fix_chars(text)
                if small:
                    # a footnote opens on its mark (the OCR reads * as *, 'f'
                    # or '-f' for a dagger, J for a double dagger); a small-
                    # type paragraph without one continues the footnote
                    # before it, as a further line of the same block
                    if re.match(r"[*†‡§‖]|[\'`-]?f\s|J\s", text) or not (paras and paras[-1].startswith("Footnote: ")):
                        text = "Footnote: " + re.sub(r"^\*\s*", "⁎ ", text)
                    else:
                        paras[-1] += "\n" + text
                        continue
                paras.append(text)
        if paras and paras[0][:1].islower():
            paras[0] = "+ " + paras[0]
        (out / f"{i:03d}.txt").write_text(f"page: {page}\n\n" + "\n\n".join(paras) + "\n")
    print(i + 1, "pages")


if __name__ == "__main__":
    main()
