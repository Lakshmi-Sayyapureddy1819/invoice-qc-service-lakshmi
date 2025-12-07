# invoice_qc/gemini_fallback.py
import os
from google import generativeai as genai

# ----------------------------------------------------
# Load API Key
# ----------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    print(f"✅ GEMINI_API_KEY loaded: {API_KEY[:6]}********")
    genai.configure(api_key=API_KEY)
else:
    print("❌ ERROR: GEMINI_API_KEY not found in environment!")


# ----------------------------------------------------
# Updated Gemini Models (2024–2025)
# ----------------------------------------------------
PREFERRED_MODELS = [
    "gemini-1.5-flash-latest",   # fast, cheap
    "gemini-1.5-pro-latest",     # smarter fallback
]


def _extract_text(response):
    """Safely extract text from Gemini response."""
    if hasattr(response, "text") and response.text:
        return response.text

    try:
        if response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                return parts[0].text
    except Exception:
        pass

    return None


def _call_gemini(prompt: str) -> str | None:
    """
    Try multiple Gemini models. Return response text or None.
    """
    if not API_KEY:
        print("❌ Gemini key missing, skipping call.")
        return None

    print("\n🧠 ---- CALLING GEMINI ----")
    print("📤 Prompt (first 200 chars):")
    print(prompt[:200], "...")
    print("---------------------------")

    for model_name in PREFERRED_MODELS:
        try:
            print(f"🤖 Trying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = _extract_text(response)

            if text:
                print("✅ Gemini responded.")
                print("📄 First 200 chars:", text[:200], "...\n")
                return text

            print(f"⚠ No usable text from {model_name}")

        except Exception as e:
            print(f"❌ ERROR with {model_name}: {e}")

    print("❌ All Gemini calls failed.")
    return None
