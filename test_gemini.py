import os
from openai import OpenAI
client = OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
try:
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("gemini-1.5-flash:", response.choices[0].message.content)
except Exception as e:
    print("Error with gemini-1.5-flash:", e)

try:
    response = client.chat.completions.create(
        model="gemini-1.5-flash-latest",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("gemini-1.5-flash-latest:", response.choices[0].message.content)
except Exception as e:
    print("Error with gemini-1.5-flash-latest:", e)
