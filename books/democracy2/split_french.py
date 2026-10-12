"""Split the four French tomes of De la Démocratie en Amérique into chapter files."""

import re
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "chapters"
OUT.mkdir(exist_ok=True)

def strip_gutenberg(text):
    """Remove Project Gutenberg header and footer."""
    # Find start marker
    start = re.search(r'\*\*\* START OF .+? \*\*\*', text)
    if start:
        text = text[start.end():]
    # Find end marker
    end = re.search(r'\*\*\* END OF .+? \*\*\*', text)
    if end:
        text = text[:end.start()]
    return text.strip()

def find_sections(text, markers):
    """Find positions of section markers in text. Returns list of (pos, marker_text, line)."""
    results = []
    for marker in markers:
        for m in re.finditer(marker, text, re.MULTILINE):
            # Get the full line for context
            line_start = text.rfind('\n', 0, m.start()) + 1
            line_end = text.find('\n', m.end())
            if line_end == -1:
                line_end = len(text)
            full_line = text[line_start:line_end].strip()
            results.append((m.start(), m.group(), full_line))
    results.sort(key=lambda x: x[0])
    return results

def get_chapter_title(text, pos, max_lines=5):
    """Extract chapter title from lines following the CHAPITRE marker."""
    lines = text[pos:pos+500].split('\n')
    title_parts = []
    for line in lines[:max_lines]:
        line = line.strip()
        if line:
            title_parts.append(line)
        elif title_parts:
            break
    return ' '.join(title_parts)

def split_tome(text, tome_name):
    """Split a tome into sections, returning list of (label, content) pairs."""
    sections = []

    # Find all CHAPITRE markers
    chapitre_pattern = r'^CHAPITRE [IVXLC]+\.'
    # Also find structural markers
    struct_patterns = [
        r'^AVERTISSEMENT',
        r'^INTRODUCTION\.',
        r'^CONCLUSION\.',
        r'^PREMIÈRE PARTIE\.',
        r'^DEUXIÈME PARTIE\.',
        r'^TROISIÈME PARTIE\.',
        r'^QUATRIÈME PARTIE\.',
    ]

    all_markers = find_sections(text, [chapitre_pattern] + struct_patterns)

    # Filter out TABLE, NOTES, APPENDICE and everything after
    cutoff_patterns = [r'^NOTES\.', r'^TABLE', r'^APPENDICE', r'^\[Notes au lecteur', r'^\[Note au lecteur']
    cutoffs = find_sections(text, cutoff_patterns)
    cutoff_pos = min((c[0] for c in cutoffs), default=len(text))

    all_markers = [m for m in all_markers if m[0] < cutoff_pos]

    # Also add the "TABLEAU SOMMAIRE" as a non-splitting marker (it's part of Ch VIII)

    for i, (pos, marker, line) in enumerate(all_markers):
        # Determine end of this section
        if i + 1 < len(all_markers):
            end = all_markers[i+1][0]
        else:
            end = cutoff_pos

        content = text[pos:end].strip()

        # Skip PARTIE markers that are just headers (very short content before next chapter)
        if 'PARTIE' in marker and len(content) < 200:
            continue

        sections.append((line, content))

    # Handle content before first marker (front matter)
    if all_markers:
        front = text[:all_markers[0][0]].strip()
        # Strip publishing boilerplate (PARIS, IMPRIMERIE, etc.)
        if front and len(front) > 200:
            sections.insert(0, (f"{tome_name} - Front Matter", front))

    return sections

# Read and process all tomes
tomes = {}
for i, name in enumerate(['tome1', 'tome2', 'tome3', 'tome4'], 1):
    path = BASE / f"{name}.txt"
    raw = path.read_text(encoding='utf-8')
    tomes[name] = strip_gutenberg(raw)
    print(f"{name}: {len(tomes[name])} chars")

# Now split each tome and assign chapter numbers
chapter_num = 0
chapter_log = []

# === VOLUME I (1835) ===
# Tome 1: Avertissement, Introduction, Chapters I-VIII
t1_sections = split_tome(tomes['tome1'], 'Tome 1')
for label, content in t1_sections:
    fname = OUT / f"{chapter_num:03d}.txt"
    fname.write_text(content, encoding='utf-8')
    chapter_log.append(f"{chapter_num:03d}: [Vol I / Tome 1] {label} ({len(content)} chars)")
    print(chapter_log[-1])
    chapter_num += 1

# Tome 2: Chapters I-X, Conclusion
t2_sections = split_tome(tomes['tome2'], 'Tome 2')
for label, content in t2_sections:
    fname = OUT / f"{chapter_num:03d}.txt"
    fname.write_text(content, encoding='utf-8')
    chapter_log.append(f"{chapter_num:03d}: [Vol I / Tome 2] {label} ({len(content)} chars)")
    print(chapter_log[-1])
    chapter_num += 1

# === VOLUME II (1840) ===
# Tome 3: Avertissement, Part 1 (21 ch), Part 2 (20 ch)
t3_sections = split_tome(tomes['tome3'], 'Tome 3')
for label, content in t3_sections:
    fname = OUT / f"{chapter_num:03d}.txt"
    fname.write_text(content, encoding='utf-8')
    chapter_log.append(f"{chapter_num:03d}: [Vol II / Tome 3] {label} ({len(content)} chars)")
    print(chapter_log[-1])
    chapter_num += 1

# Tome 4: Part 3 (26 ch), Part 4 (8 ch)
t4_sections = split_tome(tomes['tome4'], 'Tome 4')
for label, content in t4_sections:
    fname = OUT / f"{chapter_num:03d}.txt"
    fname.write_text(content, encoding='utf-8')
    chapter_log.append(f"{chapter_num:03d}: [Vol II / Tome 4] {label} ({len(content)} chars)")
    print(chapter_log[-1])
    chapter_num += 1

print(f"\n=== Total: {chapter_num} chapter files ===")

# Write chapter manifest
manifest = BASE / "chapter_manifest.txt"
manifest.write_text('\n'.join(chapter_log) + '\n', encoding='utf-8')
print(f"Manifest written to {manifest}")
