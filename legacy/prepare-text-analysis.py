"""Main translator script."""

import os
import sys
from pathlib import Path
from dotenv import dotenv_values
from anthropic import Anthropic


SYSTEM_PROMPT = "You are an expert translations system, designed to modernize old public domain works and make them accessible to a wide modern audience, while remaining faithful to the original text."

# load the environment variable
config = dotenv_values(".env")
api_key = config['ANTHROPIC_API_KEY']

client = Anthropic(api_key=api_key)

with open('initial_prompt.txt') as f:
    initial_prompt = f.read().strip()


initial_prompt = initial_prompt.format(
        ORIGINAL_TEXT=original_text, 
        TARGET_READING_LEVEL='high school',
        )

response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": initial_prompt},
            ]
        )

print(response)

print()
print(response.content[0].text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: you need to supply a target directory.")
        sys.exit(1)
    folder = Path(sys.argv[1])
