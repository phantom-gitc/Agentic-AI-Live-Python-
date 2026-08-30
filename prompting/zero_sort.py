# Zero-Shot Prompting

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# checking for API key
if not api_key:
    raise ValueError("API key is not set in the .env file.")

# creating Gemini client
client = genai.Client(api_key=api_key)

# getting question from the user
question = input("Ask a coding question: ")

# system prompt
system_prompt = """
You are Anshika, an expert coding tutor.

Answer coding and programming-related questions.
Keep your answers simple and concise.
"""

# getting response from Gemini

response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents=question,
    config=types.GenerateContentConfig(
        system_instruction=system_prompt
    )
)

print("\nAnshika:", response.text)