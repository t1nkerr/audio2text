from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
from keys.creds import GEMINI_API_KEY, GEMINI_API_KEY_TEST
import time

GEMINI_TIMEOUT = 10 * 60 * 1000  # 10 minutes
MAX_RETRIES = 0

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

# Define chunks
chunks = [
    {"name": "chunk_1", "start": 0.00, "end": 30.00},
    {"name": "chunk_2", "start": 29.83, "end": 52.37},
]

print("="*60)
print("EDITING PHASE DEBUG SCRIPT - OUTPUT TOKEN LIMIT TESTS")
print("="*60)

# Read all chunk transcripts
print("\n📂 Loading chunk transcripts...")
chunk_transcripts = []
for i, chunk in enumerate(chunks):
    transcript_filename = f"transcript/{chunk['name']}_verbatim.txt"
    try:
        with open(transcript_filename, "r") as f:
            chunk_text = f.read()
            chunk_transcripts.append({
                "number": i + 1,
                "name": chunk['name'],
                "text": chunk_text,
                "start": chunk['start'],
                "end": chunk['end']
            })
        word_count = len(chunk_text.split())
        char_count = len(chunk_text)
        print(f"✓ Loaded: {transcript_filename}")
        print(f"  └─ {word_count:,} words, {char_count:,} characters")
    except FileNotFoundError:
        print(f"❌ Missing: {transcript_filename}")
        exit(1)

# Combine transcripts with markers
combined_transcript = ""
for ct in chunk_transcripts:
    combined_transcript += f"\n\n{'='*60}\n"
    combined_transcript += f"CHUNK {ct['number']} (Minutes {ct['start']:.2f} - {ct['end']:.2f})\n"
    combined_transcript += f"{'='*60}\n\n"
    combined_transcript += ct['text']

total_words = len(combined_transcript.split())
total_chars = len(combined_transcript)
print(f"\n📊 Combined transcript stats:")
print(f"  - Total words: {total_words:,}")
print(f"  - Total characters: {total_chars:,}")
print(f"  - Estimated input tokens: ~{total_words * 1.3:.0f}")
print(f"  - Expected output tokens: ~{total_words * 1.2:.0f}")

# =============================================================================
# DEFINE ALL PROMPTS
# =============================================================================

simple_prompt = f"""The transcript below has 2 chunks with a ~10 second overlap between chunk 1 and chunk 2.

Your task: Remove the duplicate content from the overlap and output a single seamless transcript.

Keep everything else as-is. Don't edit anything else.

{combined_transcript}
"""

medium_prompt = f"""Edit this podcast transcript:

1. Remove duplicate content from the 10-second overlap between chunks
2. Remove obvious filler words (um, uh, like when overused)
3. Keep the same speaker format

{combined_transcript}
"""

complex_prompt = f"""Your goal is to edit the podcast transcript to improve readability. The transcript was generated in multiple chunks with markers.

#YOUR TASK:
1. STITCH the chunks together into one seamless transcript
   - Remove duplicate content from the 10-second overlaps between chunks
   - Ensure smooth transitions between chunks
   - Fix any speaker inconsistencies across chunks

2. CLEAN UP the transcript:
    - Remove filler words
    - Remove false starts, unnecessary repetitions, and miscellaneous noise
    - Correct misspellings 
    - Make other edits when necessary to improve readability and coherence

3. MAINTAIN FORMAT:
   - Keep the same speaker label format 
   - No markdown formatting

#OUTPUT:
A single, clean, edited transcript from start to finish with no chunk markers or duplicate content.

#CHUNKS TO STITCH AND EDIT:
{combined_transcript}
"""

# =============================================================================
# TEST 1: gemini-2.5-flash with NO output limit (baseline - should fail)
# =============================================================================
print("\n" + "="*60)
print("TEST 1: gemini-2.5-flash - NO output token limit")
print("="*60)

print(f"\n📝 Testing complex prompt without output limit...")
success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-flash",
    contents=[complex_prompt]
)

if success:
    print("✅ SUCCESS!")
    with open("transcript/test1_no_limit.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/test1_no_limit.txt")
else:
    print(f"❌ FAILED: {error}")

# =============================================================================
# TEST 2: gemini-2.5-flash with max_output_tokens=4096
# =============================================================================
print("\n" + "="*60)
print("TEST 2: gemini-2.5-flash - max_output_tokens=4096")
print("="*60)

print(f"\n📝 Testing with 4096 token output limit...")
success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-flash",
    contents=[complex_prompt],
    config=GenerateContentConfig(max_output_tokens=4096)
)

if success:
    print("✅ SUCCESS!")
    output_words = len(response.text.split())
    print(f"  Output: ~{output_words} words (~{output_words * 1.3:.0f} tokens)")
    with open("transcript/test2_limit_4096.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/test2_limit_4096.txt")
else:
    print(f"❌ FAILED: {error}")

# =============================================================================
# TEST 3: gemini-2.5-flash with max_output_tokens=8000
# =============================================================================
print("\n" + "="*60)
print("TEST 3: gemini-2.5-flash - max_output_tokens=8000")
print("="*60)

print(f"\n📝 Testing with 8000 token output limit...")
success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-flash",
    contents=[complex_prompt],
    config=GenerateContentConfig(max_output_tokens=8000)
)

if success:
    print("✅ SUCCESS!")
    output_words = len(response.text.split())
    print(f"  Output: ~{output_words} words (~{output_words * 1.3:.0f} tokens)")
    with open("transcript/test3_limit_8000.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/test3_limit_8000.txt")
else:
    print(f"❌ FAILED: {error}")

# =============================================================================
# TEST 4: gemini-2.5-pro with max_output_tokens=8000
# =============================================================================
print("\n" + "="*60)
print("TEST 4: gemini-2.5-pro - max_output_tokens=8000")
print("="*60)

print(f"\n📝 Testing gemini-2.5-pro with 8000 token output limit...")
success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-pro",
    contents=[complex_prompt],
    config=GenerateContentConfig(max_output_tokens=8000)
)

if success:
    print("✅ SUCCESS!")
    output_words = len(response.text.split())
    print(f"  Output: ~{output_words} words (~{output_words * 1.3:.0f} tokens)")
    with open("transcript/test4_pro_limit_8000.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/test4_pro_limit_8000.txt")
else:
    print(f"❌ FAILED: {error}")

# =============================================================================
# TEST 5: gemini-2.0-flash-001 with NO limit (known working baseline)
# =============================================================================
print("\n" + "="*60)
print("TEST 5: gemini-2.0-flash-001 - NO output limit (control)")
print("="*60)

print(f"\n📝 Testing with gemini-2.0-flash-001 (known working)...")
success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.0-flash-001",
    contents=[complex_prompt]
)

if success:
    print("✅ SUCCESS!")
    output_words = len(response.text.split())
    print(f"  Output: ~{output_words} words (~{output_words * 1.3:.0f} tokens)")
    with open("transcript/test5_flash20_baseline.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/test5_flash20_baseline.txt")
else:
    print(f"❌ FAILED: {error}")

# =============================================================================
# TEST 6: gemini-2.5-flash with simple prompt + max_output_tokens=8000
# =============================================================================
print("\n" + "="*60)
print("TEST 6: gemini-2.5-flash - SIMPLE prompt + max_output=8000")
print("="*60)

print(f"\n📝 Testing simple prompt with 8000 token limit...")
success, response, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-flash",
    contents=[simple_prompt],
    config=GenerateContentConfig(max_output_tokens=8000)
)

if success:
    print("✅ SUCCESS!")
    output_words = len(response.text.split())
    print(f"  Output: ~{output_words} words (~{output_words * 1.3:.0f} tokens)")
    with open("transcript/test6_simple_limit_8000.txt", "w") as f:
        f.write(response.text)
    print("✓ Saved: transcript/test6_simple_limit_8000.txt")
else:
    print(f"❌ FAILED: {error}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("\nThis test series determines:")
print("  1. If max_output_tokens limit fixes the disconnection issue")
print("  2. What output limit is needed for gemini-2.5 models")
print("  3. If prompt complexity also matters")
print("  4. Whether 2.5-flash vs 2.5-pro behaves differently")
print("\nIf TEST 2/3 succeed but TEST 1 fails:")
print("  → Issue is output token limit on free tier")
print("\nIf all 2.5 tests fail:")
print("  → Issue is server-side instability, use gemini-2.0-flash-001")
print("\nCheck transcript/ directory for successful outputs.")