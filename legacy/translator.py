"""Main translator script."""

import os
import sys
import re
from pathlib import Path
from dotenv import dotenv_values
from anthropic import Anthropic
import tqdm


TARGET_READING_LEVEL = 'eighth grade'

SYSTEM_PROMPT = "You are an expert translations system, designed to modernize old public domain works and make them accessible to a wide modern audience, writing them in contemporary and engaging English."

SYSTEM_PROMPT = ""

# load the environment variable
config = dotenv_values(".env")
api_key = config['ANTHROPIC_API_KEY']

client = Anthropic(api_key=api_key)


def load_book_env(path):
    config = dotenv_values(path / "env")
    return config

def send_message(message):
    return client.messages.create(
        # model="claude-3-haiku-20240307",
        model="claude-3-5-haiku-20241022",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": message},
            ]
        )

def extract_tag(text, tag):
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match


def prepare_text_analysis(path, env):
    SAMPLE_TEXT = ""
    chapter = 0
    while len(SAMPLE_TEXT) <= 1000:
        with open(path / 'chapters' / f'{chapter:03d}.txt', 'r') as f:
            SAMPLE_TEXT += f.read()

    with open('initial_prompt.txt') as f:
        initial_prompt = f.read().strip()


    initial_prompt = initial_prompt.format(
            TARGET_READING_LEVEL=TARGET_READING_LEVEL, 
            SAMPLE_TEXT = SAMPLE_TEXT,
            **env)
    print(f"Asking for text_analysis for {env}")
    response = send_message(initial_prompt)

    with open(path / 'prompts' / 'text_analysis.txt', 'w') as f:
        f.write(initial_prompt)

    with open(path / 'raw_responses' / 'text_analysis.txt', 'w') as f:
        f.write(repr(response))

    with open(path / 'responses' / 'text_analysis.txt', 'w') as f:
        f.write(response.content[0].text)

    text_analysis = extract_tag(response.content[0].text, 'text_analysis')
    if text_analysis is None:
        raise KeyError("Count not find text_analysis!")
    print(f"Extracted text_analysis:\n{text_analysis.group(0)}")
    with open(path / 'text_analysis.txt', 'w') as f:
        f.write(text_analysis.group(0))
    return text_analysis.group(1)


def translate_chapter(folder, env, chapter_number, text_analysis, prev_notes):
    with open(folder / 'chapters' / f"{chapter_number:03d}.txt", 'r') as f:
        original_text = f.read()

    with open('chapter_prompt.txt') as f:
        chapter_prompt = f.read().strip()

    chapter_prompt = chapter_prompt.format(
            TARGET_READING_LEVEL=TARGET_READING_LEVEL, 
            CHAPTER = chapter_number,
            ORIGINAL_TEXT = original_text,
            PREVIOUS_CHAPTER_NOTES = prev_notes,
            TEXT_ANALYSIS = text_analysis,
            **env)

    print(f"Translating Chapter {chapter_number}...")

    response = send_message(chapter_prompt)

    with open(folder / 'prompts' / f'{chapter_number:03d}.txt', 'w') as f:
        f.write(chapter_prompt)

    with open(folder / 'raw_responses' / f'{chapter_number:03d}.txt', 'w') as f:
        f.write(repr(response))

    with open(folder / 'responses' / f'{chapter_number:03d}.txt', 'w') as f:
        f.write(response.content[0].text)

    next_chapter_notes = extract_tag(response.content[0].text, 'next_chapter_notes')
    if next_chapter_notes is None:
        raise KeyError("Count not find next_chapter_notes!")
    modernized_text = extract_tag(response.content[0].text, 'modernized_text')
    if modernized_text is None:
        raise KeyError("Count not find modernized_text!")
    explanation = extract_tag(response.content[0].text, 'explanation')
    if explanation is None:
        raise KeyError("Count not find explanation!")

    print(f"Input text was {len(original_text)} and output text was {len(modernized_text.group(1))}.")

    with open(folder / 'modern_chapters' / f'{chapter_number:03d}.txt', 'w') as f:
        f.write(modernized_text.group(0))
        f.write('\n\n')
        f.write(explanation.group(0))

    return next_chapter_notes.group(1)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: you need to supply a target directory.")
        sys.exit(1)
    folder = Path(sys.argv[1])

    (folder / 'responses').mkdir(parents=True, exist_ok=True)
    (folder / 'modern_chapters').mkdir(parents=True, exist_ok=True)
    (folder / 'prompts').mkdir(parents=True, exist_ok=True)
    (folder / 'raw_responses').mkdir(parents=True, exist_ok=True)

    print(f"Asked to translate {folder}")
    book_env = load_book_env(folder)
    print(f"Loaded environment: {book_env}")

    if len(sys.argv) == 3:
        chapter = int(sys.argv[2])
        print(f"Starting at chapter: {chapter}")

        with open(folder / 'text_analysis.txt', 'r') as f:
            text_analysis = extract_tag(f.read(), 'text_analysis').group(1)

        with open(folder / 'responses' / f'{chapter-1:03d}.txt', 'r') as f:
            prev = f.read()
        prev_notes = extract_tag(prev, 'next_chapter_notes')[1]
        start = chapter

    else:

        text_analysis = prepare_text_analysis(folder, book_env)
        prev_notes = ""
        start = 0

    chapters = len(list((folder / "chapters").glob("???.txt")))
    for chapter in tqdm.trange(start, chapters):
        prev_notes = translate_chapter(folder, book_env, chapter, text_analysis, prev_notes)

    



