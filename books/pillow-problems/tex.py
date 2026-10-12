"""LaTeX -> Unicode, for the 2,436 formulas of Pillow Problems.

Gutenberg #79080 sets every piece of mathematics as a separate SVG file
pulled in by <img> -- one per symbol or fragment, so "sin OP · PN" is four
images in a row. There is no plain-text edition to fall back on. But every
one of those images carries a `data-tex` attribute holding the LaTeX it was
rendered from, and across all 2,436 there are only 55 distinct commands and
three environments. So the mathematics is not lost, it is encoded, and it
can be converted rather than guessed at.

(The `alt` text is MathSpeak -- "StartFraction x Over y EndFraction" -- and
is also machine-reversible, but it is a reading of the formula rather than
the formula. data-tex is the thing itself.)

Alex's ruling: MODERNISE THE NOTATION. Carroll's Victorian factorial, a
vertical bar with the number underlined, becomes "3!"; his mid-height
decimal point becomes "0.5". This is deliberately the opposite of the
symbolic-logic ruling, where his terminology was kept untouched -- there
the words WERE the machine and here the notation is incidental to the
argument, which is what the reader came for.

Two-dimensional work (fractions inside fractions, the aligned environments)
is returned with a `display` flag so prep can set it as an indented block;
everything else comes back as inline text.
"""

import re

GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "theta": "θ", "lambda": "λ", "phi": "φ", "pi": "π",
}

SYMBOL = {
    "therefore": "∴", "because": "∵", "angle": "∠", "triangle": "△",
    "perp": "⊥", "parallel": "∥", "odot": "⊙", "surd": "√",
    "times": "×", "div": "÷", "pm": "±", "neq": "≠",
    "gt": ">", "lt": "<", "ngtr": "≯", "nless": "≮",
    "colon": ":", "quad": " ", "qquad": "  ",
}

# Carroll writes sin, cos, cot &c. as he always did; these are not notation
# to modernise, they are the names of the functions.
FUNC = ("sin", "cos", "tan", "cot", "sec", "cosec")

# A literal "." between two atoms is Carroll's multiplication sign, and to a
# modern eye it reads as a decimal point -- "1/2.c/2" is not a number. It
# becomes "·". Two dots must survive that pass untouched: the one inside
# \text{i. e.} and the decimal point that \cdot produces, so both are
# carried on a sentinel and restored at the end.
DOT_KEEP = "\x01"
# \text{} holds English, where "-" is a hyphen and "." ends a sentence. The
# spacing passes below are for mathematics only, so its content is fenced
# out of them and restored at the end.
TEXT_A, TEXT_B = "\x03", "\x04"
# Likewise "\\&", which the alignment-tab strip would otherwise eat: an
# escaped ampersand is content, a bare one is a column separator.
AMP_KEEP = "\x02"

SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")


def _brace(s, i):
    """Read a braced group starting at s[i] == '{'; return (inner, next_i)."""
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def _arg(s, i):
    """Read one argument at s[i]: a braced group, a command, or one char."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        return _brace(s, i)
    m = re.match(r"\\[a-zA-Z]+|\\.", s[i:])
    if m:
        return m.group(0), i + m.end()
    return s[i], i + 1


# Commands that take arguments. An exponent or subscript must swallow the
# whole construct: "2^\\tfrac{3}{4}" is 2 to the three-quarters, and reading
# only the command name leaves the exponent as a bare "/" with the 3 and
# the 4 spilling into the line as text -- "2^/34". Nineteen formulas.
ARITY = {"frac": 2, "dfrac": 2, "tfrac": 2, "sqrt": 1, "text": 1,
         "overline": 1, "underline": 1, "unicode": 1}


def _script_arg(s, i):
    """Read what an exponent or subscript applies to, arguments and all."""
    a, j = _arg(s, i)
    m = re.fullmatch(r"\\([a-zA-Z]+)", a)
    if m and m.group(1) in ARITY:
        for _ in range(ARITY[m.group(1)]):
            b, j = _arg(s, j)
            a += "{" + b + "}"
    return a, j


def _needs_parens(s):
    """A fraction's part needs brackets unless it is a single atom."""
    s = s.strip()
    if re.fullmatch(r"[A-Za-z0-9α-ω]+[²³⁴⁵⁶⁷⁸⁹]?", s):
        return False
    return bool(re.search(r"[+\-−×·/ ]", s))


def convert(tex):
    """LaTeX string -> (text, is_display)."""
    t = tex.strip()
    display = bool(re.search(r"\\begin\{(aligned|align|array)\}", t)) or "\\[" in t
    t = re.sub(r"^\\[\[(]|\\[\])]$", "", t.strip()).strip()
    # a wrapper brace around the whole thing carries no meaning
    while t.startswith("{") and _brace(t, 0)[1] == len(t):
        t = _brace(t, 0)[0].strip()
    t = _fix_over(t)
    lines = _split_rows(t) if display else [t]
    out = [_inline(l) for l in lines]
    # The source puts its row break BEFORE Carroll's "&c." in one display,
    # stranding a bare "c." on a line of its own under the number it
    # belongs to. Rejoin it.
    fixed = []
    for x in out:
        if x.strip() in ("c.", "&c.", "etc.") and fixed:
            fixed[-1] = fixed[-1].rstrip() + " etc."
        else:
            fixed.append(x)
    return ("\n".join(x for x in fixed if x.strip()), display)


def _fix_over(t):
    """"{A}\\over{B}" -> "\\frac{A}{B}".

    The plain-TeX fraction carries its own groups, and left to the scanner
    it emits a bare "/" while the numerator and denominator lose their
    brackets -- which changes what the line says. Brace-matched rather than
    matched by pattern: the denominator here can be a whole \\begin{array},
    nested three deep, and a regex that allows one level of nesting walks
    straight past it."""
    while True:
        m = re.search(r"\\over(?![a-zA-Z])\s*(?:\\displaystyle\s*)?", t)
        if not m or not t[m.end():m.end() + 1] == "{":
            return t
        den, after = _brace(t, m.end())
        # walk back over the balanced group that ends just before \over
        j, depth = m.start() - 1, 0
        while j >= 0 and t[j] == " ":
            j -= 1
        if j < 0 or t[j] != "}":
            return t
        end = j + 1
        while j >= 0:
            if t[j] == "}":
                depth += 1
            elif t[j] == "{":
                depth -= 1
                if depth == 0:
                    break
            j -= 1
        num = t[j + 1:end - 1]
        t = t[:j] + "\\frac{" + num + "}{" + den + "}" + t[after:]


def _split_rows(t):
    """An aligned/array body -> one string per printed row."""
    t = re.sub(r"\\begin\{(aligned|align|array)\}(\{[^}]*\})?", "", t)
    t = re.sub(r"\\end\{(aligned|align|array)\}", "", t)
    # SPLIT THE ROWS FIRST. "\\\\&c." is a row break followed by Carroll's
    # "&c." with a bare ampersand, and any attempt to protect "\\&" before
    # the split matches the tail of the separator instead -- eating the row
    # break and welding two lines of a derivation together.
    rows = re.split(r"(?<!\\)\\\\", t)
    # within a row, a bare "&" is the alignment tab; "\\&" is content
    return [re.sub(r"(?<!\\)&", " ", r).strip() for r in rows]


# INITIALS ARE NOT MULTIPLICATION. "A. P." is arithmetical progression and
# "A. M." the arithmetic mean; run through the dot rule below they become
# "A·P." and "A·M.", which is a product of two variables. They are the only
# two in the book and both are set as mathematics, so they cannot be told
# apart from a product by shape -- only by being listed.
ABBREV = {"A. P.": "A.P.", "A. M.": "A.M.", "Q. E. F.": "Q.E.F.",
          "Q. E. D.": "Q.E.D.", "i. e.": "i.e."}


def _inline(t):
    """The scanner. One pass, left to right, resolving commands as they come."""
    for a, b in ABBREV.items():
        t = t.replace(a, b.replace(".", DOT_KEEP))
    out, i = [], 0
    while i < len(t):
        ch = t[i]
        if ch == "\\":
            m = re.match(r"\\([a-zA-Z]+)", t[i:])
            if not m:                       # \\, \{ \} \, \& and friends
                out.append({"&": AMP_KEEP, ",": " ", ";": " ", "!": "",
                            " ": " "}.get(t[i + 1:i + 2], t[i + 1:i + 2]))
                i += 2
                continue
            name, i = m.group(1), i + m.end()
            i = _command(name, t, i, out)
            continue
        if ch == "^":
            a, i = _script_arg(t, i + 1)
            out.append(_script(_inline(a), SUP))
            continue
        if ch == "_":
            a, i = _script_arg(t, i + 1)
            out.append(_script(_inline(a), SUB))
            continue
        if ch == "{":
            a, i = _brace(t, i)
            out.append(_inline(a))
            continue
        if ch == "}":
            i += 1
            continue
        if ch in "$~":
            out.append(" " if ch == "~" else "")
            i += 1
            continue
        out.append(ch)
        i += 1
    s = "".join(out)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    s = re.sub(r"(?<=[\w)\]²³⁴⁵⁶⁷⁸⁹′])\s*\.\s*(?=[\w(\[√])", "·", s)
    s = s.replace(AMP_KEEP + "c.", "etc.").replace(AMP_KEEP, "&")
    # A BINARY MINUS WANTS THE SAME AIR AS A PLUS. Left alone it gives
    # "(1 + k), (1-k)", which reads as though the two were different kinds
    # of thing. Only between two mathematical atoms, and never inside
    # \text{}, where a hyphen is a hyphen.
    fenced = re.split(f"({TEXT_A}[^{TEXT_B}]*{TEXT_B})", s)
    for j, part in enumerate(fenced):
        if part.startswith(TEXT_A):
            continue
        part = re.sub(r"\s*([+×÷±=<>])\s*", r" \1 ", part)
        part = re.sub(r"(?<=[\w)\]²³⁴⁵⁶⁷⁸⁹′])\s*-\s*(?=[\w(\[√])",
                      " - ", part)
        fenced[j] = part
    s = "".join(fenced)
    # "\sin A\sin B" comes out "sin Asin B"; a function name needs air in
    # front of it, and its exponent needs none ("sin ² B" -> "sin² B").
    s = re.sub(r"(?<=[A-Za-z0-9α-ω)\]])(?=(?:sin|cos|tan|cot|sec|cosec)\b)",
               " ", s)
    s = re.sub(r"\s+([²³⁴⁵⁶⁷⁸⁹ⁿ⁰¹])", r"\1", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = s.replace(TEXT_A, "").replace(TEXT_B, "")
    return s.replace(DOT_KEEP, ".").strip()


def _script(s, table):
    """Superscript/subscript, as real Unicode where the glyphs exist."""
    s = s.strip()
    if s and all(c in "0123456789+-=()n" for c in s) and table is SUP:
        return s.translate(SUP)
    if s and all(c in "0123456789+-=()" for c in s) and table is SUB:
        return s.translate(SUB)
    return ("^" if table is SUP else "_") + (f"({s})" if len(s) > 1 else s)


def _command(name, t, i, out):
    """Emit one command; return the new index."""
    if name in GREEK:
        out.append(GREEK[name])
        return i
    if name in SYMBOL:
        out.append(SYMBOL[name])
        return i
    if name in FUNC:
        out.append(name + " ")
        return i
    if name in ("frac", "dfrac", "tfrac"):
        a, i = _arg(t, i)
        b, i = _arg(t, i)
        # CARROLL'S FACTORIAL: a vertical bar with the number underlined.
        # \frac{1}{\mid\underline{2}} is 1/2!, and left as printed it is
        # unreadable to anyone under a hundred and thirty.
        num, den = _inline(a), _inline(b)
        num = f"({num})" if _needs_parens(num) else num
        den = f"({den})" if _needs_parens(den) else den
        out.append(f"{num}/{den}")
        return i
    if name == "over":                       # {a \over b}
        out.append("/")
        return i
    if name == "sqrt":
        a, i = _arg(t, i)
        inner = _inline(a)
        out.append(f"√({inner})" if len(inner) > 1 else f"√{inner}")
        return i
    if name in ("overline", "underline"):
        # THE VINCULUM IS CARROLL'S BRACKET. "2×10 - \\overline{x-1}" means
        # 2×10 - (x-1); drop the bar and the sign of the 1 flips silently.
        # Over a bare pair of letters it is a line SEGMENT (AB) and means
        # no such thing, so the content decides.
        a, i = _arg(t, i)
        inner = _inline(a)
        out.append(f"({inner})" if re.search(r"[+\-−]", inner) else inner)
        return i
    if name == "mid":
        # "\mid\underline{3}" -- the factorial. Consume the underline too.
        m = re.match(r"\s*\\underline\s*", t[i:])
        if m:
            a, j = _arg(t, i + m.end())
            out.append(_inline(a) + "!")
            return j
        out.append("|")
        return i
    if name == "text":
        a, i = _arg(t, i)
        out.append(TEXT_A + a.replace(".", DOT_KEEP) + TEXT_B)
        return i
    if name == "unicode":
        a, i = _arg(t, i)
        try:
            out.append(chr(int(a, 16)))
        except ValueError:
            pass
        return i
    if name == "cdot":
        # TWO MEANINGS, AND THE DIFFERENCE IS NOT DECORATIVE. Carroll sets
        # the decimal point at mid height, so "18 \\cdot 65°" is 18.65° and
        # "\\cdot 7" is 0.7, while "a \\cdot b" is a times b. Checked against
        # the MathSpeak in the alt attribute: in all 41 places where a digit
        # follows, it is the decimal point ("18 dot 65 degree"). Read as
        # multiplication it silently turns 1.5430806 into 1 times 5430806.
        m = re.match(r"\s*(\d)", t[i:])
        if m:
            prev = "".join(out).rstrip()
            if prev[-1:].isdigit():
                while out and out[-1].strip() == "":
                    out.pop()
                if out:
                    out[-1] = out[-1].rstrip()
                out.append(DOT_KEEP)
            else:
                out.append("0" + DOT_KEEP)
            return i + m.start(1)
        out.append("·")
        return i
    if name == "dot":
        a, i = _arg(t, i)
        out.append(_inline(a))
        return i
    if name == "atop":
        out.append(" ")
        return i
    if name in ("left", "right"):
        a, i = _arg(t, i)
        a = a.lstrip("\\")               # \left\{ -> {, \right\} -> }
        out.append("" if a in (".", "") else a)
        return i
    if name in ("Large", "large", "displaystyle", "DeclareMathOperator"):
        return i
    if name in ("begin", "end"):
        _, i = _arg(t, i)
        return i
    out.append(name)
    return i
