from google import genai
from google.genai.types import HttpOptions
from keys.creds import GEMINI_API_KEY
import time

GEMINI_TIMEOUT = 10 * 60 * 1000  # 10 minutes
MAX_RETRIES = 1

client = genai.Client(
    api_key=GEMINI_API_KEY, 
    http_options=HttpOptions(timeout=GEMINI_TIMEOUT)
)

# Helper function for retry logic
def retry_api_call(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """Retry an API call up to max_retries times."""
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                print(f"🔄 Retrying... (attempt {attempt + 2}/{max_retries + 1})")
                time.sleep(2)
            else:
                print(f"❌ All {max_retries + 1} attempts failed")
                return False, None, e
    return False, None, Exception("Unexpected retry loop exit")

print("="*60)
print("SINGLE CHUNK EDITING TEST")
print("="*60)

# =============================================================================
# TEST: Edit single chunk with gemini-2.5-flash
# =============================================================================
print("\n📂 Loading chunk_1_verbatim.txt...")
with open("transcript/chunk_1_verbatim.txt", "r") as f:
    chunk_1_text = f.read()

word_count = len(chunk_1_text.split())
char_count = len(chunk_1_text)
print(f"✓ Loaded: {word_count:,} words, {char_count:,} characters")
print(f"  Estimated tokens: ~{word_count * 1.3:.0f}")

# Simple cleanup prompt - no stitching needed
cleanup_prompt = f"""Your goal is to edit this podcast transcript to improve readability.

#YOUR TASK:
- Remove filler words (um, uh, you know, like, etc.)
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Correct misspellings and grammatical errors
- Improve readability and coherence

#FORMAT:
- Keep the same speaker label format (Speaker Name: followed by their text)
- No markdown formatting
- Keep paragraph breaks where natural

#TRANSCRIPT:
{chunk_1_text}
"""

print("\n" + "="*60)
print("TEST 1: Edit chunk_1 with gemini-2.5-flash")
print("="*60)

success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-flash",
    contents=[cleanup_prompt]
)

if success:
    print("✅ SUCCESS with gemini-2.5-flash!")
    with open("transcript/chunk_1_edited_flash25.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/chunk_1_edited_flash25.txt")
else:
    print(f"❌ FAILED with gemini-2.5-flash: {error}")

# =============================================================================
# TEST 2: Edit chunk_1 with gemini-2.0-flash-001
# =============================================================================
print("\n" + "="*60)
print("TEST 2: Edit chunk_1 with gemini-2.0-flash-001")
print("="*60)

success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.0-flash-001",
    contents=[cleanup_prompt]
)

if success:
    print("✅ SUCCESS with gemini-2.0-flash-001!")
    with open("transcript/chunk_1_edited_flash20.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/chunk_1_edited_flash20.txt")
else:
    print(f"❌ FAILED with gemini-2.0-flash-001: {error}")

# =============================================================================
# TEST 3: Edit chunk_1 with gemini-2.5-pro
# =============================================================================
print("\n" + "="*60)
print("TEST 3: Edit chunk_1 with gemini-2.5-pro")
print("="*60)

success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-pro",
    contents=[cleanup_prompt]
)

if success:
    print("✅ SUCCESS with gemini-2.5-pro!")
    with open("transcript/chunk_1_edited_pro25.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/chunk_1_edited_pro25.txt")
else:
    print(f"❌ FAILED with gemini-2.5-pro: {error}")

# =============================================================================
# TEST 4: Edit chunk_2 with gemini-2.5-flash
# =============================================================================
print("\n📂 Loading chunk_2_verbatim.txt...")
with open("transcript/chunk_2_verbatim.txt", "r") as f:
    chunk_2_text = f.read()

word_count = len(chunk_2_text.split())
char_count = len(chunk_2_text)
print(f"✓ Loaded: {word_count:,} words, {char_count:,} characters")
print(f"  Estimated tokens: ~{word_count * 1.3:.0f}")

cleanup_prompt_2 = f"""Your goal is to edit this podcast transcript to improve readability.

#YOUR TASK:
- Remove filler words (um, uh, you know, like, etc.)
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Correct misspellings and grammatical errors
- Improve readability and coherence

#FORMAT:
- Keep the same speaker label format (Speaker Name: followed by their text)
- No markdown formatting
- Keep paragraph breaks where natural

#TRANSCRIPT:
{chunk_2_text}
"""

print("\n" + "="*60)
print("TEST 4: Edit chunk_2 with gemini-2.5-flash")
print("="*60)

success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-flash",
    contents=[cleanup_prompt_2]
)

if success:
    print("✅ SUCCESS with gemini-2.5-flash!")
    with open("transcript/chunk_2_edited_flash25.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/chunk_2_edited_flash25.txt")
else:
    print(f"❌ FAILED with gemini-2.5-flash: {error}")

# =============================================================================
# TEST 5: Edit chunk_2 with gemini-2.0-flash-001
# =============================================================================
print("\n" + "="*60)
print("TEST 5: Edit chunk_2 with gemini-2.0-flash-001")
print("="*60)

success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.0-flash-001",
    contents=[cleanup_prompt_2]
)

if success:
    print("✅ SUCCESS with gemini-2.0-flash-001!")
    with open("transcript/chunk_2_edited_flash20.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/chunk_2_edited_flash20.txt")
else:
    print(f"❌ FAILED with gemini-2.0-flash-001: {error}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("\nThis test checks if:")
print("  1. Single chunk editing works (vs combined)")
print("  2. Which models are stable for discrete chunk editing")
print("  3. If the stitching task was causing the failures")
print("\nIf single chunks work with 2.5-flash, the issue is:")
print("  - Combined transcript length OR")
print("  - The complexity of finding/removing duplicates")
print("\nCheck transcript/ directory for edited chunks.")

