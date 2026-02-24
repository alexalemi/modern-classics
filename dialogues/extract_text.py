#!/usr/bin/env python3
"""Extract clean text from Standard Ebooks XHTML files for Plato's Dialogues.

Uses regex-based extraction since the HTML structure is consistent and predictable.
"""

import re
import os


def strip_tags(html):
    """Remove HTML tags, keeping text content."""
    # Remove footnote references
    html = re.sub(r'<a[^>]*epub:type="noteref"[^>]*>.*?</a>', '', html)
    # Remove all other tags
    text = re.sub(r'<[^>]+>', '', html)
    # Decode common entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('⁠', '')  # word joiner
    text = text.replace('\u2060', '')  # word joiner
    return text


def extract_dialogue_text(xhtml_path, dialogue_name):
    """Extract the dialogue text (not introduction) from an XHTML file."""
    with open(xhtml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the text section (the actual dialogue, not the introduction)
    text_pattern = rf'<section id="{dialogue_name}-text"[^>]*>(.*?)(?=<section id="{dialogue_name}-introduction"|</article>)'
    text_match = re.search(text_pattern, content, re.DOTALL)
    if not text_match:
        # Try to find just the text section until end of article
        text_pattern = rf'<section id="{dialogue_name}-text"[^>]*>(.*?)</article>'
        text_match = re.search(text_pattern, content, re.DOTALL)

    if not text_match:
        print(f"  WARNING: Could not find text section for {dialogue_name}")
        return ""

    text_html = text_match.group(1)

    # Extract dramatis personae
    dp_match = re.search(r'<section[^>]*dramatis-personae[^>]*>(.*?)</section>', text_html, re.DOTALL)
    dramatis = ""
    if dp_match:
        dp_html = dp_match.group(1)
        # Get bold labels
        bold_parts = re.findall(r'<b>(.*?)</b>', dp_html)
        # Get list items
        items = re.findall(r'<li>\s*<p>(.*?)</p>\s*</li>', dp_html, re.DOTALL)
        if bold_parts:
            dramatis += strip_tags(bold_parts[0]).strip() + "\n"
        if items:
            for item in items:
                dramatis += "  " + strip_tags(item).strip() + "\n"
        # Scene line
        scene_parts = [b for b in bold_parts if 'Scene' in strip_tags(b)]
        if len(bold_parts) > 1:
            last_bold = bold_parts[-1]
            # Get the paragraph containing Scene
            scene_match = re.search(r'<p><b>Scene:?</b>\s*(.*?)</p>', dp_html, re.DOTALL)
            if scene_match:
                dramatis += "\nScene: " + strip_tags(scene_match.group(1)).strip() + "\n"

    # Extract dialogue from table rows
    lines = []
    if dramatis:
        lines.append(dramatis)

    # Process table rows (dialogue format)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', text_html, re.DOTALL)
    for row in rows:
        # Get persona
        persona_match = re.search(r'<td[^>]*persona[^>]*>(.*?)</td>', row, re.DOTALL)
        # Get speech
        speech_match = re.search(r'<td(?![^>]*persona)[^>]*>(.*?)</td>', row, re.DOTALL)

        if persona_match and speech_match:
            speaker = strip_tags(persona_match.group(1)).strip()
            speech = strip_tags(speech_match.group(1)).strip()
            if speaker and speech:
                lines.append(f"\n{speaker}\n{speech}")
        elif speech_match:
            speech = strip_tags(speech_match.group(1)).strip()
            if speech:
                lines.append(f"\n{speech}")

    # Also extract any standalone paragraphs (not in tables)
    # These appear in some dialogues like the Apology which is more monologue
    # Remove table content first to avoid duplication
    non_table_html = re.sub(r'<table>.*?</table>', '', text_html, flags=re.DOTALL)
    non_table_html = re.sub(r'<section[^>]*dramatis-personae[^>]*>.*?</section>', '', non_table_html, flags=re.DOTALL)
    # Remove headers
    non_table_html = re.sub(r'<h[23456][^>]*>.*?</h[23456]>', '', non_table_html, flags=re.DOTALL)

    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', non_table_html, re.DOTALL)
    for p in paragraphs:
        text = strip_tags(p).strip()
        if text and len(text) > 10:  # Skip tiny fragments
            lines.append(f"\n{text}")

    return '\n'.join(lines).strip()


def extract_introduction(xhtml_path, dialogue_name):
    """Extract Jowett's introduction for use in text analysis."""
    with open(xhtml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    intro_pattern = rf'<section id="{dialogue_name}-introduction"[^>]*>(.*?)</section>'
    intro_match = re.search(intro_pattern, content, re.DOTALL)

    if not intro_match:
        return ""

    intro_html = intro_match.group(1)
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', intro_html, re.DOTALL)

    lines = []
    for p in paragraphs:
        text = strip_tags(p).strip()
        if text:
            lines.append(text)

    return '\n\n'.join(lines)


def extract_multibook(xhtml_path, work_name, num_books):
    """Extract a multi-book work (Republic, Laws) into individual books."""
    with open(xhtml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    books = {}

    for book_num in range(1, num_books + 1):
        # Match from this book's section to the next book's section (or end)
        if book_num < num_books:
            pattern = rf'<section id="{work_name}-book-{book_num}"[^>]*>(.*?)(?=<section id="{work_name}-book-{book_num+1}")'
        else:
            pattern = rf'<section id="{work_name}-book-{book_num}"[^>]*>(.*?)(?:</article>)'

        match = re.search(pattern, content, re.DOTALL)
        if not match:
            # Lenient fallback
            pattern = rf'<section id="{work_name}-book-{book_num}"[^>]*>(.*?)(?=<section id="{work_name}-book-{book_num+1}"|<section id="{work_name}-introduction"|</article>)'
            match = re.search(pattern, content, re.DOTALL)

        if match:
            book_html = match.group(1)

            # Extract dramatis personae if present
            dp_match = re.search(r'<section[^>]*dramatis-personae[^>]*>(.*?)</section>', book_html, re.DOTALL)
            dp_text = ""
            if dp_match:
                items = re.findall(r'<li>\s*<p>(.*?)</p>\s*</li>', dp_match.group(1), re.DOTALL)
                bold_parts = re.findall(r'<b>(.*?)</b>', dp_match.group(1))
                parts = []
                for b in bold_parts:
                    parts.append(strip_tags(b).strip())
                for item in items:
                    parts.append("  " + strip_tags(item).strip())
                dp_text = '\n'.join(parts)

            # Extract dialogue rows
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', book_html, re.DOTALL)
            lines = []
            if dp_text:
                lines.append(dp_text + "\n")

            for row in rows:
                persona_match = re.search(r'<td[^>]*persona[^>]*>(.*?)</td>', row, re.DOTALL)
                speech_match = re.search(r'<td(?![^>]*persona)[^>]*>(.*?)</td>', row, re.DOTALL)

                if persona_match and speech_match:
                    speaker = strip_tags(persona_match.group(1)).strip()
                    speech = strip_tags(speech_match.group(1)).strip()
                    if speaker and speech:
                        lines.append(f"\n{speaker}\n{speech}")

            # Also get standalone paragraphs
            non_table = re.sub(r'<table>.*?</table>', '', book_html, flags=re.DOTALL)
            non_table = re.sub(r'<section[^>]*dramatis-personae[^>]*>.*?</section>', '', non_table, flags=re.DOTALL)
            non_table = re.sub(r'<h[23456][^>]*>.*?</h[23456]>', '', non_table, flags=re.DOTALL)
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', non_table, re.DOTALL)
            for p in paragraphs:
                text = strip_tags(p).strip()
                if text and len(text) > 10:
                    lines.append(f"\n{text}")

            books[book_num] = '\n'.join(lines).strip()
            title = work_name.title()
            print(f"  {title} Book {book_num}: {len(books[book_num])} chars")
        else:
            print(f"  WARNING: Could not find {work_name.title()} Book {book_num}")

    # Extract introduction
    intro = extract_introduction(xhtml_path, work_name)
    if intro:
        books[0] = intro

    return books


def extract_republic(xhtml_path):
    """Extract Republic into individual books."""
    return extract_multibook(xhtml_path, 'republic', 10)


def extract_laws(xhtml_path):
    """Extract Laws into individual books (12 books)."""
    return extract_multibook(xhtml_path, 'laws', 12)


def write_chapter(chapters_dir, chapter_num, text, label, chapter_map):
    """Write a chapter file and update the chapter map. Returns next chapter_num."""
    # Split if over 80K chars
    if len(text) > 80000:
        mid = len(text) // 2
        split_point = text.rfind('\n\n', mid - 5000, mid + 5000)
        if split_point == -1:
            split_point = mid

        for i, part in enumerate([text[:split_point].strip(), text[split_point:].strip()]):
            out_path = os.path.join(chapters_dir, f'{chapter_num:03d}.txt')
            with open(out_path, 'w') as f:
                f.write(part)
            part_label = f'{label} (Part {i+1})'
            chapter_map.append((chapter_num, part_label))
            print(f"  {chapter_num:03d}.txt: {part_label} - {len(part)} chars")
            chapter_num += 1
    else:
        out_path = os.path.join(chapters_dir, f'{chapter_num:03d}.txt')
        with open(out_path, 'w') as f:
            f.write(text)
        chapter_map.append((chapter_num, label))
        print(f"  {chapter_num:03d}.txt: {label} - {len(text)} chars")
        chapter_num += 1

    return chapter_num


def extract_dialogues(raw_dir, chapters_dir, dialogues, chapter_num, chapter_map, introductions):
    """Extract a list of simple dialogues. Returns updated chapter_num."""
    for filename, title in dialogues:
        xhtml_path = os.path.join(raw_dir, f'{filename}.xhtml')
        if not os.path.exists(xhtml_path):
            print(f"WARNING: {xhtml_path} not found")
            continue

        text = extract_dialogue_text(xhtml_path, filename)
        intro = extract_introduction(xhtml_path, filename)
        if intro:
            introductions[title] = intro

        if not text or len(text) < 100:
            print(f"  WARNING: {filename} extracted only {len(text)} chars")
            continue

        chapter_num = write_chapter(chapters_dir, chapter_num, text, title, chapter_map)

    return chapter_num


def extract_multibook_chapters(raw_dir, chapters_dir, work_name, title_prefix, num_books, chapter_num, chapter_map, introductions):
    """Extract a multi-book work into chapters. Returns updated chapter_num."""
    xhtml_path = os.path.join(raw_dir, f'{work_name}.xhtml')
    books = extract_multibook(xhtml_path, work_name, num_books)

    intro = extract_introduction(xhtml_path, work_name)
    if intro:
        introductions[title_prefix] = intro

    for book_num in range(1, num_books + 1):
        if book_num not in books:
            continue
        text = books[book_num]
        label = f'{title_prefix} Book {book_num}'
        chapter_num = write_chapter(chapters_dir, chapter_num, text, label, chapter_map)

    return chapter_num


def main():
    raw_dir = '/home/alemi/projects/modern-classics/dialogues/raw'
    chapters_dir = '/home/alemi/projects/modern-classics/dialogues/chapters'
    os.makedirs(chapters_dir, exist_ok=True)

    chapter_num = 0
    chapter_map = []
    introductions = {}

    # ── Phase 1: Core canon (chapters 000-023) ──
    print("=== Phase 1: Core Canon ===\n")

    core_dialogues = [
        ('euthyphro', 'Euthyphro'),
        ('apology', 'Apology'),
        ('crito', 'Crito'),
        ('phaedo', 'Phaedo'),
        ('meno', 'Meno'),
        ('protagoras', 'Protagoras'),
        ('gorgias', 'Gorgias'),
        ('symposium', 'Symposium'),
        ('phaedrus', 'Phaedrus'),
    ]

    chapter_num = extract_dialogues(raw_dir, chapters_dir, core_dialogues, chapter_num, chapter_map, introductions)

    # Republic (10 books)
    print("\nExtracting Republic...")
    chapter_num = extract_multibook_chapters(raw_dir, chapters_dir, 'republic', 'Republic', 10, chapter_num, chapter_map, introductions)

    print(f"\n  Core canon: {chapter_num} chapters (000-{chapter_num-1:03d})")

    # ── Phase 2: Remaining dialogues (chapters 024+) ──
    print("\n=== Phase 2: Remaining Dialogues ===\n")

    # Short early dialogues
    print("Extracting early dialogues...")
    early_dialogues = [
        ('ion', 'Ion'),
        ('laches', 'Laches'),
        ('lysis', 'Lysis'),
        ('charmides', 'Charmides'),
    ]
    chapter_num = extract_dialogues(raw_dir, chapters_dir, early_dialogues, chapter_num, chapter_map, introductions)

    # Euthydemus (comic dialogue, stands alone)
    print("\nExtracting Euthydemus...")
    comic_dialogues = [
        ('euthydemus', 'Euthydemus'),
    ]
    chapter_num = extract_dialogues(raw_dir, chapters_dir, comic_dialogues, chapter_num, chapter_map, introductions)

    # Language and Being cluster
    print("\nExtracting Language and Being dialogues...")
    language_being_dialogues = [
        ('cratylus', 'Cratylus'),
        ('theaetetus', 'Theaetetus'),
        ('parmenides', 'Parmenides'),
        ('sophist', 'Sophist'),
        ('statesman', 'Statesman'),
    ]
    chapter_num = extract_dialogues(raw_dir, chapters_dir, language_being_dialogues, chapter_num, chapter_map, introductions)

    # The Good Life
    print("\nExtracting Philebus...")
    good_life_dialogues = [
        ('philebus', 'Philebus'),
    ]
    chapter_num = extract_dialogues(raw_dir, chapters_dir, good_life_dialogues, chapter_num, chapter_map, introductions)

    # Cosmology
    print("\nExtracting Cosmology dialogues...")
    cosmology_dialogues = [
        ('timaeus', 'Timaeus'),
        ('critias', 'Critias'),
    ]
    chapter_num = extract_dialogues(raw_dir, chapters_dir, cosmology_dialogues, chapter_num, chapter_map, introductions)

    # Laws (12 books — like the Republic but bigger)
    print("\nExtracting Laws...")
    chapter_num = extract_multibook_chapters(raw_dir, chapters_dir, 'laws', 'Laws', 12, chapter_num, chapter_map, introductions)

    # ── Save outputs ──

    # Save chapter map
    map_path = os.path.join(chapters_dir, 'chapter_map.txt')
    with open(map_path, 'w') as f:
        for num, title in chapter_map:
            f.write(f'{num:03d}\t{title}\n')

    # Save introductions for reference
    intro_path = os.path.join('/home/alemi/projects/modern-classics/dialogues', 'jowett_introductions.txt')
    with open(intro_path, 'w') as f:
        for title, intro in introductions.items():
            f.write(f'{"="*60}\n')
            f.write(f'{title}\n')
            f.write(f'{"="*60}\n\n')
            f.write(intro)
            f.write('\n\n')

    print(f"\nTotal chapters: {chapter_num}")
    print(f"Chapter map: {map_path}")
    print(f"Jowett introductions saved for reference")


if __name__ == '__main__':
    main()
