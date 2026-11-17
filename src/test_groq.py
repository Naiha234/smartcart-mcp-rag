
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found. Check your .env file."
    )


# ==========================================
# 2. CONNECT TO GROQ
# ==========================================

client = Groq(
    api_key=api_key
)


# ==========================================
# 3. SEND TEST QUESTION
# ==========================================

print("Connecting to Groq API...")

response = client.chat.completions.create(

    model="openai/gpt-oss-120b",

    messages=[
        {
            "role": "system",
            "content": (
                "You are SmartCart AI, an e-commerce "
                "customer support assistant. "
                "Give clear and helpful answers."
            )
        },
        {
            "role": "user",
            "content": (
                "Reply with exactly: "
                "SmartCart connection successful."
            )
        }
    ],

    temperature=0,
    max_completion_tokens=150
)


# ==========================================
# 4. DISPLAY RESPONSE DETAILS
# ==========================================

print("\nGroq API connected successfully!")

print("\nModel:", response.model)

print(
    "Finish reason:",
    response.choices[0].finish_reason
)

message = response.choices[0].message

print("\nMessage:", repr(message))

print("\nModel response:")

if message.content:
    print(message.content)
else:
    print("Model returned empty text.")

print("\nToken Usage:", response.usage)


# ==========================================
# 5. CONNECTION TEST RESULT
# ==========================================

if message.content and message.content.strip():

    print("\nSmartCart LLM test passed!")

else:

    print("\nSmartCart LLM test needs further checking.")
