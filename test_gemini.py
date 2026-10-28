from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API key not found in .env")
    raise SystemExit

client = genai.Client(
    api_key=api_key,
    http_options={"timeout": 30000}
)

print("Sending test...", flush=True)

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Reply with only: Hi!"
    )
    print("Gemini says:", response.text, flush=True)

except Exception as error:
    print("Request failed:", repr(error), flush=True)