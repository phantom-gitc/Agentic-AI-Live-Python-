import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

question = input("Ask a math question: ")

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=question,
    config=types.GenerateContentConfig(
        system_instruction=(
            "You are an expert in mathematics. "
            "Only answer mathematics-related questions. "
            "If the user asks something unrelated to mathematics, "
            "say: I can only answer mathematics-related questions."
        ),
        temperature=0.2,
        max_output_tokens=180,
        top_p=0.9,
        candidate_count=1,
    ),
)

print("\nGemini:", response.text)