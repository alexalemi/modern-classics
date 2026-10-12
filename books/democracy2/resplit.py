"""Re-split oversized chapter files on subsection headings."""

import re
from pathlib import Path

BASE = Path(__file__).parent
CHAPTERS = BASE / "chapters"
MAX_CHARS = 45000  # Target max size per chapter file

def find_subsection_splits(text, target_size):
    """Find ALL-CAPS subsection headings as potential split points."""
    # Pattern: line starting with ALL CAPS words (at least 15 chars), often a subsection title
    pattern = re.compile(r'^([A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ][A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ\' ,\-]{14,})', re.MULTILINE)
    candidates = []
    for m in pattern.finditer(text):
        # Check this isn't the very first line
        if m.start() < 10:
            continue
        # Check there's a blank line before it (section boundary)
        before = text[max(0, m.start()-3):m.start()]
        if '\n\n' in before or m.start() < 5:
            candidates.append(m.start())

    if not candidates:
        # Fallback: split on paragraph boundaries near the midpoint
        mid = len(text) // 2
        # Find nearest double-newline to midpoint
        pos = text.rfind('\n\n', mid - 5000, mid + 5000)
        if pos > 0:
            return [pos]
        return []

    # Select split points to keep chunks under target_size
    splits = []
    last_split = 0
    for pos in candidates:
        chunk_size = pos - last_split
        if chunk_size >= target_size:
            splits.append(pos)
            last_split = pos

    # If the last chunk is too big, we might need more splits
    # But our candidates should cover it
    return splits


# Read manifest to preserve labels
manifest_lines = (BASE / "chapter_manifest.txt").read_text().strip().split('\n')
manifest = {}
for line in manifest_lines:
    num = line[:3]
    manifest[num] = line[5:]  # Everything after "NNN: "

# Process all chapters
new_chapters = []  # (label, content) pairs

for chap_file in sorted(CHAPTERS.glob('*.txt')):
    num = chap_file.stem
    content = chap_file.read_text(encoding='utf-8')
    label = manifest.get(num, f"Chapter {num}")

    if len(content) <= MAX_CHARS:
        new_chapters.append((label, content))
    else:
        # Need to split
        splits = find_subsection_splits(content, MAX_CHARS)
        if not splits:
            print(f"WARNING: Could not split {num} ({len(content)} chars)")
            new_chapters.append((label, content))
            continue

        parts = []
        prev = 0
        for sp in splits:
            parts.append(content[prev:sp].strip())
            prev = sp
        parts.append(content[prev:].strip())

        base_label = label.split('(')[0].strip()
        for i, part in enumerate(parts):
            part_label = f"{base_label} — Part {i+1}/{len(parts)} ({len(part)} chars)"
            new_chapters.append((part_label, part))
            print(f"  Split {num}: Part {i+1}/{len(parts)} = {len(part)} chars")

# Rewrite all chapter files with new numbering
# First, clear old files
for f in CHAPTERS.glob('*.txt'):
    f.unlink()

new_manifest = []
for i, (label, content) in enumerate(new_chapters):
    fname = CHAPTERS / f"{i:03d}.txt"
    fname.write_text(content, encoding='utf-8')
    # Update char count in label
    if '(' in label and 'chars)' in label:
        label_base = label[:label.rfind('(')].strip()
    else:
        label_base = label
    entry = f"{i:03d}: {label_base} ({len(content)} chars)"
    new_manifest.append(entry)

(BASE / "chapter_manifest.txt").write_text('\n'.join(new_manifest) + '\n', encoding='utf-8')

print(f"\n=== Total: {len(new_chapters)} chapter files ===")

# Report any remaining large files
for i, (label, content) in enumerate(new_chapters):
    if len(content) > MAX_CHARS:
        print(f"  STILL LARGE: {i:03d} = {len(content)} chars")
