"""Build RSS and OPDS feeds for the site.

    python3 build_feeds.py [--base-url URL]

Writes:
  site/feed.xml    RSS 2.0 — one item per book, newest first, with the
                   book page as the link and the epub as the enclosure
  site/opds.xml    OPDS 1.2 acquisition feed — one entry per book with
                   open-access epub links and cover images
  site/covers/     cover JPEGs copied from build/ebooks/<slug>/images/
                   (skipped, with a warning, for books whose build tree
                   is missing)

Book list and descriptions come from ebook_meta.json + each book's env.
Publication dates come from git: the commit that first added the book's
site page. Books are ordered newest-first in both feeds.
"""

import argparse
import datetime
import email.utils
import html
import json
import shutil
import subprocess
from pathlib import Path

import assemble  # find_epub, read_env

ROOT = Path(__file__).parent
DEFAULT_BASE = "https://alexalemi.com/modern-classics"

# book dir -> site page, where the page name differs from the dir name
PAGE_OVERRIDES = {"malthus": "population.html",
                  "descartes": "philosophical-works.html"}


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
        bdir = ROOT / m["dir"]
        env = assemble.read_env(bdir / "env")
        page = PAGE_OVERRIDES.get(m["dir"], f"{m['dir']}.html")
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


def build_opds(books, base):
    entries = []
    for b in books:
        links = [f'      <link rel="alternate" type="text/html" href="{base}/{b["page"]}"/>']
        if b["epub"]:
            links.append(f'      <link rel="http://opds-spec.org/acquisition/open-access" '
                         f'type="application/epub+zip" href="{base}/ebooks/{esc(b["epub"])}"/>')
        if b.get("cover"):
            links.append(f'      <link rel="http://opds-spec.org/image" '
                         f'type="image/jpeg" href="{base}/{b["cover"]}"/>')
            links.append(f'      <link rel="http://opds-spec.org/image/thumbnail" '
                         f'type="image/jpeg" href="{base}/{b["cover"]}"/>')
        author_uri = f"\n        <uri>{esc(b['author'])}</uri>" if b["author"] else ""
        entries.append(f"""  <entry>
    <title>{esc(b['title'])}</title>
    <id>{base}/{b['page']}</id>
    <updated>{b['date']}</updated>
    <author>
      <name>{esc(b['author_name'])}</name>{author_uri}
    </author>
    <summary type="text">{esc(b['description'])}</summary>
{chr(10).join(links)}
  </entry>""")
    newest = books[0]["date"] if books else ""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>{base}/opds.xml</id>
  <title>Modern Classics</title>
  <updated>{newest}</updated>
  <author><name>Modern Classics</name><uri>{base}/</uri></author>
  <link rel="self" type="application/atom+xml;profile=opds-catalog;kind=acquisition" href="{base}/opds.xml"/>
  <link rel="start" type="application/atom+xml;profile=opds-catalog;kind=acquisition" href="{base}/opds.xml"/>
{chr(10).join(entries)}
</feed>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    books = collect(base)
    copy_covers(books)
    (ROOT / "site" / "feed.xml").write_text(build_rss(books, base))
    (ROOT / "site" / "opds.xml").write_text(build_opds(books, base))
    print(f"wrote site/feed.xml and site/opds.xml ({len(books)} books, "
          f"newest: {books[0]['key'] if books else 'n/a'})")


if __name__ == "__main__":
    main()
