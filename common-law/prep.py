"""Oliver Wendell Holmes Jr., The Common Law (1881): source preparation
for a MODERN CLASSIC (a retelling).

    python3 common-law/prep.py

Gutenberg #2449, plain text. Page numbers are inline as [245]; footnote
marks as /1/, numbered page by page; the notes are collected at the end
as "245/1 ...". Each mark is resolved by the page it falls on, and each
note is set as a "Footnote:" paragraph after the paragraph that cites it
(the candle/mill pattern), so chapters/ carries the whole of the book --
which the --original companion page shows.

THE RETELLING KEEPS ONLY THE NOTES THAT SAY SOMETHING. Most of Holmes's
832 notes are bare citations ("Y.B. 6 Ed. IV. 7, pl. 18") that a reader
of the retelling cannot use; those are dropped from modern_chapters/ and
kept in the original. A note that argues, explains or quotes is
SUBSTANTIVE and is retold. footnotes.json records which is which, per
file, and check.py holds the retelling to it.

The Greek book-letters of the Plato citations ([theta]) are restored as
Greek letters; "[Greek characters]", where the transcriber omitted Greek,
is left for the original page and the retelling says what it was.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "source.txt"
MAX_WORDS = 6500
# NOTES THE TRANSCRIPTION MISNUMBERED, keyed by their opening words so a
# fix can only land on the note it names. Found because two notes claimed
# one number; each was resolved by lining the page's marks up with its
# notes in order. Pages 356-358 print nine marks and carry nine notes, but
# four of the notes are headed with the wrong page.
NOTE_FIXES = {
    "7 Am. Law Rev. 63": (231, 4),          # the second "231/3": the text's /4/ cites the Review
    "Windscheid, Pand. Section 155": (233, 5),
    '"Quantum dare voluerit': (356, 3),
    "Lex Sal. (Merkel), Cap. XLVI.": (356, 4),
    "Beseler, Erbvertraege, I. 101": (356, 5),
    '"Omnem facultatem suam': (357, 1),
}
GREEK = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "zeta": "ζ", "eta": "η",
         "theta": "θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
         "omicron": "ο", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ",
         "chi": "χ", "psi": "ψ", "omega": "ω"}
# A NOTE THE TRANSCRIPTION LOST, typed from the page (both 1881 scans,
# commonlaw00holmuoft and commonlaw00holmgoog): page 406's fourth note.
NOTE_ADD = {(406, 4): "5 Co. Rep. 16, a."}
# A MARK WITH NOTHING BEHIND IT: page 65 prints no footnotes at all, and
# the page image has no mark after "cause the same harm?".
SPURIOUS_MARKS = {(65, 1)}
# vote inserts that are not (wholly) the transcription's loss: a running
# head the vote could not tell from text ("VOID CONTRACTS. 313" around a
# real dropped "that")
SKIP_INSERTS = set()
INSERT_OVERRIDE = {"void contracts that": "that"}
# the lecture titles as printed, with the book's ".--" set as a dash
TITLES = {"I": "Early Forms of Liability", "II": "The Criminal Law", "III": "Torts—Trespass and Negligence",
          "IV": "Fraud, Malice, and Intent—The Theory of Torts", "V": "The Bailee at Common Law",
          "VI": "Possession", "VII": "Contract—I. History", "VIII": "Contract—II. Elements",
          "IX": "Contract—III. Void and Voidable", "X": "Successions after Death",
          "XI": "Successions—II. Inter Vivos"}
# against both 1881 scans
# (commonlaw00holmuoft, 1881; commonlaw00holmgoog, a 1909 printing from
# the same plates): readings where both agree against the transcription
TEXT_FIXES = [
    ("surrounding circumstances to cause the same harm.", "surrounding circumstances to cause the same harm?"),
    ("prevailed in the eases first mentioned", "prevailed in the cases first mentioned"),
    ("law of trespass upon laud to", "law of trespass upon land to"),
    ("the essential clement is", "the essential element is"),
    ("Beyond these scientific rules", "Beyond these specific rules"),
    ("even such things as these should be punished", "even such things as those should be punished"),
    ("taking to one's own user It", "taking to one's own use. It"),
    ("more complex than those so far considered", "more complex than those thus far considered"),
    ("custody by law, who factor", "custody by law, and factor"),
    ("A bailee was in general liable for goods stolen", "A bailee was in general answerable for goods stolen"),
    ("by conveyance from the previous owner", "by conveyance from a previous owner"),
    ("it was objected to au action", "it was objected to an action"),
    ("as in the ease of an agreement", "as in the case of an agreement"),
    ("the pursuer had the fight to take", "the pursuer had the right to take"),
    ("of a pistol is next to it or not", "of a pistol is next it or not"),
    ("of the action, and so it shall be", "of the action, and it shall be"),
]
STOP = set("the of and to a in is that it which be this was as by not but with are an for have has "
           "had or if he his they their there when so been would may can from were we one than".split())


def greek(s):
    return re.sub(r"\[((?:" + "|".join(GREEK) + r")(?: (?:" + "|".join(GREEK) + r"))*)\]",
                  lambda m: "".join(GREEK[g] for g in m.group(1).split()).upper(), s)


def restore_dropped(sections):
    """WORDS THE TRANSCRIPTION DROPPED, put back. scan_diff.py --vote --json
    lists every short run that both scans print and the transcription lacks
    ("the law _ always approaching": both print "is"). Each is located by
    the words either side of it, in the text, and must match exactly once;
    its case and punctuation are taken from the scan, not from the vote's
    lowercased words. Anything that cannot be placed stops the prep."""
    vote = json.loads((HERE / "_src" / "vote.json").read_text())
    scan = re.sub(r"-\s*\n\s*", "", (HERE / "_src" / "scan-commonlaw00holmuoft-djvu.txt").read_text())
    scan = re.sub(r"\s+", " ", scan)
    W = lambda ws: r"\W+".join(re.escape(w) for w in ws.split())
    placed, skipped = 0, []
    for v in vote:
        if v["tag"] != "insert" or v["print"] in SKIP_INSERTS:
            continue
        L, R, ins = v["left"], v["right"], INSERT_OVERRIDE.get(v["print"], v["print"])
        if v["print"] in INSERT_OVERRIDE:
            words_ = ins
        else:
            m = re.search(r"(?i)\b" + W(L) + r"(\W+)(" + W(ins) + r")(\W+)" + W(R) + r"\b", scan)
            if not m:
                skipped.append(v); continue
            words_ = m.group(2)
        pat = re.compile(r"(?i)(\b" + W(L) + r")(\W+)(" + W(R) + r"\b)")
        hits = [(si, pi) for si, sec in enumerate(sections) for pi, (t, _) in enumerate(sec["pars"]) if pat.search(t)]
        count = sum(len(pat.findall(sections[si]["pars"][pi][0])) for si, pi in hits)
        if count != 1:
            skipped.append(v); continue
        si, pi = hits[0]
        t, refs = sections[si]["pars"][pi]
        t = pat.sub(lambda mm: mm.group(1) + mm.group(2) + words_ + " " + mm.group(3), t, count=1)
        sections[si]["pars"][pi] = (t, refs)
        placed += 1
    print(f"dropped words restored: {placed}; not placed: {len(skipped)}")
    for v in skipped:
        print("   NOT PLACED", v)
    assert not skipped


def substantive(note):
    """True when a note says something beyond where to look it up."""
    t = re.sub(r'"[^"]*"', " ", note)                 # quotations (usually Latin or law French)
    words = re.findall(r"[a-z]+", t)
    return sum(w in STOP for w in words) >= 6


def main():
    lines = SRC.read_text().replace("\r", "").split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("LECTURE I. --"))
    fn = next(i for i, l in enumerate(lines) if l.strip() == "FOOTNOTES")
    end = next(i for i, l in enumerate(lines) if l.startswith("End of Project Gutenberg"))
    body, notes_raw = lines[start:fn], lines[fn + 1:end]

    # the notes: "245/1 text", "3 /4 text", continuing to a blank line
    notes, cur, applied = {}, None, set()
    for l in notes_raw:
        m = re.match(r"^(\d+) ?/(\d+) (.*)", l)
        if m:
            cur = (int(m.group(1)), int(m.group(2)))
            fix = [v for k_, v in NOTE_FIXES.items() if m.group(3).startswith(k_)]
            if fix:
                cur = fix[0]
                applied.add(cur)
            assert cur not in notes, cur
            notes[cur] = m.group(3)
        elif l.strip() and cur:
            notes[cur] += " " + l.strip()
        elif not l.strip():
            cur = None
    assert applied == set(NOTE_FIXES.values()), applied
    for k_, v in NOTE_ADD.items():
        assert k_ not in notes
        notes[k_] = v
    notes = {k: greek(re.sub(r"\s+", " ", v).strip()) for k, v in notes.items()}

    # paragraphs, tracking the page; marks resolved to notes
    text = "\n".join(body)
    pars = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    page, used, sections, cur_sec, marks, dropped, fixed = 0, set(), [], None, [], set(), set()
    for par in pars:
        p1 = par.strip()
        h = re.fullmatch(r"LECTURE ([IVX]+)\. -- (.+?)\.?", re.sub(r"\s+", " ", p1))
        if h:
            title = h.group(2).title().replace("--", "—").replace(" Of ", " of ").replace(" And ", " and ") \
                .replace(" At ", " at ").replace(" The ", " the ").replace("After", "after").replace("Inter Vivos", "Inter Vivos")
            title = re.sub(r"\.—", "—", title)
            if cur_sec and cur_sec["num"] == h.group(1):
                # Lecture X's second subhead: a heading inside the lecture
                cur_sec["pars"].append(("Successions Inter Vivos", []))
                continue
            cur_sec = {"num": h.group(1), "title": f"Lecture {h.group(1)}: {TITLES[h.group(1)]}", "pars": []}
            sections.append(cur_sec)
            continue
        out, refs = [], []
        pos = 0
        par = re.sub(r"\[(\d+)(?=\s)", r"[\1]", par)     # "[108 The standards": a page marker missing its bracket
        for m in re.finditer(r"\[(\d+)\]|/(\d+)/", par):
            out.append(par[pos:m.start()])
            if m.group(1):
                page = int(m.group(1))
            else:
                key = (page, int(m.group(2)))
                if key in SPURIOUS_MARKS:
                    dropped.add(key)
                    pos = m.end()          # step past the mark (skipping it without this doubled the text)
                    continue
                refs.append(key)
                marks.append((page, int(m.group(2)), len(marks)))
            pos = m.end()
        out.append(par[pos:])
        t = re.sub(r"\s+", " ", "".join(out)).strip()
        t = t.replace(" --", "—").replace("-- ", "—").replace("--", "—")
        t = greek(t)
        for bad, good in TEXT_FIXES:
            if bad in t:
                t = t.replace(bad, good)
                fixed.add(bad)
        cur_sec["pars"].append((t, refs))
    # ALIGN THE SEQUENCES (Needleman-Wunsch): marks in text order against
    # notes in page order. The printed numbers are evidence, not keys: the
    # transcription drops marks, and a page marker set a line early or late
    # moves a mark across the page turn. Costs: exact 0, neighbouring page 1,
    # same page another number 2, otherwise 6; a note with no mark 3 (it
    # goes with the note before it, so nothing is lost); a mark with no
    # note 4 (it must not happen, and is asserted).
    order = sorted(notes)
    M, N = [(pg, num) for pg, num, _ in marks], order
    INF = float("inf")
    def cost(m, n):
        if m == n: return 0
        if m[1] == n[1] and abs(m[0] - n[0]) == 1: return 1
        if m[0] == n[0]: return 2
        return 6
    D = [[INF] * (len(N) + 1) for _ in range(len(M) + 1)]
    D[0] = [3 * j for j in range(len(N) + 1)]
    for i in range(1, len(M) + 1):
        D[i][0] = 4 * i
        mi = M[i - 1]
        Di, Dp = D[i], D[i - 1]
        for j in range(1, len(N) + 1):
            Di[j] = min(Dp[j - 1] + cost(mi, N[j - 1]), Di[j - 1] + 3, Dp[j] + 4)
    i, j, pairs = len(M), len(N), []
    while i or j:
        if i and j and D[i][j] == D[i - 1][j - 1] + cost(M[i - 1], N[j - 1]):
            pairs.append((i - 1, j - 1)); i -= 1; j -= 1
        elif j and D[i][j] == D[i][j - 1] + 3:
            pairs.append((None, j - 1)); j -= 1
        else:
            pairs.append((i - 1, None)); i -= 1
    pairs.reverse()
    missing = []
    resolve, extra, last, stats = {}, {}, None, {"exact": 0, "turn": 0, "renumbered": 0, "unmarked": 0}
    for mi, nj in pairs:
        if nj is None:                              # the transcription lost the note
            missing.append(M[mi])
            resolve[marks[mi][2]] = None
            continue
        if mi is None:
            extra.setdefault(last, []).append(N[nj])
            stats["unmarked"] += 1
            continue
        c = cost(M[mi], N[nj])
        stats["exact" if c == 0 else "turn" if c == 1 else "renumbered"] += 1
        if c >= 2:
            print("RENUMBERED", M[mi], "->", N[nj])
        resolve[marks[mi][2]] = N[nj]
        last = marks[mi][2]
    print(stats, "marks with no note:", missing)
    assert dropped == SPURIOUS_MARKS and not missing, (dropped, missing)
    used = set(resolve.values()) | {n for v in extra.values() for n in v}
    ctr = iter(range(len(marks)))
    for sec in sections:
        newp = []
        for t, refs in sec["pars"]:
            if isinstance(refs, list) and refs:
                keys = []
                for _ in refs:
                    idx = next(ctr)
                    if resolve[idx] is not None:
                        keys.append(resolve[idx])
                    keys.extend(extra.get(idx, []))
                refs = keys
            newp.append((t, refs))
        sec["pars"] = newp
    assert fixed == {b for b, _ in TEXT_FIXES}, fixed
    restore_dropped(sections)
    unused = sorted(set(notes) - used)
    print(f"{len(notes)} notes, {len(used)} cited, unused: {unused[:12]}")

    # files: each lecture, cut into parts at paragraph boundaries
    manifest, meta = [], {}
    out_dir = HERE / "chapters"
    out_dir.mkdir(exist_ok=True)
    for f in out_dir.glob("*.txt"):
        f.unlink()
    k = 0
    for sec in sections:
        blocks, size = [[]], 0
        words = lambda p: len(p[0].split()) + sum(len(notes[r].split()) for r in p[1])
        total = sum(words(p) for p in sec["pars"])
        nparts = max(1, round(total / MAX_WORDS + 0.49))
        target = total / nparts
        for p in sec["pars"]:
            if size >= target and len(blocks) < nparts:
                blocks.append([])
                size = 0
            blocks[-1].append(p)
            size += words(p)
        for i, b in enumerate(blocks):
            name = f"{k:03d}.txt"
            head = [sec["title"]] + ([f"(Part {i + 1} of {len(blocks)})"] if len(blocks) > 1 else []) + [""]
            lines_out, kinds = head, []
            for t, refs in b:
                lines_out += [t, ""]
                for r in refs:
                    lines_out += ["Footnote: " + notes[r], ""]
                    kinds.append({"note": f"{r[0]}/{r[1]}", "substantive": substantive(notes[r])})
            (out_dir / name).write_text("\n".join(lines_out).rstrip() + "\n")
            manifest.append({"file": name, "title": sec["title"], "part": i + 1, "of": len(blocks)})
            meta[name] = kinds
            k += 1
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    (HERE / "footnotes.json").write_text(json.dumps(meta, indent=1) + "\n")
    subs = sum(x["substantive"] for v in meta.values() for x in v)
    print(f"{k} files, {sum(len(v) for v in meta.values())} footnotes set, {subs} substantive")
    for f in sorted(out_dir.glob("*.txt")):
        print(f.name, len(f.read_text().split()), f.read_text().split("\n")[0][:60])


if __name__ == "__main__":
    main()
