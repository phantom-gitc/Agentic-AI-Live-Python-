
from dotenv import dotenv_values
from google import genai


# Load API key from .env
config = dotenv_values(".env")

api_key = config.get("GEMINI_API_KEY") or config.get("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key is not set in the .env file.")


client = genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
You are Tyson, a helpful coding tutor.

Answer according to the user's requirement.
Keep your answers short and to the point.
Do not provide unnecessary explanations or examples.
Give more details only when the user asks for them.
"""


question = input("Ask Your AI: ")


messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    },
    {
        "role": "user",
        "content": question
    }
]


prompt = ""

for message in messages:
    prompt += f"""
[{message["role"].upper()}]

{message["content"]}
"""

prompt += """
[ASSISTANT]
"""


response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)

print("\nTyson:", response.text)