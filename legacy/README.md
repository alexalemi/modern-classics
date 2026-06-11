# Legacy scripts

These are the original API-based translation tools, kept for reference.
They are no longer the recommended path:

- `translator.py`, `chapter-script.py`, `prepare-text-analysis.py` — batch
  translators calling the Anthropic API directly. They target old models
  (claude-3-haiku / claude-3-5-haiku) with `max_tokens` of 2048–4096, which
  is too small to return a full translated chapter — a likely source of the
  truncation problems in early books. If you revive them, update the model
  and raise `max_tokens` well above the longest chapter.
- `chapter_prompt.txt`, `chapter_prompt.0.txt`, `prompt.00.txt`,
  `prompt.01.txt`, `initial_prompt.txt` — the prompt templates those
  scripts format.
- `assemble_democracy.py` — book-specific assembler for Democracy in
  America, superseded by the generic `assemble.py` at the repo root.

The current workflow (Claude Code orchestrating subagents with a shared
instruction file and running-notes ledger) is documented in `CLAUDE.md`.
