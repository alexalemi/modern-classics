# Modern Classics

Modernize classic public domain texts into engaging, accessible contemporary English
using Claude as both the orchestrator and the translator.

## Project Goal

Take old public domain books with archaic language and retell them in a modern,
conversational voice — faithful to the original meaning but genuinely fun to read.
Target reading level: eighth grade to high school.

## How a Translation Works

Each book goes through these phases:

### 1. Setup — Prepare the source text

- Obtain a plain text version of the book (standardebooks.org is the best source, Project Gutenberg is the secondary source)
- Place the source text in a new directory: `{book}/`
- Create a `{book}/env` file with metadata:
  ```
  ORIGINAL_WORK=Title of the Work
  AUTHOR=Author Name
  DATE=Year
  ```
- Download the book into chapters or sections, they need to fit into context, if they are too long you have to split them.
  The `splitter.py` tool can help — it takes a source text file and a splits file
  (one split delimiter per line) and produces numbered chapter files.

### 2. Text Analysis — Develop a translation strategy

Before translating any chapters, analyze the full work to create a consistent
strategy. This analysis should cover:

- Style, tone, and key themes of the original
- Challenges specific to this text (archaic vocabulary, cultural references, etc.)
- Consistent vocabulary mappings (e.g. archaic → modern equivalents)
- How to preserve the author's distinctive voice in modern English
- Any content that needs careful handling

Save the analysis to `{book}/text_analysis.txt`.

### 3. Chapter-by-chapter Translation

Translate each chapter sequentially using subagents. For each chapter:

- Read the original chapter text from `{book}/chapters/NNN.txt`
- Use the text analysis and the previous chapter's notes for consistency
- Produce three outputs:
  - **Modernized text** — the full chapter in modern English
  - **Explanation** — brief notes on major changes and rationale
  - **Next chapter notes** — consistency guidance for the next chapter
- Save the modernized chapter to `{book}/modern_chapters/NNN.txt`

### 4. Assembly — Combine into a readable book

- Combine all modernized chapters into a single HTML file using the style
  from `index.html` as a template (clean serif typography, readable layout)
- The HTML should have a table of contents and chapter headings

## Translation Philosophy

The translator persona is: an expert scholar who has studied this work their
entire life, who is also a gifted storyteller, retelling the story for a modern
audience.

Key principles:
- **Faithful but not literal** — preserve meaning, tone, and narrative arc
- **Conversational and engaging** — modern turns of phrase, natural rhythm
- **Complete** — translate the entire text, don't summarize or truncate
- **Consistent** — maintain vocabulary choices and voice across chapters
- **Respectful** — handle dated cultural content thoughtfully

What to modernize:
- Archaic vocabulary → modern equivalents
- Complex/nested sentence structures → clearer modern syntax
- Outdated references → brief contextual explanations where needed
- Punctuation and formatting → modern conventions

What to preserve:
- The author's distinctive voice and style
- Famous passages and quotations
- Narrative structure and pacing
- Literary devices and imagery

## Directory Structure

```
{book}/                    # One directory per book
  env                      # Metadata (ORIGINAL_WORK, AUTHOR, DATE)
  {source}.txt             # Original full text
  chapters/                # Split chapter files (000.txt, 001.txt, ...)
  text_analysis.txt        # Translation strategy document
  modern_chapters/         # Translated chapters (000.txt, 001.txt, ...)
```

## Existing Scripts

- `splitter.py` — splits a source text into chapter files given a splits file
- `translator.py` — original API-based batch translator (uses Anthropic API directly)
- `chapter_prompt.txt` — the prompt template used for chapter translation
- `prompt.01.txt` — the prompt template used for text analysis

These scripts represent the original approach (calling the API programmatically).
Claude Code can now do this work directly — reading chapters, translating them
in-context, and writing the output files — without needing the API scripts.

## Books Completed

- **The Decameron** by Giovanni Boccaccio (1492) — two passes (decameron1/, decameron2/)
- **Flatland** by Edwin A. Abbott (1884) — one pass (flatland1/)
