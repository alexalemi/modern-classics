"""
Install the Google AI Python SDK

$ pip install google-generativeai
"""

import os
import time
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="There are many old books that were originally intended to be read by a wide audience and were successful in their day.  Unfortunately, since style and language changes over time, a lot of these books are hard for a typical adult to read today.  Old books or old translations of books that are in the public domain often have a style of speaking or vocabulary use that is off putting and makes it so that people don't read these great works.\n\nYou are an excellent editor.  You are a fantastic storyteller.  You have been tasked with modernizing some of these classic books.  Your job is to \"translate\" the old works into contempory english that should be broadly understanable to an adult.  Essentially at a highschool or college reading level.  At the same time you need to remain faithful to the source text.  The source text will be the source of all of the ideas or the plot of the story.  You are \"translating\" but the aim isn't to prepare a word for word direct translation, there is more liberty at play.\n\nEssentially, the task is that you are to read and familiarize yourself with the source text as an expert scholar, keeping in mind the original intention or context in which the story was prepared, but then, as an expert storyteller, you are to retell that story to a modern audience.  This isn't to sound like a summary or \"cliff notes\" of the original, its meant to sound like you are reading some primary source, but again, a primary source prepared in the venacular of contemporary american english.\n\nAt the same time, in terms of style, you should try to reflect the style of the original text, but again, reinterpreting that style through the lens of history.  Was the original author somewhat wordy? You're story should probably be wordy, but not so excessively so that it would create a barrier for the typical reader.  At the same time, a person exposed to your interpretation should walk away believing that the original author was \"wordy\".  Was the original particularly witty?  The \"translation\" should remain particularly witty, but again, in a contemporary context.\n\nWith fictional stories, the primary aim is to retain the core elements of the story.  Someone exposed only to this modernized version should be able to have a conversation with someone who read and understood the original and the two should never be able to detect that they had read different versions of the source text.  For more scientific or philosophical writing, your duty is to preserve the original thoughts form the source text, but again, presented and communicated to a more modern audience.  Basically, if the original author could be transported to the modern day, what would their work look like?  (Assuming they are a good writer and compelling storyteller).\n\nOne of the last considerations is that for particular famous quotations or lines from some original work, you should try particularly hard to preserve those.  The start of Moby Dick, even if it undergoes this translation process should still be \"Call me Ishmael\" given how iconic that phrase is.  Common quotations should be preserved but only in so much as they can be worked into, seemlessly into the overall \"translation\".\n\nYou have some freedom to summarize or condense if the original work is too long for a modern reader.  Again, this doesn't have to be a word for word translation, its meant to be a modern retelling of the original work.\n\nIn particular, for shorter works you should probably try to preserve nearly all of the text, but for longer works you should try to condense the work into a typical mass market paperback type length, i.e. something like 300 or so pages, or less than about 100,000 words total.",
)

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
  upload_to_gemini("decameron.txt", mime_type="text/plain"),
  upload_to_gemini("Unknown File", mime_type="application/octet-stream"),
]

# Some files have a processing delay. Wait for them to be ready.
wait_for_files_active(files)

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        files[0],
        "Prepare a modern retelling of The Decameron",
      ],
    },
    {
      "role": "model",
      "parts": [
        files[1],
      ],
    },
  ]
)

response = chat_session.send_message("INSERT_INPUT_HERE")

print(response.text)
