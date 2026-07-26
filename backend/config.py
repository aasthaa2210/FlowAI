"""
API keys are read from environment variables, not hardcoded here.

Locally: create a file called .env in this same backend/ folder with:
    ORS_API_KEY=your-key-here
    GEMINI_API_KEY=your-key-here
    GROQ_API_KEY=your-key-here

On a hosting platform (Render, Railway, etc.): set these same three
names as Environment Variables in that platform's dashboard — do not
put real key values in this file or commit them anywhere.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env locally; harmless no-op if the file doesn't exist

ORS_API_KEY = os.environ.get("ORS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

missing = [name for name, val in [
    ("ORS_API_KEY", ORS_API_KEY),
    ("GEMINI_API_KEY", GEMINI_API_KEY),
    ("GROQ_API_KEY", GROQ_API_KEY),
] if not val]

if missing:
    print(f"WARNING: missing environment variables: {', '.join(missing)}. "
          f"Set them in a .env file (local) or your hosting platform's env vars (deployed).")
