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

response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": "Hi Claude."}
            ]
        )

print(response)

