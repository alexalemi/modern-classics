"""Build RSS and OPDS feeds for the site.

    python3 build_feeds.py [--base-url URL]

Writes:
  site/feed.xml    RSS 2.0 — one item per book, newest first, with the
                   book page as the link and the epub as the enclosure
  site/opds.atom   OPDS 1.2 NAVIGATION root (opds.xml is a copy): Recently
                   added, one feed per front-page shelf and restored topic,
                   and All books A-Z in pages; the books themselves are in
                   site/opds/*.atom with epub links, cover and thumbnail.
                   Split because CrossPoint keeps only 62 entries per feed.
  site/covers/     cover JPEGs copied from build/ebooks/<slug>/images/
                   (skipped, with a warning, for books whose build tree
                   is missing)

Book list and descriptions come from ebook_meta.json + each book's env.
Publication dates come from git: the commit that first added the book's
site page. Books are ordered newest-first in both feeds.
"""

import paths
import argparse
import datetime
import email.utils
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import assemble  # find_epub, read_env
import seo

ROOT = Path(__file__).parent
# emend.press is the canonical host (GitHub Pages custom domain, set in the
# repo's Pages settings; site/CNAME records it). Before 2026-10 the site
# lived at www.alexalemi.com/modern-classics, which GitHub now redirects.
# Historical note: www was the no-redirect host: bare alexalemi.com 301s via plain http,
# which simple e-reader OPDS clients refuse to follow.
# The host itself is written once, in seo.BASE (canonical links use it too).
DEFAULT_BASE = seo.BASE

# book dir -> site page, where the page name differs from the dir name
# The published filename now lives in each book's env as PAGE, read by
# assemble.py, sweep.py and this script alike. It used to be a dict here
# and nowhere else, which is how assemble came to write a page that
# nothing linked to while the site served a stale one.


def esc(s):
    return html.escape(s, quote=True)


def added_date(page):
    """ISO date of the commit that first added site/<page> (None if unknown)."""
    out = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%aI", "--", f"site/{page}"],
        capture_output=True, text=True, cwd=ROOT).stdout.strip().splitlines()
    return out[-1] if out else None


def collect(base):
    books = []
    meta = json.loads((ROOT / "ebook_meta.json").read_text())
    for key, m in meta.items():
        bdir = paths.book_dir(m["dir"])
        env = assemble.read_env(bdir / "env")
        page = env.get("PAGE", m["dir"]) + ".html"
        if not (ROOT / "site" / page).exists():
            print(f"  skipping {key}: no site page")
            continue
        epub = assemble.find_epub(bdir, ROOT)
        date = added_date(page)
        books.append({
            "key": key, "dir": m["dir"], "page": page, "epub": epub,
            "title": env["ORIGINAL_WORK"], "author": m.get("author_wiki", ""),
            "author_name": env["AUTHOR"], "date": date or "2026-01-01T00:00:00+00:00",
            "description": m.get("description", env.get("SUBTITLE", "")),
            "shelf": env.get("SHELF"), "topic": env.get("TOPIC"),
            "restored": env.get("EDITION", "").lower() == "restored",
            "year": env.get("DATE", ""),
        })
    books.sort(key=lambda b: b["date"], reverse=True)
    return books


def copy_covers(books):
    out = ROOT / "site" / "covers"
    out.mkdir(exist_ok=True)
    for b in books:
        if not b["epub"]:
            continue
        slug = b["epub"][:-len(".epub")]
        src = ROOT / "build" / "ebooks" / slug / "images" / "cover.jpg"
        dest = out / f"{b['dir']}.jpg"
        if src.exists():
            shutil.copy(src, dest)
            b["cover"] = f"covers/{b['dir']}.jpg"
        elif dest.exists():
            b["cover"] = f"covers/{b['dir']}.jpg"
        else:
            print(f"  no cover for {b['key']} (missing {src})")
            b["cover"] = None


THUMB_SIZE = (300, 450)   # the OPDS thumbnail, and the cards' fallback src
# The index cards show covers 110px wide (80px on phones), so they load WebP
# at the widths a 2x-3x screen needs instead of the 300px JPEG: a median of
# 5 KB (160px) or 11 KB (240px) against 25 KB.
CARD_WIDTHS = (160, 240)


def make_thumbs():
    """site/covers/thumb/<dir>.jpg for every cover, for the index cards.

    The full covers are 1400x2100 and ~700 KB; an index of a hundred of
    them would be ~80 MB. Regenerated when the cover is newer, and a
    thumb whose cover is gone is removed -- a step that writes a SET of
    files must own the set (the copy_figures lesson)."""
    from PIL import Image
    src_dir = ROOT / "site" / "covers"
    out = src_dir / "thumb"
    out.mkdir(exist_ok=True)
    wanted = set()
    for src in sorted(src_dir.glob("*.jpg")):
        dest = out / src.name
        smalls = [out / f"{src.stem}-{w}.webp" for w in CARD_WIDTHS]
        wanted.update(d.name for d in [dest, *smalls])
        if all(d.exists() and d.stat().st_mtime >= src.stat().st_mtime
               for d in [dest, *smalls]):
            continue
        with Image.open(src) as im:
            im = im.convert("RGB")
            for w, small in zip(CARD_WIDTHS, smalls):
                im.resize((w, w * 3 // 2), Image.LANCZOS).save(small, "WEBP", quality=78, method=6)
            im.thumbnail(THUMB_SIZE, Image.LANCZOS)
            im.save(dest, "JPEG", quality=80, optimize=True, progressive=True)
    for stale in [*out.glob("*.jpg"), *out.glob("*.webp")]:
        if stale.name not in wanted:
            stale.unlink()


def rfc822(iso):
    return email.utils.format_datetime(datetime.datetime.fromisoformat(iso))


def build_rss(books, base):
    items = []
    for b in books:
        pub = rfc822(b["date"])
        enclosure = ""
        if b["epub"]:
            size = (ROOT / "site" / "ebooks" / b["epub"]).stat().st_size
            enclosure = (f'\n      <enclosure url="{base}/ebooks/{esc(b["epub"])}" '
                         f'length="{size}" type="application/epub+zip"/>')
        items.append(f"""    <item>
      <title>{esc(b['title'])} — {esc(b['author_name'])}</title>
      <link>{base}/{b['page']}</link>
      <guid>{base}/{b['page']}</guid>
      <pubDate>{pub}</pubDate>
      <description>{esc(b['description'])}</description>{enclosure}
    </item>""")
    newest = rfc822(books[0]["date"]) if books else ""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Modern Classics</title>
    <link>{base}/</link>
    <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Classic public-domain texts, retold in contemporary English. New retellings as they are finished.</description>
    <language>en-us</language>
    <lastBuildDate>{newest}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""


ACQ = "application/atom+xml;profile=opds-catalog;kind=acquisition"
NAV = "application/atom+xml;profile=opds-catalog;kind=navigation"
ROOT_HREF = "opds.atom"
RECENT = 25          # books in "Recently added"
PAGE_SIZE = 50       # books per page of "All books"; CrossPoint keeps 62


def book_entries(books, base):
    entries = []
    for b in books:
        links = [f'      <link rel="alternate" type="text/html" href="{base}/{b["page"]}"/>']
        if b["epub"]:
            # Two acquisition links, deliberately. "open-access" is the
            # correct OPDS 1.2 rel for a free book, but several minimal
            # readers look ONLY for the bare "acquisition" rel and report
            # the whole catalog as broken when they do not find one.
            links.append(f'      <link rel="http://opds-spec.org/acquisition" '
                         f'type="application/epub+zip" href="{base}/ebooks/{esc(b["epub"])}"/>')
            links.append(f'      <link rel="http://opds-spec.org/acquisition/open-access" '
                         f'type="application/epub+zip" href="{base}/ebooks/{esc(b["epub"])}"/>')
        if b.get("cover"):
            links.append(f'      <link rel="http://opds-spec.org/image" '
                         f'type="image/jpeg" href="{base}/{b["cover"]}"/>')
            # the 300x450 card thumbnail (~25 KB), not the 1400x2100 cover:
            # an e-reader lists a whole page of these over slow Wi-Fi
            thumb = b["cover"].replace("covers/", "covers/thumb/", 1)
            links.append(f'      <link rel="http://opds-spec.org/image/thumbnail" '
                         f'type="image/jpeg" href="{base}/{thumb}"/>')
        author_uri = f"\n        <uri>{esc(b['author'])}</uri>" if b["author"] else ""
        entries.append(f"""  <entry>
    <title>{esc(b['title'])}</title>
    <id>{base}/{b['page']}</id>
    <updated>{b['date']}</updated>
    <author>
      <name>{esc(b['author_name'])}</name>{author_uri}
    </author>
    <summary type="text">{esc(b['description'])}</summary>
    <content type="text">{esc(b['description'])}</content>
{chr(10).join(links)}
  </entry>""")
    return entries


def feed(base, href, title, kind, entries, updated, extra_links=()):
    """One OPDS feed document. Every feed links home (start) and to itself."""
    links = [f'  <link rel="self" type="{kind}" href="{base}/{href}"/>',
             f'  <link rel="start" type="{NAV}" href="{base}/{ROOT_HREF}"/>']
    if href != ROOT_HREF:
        links.append(f'  <link rel="up" type="{NAV}" href="{base}/{ROOT_HREF}"/>')
    links += list(extra_links)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>{base}/{href}</id>
  <title>{esc(title)}</title>
  <updated>{updated}</updated>
  <author><name>Emend Press</name><uri>{base}/</uri></author>
{chr(10).join(links)}
{chr(10).join(entries)}
</feed>
"""


def nav_entry(base, href, title, summary, updated, rel="subsection"):
    return f"""  <entry>
    <title>{esc(title)}</title>
    <id>{base}/{href}</id>
    <updated>{updated}</updated>
    <content type="text">{esc(summary)}</content>
    <link rel="{rel}" type="{ACQ}" href="{base}/{href}"/>
  </entry>"""


def build_opds(books, base):
    """The OPDS catalog as {path: document}.

    A NAVIGATION ROOT with one entry per category, because CrossPoint (the
    X3's firmware) keeps only the first 62 entries of any one feed and the
    flat catalog had 135. Categories are the front page's own: Recently
    added, the nine retelling shelves (build_index.SHELVES), the restored
    editions' topics (build_restored.TOPICS), and All books A-Z in pages of
    PAGE_SIZE with next/previous links. The original-text companions stay
    out, as before: they are the same books."""
    import build_index, build_restored
    from build_index import first_year
    out = {}
    newest = books[0]["date"] if books else ""
    def by_year(bs):
        return sorted(bs, key=lambda b: (first_year(b["year"])[0], b["date"]))
    def latest(bs):
        return max(b["date"] for b in bs)
    def plural(n):
        return f"{n} book" + ("" if n == 1 else "s")

    cats = []   # (href, title, summary, books, rel)
    recent = books[:RECENT]
    cats.append(("opds/recent.atom", "Recently added",
                 f"The {len(recent)} newest books, newest first.", recent,
                 "http://opds-spec.org/sort/new"))
    for shelf in build_index.SHELVES:
        bs = by_year([b for b in books if b["shelf"] == shelf and not b["restored"]])
        if bs:
            cats.append((f"opds/{assemble.slugify(shelf)}.atom", shelf,
                         f"Retellings: {plural(len(bs))}, oldest first.", bs, "subsection"))
    for topic in build_restored.TOPICS:
        bs = by_year([b for b in books if b["restored"] and b["topic"] == topic])
        if bs:
            cats.append((f"opds/restored-{assemble.slugify(topic)}.atom",
                         f"Restored: {topic}",
                         f"Restored editions, the author's own words: {plural(len(bs))}.",
                         bs, "subsection"))
    for href, title, _, bs, _ in cats:
        out[href] = feed(base, href, title, ACQ, book_entries(bs, base), latest(bs))

    # All books, A-Z, paged
    az = sorted(books, key=lambda b: assemble.slugify(re.sub(r"^(the|a|an) ", "", b["title"].lower())))
    pages = [az[i:i + PAGE_SIZE] for i in range(0, len(az), PAGE_SIZE)]
    hrefs = [f"opds/all-{i + 1}.atom" for i in range(len(pages))]
    for i, chunk in enumerate(pages):
        extra = []
        if i > 0:
            extra.append(f'  <link rel="previous" type="{ACQ}" href="{base}/{hrefs[i - 1]}"/>')
        if i + 1 < len(pages):
            extra.append(f'  <link rel="next" type="{ACQ}" href="{base}/{hrefs[i + 1]}"/>')
        out[hrefs[i]] = feed(base, hrefs[i], f"All books, A-Z ({i + 1} of {len(pages)})",
                             ACQ, book_entries(chunk, base), latest(chunk), extra)

    nav = [nav_entry(base, h, t, s, latest(bs), rel) for h, t, s, bs, rel in cats]
    nav.append(nav_entry(base, hrefs[0], "All books, A-Z",
                         f"Every book, {plural(len(books))}, in pages of {PAGE_SIZE}.", newest))
    out[ROOT_HREF] = feed(base, ROOT_HREF, "Modern Classics", NAV, nav, newest)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    books = collect(base)
    copy_covers(books)
    make_thumbs()
    seo.make_share_cards()
    (ROOT / "site" / "feed.xml").write_text(build_rss(books, base))
    # The SAME catalog is written twice, under two extensions. GitHub
    # Pages picks the Content-Type from the extension alone and cannot be
    # given custom headers, so opds.xml goes out as "application/xml" —
    # which some OPDS readers reject outright. ".atom" is served as
    # "application/atom+xml", which is what the spec asks for, so
    # opds.atom is the URL to hand out. opds.xml stays for anyone
    # already subscribed to it.
    # opds.xml is the same root document, for anyone subscribed to it.
    catalog = build_opds(books, base)
    out = ROOT / "site" / "opds"
    out.mkdir(exist_ok=True)
    for old_feed in out.glob("*.atom"):      # the set is ours: drop stale categories
        if f"opds/{old_feed.name}" not in catalog:
            old_feed.unlink()
    for href, doc in catalog.items():
        (ROOT / "site" / href).write_text(doc)
    (ROOT / "site" / "opds.xml").write_text(catalog[ROOT_HREF])
    print(f"wrote site/feed.xml, site/opds.xml, site/opds.atom and "
          f"{len(catalog) - 1} OPDS category feeds "
          f"({len(books)} books, newest: {books[0]['key'] if books else 'n/a'})")


if __name__ == "__main__":
    main()
