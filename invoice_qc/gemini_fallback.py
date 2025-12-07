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
# Updated Gemini Models (100% correct for 2024–2025)
# ----------------------------------------------------
PREFERRED_MODELS = [
    "gemini-1.5-flash-latest",   # Fastest, cheapest
    "gemini-1.5-pro-latest"      # Best reasoning, most accurate
]


# ----------------------------------------------------
# Clean extractor for response text
# ----------------------------------------------------
def _extract_text(response):
    """Safely extract text from response"""
    if hasattr(response, "text") and response.text:
        return response.text

    # candidate-based fallback
    try:
        if response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                return parts[0].text
    except Exception:
        pass

    return None


# ----------------------------------------------------
# MAIN CALL FUNCTION
# ----------------------------------------------------
def _call_gemini(prompt: str):
    """
    Tries each modern Gemini model until one succeeds.
    Returns string or None.
    """

    if not API_KEY:
        print("❌ Gemini API key missing, cannot call model.")
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
                print("✅ Response received.")
                print("📄 AI Output:", text[:200], "...\n")
                return text
            else:
                print(f"⚠ No usable text extracted from {model_name}")

        except Exception as e:
            print(f"❌ ERROR with {model_name}: {e}")

    print("❌ All Gemini model attempts failed.")
    return None
