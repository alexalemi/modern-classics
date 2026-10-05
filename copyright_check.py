"""Was a US book of 1929-1963 registered, and was the registration renewed?

    python3 copyright_check.py "Evolution of Physics" --author Einstein --year 1938
    python3 copyright_check.py "Title words" --author Name --year 1950 --foreign
    python3 copyright_check.py --batch candidates.tsv   # title<TAB>author<TAB>year
    python3 copyright_check.py --fetch 1929-1964        # warm the cache

A US book published 1929-1963 entered the public domain if its copyright
was not RENEWED in the 28th year. Published 1929-30, it is public domain by
age now (95 years from publication; 1930 works came out on 1 Jan 2026);
1964 on, renewal was automatic (1992 Renewal Act). This tool answers the
middle band from two NYPL transcriptions, because Stanford's renewal
database is bot-walled from the sandbox:

  REGISTRATIONS  github.com/NYPL/catalog_of_copyright_entries_project,
                 xml/{year}/*.xml -- the Catalog of Copyright Entries, Part 1
                 (Books), OCR'd and tagged. Each file is downloaded once,
                 reduced to a TSV index in build/copyright/reg/, and the XML
                 thrown away (--keep-xml keeps it; 1929-1964 is ~640 MB).
  RENEWALS       github.com/NYPL/cce-renewals, data/{year}-1.tsv (renewal
                 years 1950-1977, transcribed from the CCE) and
                 {year}-from-db.tsv (1978 on, the Copyright Office's own
                 online records), cached raw in build/copyright/ren/.

A renewal is matched to its registration by ORIGINAL REGISTRATION NUMBER
(the renewal's `oreg`), anywhere in the renewal data, and separately by
fuzzy title + author within the renewal window (registration year +26 to
+29; the statutory window is +27/+28) so an OCR'd number that disagrees is
still seen. Near misses are printed for a human to judge. Renewals of the
same title OUTSIDE the window are listed as OTHER EDITION/YEAR: they never
change the verdict, but they are how a renewed revised edition shows up
(Schumpeter's 1950 third edition, Think and Grow Rich's 1960 printings).

Two traps found while testing, both handled:
  * Registration numbers were REUSED (the A series restarted in 1947), so
    a number match only counts when the renewal's original date agrees.
    Without that check Niebuhr's Moral Man and Immoral Society (A58707,
    1932) came out "renewed" by a 1951 children's book with the same number.
  * About 5% of the 1950-77 renewal rows have empty author/title/oreg
    columns and only full_text. R. E. Lee's renewal (R301519, citing
    "A75789-75790") is one; full_text is parsed, ranges expanded.

Verdicts:
  RENEWED                    a renewal matches; in copyright (95 years)
  NOT RENEWED                registered, no renewal found: LIKELY US public
                             domain -- confirm the printed notice, the
                             edition, and (foreign works) URAA restoration
  NOT FOUND IN REGISTRATIONS no registration matched: either never
                             registered (then the notice decides) or the
                             OCR lost it. Never read this as "PD".
  OUT OF RANGE               published <= 1930: PD by age; >= 1964: renewed
                             automatically, in copyright

CAVEATS, all of which this tool cannot see:
  * The data are OCR transcriptions. A typo in a title, name or number can
    hide a real renewal; the near-miss list is there to be read.
  * URAA (1996) restored foreign works that fell into the US public domain
    for want of renewal, if still protected at home on 1 Jan 1996. A work
    FIRST published abroad (source country not the US) can be in copyright
    with no renewal at all. Flagged when the registration looks foreign
    (AF / ad interim numbers, a foreign place) or when --foreign is given.
  * A renewed LATER edition protects only its new matter; a renewed
    original protects every later printing. Check which edition you hold.
  * Illustrations, introductions and translations may be separately owned.
  * A contribution renewed as part of a periodical is not in this index.
The Copyright Office's records, not these transcriptions, are authoritative.
"""

import argparse
import csv
import datetime
import difflib
import gzip
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "build" / "copyright"
REG_REPO = "NYPL/catalog_of_copyright_entries_project"
REN_REPO = "NYPL/cce-renewals"
RAW = "https://raw.githubusercontent.com/{repo}/master/{path}"
API_TREE = "https://api.github.com/repos/{repo}/git/trees/master?recursive=1"

csv.field_size_limit(10**8)
THIS_YEAR = datetime.date.today().year
PD_THROUGH = THIS_YEAR - 96          # 1930 in 2026

STOP = set("""a an the of and in on to for by with from at as or its his her
their our your into upon und der die das le la les de du des el los""".split())

FOREIGN_PLACES = re.compile(
    r"\b(england|london|oxford|cambridge, eng|edinburgh|glasgow|dublin|"
    r"scotland|ireland|wales|paris|france|berlin|leipzig|munich|m\w*nchen|"
    r"stuttgart|hamburg|vienna|wien|germany|austria|zurich|z\w*rich|bern|"
    r"switzerland|geneva|rome|milan|milano|italy|madrid|spain|barcelona|"
    r"lisbon|amsterdam|holland|netherlands|brussels|belgium|copenhagen|"
    r"stockholm|oslo|norway|sweden|denmark|helsinki|moscow|russia|u\.s\.s\.r|"
    r"prague|warsaw|budapest|toronto|montreal|canada|sydney|melbourne|"
    r"australia|tokyo|japan|mexico|buenos aires|argentina|rio de janeiro|"
    r"brazil|india|calcutta|bombay|jerusalem|tel aviv)\b", re.I)

US_PLACES = re.compile(
    r"\b(new york|n\. ?y|boston|chicago|philadelphia|washington|baltimore|"
    r"new haven|princeton|garden city|indianapolis|minneapolis|san francisco|"
    r"los angeles|cleveland|cincinnati|st\. louis|detroit|norman|caldwell|"
    r"[a-z]+, (mass|conn|calif|ill|mich|ohio|pa|n\. ?j|md|va|ind|wis|minn|"
    r"tex|okla|iowa|mo|neb|colo|wash|ore|n\. ?c|ga|tenn|ky|vt|n\. ?h|me|"
    r"r\. ?i|del|fla|ala|la|miss|ariz|utah|idaho|mont|kan)\b)", re.I)


# ---------------------------------------------------------------- fetching

def fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size:
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "copyright_check"})
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.rename(dest)
    return dest


def tree(repo, key):
    p = CACHE / f"{key}-tree.json"
    fetch(API_TREE.format(repo=repo), p)
    return [x["path"] for x in json.loads(p.read_text())["tree"]]


# ---------------------------------------------------------- registrations

def text(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


REGTOK = re.compile(r"\b([A-Z]{1,3})?\s*(\d{2,7})\b")


def parse_regnums(raw):
    """'A 114668', 'A\u2014Foreign 38374', 'A ad int. 23600', 'A134941 A134942',
    'A75789-75790' -> normalised numbers (A114668, AF38374, AI23600, ...).
    A bare number takes the prefix of the number before it."""
    s = raw.upper().replace("\u2014", " ").replace("FOREIGN", "F")
    s = re.sub(r"AD\s*INT\.?", "I", s)
    s = re.sub(r"\b([A-Z]{1,2})\s+([FI])\s+(?=\d)", r"\1\2", s)   # 'A F 38374'
    s = re.sub(r"\b([A-Z]{1,3})[\s-]+(?=\d)", r"\1", s)
    out, prefix, last = [], None, None
    for m in REGTOK.finditer(s):
        pre, num = m.group(1), m.group(2)
        if pre:
            prefix = pre
        elif prefix is None:
            continue
        elif last and len(num) < len(last):          # A75789-790 style range end
            num = last[:len(last) - len(num)] + num
        out.append(prefix + num)
        last = num
    return list(dict.fromkeys(out))


def entry_record(e, group_authors, src):
    raw = e.get("regnum", "") + " " + " ".join(text(r) for r in e.iter("regNum"))
    regnums = parse_regnums(raw)
    authors = [text(a) for a in e.iter("authorName")] or group_authors
    titles = [text(t) for t in e.iter("title")]
    pubs = [text(p) for p in e.iter("pubName")]
    places = [text(p) for p in e.iter("pubPlace")] + \
             [text(p) for p in e.iter("authorPlace")]
    dates = [d.get("date", "") for d in e.iter("regDate")]
    pubdates = [d.get("date", "") for d in e.iter("pubDate")]
    regraw = " ".join(text(r) for r in e.iter("regNum"))
    return [";".join(regnums), ";".join(dates), ";".join(pubdates),
            " | ".join(authors), " | ".join(titles), " | ".join(pubs),
            " | ".join(places), regraw, src]


def index_xml(xml_path, out_path):
    """XML file -> gzipped TSV of entries (one row per copyrightEntry)."""
    rows = []
    src = xml_path.name
    data = xml_path.read_bytes()
    data = re.sub(rb"<!DOCTYPE[^>]*>", b"", data, count=1)
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        # A malformed file: parse entry by entry, skipping the broken ones.
        root = None
        for m in re.finditer(rb"<copyrightEntry\b.*?</copyrightEntry>", data, re.S):
            try:
                rows.append(entry_record(ET.fromstring(m.group(0)), [], src))
            except ET.ParseError:
                continue
    if root is not None:
        def walk(node, group_authors):
            for ch in node:
                if ch.tag == "entryGroup":
                    ga = [text(a) for a in ch.findall("author/authorName")]
                    walk(ch, ga or group_authors)
                elif ch.tag == "copyrightEntry":
                    rows.append(entry_record(ch, group_authors, src))
                elif ch.tag not in ("crossRef", "header", "page"):
                    walk(ch, group_authors)
        walk(root, [])
    tmp = out_path.with_suffix(".part")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerows(rows)
    tmp.rename(out_path)


def reg_files(year):
    return sorted(p for p in tree(REG_REPO, "reg")
                  if p.startswith(f"xml/{year}/") and p.endswith(".xml"))


def ensure_reg_year(year, keep_xml=False, quiet=False):
    outs = []
    for p in reg_files(year):
        out = CACHE / "reg" / str(year) / (Path(p).stem + ".tsv.gz")
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            xml = CACHE / "xml" / p[4:]
            if not quiet:
                print(f"  fetching {p} ...", file=sys.stderr)
            fetch(RAW.format(repo=REG_REPO, path=p), xml)
            index_xml(xml, out)
            if not keep_xml:
                xml.unlink()
        outs.append(out)
    return outs


_REG = {}


def load_reg_year(year, keep_xml=False):
    if year not in _REG:
        rows = []
        for f in ensure_reg_year(year, keep_xml):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for r in csv.reader(fh, delimiter="\t"):
                    if len(r) == 9:
                        d = dict(zip(("regnum", "regdate", "pubdate", "author",
                                      "title", "publisher", "place", "regraw",
                                      "src"), r))
                        d["_t"] = toks(d["title"])
                        d["_a"] = toks(d["author"] + " " + d["publisher"])
                        # re-derived at load: indexes built before
                        # parse_regnums kept 'A75789 A75790' as one token
                        d["regnum"] = ";".join(parse_regnums(
                            d["regnum"].replace(";", " ") + " " + d["regraw"]))
                        rows.append(d)
        _REG[year] = rows
    return _REG[year]


# ---------------------------------------------------------------- renewals

def ren_files():
    out = {}
    for p in tree(REN_REPO, "ren"):
        m = re.match(r"data/(\d{4})-[^/]*\.tsv$", p)
        if m:
            out.setdefault(int(m.group(1)), []).append(p)
    return out


_REN = {}


def load_ren_year(year):
    if year not in _REN:
        rows = []
        for p in ren_files().get(year, []):
            f = fetch(RAW.format(repo=REN_REPO, path=p), CACHE / "ren" / Path(p).name)
            with open(f, encoding="utf-8", errors="replace") as fh:
                for r in csv.DictReader(fh, delimiter="\t"):
                    d = {"author": r.get("author") or r.get("auth") or "",
                         "title": r.get("title") or r.get("titl") or "",
                         "oreg": r.get("oreg") or "", "odat": r.get("odat") or "",
                         "id": r.get("id") or "",
                         "rdat": r.get("rdat") or r.get("dreg") or "",
                         "claimants": r.get("claimants") or "",
                         "new_matter": r.get("new_matter") or "",
                         "full_text": r.get("full_text") or "",
                         "file": Path(p).name}
                    # ~5% of the 1950-77 rows carry only full_text (R. E. Lee's
                    # renewal R301519 is one): fall back to it for every field,
                    # and always add the numbers it cites, ranges expanded.
                    ft = d["full_text"]
                    d["_oreg"] = ";".join(x for x in [norm_reg(d["oreg"]),
                                                      ft_regnums(ft)] if x)
                    d["_t"] = toks(d["title"] or ft)
                    d["_a"] = toks(d["author"] + " " + d["claimants"] +
                                   ("" if d["author"] else " " + ft))
                    if not d["title"]:
                        d["title"] = ft
                    if not d["oreg"]:
                        d["oreg"] = ft_regnums(ft)
                    if not d["id"]:
                        ids = re.findall(r"\b(RE?\d{4,7})\b", ft)
                        d["id"] = ids[0] if ids else ""
                    if not d["rdat"]:
                        m = re.search(r"\b(\d{1,2}[A-Z][a-z]{2}\d{2}); RE?\d", ft)
                        d["rdat"] = m.group(1) if m else ""
                    rows.append(d)
        _REN[year] = rows
    return _REN[year]


def all_ren_years():
    return sorted(ren_files())


# ---------------------------------------------------------------- matching

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def toks(s):
    return norm(s).split()


def norm_reg(s):
    return ";".join(re.sub(r"[^A-Z0-9]", "", x.upper())
                    for x in re.split(r"[;,|]", s) if x.strip())


FT_REG = re.compile(r"\b(A[A-Z]?|AF|AI|B|AA)[ -]?(\d{3,7})(?:-(\d{1,7}))?\b")


def ft_regnums(ft):
    """Registration numbers cited in a renewal's full text, after the (c)
    mark; "A75789-75790" expands to both."""
    out = []
    for m in FT_REG.finditer(ft.split("\u00a9", 1)[-1] if "\u00a9" in ft else ft):
        pre, a, b = m.group(1), m.group(2), m.group(3)
        out.append(pre + a)
        if b and len(b) <= len(a) and int(a[:len(a) - len(b)] + b) - int(a) < 20:
            hi = int(a[:len(a) - len(b)] + b)
            out += [pre + str(n) for n in range(int(a) + 1, hi + 1)]
    return ";".join(dict.fromkeys(out))


def tok_hit(q, cands):
    if q in cands:
        return 1.0
    if len(q) < 4:
        return 0.0
    best = 0.0
    for c in cands:
        if abs(len(c) - len(q)) <= 2 and c[:1] == q[:1]:
            r = difflib.SequenceMatcher(None, q, c).ratio()
            if r > best:
                best = r
    return best if best >= 0.8 else 0.0


def title_score(qt, ct):
    """Recall of the query's content words in the candidate title, with a
    small penalty when the query's words are a tiny part of a long title."""
    q = [w for w in qt if w not in STOP] or qt
    if not q or not ct:
        return 0.0
    cs = set(ct)
    rec = sum(tok_hit(w, cs) for w in q) / len(q)
    # Order/prefix bonus: the query is usually the start of the title.
    # ...from where the query's first word appears (a renewal known only by
    # its full text starts with the author's name)
    i = next((k for k, w in enumerate(ct) if w == qt[0]), 0)
    head = " ".join(ct[i:i + len(qt) + 2])
    pre = difflib.SequenceMatcher(None, " ".join(qt), head).ratio()
    return 0.75 * rec + 0.25 * pre


def author_score(qa, ca):
    if not qa:
        return 1.0
    q = [w for w in qa if len(w) > 1]
    if not q:
        return 1.0
    cs = set(ca)
    # The surname (the longest word given, typically) must be there.
    return max(tok_hit(w, cs) for w in q)


def score(q_title, q_author, rec):
    t = title_score(q_title, rec["_t"])
    a = author_score(q_author, rec["_a"])
    return t, a, (t * 0.7 + a * 0.3) if q_author else t


def search(rows, q_title, q_author, limit=8):
    q = [w for w in q_title if w not in STOP] or q_title
    key = max(q, key=len)
    sur = max(q_author, key=len) if q_author else None
    out = []
    for r in rows:
        # cheap prefilter: the rarest-looking title word, or the surname
        rt = r["_t"]
        if key not in rt and not (sur and sur in r["_a"]):
            if not any(abs(len(w) - len(key)) <= 2 and w[:2] == key[:2] for w in rt):
                continue
        t, a, s = score(q_title, q_author, r)
        if s >= 0.45:
            out.append((s, t, a, r))
    out.sort(key=lambda x: -x[0])
    return out[:limit]


def is_match(t, a, has_author):
    return t >= 0.8 and (a >= 0.8 or not has_author)


def foreign_signals(rec):
    sig = []
    for rn in rec["regnum"].split(";"):
        if rn.startswith("AF"):
            sig.append(f"{rn}: an A-Foreign registration (first published abroad)")
        elif rn.startswith("AI") or "ad int" in rec.get("regraw", "").lower():
            sig.append(f"{rn}: an ad interim registration (English-language "
                       "book first printed abroad)")
    # "New York and London" is a US imprint with a London office; only a
    # place list with no US place in it counts.
    if FOREIGN_PLACES.search(rec["place"]) and not US_PLACES.search(rec["place"]):
        sig.append(f"place: {rec['place']}")
    return sig


# ------------------------------------------------------------------ report

def fmt_reg(r):
    yr = (r["regdate"] or r["pubdate"])[:10]
    pub = f"; {r['publisher']}" if r["publisher"] else ""
    pl = f" ({r['place']})" if r["place"] else ""
    return (f"{r['regnum'] or '?':<10} {yr:<10} {r['author'][:40]} -- "
            f"{r['title'][:90]}{pub[:50]}{pl[:40]}  [{r['src']}]")


def fmt_ren(r):
    return (f"{r['id']:<10} renewed {r['rdat']:<10} orig {r['oreg'] or '?'} "
            f"{r['odat']} {r['author'][:30]} -- {r['title'][:80]} "
            f"(claimant: {r['claimants'][:50]}) [{r['file']}]")


def check(title, author, year, foreign=False, keep_xml=False, verbose=True):
    """Return (verdict, details dict); print a report when verbose."""
    p = print if verbose else (lambda *a, **k: None)
    qt, qa = toks(title), toks(author or "")
    p(f"\n== {title}" + (f" / {author}" if author else "") + f" ({year})")
    if year <= PD_THROUGH:
        p(f"VERDICT: OUT OF RANGE -- published {year}, public domain in the US "
          f"by age (works through {PD_THROUGH} are PD as of {THIS_YEAR}).")
        return "OUT OF RANGE (PD)", {}
    if year >= 1964:
        p("VERDICT: OUT OF RANGE -- published 1964 or later: renewal was "
          "automatic (1992 Act); in copyright.")
        return "OUT OF RANGE (in copyright)", {}

    # 1. registrations: the year given, and a year either side (a book can
    #    be registered the year after its imprint date, or carry a later one)
    regs = []
    for y in (year - 1, year, year + 1):
        if 1923 <= y <= 1977:
            regs += search(load_reg_year(y, keep_xml), qt, qa)
    regs.sort(key=lambda x: -x[0])
    matched = [x for x in regs if is_match(x[1], x[2], bool(qa))]
    near = [x for x in regs if x not in matched][:5]

    p(f"Registrations searched: CCE {year - 1}-{year + 1}")
    for s, t, a, r in matched[:6]:
        p(f"  MATCH {s:.2f}  {fmt_reg(r)}")
    for s, t, a, r in near:
        p(f"  near  {s:.2f}  {fmt_reg(r)}")
    if not regs:
        p("  (nothing)")

    # 2. renewals: by original registration number anywhere, then by title
    #    in the window
    years = sorted({int((r['regdate'] or str(year))[:4]) for _, _, _, r in matched}
                   or {year})
    lo, hi = min(years) + 26, max(years) + 29
    window = f"{min(years) + 27}-{max(years) + 28} (searched {lo}-{hi})"
    regnums = {n for _, _, _, r in matched for n in r["regnum"].split(";") if n}
    by_num = []
    if regnums:
        for ry in all_ren_years():
            for rr in load_ren_year(ry):
                if rr["_oreg"] and set(rr["_oreg"].split(";")) & regnums:
                    # Registration numbers were reused (the A series restarted
                    # in 1947): the original's date has to agree too.
                    od = rr["odat"][:4]
                    if od.isdigit() and not any(abs(int(od) - y) <= 2 for y in years):
                        continue
                    by_num.append(rr)
    by_title = []
    for ry in range(lo, hi + 1):
        if ry in ren_files():
            for s, t, a, rr in search(load_ren_year(ry), qt, qa):
                by_title.append((s, t, a, rr))
    by_title.sort(key=lambda x: -x[0])
    tmatch = [x for x in by_title if is_match(x[1], x[2], bool(qa))]
    tnear = [x for x in by_title if x not in tmatch][:5]

    p(f"Renewal window: {window}; renewals by orig. reg. no. "
      f"{', '.join(sorted(regnums)) or '(none to look up)'} searched in all "
      f"renewal years {all_ren_years()[0]}-{all_ren_years()[-1]}")
    seen = set()
    for rr in by_num:
        seen.add(rr["id"])
        p(f"  RENEWAL (by number) {fmt_ren(rr)}")
    for s, t, a, rr in tmatch:
        if rr["id"] not in seen:
            seen.add(rr["id"])
            p(f"  RENEWAL (by title {s:.2f}) {fmt_ren(rr)}")
    for s, t, a, rr in tnear:
        if rr["id"] not in seen:
            p(f"  near    {s:.2f}  {fmt_ren(rr)}")
    if not seen and not tnear:
        p("  (no renewal found)")

    renewals = by_num + [x[3] for x in tmatch if x[3] not in by_num]

    # 3. the same title renewed OUTSIDE the window: a revised edition, a
    #    reissue, or a mis-dated original. Never changes the verdict; always
    #    worth reading, since a renewed later edition protects its new matter
    #    and a renewal with a wrong date may still be this book.
    other = []
    if qa:
        for ry in all_ren_years():
            if lo <= ry <= hi:
                continue
            for s, t, a, rr in search(load_ren_year(ry), qt, qa, limit=4):
                if is_match(t, a, True) and rr not in renewals:
                    other.append(rr)
    for rr in other[:6]:
        p(f"  OTHER EDITION/YEAR renewed: {fmt_ren(rr)}")
    # a title match on a renewal only counts against an unmatched or
    # same-number registration; flag renewals of other editions.
    if renewals:
        verdict = "RENEWED"
        p("VERDICT: RENEWED -- in copyright in the US (95 years from "
          "publication). Check that the renewal is this work and edition.")
    elif matched:
        verdict = "NOT RENEWED"
        p("VERDICT: NOT RENEWED -- LIKELY US public domain. Confirm: the "
          "edition in hand is the registered one, the printed notice, and "
          "(if first published abroad) URAA restoration.")
    else:
        verdict = "NOT FOUND IN REGISTRATIONS"
        p("VERDICT: NOT FOUND IN REGISTRATIONS -- published without "
          "registration, or the OCR lost it. Check the near misses and the "
          "book's printed notice; this is NOT a public-domain finding.")

    sig = [s for _, _, _, r in matched[:3] for s in foreign_signals(r)]
    if sig or foreign:
        p("URAA CAVEAT: foreign works that lapsed for want of renewal were "
          "restored on 1 Jan 1996 if still protected at home (most such works "
          "are, life+70). Applies if the work was FIRST published outside "
          "the US (not within 30 days in the US).")
        for s in sig:
            p(f"  signal: {s}")
    elif verdict == "NOT RENEWED":
        p("Reminder: if the author is not American, establish where the book "
          "was FIRST published; URAA restores foreign-first works.")
    if other and verdict != "RENEWED":
        p("  NOTE: renewals of the same title outside the window are listed "
          "above; the original may be free while a later edition is not.")
    return verdict, {"reg": [x[3] for x in matched], "ren": renewals,
                     "foreign": sig, "other": other}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title", nargs="?")
    ap.add_argument("--author", default="")
    ap.add_argument("--year", type=int)
    ap.add_argument("--foreign", action="store_true",
                    help="the author is not American: always print the URAA caveat")
    ap.add_argument("--batch", help="TSV: title, author, year[, foreign]; "
                    "prints a one-line summary per title after the reports")
    ap.add_argument("--fetch", help="warm the registration cache, e.g. 1929-1964")
    ap.add_argument("--keep-xml", action="store_true")
    ap.add_argument("--quiet", action="store_true",
                    help="batch: print only the summary table")
    args = ap.parse_args()

    if args.fetch:
        a, _, b = args.fetch.partition("-")
        for y in range(int(a), int(b or a) + 1):
            ensure_reg_year(y, args.keep_xml)
            print(f"{y}: indexed", file=sys.stderr)
        for y in all_ren_years():
            load_ren_year(y)
        return
    if args.batch:
        summary = []
        for line in open(args.batch, encoding="utf-8"):
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            t, au, yr = f[0], f[1], int(f[2])
            fo = len(f) > 3 and f[3].strip().lower() in ("1", "y", "yes", "foreign")
            v, d = check(t, au, yr, fo, args.keep_xml, verbose=not args.quiet)
            reg = d.get("reg", [])
            ren = d.get("ren", [])
            summary.append([v, t, au, str(yr),
                            ";".join(r["regnum"] for r in reg[:3]),
                            (reg[0]["publisher"][:40] if reg else ""),
                            ";".join(f"{r['id']}@{r['rdat']}" for r in ren[:3]),
                            "FOREIGN" if d.get("foreign") or fo else "",
                            ";".join(f"other:{r['id']}({r['odat'][:4]})"
                                     for r in d.get("other", [])[:3])])
        print("\n# SUMMARY")
        for s in summary:
            print("\t".join(s))
        return
    if not (args.title and args.year):
        ap.error("give a title and --year (or --batch / --fetch)")
    v, _ = check(args.title, args.author, args.year, args.foreign, args.keep_xml)
    sys.exit(0)


if __name__ == "__main__":
    main()
