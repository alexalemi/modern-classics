"""Rebrand an se create-draft skeleton as a Modern Classics production.

Standard Ebooks' name and logo identify *their* editions; these retellings
are not SE productions, so every SE trademark is replaced with Modern
Classics attribution while keeping SE's structure, semantics, and file
layout (so `se lint` still validates the important things).
"""

import html
import json
import re
from pathlib import Path

REPO = "https://github.com/alexalemi/modern-classics"


def esc(s):
    return html.escape(s, quote=False)


def apply(dest, env, meta, spine):
    _content_opf(dest, env, meta)
    pn = dest / "production-notes.md"
    if pn.exists() and not pn.read_text().strip():
        pn.unlink()
    _imprint(dest, env, meta)
    _colophon(dest, env, meta)
    _uncopyright(dest, env, meta)
    logo = dest / "src/epub/images/logo.svg"
    if logo.exists():
        logo.unlink()


def _content_opf(dest, env, meta):
    p = dest / "src/epub/content.opf"
    t = p.read_text()
    book = meta["dir"]

    t = t.replace(
        re.search(r"<dc:identifier id=\"uid\">[^<]*</dc:identifier>", t).group(0),
        f'<dc:identifier id="uid">{REPO}/tree/main/{book}</dc:identifier>')

    # publisher block: Modern Classics
    t = t.replace('<dc:publisher id="publisher">Standard Ebooks</dc:publisher>',
                  '<dc:publisher id="publisher">Modern Classics</dc:publisher>')
    t = t.replace('<meta property="file-as" refines="#publisher">Standard Ebooks</meta>',
                  '<meta property="file-as" refines="#publisher">Modern Classics</meta>')
    t = t.replace('<link href="https://standardebooks.org/" refines="#publisher" rel="schema:url"/>',
                  f'<link href="{REPO}" refines="#publisher" rel="schema:url"/>')
    t = t.replace('<meta property="a11y:certifiedBy" refines="#conformance-statement">Standard Ebooks</meta>',
                  '<meta property="a11y:certifiedBy" refines="#conformance-statement">Modern Classics</meta>')

    # title/subtitle
    if env.get("SUBTITLE") and 'id="subtitle"' not in t:
        t = t.replace(
            '<meta property="file-as" refines="#title">',
            f'<dc:title id="subtitle">{esc(env["SUBTITLE"])}</dc:title>\n\t\t'
            '<meta property="file-as" refines="#title">', 1) if False else t

    t = t.replace("<dc:language>LANG</dc:language>", "<dc:language>en-US</dc:language>")
    # not an SE production and not published from an SE-convention repo
    t = re.sub(r'\t*<meta id="vcs-repository".*?rel="schema:codeRepository"/>\n', "", t, flags=re.S)

    # subjects, genre, descriptions
    subs = meta["subjects"]
    t = t.replace("<dc:subject id=\"subject-1\">SUBJECT_1</dc:subject>",
                  f"<dc:subject id=\"subject-1\">{esc(subs[0][0])}</dc:subject>")
    t = t.replace("<dc:subject id=\"subject-2\">SUBJECT_2</dc:subject>",
                  f"<dc:subject id=\"subject-2\">{esc(subs[1][0])}</dc:subject>")
    t = t.replace("<meta property=\"term\" refines=\"#subject-1\">SUBJECT_1_LCSH_ID</meta>",
                  f"<meta property=\"term\" refines=\"#subject-1\">{subs[0][1]}</meta>")
    t = t.replace("<meta property=\"term\" refines=\"#subject-2\">SUBJECT_2_LCSH_ID</meta>",
                  f"<meta property=\"term\" refines=\"#subject-2\">{subs[1][1]}</meta>")
    t = t.replace("<meta property=\"schema:genre\">TAG</meta>",
                  f"<meta property=\"schema:genre\">{meta['genre']}</meta>")
    t = t.replace("<dc:description id=\"description\">DESCRIPTION</dc:description>",
                  f"<dc:description id=\"description\">{esc(meta['description'])}</dc:description>")
    long_desc = "\n\t\t\t".join(
        html.escape(p_, quote=False).replace("<", "&lt;").replace(">", "&gt;")
        for p_ in (f"<p>{d}</p>" for d in meta["long_description"]))
    t = re.sub(r"(<meta id=\"long-description\"[^>]*>\n)\t*LONG_DESCRIPTION\n",
               lambda m: m.group(1) + "\t\t\t" + long_desc + "\n", t)

    # sources: original transcription + this project
    sources = []
    if env.get("SOURCE_URL"):
        sources.append(env["SOURCE_URL"])
    sources.append(f"{REPO}/tree/main/{book}")
    t = t.replace("<dc:source>TRANSCRIPTION_URL</dc:source>",
                  f"<dc:source>{sources[0]}</dc:source>")
    if len(sources) > 1:
        t = t.replace("<dc:source>PAGE_SCANS_URL</dc:source>",
                      f"<dc:source>{sources[-1]}</dc:source>")
    else:
        t = t.replace("\t\t<dc:source>PAGE_SCANS_URL</dc:source>\n", "")

    t = t.replace("<meta property=\"schema:alternateName\" refines=\"#author\">CONTRIBUTOR_FULL_NAME</meta>\n\t\t", "")
    sort = meta.get("author_sort", env["AUTHOR"])
    t = t.replace('<meta property="file-as" refines="#author">CONTRIBUTOR_SORT</meta>',
                  f'<meta property="file-as" refines="#author">{esc(sort)}</meta>')

    # author authority links (create-draft leaves placeholders for names it can't resolve)
    if meta.get("author_wiki"):
        t = re.sub(r'<link href="(https://en\.wikipedia\.org/wiki/[^"]*|CONTRIBUTOR_WIKI_URL)" refines="#author" rel="schema:sameAs"/>',
                   f'<link href="{meta["author_wiki"]}" refines="#author" rel="schema:sameAs"/>', t, count=1)
    t = re.sub(r'\t*<link href="(CONTRIBUTOR_WIKI_URL|CONTRIBUTOR_NACOAF_URI|https://id\.loc\.gov[^"]*)" refines="#author" rel="schema:sameAs"/>\n', "", t)
    if not meta.get("author_wiki"):
        t = re.sub(r'\t*<link href="[^"]*" refines="#author" rel="schema:sameAs"/>\n', "", t)

    # author also wrote the book's dedication/preface
    roles = ""
    if meta.get("_has_dedication"):
        roles += '\n\t\t<meta property="role" refines="#author" scheme="marc:relators">dto</meta>'
    if meta.get("_has_preface"):
        roles += '\n\t\t<meta property="role" refines="#author" scheme="marc:relators">wpr</meta>'
    if roles:
        t = t.replace('<meta property="role" refines="#author" scheme="marc:relators">aut</meta>',
                      '<meta property="role" refines="#author" scheme="marc:relators">aut</meta>' + roles)
    if meta.get("alt_title"):
        t = t.replace('<meta property="file-as" refines="#title">',
                      f'<meta property="dcterms:alternative" refines="#title">{esc(meta["alt_title"])}</meta>\n'
                      '\t\t<meta property="file-as" refines="#title">', 1)

    # artist block
    art = meta.get("cover", {})
    if art:
        t = t.replace("<dc:contributor id=\"artist\">COVER_ARTIST_NAME</dc:contributor>",
                      f"<dc:contributor id=\"artist\">{esc(art['artist'])}</dc:contributor>")
        t = t.replace("<meta property=\"file-as\" refines=\"#artist\">COVER_ARTIST_SORT</meta>",
                      f"<meta property=\"file-as\" refines=\"#artist\">{esc(art['artist_sort'])}</meta>")
        t = t.replace('<link href="COVER_ARTIST_WIKI_URL" refines="#artist" rel="schema:sameAs"/>',
                      f'<link href="{art["artist_wiki"]}" refines="#artist" rel="schema:sameAs"/>' if art.get("artist_wiki") else "")
        t = re.sub(r'\t*<link href="COVER_ARTIST_NACOAF_URI"[^\n]*\n', "", t)
        t = re.sub(r'\t*\n(\t*<meta property="role" refines="#artist")', r"\n\1", t)
    if not art:
        t = re.sub(r'\t\t<dc:contributor id="artist">.*?scheme="marc:relators">art</meta>\n', "", t, flags=re.S)
    # transcriber blocks: none — the modern text is original to this project
    t = re.sub(r'\t\t<dc:contributor id="transcriber-\d">.*?scheme="marc:relators">trc</meta>\n',
               "", t, flags=re.S)
    # producer
    t = t.replace("<dc:contributor id=\"producer-1\">PRODUCER_NAME</dc:contributor>",
                  '<dc:contributor id="producer-1">Alex Alemi</dc:contributor>')
    t = t.replace("<meta property=\"file-as\" refines=\"#producer-1\">PRODUCER_SORT</meta>",
                  '<meta property="file-as" refines="#producer-1">Alemi, Alex</meta>')
    t = t.replace('<link href="PRODUCER_URL" refines="#producer-1" rel="schema:url"/>\n\t\t', "")

    # the retelling itself is a new work: credit the modernizer as translator
    t = t.replace('<meta property="role" refines="#producer-1" scheme="marc:relators">tyg</meta>',
                  '<meta property="role" refines="#producer-1" scheme="marc:relators">trl</meta>\n'
                  '\t\t<meta property="role" refines="#producer-1" scheme="marc:relators">tyg</meta>')

    # wikipedia page for the work (create-draft leaves EBOOK_WIKI_URL when it
    # can't find the title on Wikipedia)
    if meta.get("work_wiki"):
        t = re.sub(r'<link href="(?:EBOOK_WIKI_URL|https://en\.wikipedia\.org/wiki/[^"]*)" rel="schema:sameAs"/>',
                   f'<link href="{meta["work_wiki"]}" rel="schema:sameAs"/>', t, count=1)
    else:
        t = t.replace('\t\t<link href="EBOOK_WIKI_URL" rel="schema:sameAs"/>\n', "")

    p.write_text(t)


def _imprint(dest, env, meta):
    p = dest / "src/epub/text/imprint.xhtml"
    t = p.read_text()
    t = re.sub(r'\t*<img[^>]*logo\.svg[^>]*/>\n', "", t)
    t = re.sub(r'<header>\s*<h2 epub:type="title">([^<]*)</h2>\s*</header>',
               r'<h2 epub:type="title">\1</h2>', t)
    t = t.replace(
        'This ebook is the product of many hours of hard work by volunteers for <a href="https://standardebooks.org/">Standard Ebooks</a>, and builds on the hard work of other literature lovers made possible by the public domain.',
        f'This ebook is a <a href="{REPO}">Modern Classics</a> retelling: a classic public domain text, retold in contemporary English with the help of Claude, an AI model by Anthropic. It is not affiliated with or endorsed by Standard Ebooks, whose open tooling and style manual were used to produce it.')
    src = env.get("SOURCE_URL")
    src_name = env.get("SOURCE_NAME", "Project Gutenberg")
    trl = env.get("TRANSLATOR") or env.get("TRANSLATORS")
    based = f'This particular ebook is a modern retelling of <i epub:type="se:name.publication.book">{esc(env["ORIGINAL_WORK"])}</i> by {esc(env["AUTHOR"])}'
    if trl:
        based += f", working from the English translation by {esc(trl)}"
    if src:
        based += f', with the source text drawn from <a href="{src}">{esc(src_name)}</a>'
    based += "."
    t = re.sub(r'<p>This particular ebook is based on a transcription[^<]*<a href="TRANSCRIPTION_URL">TRANSCRIPTION_SOURCE</a>[^<]*<a href="PAGE_SCANS_URL">PAGE_SCANS_SOURCE</a>\.</p>',
               f"<p>{based}</p>", t)
    t = t.replace(
        'The source text and artwork in this ebook are believed to be in the United States public domain',
        'The original source text and artwork in this ebook are believed to be in the United States public domain')
    t = t.replace(
        'Standard Ebooks is a volunteer-driven project that produces ebook editions of public domain literature using modern typography, technology, and editorial standards, and distributes them free of cost. You can download this and other ebooks carefully produced for true book lovers at <a href="https://standardebooks.org/">standardebooks.org</a>.',
        f'Modern Classics retells great books in a modern, conversational voice — faithful to the original meaning, and genuinely fun to read. The retelling is released under the MIT license; you can read all the books, and inspect every stage of how they were made, at <a href="{REPO}">github.com/alexalemi/modern-classics</a>.')
    p.write_text(t)


def _colophon(dest, env, meta):
    p = dest / "src/epub/text/colophon.xhtml"
    t = p.read_text()
    t = re.sub(r'\t*<img[^>]*logo\.svg[^>]*/>\n', "", t)
    t = re.sub(r'<header>\s*<h2 epub:type="title">([^<]*)</h2>\s*</header>',
               r'<h2 epub:type="title">\1</h2>', t)
    t = t.replace("was published in <time>YEAR</time> by",
                  f"was published in {esc(env['DATE'])} by" if not env["DATE"].isdigit()
                  else f"was published in <time>{env['DATE']}</time> by")
    author_link = (f'<a href="{meta["author_wiki"]}">{esc(env["AUTHOR"])}</a>'
                   if meta.get("author_wiki") else
                   f'<b epub:type="z3998:personal-name">{esc(env["AUTHOR"])}</b>')
    t = re.sub(r'<a href="https://en\.wikipedia\.org/wiki/E\._W\._Hornung">.*?</a>\.</p>',
               author_link + ".</p>", t)  # no-op for non-draft templates
    t = re.sub(r'<a href="https://en\.wikipedia\.org/wiki/[^"]*">[^<]*</a>\.</p>\n(\t*<p>This ebook was produced for)',
               author_link + ".</p>\n" + r"\1", t, count=1)
    t = t.replace('This ebook was produced for<br/>\n\t\t\t<a href="https://standardebooks.org/">Standard Ebooks</a><br/>\n\t\t\tby<br/>\n\t\t\t<a href="PRODUCER_URL">PRODUCER_NAME</a>,<br/>',
                  f'This ebook was retold in contemporary English for<br/>\n\t\t\t<a href="{REPO}">Modern Classics</a><br/>\n\t\t\tby<br/>\n\t\t\t<b epub:type="z3998:personal-name">Alex Alemi</b> and Claude,<br/>')
    src = env.get("SOURCE_URL")
    src_name = env.get("SOURCE_NAME", "Project Gutenberg")
    trl = env.get("TRANSLATOR") or env.get("TRANSLATORS")
    tail = ""
    if trl:
        tail += f'and is based on the English translation by<br/>\n\t\t\t<b epub:type="z3998:personal-name">{esc(trl)}</b>'
        tail += (f'<br/>\n\t\t\tfrom<br/>\n\t\t\t<a href="{src}">{esc(src_name)}</a>.</p>' if src else ".</p>")
    elif src:
        tail = f'and is based on the source text from<br/>\n\t\t\t<a href="{src}">{esc(src_name)}</a>.</p>'
    else:
        tail = ".</p>"
    t = t.replace('and is based on a transcription produced in <time>TRANSCRIPTION_YEAR</time> by<br/>\n\t\t\t<b epub:type="z3998:personal-name">TRANSCRIBER_1_NAME</b>, <b epub:type="z3998:personal-name">TRANSCRIBER_2_NAME</b>, and <a href="https://www.pgdp.net/">Distributed Proofreaders</a><br/>\n\t\t\tfor<br/>\n\t\t\t<a href="TRANSCRIPTION_URL">TRANSCRIPTION_SOURCE</a><br/>\n\t\t\tand on digital scans from<br/>\n\t\t\t<a href="PAGE_SCANS_URL">PAGE_SCANS_SOURCE</a>.</p>', tail)
    art = meta.get("cover", {})
    if art:
        t = t.replace("<i epub:type=\"se:name.visual-art.painting\">PAINTING</i>",
                      f"<i epub:type=\"se:name.visual-art.painting\">{esc(art['painting'])}</i>")
        t = t.replace("a painting completed in <time>YEAR</time> by",
                      f"a {art.get('medium', 'painting')} completed in <time>{art['year']}</time> by")
        artist = (f'<a href="{art["artist_wiki"]}">{esc(art["artist"])}</a>'
                  if art.get("artist_wiki") else f'<b epub:type="z3998:personal-name">{esc(art["artist"])}</b>')
        t = t.replace('<a href="COVER_ARTIST_WIKI_URL">COVER_ARTIST_NAME</a>', artist)
    t = re.sub(r'You can check for updates to this ebook.*?</a>\.</p>',
               f'You can find this ebook, and the whole Modern Classics library, at<br/>\n\t\t\t<a href="{REPO}">github.com/alexalemi/modern-classics</a>.</p>', t, flags=re.S)
    t = t.replace('The volunteer-driven Standard Ebooks project relies on readers like you to submit typos, corrections, and other improvements. Anyone can contribute at <a href="https://standardebooks.org/">standardebooks.org</a>.',
                  f'Corrections and improvements are welcome — open an issue or pull request at <a href="{REPO}">github.com/alexalemi/modern-classics</a>.')
    p.write_text(t)


def _uncopyright(dest, env, meta):
    p = dest / "src/epub/text/uncopyright.xhtml"
    t = p.read_text()
    t = t.replace("<a href=\"https://standardebooks.org/\">standardebooks.org</a>",
                  f"<a href=\"{REPO}\">github.com/alexalemi/modern-classics</a>")
    t = t.replace("Standard Ebooks", "Modern Classics")
    p.write_text(t)


def order_spine(dest, spine):
    """Rewrite the <spine> in content.opf into reading order."""
    p = dest / "src/epub/content.opf"
    t = p.read_text()
    items = ["titlepage.xhtml", "imprint.xhtml"] + spine + ["colophon.xhtml", "uncopyright.xhtml"]
    xml = "\t<spine>\n" + "\n".join(
        f'\t\t<itemref idref="{f}"/>' for f in items) + "\n\t</spine>"
    t = re.sub(r"\t<spine>.*?</spine>", xml, t, flags=re.S)
    p.write_text(t)
