"""Search-engine and link-preview plumbing for the site.

    python3 seo.py      # share cards, sitemap.xml, 404.html

What is here:
  head_tags()          -- <meta description>, canonical link, and the Open
                          Graph / Twitter tags that make a pasted link show a
                          card (title, blurb, image) in iMessage, Slack, X,
                          Bluesky, Facebook, Discord.
  describe()           -- the one-sentence description of a book page. It is
                          the shelf blurb; nothing new is stored here.
  make_share_cards()   -- site/covers/share/<dir>.jpg, 1200x630, for every
                          cover, plus site/brand/share.jpg for the front pages.
  write_sitemap()      -- site/sitemap.xml from the pages actually in site/.
  write_404()          -- site/404.html, which GitHub Pages serves for a
                          missing path.

THE CANONICAL HOST IS emend.press. BASE is the one place it is written;
build_feeds.DEFAULT_BASE reads it from here. The same site is reachable at
www.emend.press, emendpress.com and the old www.alexalemi.com/modern-classics,
and every page names https://emend.press/... as the real address.

WHY 1200x630 AND NOT THE COVER ITSELF. Facebook, LinkedIn and X crop a link
image to ~1.91:1 from the centre, which cuts a 2:3 cover to a band across the
middle and loses the title. A card that is already 1.91:1, with the whole
cover on it, survives every platform uncropped. The full covers are also
~650 KB, which some previewers refuse.
"""
import paths
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BASE = "https://emend.press"
SITE_NAME = "Modern Classics"
SITE_DESCRIPTION = ("Classic books retold in plain contemporary English, and "
                    "restored editions of the originals. Free to read online "
                    "and as ebooks, from Emend Press.")

CARD = (1200, 630)
CREAM = (0xFB, 0xF8, 0xF1)
SITE_CARD = "brand/share.jpg"
SITE_CARD_COVERS = ["odyssey", "quixote", "flatland", "origin-of-species"]
# Pages in site/ that are not pages a reader should land on from a search.
NOT_PAGES = {"template.html", "404.html"}


def url(page):
    """The canonical address of a site file: the front page is BASE/."""
    return f"{BASE}/" if page == "index.html" else f"{BASE}/{page}"


def _plain(s):
    """A blurb or title as plain text: tags out, entities decoded."""
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def describe(book, original=False, restored=False):
    """The description of book <dir>'s page: its shelf blurb.

    Retellings have their blurb in build_index.BLURBS, restored editions in
    build_restored.BLURBS. Imported here, not at the top, because
    build_restored imports assemble, which imports this."""
    import build_index
    import build_restored
    blurb = build_index.BLURBS.get(book) or build_restored.BLURBS.get(book, "")
    blurb = _plain(blurb)
    if not blurb:
        return ""
    # The blurbs are written for a card under a cover, often 60-90
    # characters; a search result has room for ~155, so say what the page
    # is as well. Which kind of page this is decides the sentence.
    if original:
        return f"{blurb} The original text, unmodernized: free to read online."
    if restored:
        return f"{blurb} A restored edition, free to read online and as an ebook."
    return f"{blurb} Retold in modern English, free to read online and as an ebook."


def head_tags(page, title, description, image=None, kind="website"):
    """Tags for the <head> of site/<page>.

    title and description are plain text (they are escaped here). image is a
    path inside site/, or None for the site card."""
    image = image or SITE_CARD
    t, d = html.escape(_plain(title)), html.escape(_plain(description))
    lines = [
        f'<meta name="description" content="{d}">',
        f'<link rel="canonical" href="{url(page)}">',
        f'<meta property="og:type" content="{kind}">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">',
        f'<meta property="og:url" content="{url(page)}">',
        f'<meta property="og:image" content="{BASE}/{image}">',
        f'<meta property="og:image:width" content="{CARD[0]}">',
        f'<meta property="og:image:height" content="{CARD[1]}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    return "\n\t".join(lines)


def _year(date):
    """A schema.org date from an env DATE, or None: "1884" yes, "c. 1200" no."""
    m = re.fullmatch(r"(\d{3,4})", str(date).strip())
    return m.group(1).zfill(4) if m else None


def _ld(obj):
    """A JSON-LD <script> block; "</" is escaped so text can never close it."""
    import json
    text = json.dumps(obj, ensure_ascii=False, indent=None).replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>'


PUBLISHER = {"@type": "Organization", "name": "Emend Press", "url": f"{BASE}/",
             "logo": f"{BASE}/apple-touch-icon.png"}


def book_jsonld(env, page, description, book, epub, original=False):
    """schema.org/Book for a book page: what search engines read to know the
    page is a book, by whom, from when, free, with an epub.

    A retelling is a new edition (datePublished = MODERN_YEAR) that
    isBasedOn the original work (its own DATE); the original-text and
    restored pages are the work itself."""
    title, author = _plain(env["ORIGINAL_WORK"]), _plain(env["AUTHOR"])
    restored = original or env.get("EDITION", "").lower() == "restored"
    person = {"@type": "Person", "name": author}
    ld = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": title + (": The Original Text" if original else ""),
        "author": person,
        "inLanguage": "en",
        "url": url(page),
        "description": _plain(description),
        "publisher": PUBLISHER,
        "isAccessibleForFree": True,
        "isPartOf": {"@type": "BookSeries", "name": SITE_NAME, "url": f"{BASE}/"},
    }
    if (SITE / "covers" / f"{book}.jpg").exists():
        ld["image"] = f"{BASE}/covers/{book}.jpg"
    if restored:
        if _year(env["DATE"]):
            ld["datePublished"] = _year(env["DATE"])
    else:
        ld["datePublished"] = env.get("MODERN_YEAR", "2026")
        ld["bookEdition"] = "Modern English retelling"
        based = {"@type": "Book", "name": title, "author": person}
        if _year(env["DATE"]):
            based["datePublished"] = _year(env["DATE"])
        ld["isBasedOn"] = based
    if epub:
        ld["workExample"] = {
            "@type": "Book",
            "bookFormat": "https://schema.org/EBook",
            "encodingFormat": "application/epub+zip",
            "url": f"{BASE}/ebooks/{epub}",
        }
    return _ld(ld)


def site_jsonld():
    """WebSite + publisher for the front page."""
    return _ld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": f"{BASE}/",
        "description": SITE_DESCRIPTION,
        "publisher": PUBLISHER,
    })


def share_image(book):
    """The share card for book <dir>, if its cover exists."""
    return f"covers/share/{book}.jpg" if (SITE / "covers" / f"{book}.jpg").exists() else None


def _wordmark(height):
    """The Emend wordmark as an RGBA image `height` pixels tall."""
    from PIL import Image
    png = ROOT / "build" / f"wordmark-{height}.png"
    if not png.exists():
        png.parent.mkdir(exist_ok=True)
        subprocess.run(["rsvg-convert", "-h", str(height), "-o", str(png),
                        str(ROOT / "brand" / "emend-wordmark.svg")], check=True)
    return Image.open(png).convert("RGBA")


def _paste_cover(card, src, height, x, y):
    from PIL import Image
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((height * 2, height), Image.LANCZOS)
        card.paste(im, (x, y))
        return im.size


def _font(name, size, weight):
    from PIL import ImageFont
    f = ImageFont.truetype(str(ROOT / "brand" / "fonts" / name), size)
    f.set_variation_by_axes([weight])
    return f


def _wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and draw.textlength(trial, font=font) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


NAVY = (0x24, 0x30, 0x3F)


def _book_card(src, title, author):
    """Cover on the left; title, author and the Emend wordmark on the right.
    The covers are paintings with no lettering, so without the title the
    card would not say which book it is."""
    from PIL import Image, ImageDraw
    card = Image.new("RGB", CARD, CREAM)
    w, _ = _paste_cover(card, src, CARD[1] - 80, 80, 40)
    draw = ImageDraw.Draw(card)
    x = 80 + w + 60
    width = CARD[0] - x - 60
    for size in (64, 56, 48, 42, 36):
        tfont = _font("CormorantGaramond[wght].ttf", size, 600)
        lines = _wrap(draw, title, tfont, width)
        if len(lines) <= 4:
            break
    afont = _font("Montserrat[wght].ttf", 26, 500)
    alines = _wrap(draw, author, afont, width)
    lead = int(size * 1.1)
    y = 70
    for line in lines:
        draw.text((x, y), line, font=tfont, fill=NAVY)
        y += lead
    y += 24
    for line in alines:
        draw.text((x, y), line, font=afont, fill=NAVY)
        y += 36
    mark = _wordmark(90)
    card.paste(mark, (x - 8, CARD[1] - 40 - mark.height), mark)
    return card


def make_share_cards():
    """site/covers/share/<dir>.jpg for every cover, and the site card.

    Regenerated when the cover or the book's env (title, author) is newer;
    a card whose cover is gone is removed (a step that writes a set of files
    owns the set)."""
    import assemble
    from PIL import Image
    src_dir = SITE / "covers"
    out = src_dir / "share"
    out.mkdir(exist_ok=True)
    wanted = set()
    for src in sorted(src_dir.glob("*.jpg")):
        dest = out / src.name
        wanted.add(dest.name)
        env_file = paths.book_dir(src.stem) / "env"
        newest = max(src.stat().st_mtime, Path(__file__).stat().st_mtime,
                     env_file.stat().st_mtime if env_file.exists() else 0)
        if dest.exists() and dest.stat().st_mtime >= newest:
            continue
        env = assemble.read_env(env_file) if env_file.exists() else {}
        card = _book_card(src, env.get("ORIGINAL_WORK", ""), env.get("AUTHOR", ""))
        card.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
    for stale in out.glob("*.jpg"):
        if stale.name not in wanted:
            stale.unlink()

    # The front pages' card: four covers in a row over the wordmark.
    card = Image.new("RGB", CARD, CREAM)
    h, gap = 390, 24
    w = h * 2 // 3
    x0 = (CARD[0] - 4 * w - 3 * gap) // 2
    for i, book in enumerate(SITE_CARD_COVERS):
        _paste_cover(card, src_dir / f"{book}.jpg", h, x0 + i * (w + gap), 40)
    mark = _wordmark(150)
    card.paste(mark, ((CARD[0] - mark.width) // 2, 40 + h + 20), mark)
    card.save(SITE / SITE_CARD, "JPEG", quality=82, optimize=True, progressive=True)


def write_sitemap():
    pages = sorted(p.name for p in SITE.glob("*.html") if p.name not in NOT_PAGES)
    # the front pages first: they are what a crawler should start from
    front = ["index.html", "restored.html", "about.html"]
    pages = front + [p for p in pages if p not in front]
    body = "\n".join(f"  <url><loc>{url(p)}</loc></url>" for p in pages)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n")
    print(f"wrote site/sitemap.xml ({len(pages)} pages)")


def write_404():
    """GitHub Pages serves 404.html at whatever path was missing, so a
    relative link on it would resolve against that path: <base href="/">
    makes every link and stylesheet resolve from the site root."""
    import build_index
    page = build_index.page_shell(
        "404.html", "Page not found &mdash; Modern Classics", "Page not found",
        "Classic books, retold and restored",
        '<article class="prose">\n<p>There is no page at this address. '
        'It may have moved, or the link may have a typo.</p>\n'
        '<p><a href="./">Browse the whole library</a>, or see the '
        '<a href="restored.html">restored editions</a>.</p>\n</article>',
        description="")
    page = page.replace('<meta charset="utf-8">',
                        '<meta charset="utf-8">\n\t<base href="/">\n\t'
                        '<meta name="robots" content="noindex">', 1)
    page = page.replace('<a href="./">', '<a href="/">')
    (SITE / "404.html").write_text(page)
    print("wrote site/404.html")


if __name__ == "__main__":
    make_share_cards()
    write_sitemap()
    write_404()
    sys.exit(0)
