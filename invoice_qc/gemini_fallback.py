import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file if present
load_dotenv()

# -----------------------------------------------------------
# LOAD GEMINI API KEY
# -----------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY is missing. Set it in your .env file.")
else:
    print(f"✅ GEMINI_API_KEY loaded: {GEMINI_API_KEY[:6]}********")

# Configure Gemini
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"⚠️  Warning: Gemini configuration failed: {e}")
    GEMINI_API_KEY = None



# -----------------------------------------------------------
# INTERNAL: Cleanly extract text from Gemini response
# -----------------------------------------------------------
def _extract_response_text(response):
    """Extracts text safely from Gemini's response object."""
    try:
        # Standard format
        if hasattr(response, "text") and response.text:
            return response.text

        # Some responses return candidate parts
        if hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                return parts[0].text

        # No usable text found
        return None
    except Exception as e:
        print("❌ RESPONSE PARSING ERROR:", e)
        return None


# -----------------------------------------------------------
# MAIN GEMINI CALL
# -----------------------------------------------------------
def _call_gemini(prompt: str) -> str:
    """
    Calls Gemini API safely.
    - Attempts gemini-pro first
    - Falls back to gemini-1.5-flash if needed
    - Returns clean text or None on failure
    """

    if not GEMINI_API_KEY:
        print("❌ ERROR: No Gemini API key found")
        return None

    print("\n🧠 ---- CALLING GEMINI ----")
    print("📤 Prompt (first 300 chars):")
    print(prompt[:300], "...")
    print("---------------------------\n")

    models_to_try = ["gemini-pro", "gemini-1.5-flash"]

    for model_name in models_to_try:
        try:
            print(f"🤖 Trying model: {model_name}")

            model = genai.GenerativeModel(model_name)

            response = model.generate_content(prompt)

            # Log raw response for debugging
            print("📥 Raw Gemini Response:", response)

            text = _extract_response_text(response)

            if text:
                print("✅ Gemini responded successfully!")
                print("📄 Response text:", text[:300], "...\n")
                return text
            else:
                print(f"⚠ No text extracted from model {model_name}")

        except Exception as e:
            print(f"❌ ERROR with model {model_name}: {e}")

    print("❌ All Gemini models failed. Returning None.")
    return None
