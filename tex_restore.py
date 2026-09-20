"""Distributed Proofreaders LaTeX -> the restored-edition stream.

    import tex_restore as T
    doc = T.Doc(tex_source, macros={...})
    sections = doc.sections(...)          # [{"title", "stream"}]

Some Gutenberg books exist only as the LaTeX a Distributed Proofreaders
volunteer typeset them in (Whitehead's Introduction to Mathematics,
Poincaré's Science and Hypothesis). That LaTeX is a far better source
than any HTML would be -- the mathematics is already mathematics -- but
it is a document to be READ, not compiled: page separators, index
entries, running heads, and a small set of editorial macros that record
what the transcriber changed:

    \\Typo{printed}{corrected}   the printer's misprint, and its correction
    \\Chg{printed}{regularised}  a change made for consistency only
    \\Add{x}                     punctuation the printer left out

The house rule for a restored edition decides them: a misprint stays
corrected (it is an error, not the author's word), a regularisation is
REVERSED to what was printed, and an addition is kept (it is the
missing stop after a displayed formula). Each book's prep can override.

The stream is the one restore_lib.compose() takes: ("P", text) with
*emphasis* and \\(tex\\) / \\[tex\\], ("BLOCK", tab-indented lines),
("PLATE", src, printed), ("H", level, text).
"""
import re


class Doc:
    def __init__(self, src, *, chg="printed", extra=None):
        self.src = src
        self.chg = chg
        self.extra = extra or {}
        self.labels = {}          # \Pagelabel{x} -> section index, filled by sections()
        self.pagerefs = []        # (section index, label) of every \Pageref
        self.footnotes = 0

    # ------------------------------------------------------------ lexing
    @staticmethod
    def group(s, i):
        """s[i] == '{': return (content, index after the closing brace)."""
        assert s[i] == "{", s[i:i + 30]
        depth, j = 0, i
        while j < len(s):
            c = s[j]
            if c == "\\":
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return s[i + 1:j], j + 1
            j += 1
        raise ValueError("unbalanced brace at " + s[i:i + 60])

    @staticmethod
    def opt(s, i):
        """Optional [..] at s[i] (after spaces): (content or None, index)."""
        j = i
        while j < len(s) and s[j] in " \t":
            j += 1
        if j < len(s) and s[j] == "[":
            depth, k = 0, j
            while k < len(s):
                if s[k] == "[":
                    depth += 1
                elif s[k] == "]":
                    depth -= 1
                    if depth == 0:
                        return s[j + 1:k], k + 1
                k += 1
        return None, i

    def args(self, s, i, n, optional=False):
        o, i = self.opt(s, i) if optional else (None, i)
        out = []
        for _ in range(n):
            while i < len(s) and s[i] in " \t\n":
                i += 1
            if s[i] == "{":
                a, i = self.group(s, i)
            else:                                  # a bare token argument
                a, i = s[i], i + 1
            out.append(a)
        return o, out, i

    # ------------------------------------------------------------ cleanup
    @staticmethod
    def strip_comments(s):
        return re.sub(r"(?<!\\)%.*", "", s)

    def drop_macro(self, s, name, nargs, optional=False):
        """Remove every \\name[opt]{..}... with its arguments."""
        out, i = [], 0
        pat = re.compile(r"\\" + name + r"(?![A-Za-z])")
        while True:
            m = pat.search(s, i)
            if not m:
                out.append(s[i:])
                return "".join(out)
            out.append(s[i:m.start()])
            _, _, i = self.args(s, m.end(), nargs, optional)

    def replace_macro(self, s, name, nargs, fn, optional=False):
        out, i = [], 0
        pat = re.compile(r"\\" + name + r"(?![A-Za-z])")
        while True:
            m = pat.search(s, i)
            if not m:
                out.append(s[i:])
                return "".join(out)
            out.append(s[i:m.start()])
            o, a, i = self.args(s, m.end(), nargs, optional)
            out.append(fn(o, *a))

    # ------------------------------------------------------------ text
    MATH_ENVS = ("align*", "alignat*", "gather*", "multline*", "equation*", "displaymath")

    def hold_math(self, s):
        """Take every formula out, so text rules cannot touch it."""
        held = []

        def keep(tex, display):
            tex = tex.replace("·", r"\cdot ").replace("°", r"^{\circ}").replace("×", r"\times ")
            held.append((tex.strip(), display))
            return f"\x00M{len(held) - 1}\x00"
        for env in self.MATH_ENVS:
            e = re.escape(env)
            def envsub(m, env=env):
                body = m.group(2)
                if env.startswith("alignat"):
                    body = re.sub(r"^\{\d+\}", "", body.lstrip())
                    return keep(r"\begin{alignedat}{9}" + body + r"\end{alignedat}", True)
                if env.startswith("align"):
                    return keep(r"\begin{aligned}" + body + r"\end{aligned}", True)
                if env.startswith("gather") or env.startswith("multline"):
                    return keep(r"\begin{gathered}" + body + r"\end{gathered}", True)
                return keep(body, True)
            s = re.sub(r"\\begin\{(" + e + r")\}(.*?)\\end\{" + e + r"\}", envsub, s, flags=re.S)
        # \Eq{..} in running text is \ensuremath: inline math
        s = self.replace_macro(s, "Eq", 1, lambda o, a: "$" + a + "$")
        s = re.sub(r"\\\[(.*?)\\\]", lambda m: keep(m.group(1), True), s, flags=re.S)
        s = re.sub(r"\$\$(.*?)\$\$", lambda m: keep(m.group(1), True), s, flags=re.S)
        s = re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lambda m: keep(m.group(1), False), s, flags=re.S)
        return s, held

    @staticmethod
    def math_cleanup(tex, doc):
        tex = doc.replace_macro(tex, "Tag", 1, lambda o, a: r"\qquad " + a)
        tex = doc.replace_macro(tex, "Eq", 1, lambda o, a: a)
        tex = doc.drop_macro(tex, "Strut", 0, optional=True)
        tex = doc.replace_macro(tex, "Typo", 2, lambda o, a, b: b)
        tex = doc.replace_macro(tex, "Chg", 2, lambda o, a, b: a if doc.chg == "printed" else b)
        tex = doc.replace_macro(tex, "Add", 1, lambda o, a: a)
        tex = re.sub(r"\\(ie|eg|cf|Cf|viz)(?![A-Za-z])",
                     lambda m: r"\text{" + {"ie": "i.e.", "eg": "e.g.", "cf": "cf.", "Cf": "Cf.", "viz": "viz."}[m.group(1)] + "}", tex)
        tex = re.sub(r"\\index\{[^{}]*(\{[^{}]*\}[^{}]*)*\}", "", tex)
        # arrays pandoc cannot read: *{n}{spec} column repeats, @{} gaps, and
        # \cline, which becomes a full rule (Whitehead's long multiplication)
        tex = re.sub(r"\*\{(\d+)\}\{([^{}]*(?:\{\}[^{}]*)*)\}", lambda m: m.group(2) * int(m.group(1)), tex)
        tex = tex.replace("@{}", "")
        tex = underline_clines(tex)
        tex = re.sub(r"\s+", " ", tex).strip()
        return tex

    # ------------------------------------------------------------ the book
    def convert(self, body):
        """TeX body -> list of sections [{"title", "stream"}]. Headings come
        from \\Chapter and \\Appendix; everything before the first is dropped."""
        s = self.strip_comments(body)
        for name, n, o in (("PageSep", 1, False), ("index", 1, False), ("BookMark", 2, False),
                           ("label", 1, False), ("SetRunningHeads", 1, False),
                           ("FlushRunningHeads", 0, False), ("InitRunningHeads", 0, False),
                           ("phantomsection", 0, False), ("newpage", 0, False),
                           ("clearpage", 0, False), ("cleardoublepage", 0, False),
                           ("medskip", 0, False), ("smallskip", 0, False), ("bigskip", 0, False),
                           ("noindent", 0, False), ("vfill", 0, False), ("raggedright", 0, False),
                           ("normalsize", 0, False), ("small", 0, False), ("footnotesize", 0, False),
                           ("MainMatter", 0, False), ("BackMatter", 0, False), ("tb", 0, False),
                           ("Loosen", 0, False), ("dotfill", 0, False)):
            s = self.drop_macro(s, name, n, o)
        # page labels become anchors, to resolve page references to sections
        s = self.replace_macro(s, "Pagelabel", 1, lambda o, a: f"\x01L{a}\x01", optional=True)
        # footnotes, in place, their text held
        self.notes = []
        def fn(o, a):
            self.notes.append(a)
            return f"\x02F{len(self.notes) - 1}\x02"
        s = self.replace_macro(s, "footnote", 1, fn)
        marks = []
        s = re.sub(r"\\footnotemark(?![A-Za-z])", lambda m: (marks.append(1), "\x02MARK\x02")[1], s)
        def ftext(o, a):
            self.notes.append(a)
            return f"\x02T{len(self.notes) - 1}\x02"
        s = self.replace_macro(s, "footnotetext", 1, ftext)
        # a \footnotemark takes the next \footnotetext's number
        while "\x02MARK\x02" in s:
            m = re.search(r"\x02T(\d+)\x02", s)
            i = s.index("\x02MARK\x02")
            s = s[:i] + f"\x02F{m.group(1)}\x02" + s[i + 6:]
            s = s.replace(m.group(0), "", 1)
        self.footnotes = len(self.notes)
        s = self.replace_macro(s, "Figure", 1, lambda o, a: f"\n\n\x03FIG:fig{a}\x03\n\n", optional=True)
        s = self.replace_macro(s, "Diagram", 1, lambda o, a: f"\n\n\x03FIG:{a}\x03\n\n")
        # Poincaré's structure: Parts, unnumbered chapters, numbered sections
        s = self.replace_macro(s, "Part", 2, lambda o, a, b: f"\n\n\x04PART:Part {a.rstrip('.')}: {b.rstrip('.')}\x04\n\n")
        s = self.replace_macro(s, "OtherChapter", 1, lambda o, a: f"\n\n\x04H:{a.rstrip('.')}\x04\n\n")
        s = self.replace_macro(s, "Section", 1, lambda o, a: f"\n\n{a.rstrip('.')}\n\n")
        s = self.replace_macro(s, "Subsection", 1, lambda o, a: f"\n\n{a.rstrip('.')}\n\n")
        s = self.replace_macro(s, "Par", 1, lambda o, a: (o or "") + "*" + a + "*", optional=True)
        s = self.replace_macro(s, "Chapter", 2, lambda o, a, b: f"\n\n\x04H:Chapter {a}: {b}\x04\n\n", optional=True)
        s = self.replace_macro(s, "Appendix", 1,
                               lambda o, a: f"\n\n\x04H:{a}\x04\n\n" + (f"\x04SUB:{o}\x04\n\n" if o else ""), optional=True)
        for k, v in self.extra.items():
            s = s.replace(k, v)
        self.notes = [self.hold_and_text(n)[0] for n in self.notes]
        text, held = self.hold_and_text(s)
        return self.split(text)

    def hold_and_text(self, s):
        s, held = self.hold_math(s)
        s = self.text_macros(s)
        s = self.chars(s)
        # math back, cleaned
        def back(m):
            tex, display = held[int(m.group(1))]
            tex = self.math_cleanup(tex, self)
            return ("\n\n\\[" + tex + "\\]\n\n") if display else ("\\(" + tex + "\\)")
        s = re.sub(r"\x00M(\d+)\x00", back, s)
        return s, held

    def text_macros(self, s):
        emph = lambda o, a: "*" + a.strip() + "*" if a.strip() else ""
        for name in ("emph", "textit", "Title", "Foreign", "textsl"):
            s = self.replace_macro(s, name, 1, emph)
        s = self.replace_macro(s, "MakeLowercase", 1, lambda o, a: a.lower())
        s = self.replace_macro(s, "MakeUppercase", 1, lambda o, a: a.upper())
        for name in ("First", "textsc", "textbf", "textrm", "mbox", "hbox", "textup", "Heading"):
            s = self.replace_macro(s, name, 1, lambda o, a: a)
        s = self.replace_macro(s, "Typo", 2, lambda o, a, b: b)
        s = self.replace_macro(s, "Chg", 2, lambda o, a, b: a if self.chg == "printed" else b)
        s = self.replace_macro(s, "Add", 1, lambda o, a: a)
        s = self.replace_macro(s, "AD", 1, lambda o, a: "A.D." + ("" if a == "." else a))
        s = self.replace_macro(s, "BC", 1, lambda o, a: "B.C." + ("" if a == "." else a))
        s = self.replace_macro(s, "Fig", 1, lambda o, a: (o or "Fig.") + "~" + a, optional=True)
        s = self.replace_macro(s, "FigNum", 1, lambda o, a: a)
        s = self.replace_macro(s, "ChapNum", 1, lambda o, a: a)
        s = self.replace_macro(s, "ChapRef", 1, lambda o, a: (o or "Chapter") + "~" + a, optional=True)
        s = self.replace_macro(s, "Pageref", 1, lambda o, a: f"\x05R{o or 'p.'}|{a}\x05", optional=True)
        s = self.replace_macro(s, "Note", 1, lambda o, a: a + f"\x01Lnote{a}\x01")   # \Note{A} labels itself
        s = self.replace_macro(s, "hyperref", 1, lambda o, a: a, optional=True)
        for k, v in (("ie", "i.e."), ("eg", "e.g."), ("cf", "cf."), ("Cf", "Cf."), ("viz", "viz.")):
            s = re.sub(r"\\" + k + r"(?![A-Za-z])", "*" + v + "*", s)
        # environments that are lines
        def lines(m):
            body = m.group(2)
            ls = [l.strip() for l in re.split(r"\\\\(?:\[[^\]]*\])?|\n", body) if l.strip()]
            return "\n\n" + "\n".join("\t" + l for l in ls) + "\n\n"
        s = re.sub(r"\\begin\{(verse|alltt|center|flushleft|flushright|quote|quotation)\}(.*?)\\end\{\1\}", lines, s, flags=re.S)
        return s

    @staticmethod
    def chars(s):
        s = s.replace("``", "“").replace("''", "”")
        s = re.sub(r"(?<![\w\\])`", "‘", s)
        s = re.sub(r"'", "’", s)
        s = s.replace("---", "—").replace("--", "–")
        # thin spaces go; a control space (also before a line break) is a space
        s = re.sub(r"\\,|\\;|\\:|\\ |\\\n|\\@|\\/", lambda m: " " if m.group(0) in ("\\ ", "\\\n") else "", s)
        s = s.replace("~", " ")
        for a, b in (("\\&", "&"), ("\\%", "%"), ("\\#", "#"), ("\\$", "$"), ("\\_", "_"),
                     ("\\dots", "…"), ("\\ldots", "…"), ("\\S ", "§ "), ("\\pounds", "£"), ("\\-", "")):
            s = s.replace(a, b)
        s = re.sub(r"\\\\(\[[^\]]*\])?", "\n", s)
        s = s.replace("{", "").replace("}", "")
        return s

    def split(self, text):
        sections, cur, pending_part = [], None, None
        for par in re.split(r"\n\s*\n", text):
            raw = par.strip("\n")
            if not raw.strip():
                continue
            is_block = raw.startswith("\t")
            t = raw if is_block else re.sub(r"\s+", " ", raw).strip()
            pt = re.fullmatch(r"\x04PART:(.*?)\x04", t)
            if pt:
                pending_part = re.sub(r"\s+", " ", pt.group(1)).strip()
                continue
            h = re.fullmatch(r"\x04H:(.*?)\x04", t)
            if h:
                cur = {"title": re.sub(r"\s+", " ", h.group(1)).strip(), "stream": []}
                if pending_part:
                    cur["part_before"], pending_part = pending_part, None
                sections.append(cur)
                continue
            if cur is None:
                continue
            sub = re.fullmatch(r"\x04SUB:(.*?)\x04", t)
            if sub:
                cur["subtitle"] = sub.group(1)
                continue
            f = re.fullmatch(r"\x03FIG:(\w+)\x03", t)
            if f:
                cur["stream"].append(("PLATE", f.group(1), ""))
                continue
            for lab in re.findall(r"\x01L(.*?)\x01", t):
                self.labels[lab] = len(sections) - 1
            t = re.sub(r"\x01L.*?\x01", "", t)
            for ref in re.findall(r"\x05R.*?\|(.*?)\x05", t):
                self.pagerefs.append((len(sections) - 1, ref))
            notes = [int(n) for n in re.findall(r"\x02[FT](\d+)\x02", t)]
            t = re.sub(r"\s*\x02[FT]\d+\x02", "", t)
            if not is_block:
                t = re.sub(r"\s+([,.;:])", r"\1", t) if False else t
                t = re.sub(r"  +", " ", t).strip()
            if t.strip():
                cur["stream"].append(("BLOCK" if is_block else "P", t))
            for n in notes:
                note = re.sub(r"\s+", " ", self.notes[n]).strip()
                for lab in re.findall(r"\x01L(.*?)\x01", note):
                    self.labels[lab] = len(sections) - 1
                note = re.sub(r"\x01L.*?\x01", "", note)
                cur["stream"].append(("P", "Footnote: " + note))
        return sections

    def resolve_pagerefs(self, sections, name=lambda s: s["title"].split(":")[0]):
        """\x05R<p.>|<label>\x05 -> the section the label is in, or above/below."""
        n = 0
        for i, s in enumerate(sections):
            for k, it in enumerate(s["stream"]):
                if it[0] in ("P", "BLOCK") and "\x05R" in it[1]:
                    def sub(m):
                        nonlocal n
                        n += 1
                        lab = m.group(2)
                        j = self.labels[lab]
                        if j == i:
                            return "\x06SAME\x06"
                        return name(sections[j])
                    s["stream"][k] = (it[0], re.sub(r"\x05R(.*?)\|(.*?)\x05", sub, it[1])) + tuple(it[2:])
        return n

    @staticmethod
    def leftovers(sections):
        """Every backslash command still in the prose: the prep must see these."""
        found = {}
        for s in sections:
            for it in s["stream"]:
                if it[0] in ("P", "BLOCK"):
                    t = re.sub(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", "", it[1], flags=re.S)
                    for m in re.findall(r"\\[A-Za-z]+", t):
                        found[m] = found.get(m, 0) + 1
        return found


def underline_clines(tex):
    """texmath cannot rule part of an array (\\cline) or rule mid-array at
    all, so a rule under cells a..b becomes \\underline on those cells of
    the row above -- the ruled columns of a long multiplication."""
    if "\\cline" not in tex:
        return tex
    m = re.search(r"(\\begin\{array\}\{[^}]*\})(.*?)(\\end\{array\})", tex, re.S)
    head, body, tail = m.groups()
    rows = [r for r in re.split(r"\\\\", body)]
    out = []
    for r in rows:
        r = r.replace("\\Strut", "")
        cl = re.findall(r"\\cline\{(\d+)-(\d+)\}", r)
        r = re.sub(r"\\cline\{\d+-\d+\}", "", r)
        if cl and out:
            cells = out[-1].split("&")
            for a, b in cl:
                for c in range(int(a) - 1, int(b)):
                    if cells[c].strip():
                        cells[c] = "\\underline{" + cells[c].strip() + "}"
            out[-1] = "&".join(cells)
        if r.strip():
            out.append(r)
    return tex[:m.start()] + head + " \\\\ ".join(out) + tail + tex[m.end():]
