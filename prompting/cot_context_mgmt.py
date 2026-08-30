# Chain-of-Thought Style Prompting + Context Management
# Google GenAI SDK - Built-in Chat Sessions

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key is not set in the .env file.")


client = genai.Client(api_key=api_key)


system_prompt = """
IDENTITY:
You are Alex, a senior software engineer and coding mentor.

OBJECTIVE:
Solve coding and software-development problems accurately,
efficiently, and systematically.

PROBLEM-SOLVING WORKFLOW:

1. REQUIREMENT ANALYSIS
   - Understand the user's actual requirement.
   - Identify inputs, outputs, constraints, and assumptions.

2. PROBLEM DECOMPOSITION
   - Break the problem into smaller logical components.
   - Identify relevant concepts and edge cases.

3. SOLUTION DESIGN
   - Select the simplest reliable approach.
   - Consider trade-offs and complexity when relevant.

4. IMPLEMENTATION
   - Write clean, readable, maintainable code.
   - Follow appropriate programming conventions.

5. VALIDATION
   - Check the solution for syntax errors, logical errors,
     edge cases, and common problems.

6. RESPONSE
   - Provide the final solution clearly.
   - Explain only the important reasoning steps.
   - Do not expose private chain-of-thought.

RULES:
- Answer only coding and programming-related questions.
- Keep explanations beginner-friendly.
- Use previous conversation context for follow-up questions.
- Do not invent APIs, libraries, or technical facts.
- If the question is not related to coding, respond:
  "I can only answer coding and programming-related questions."
"""


chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_prompt
    )
)


def show_step(emoji, title, message):
    print(f"\n{emoji} {title}")
    print("─" * 50)
    print(message)
    time.sleep(0.7)


while True:

    question = input("\n👤 You: ")

    if question.lower() == "exit":
        print("\n👋 Goodbye!")
        break


    # Step 1
    show_step(
        "📥",
        "INPUT RECEIVED",
        f"Question: {question}"
    )


    # Step 2
    show_step(
        "🧠",
        "ANALYZING",
        "Understanding the requirement and identifying the "
        "important details..."
    )


    # Step 3
    show_step(
        "🧩",
        "DECOMPOSING",
        "Breaking the problem into smaller logical components..."
    )


    # Step 4
    show_step(
        "📋",
        "PLANNING",
        "Selecting an appropriate and efficient solution..."
    )


    # Step 5
    show_step(
        "⚙️",
        "GENERATING SOLUTION",
        "Preparing the implementation..."
    )


    # Gemini request
    response = chat.send_message(question)


    # Step 6
    show_step(
        "🔍",
        "VERIFYING",
        "Checking the generated solution for common errors "
        "and edge cases..."
    )


    # Step 7
    print("\n💡 FINAL ANSWER")
    print("═" * 50)
    print(response.text)
    print("═" * 50)