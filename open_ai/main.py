from dotenv import load_dotenv
from groq import Groq

# Load variables from .env
load_dotenv()

# Create Groq client
client = Groq()

# Send request to the AI
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Hello, I am Tyson! Nice to meet you."
        }
    ]
)

# Print AI response
print(response.choices[0].message.content)