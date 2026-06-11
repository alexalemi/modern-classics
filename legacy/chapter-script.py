"""Main translator script."""

import os
from pathlib import Path
from dotenv import dotenv_values
from anthropic import Anthropic


SYSTEM_PROMPT = "You are an expert translations system, designed to modernize old public domain works and make them accessible to a wide modern audience, while remaining faithful to the original text."

# load the environment variable
config = dotenv_values(".env")
api_key = config['ANTHROPIC_API_KEY']

client = Anthropic(api_key=api_key)

with open('chapter_prompt.txt') as f:
    chapter_prompt = f.read().strip()

with open('flatland/flatland.txt') as f:
    original_text = f.read().strip()

with open('text_analysis.txt') as f:
    text_analysis = f.read().strip()


chapter_prompt = chapter_prompt.format(
        ORIGINAL_TEXT=original_text, 
        TARGET_READING_LEVEL='high school',
        TEXT_ANALYSIS=text_analysis,
        CHAPTER=1,
        PREVIOUS_CHAPTER_NOTES="",
        )

response = client.messages.create(
       model="claude-3-haiku-20240307",
       max_tokens=2048,
       messages=[
           {"role": "user", "content": chapter_prompt},
           ]
       )

print(response)

print()
print(response.content[0].text)


