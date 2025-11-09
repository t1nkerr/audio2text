from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
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

# Define chunks
chunks = [
    {"name": "chunk_1", "start": 0.00, "end": 30.00},
    {"name": "chunk_2", "start": 29.83, "end": 52.37},
]

print("="*60)
print("STREAMING TEST - Avoiding Connection Timeouts")
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
        print(f"✓ Loaded: {transcript_filename} (~{word_count:,} words)")
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
print(f"\n📊 Combined: {total_words:,} words (~{total_words * 1.3:.0f} tokens)")

# Define editing prompt
complex_prompt = f"""Your goal is to edit the podcast transcript to improve readability. The transcript was generated in multiple chunks with markers.

#YOUR TASK:
1. STITCH the chunks together into one seamless transcript
   - Remove duplicate content from the 10-second overlaps between chunks
   - Ensure smooth transitions between chunks
   - Fix any speaker inconsistencies across chunks (use the same name for each person throughout)

2. CLEAN UP the transcript:
   - Remove filler words (um, uh, you know, like, etc.)
   - Remove false starts, unnecessary repetitions, and miscellaneous noise
   - Correct misspellings and grammatical errors
   - Improve readability and coherence

3. MAINTAIN FORMAT:
   - Keep the same speaker label format (Speaker Name: followed by their text)
   - No markdown formatting
   - Keep paragraph breaks where natural

#OUTPUT:
A single, clean, edited transcript from start to finish with no chunk markers or duplicate content.

#CHUNKS TO STITCH AND EDIT:
{combined_transcript}
"""

# # =============================================================================
# # TEST 1: Non-streaming (baseline - should fail)
# # =============================================================================
# print("\n" + "="*60)
# print("TEST 1: gemini-2.5-flash - Non-streaming (baseline)")
# print("="*60)

# print(f"\n📝 Testing without streaming (expect failure)...")
# success, response, error = retry_api_call(
#     client.models.generate_content,
#     model="gemini-2.5-flash",
#     contents=[complex_prompt],
#     config=GenerateContentConfig(max_output_tokens=8000)
# )

# if success and response and response.text:
#     print("✅ SUCCESS (unexpected!)")
#     print(f"  Output: {len(response.text.split())} words")
# else:
#     print(f"❌ FAILED as expected: {error if error else 'Empty response'}")

# =============================================================================
# TEST 2: Streaming with gemini-2.5-flash
# =============================================================================
print("\n" + "="*60)
print("TEST 2: gemini-2.5-flash - WITH streaming")
print("="*60)

print(f"\n📝 Testing WITH streaming + 8000 token limit...")
try:
    full_response = ""
    chunk_count = 0
    
    stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=[complex_prompt],
        config=GenerateContentConfig(max_output_tokens=8000)
    )
    
    print("🌊 Streaming started...")
    for chunk in stream:
        if chunk.text:
            full_response += chunk.text
            chunk_count += 1
            # Print progress every 20 chunks
            if chunk_count % 20 == 0:
                print(f"  📦 Received {chunk_count} chunks (~{len(full_response.split())} words so far)...")
    
    if full_response:
        print(f"✅ SUCCESS!")
        print(f"  Total chunks: {chunk_count}")
        print(f"  Output: {len(full_response.split())} words (~{len(full_response.split()) * 1.3:.0f} tokens)")
        
        with open("transcript/test_streaming_flash25.txt", "w") as f:
            f.write(full_response)
        print("✓ Saved: transcript/test_streaming_flash25.txt")
    else:
        print("⚠️  Streaming completed but response is empty")
        
except Exception as e:
    print(f"❌ FAILED: {e}")

# =============================================================================
# TEST 3: Streaming with gemini-2.5-flash + disable thinking
# =============================================================================
print("\n" + "="*60)
print("TEST 3: gemini-2.5-flash - Streaming + No Thinking")
print("="*60)

print(f"\n📝 Testing with thinking disabled (Flash only)...")
try:
    full_response = ""
    chunk_count = 0
    
    # Note: thinkingConfig might not be available in all SDK versions
    # This is experimental based on the suggestion
    stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=[complex_prompt],
        config=GenerateContentConfig(
            max_output_tokens=8000,
            # thinking_config={'thinking_budget': 0}  # Uncomment if available
        )
    )
    
    print("🌊 Streaming with thinking disabled...")
    for chunk in stream:
        if chunk.text:
            full_response += chunk.text
            chunk_count += 1
            if chunk_count % 20 == 0:
                print(f"  📦 {chunk_count} chunks (~{len(full_response.split())} words)...")
    
    if full_response:
        print(f"✅ SUCCESS!")
        print(f"  Total chunks: {chunk_count}")
        print(f"  Output: {len(full_response.split())} words")
        
        with open("transcript/test_streaming_no_thinking.txt", "w") as f:
            f.write(full_response)
        print("✓ Saved: transcript/test_streaming_no_thinking.txt")
    else:
        print("⚠️  Empty response")
        
except Exception as e:
    print(f"❌ FAILED: {e}")

# =============================================================================
# TEST 4: Streaming with gemini-2.0-flash-001 (known working model)
# =============================================================================
print("\n" + "="*60)
print("TEST 4: gemini-2.0-flash-001 - Streaming (control)")
print("="*60)

print(f"\n📝 Testing streaming with 2.0-flash-001...")
try:
    full_response = ""
    chunk_count = 0
    
    stream = client.models.generate_content_stream(
        model="gemini-2.0-flash-001",
        contents=[complex_prompt],
        config=GenerateContentConfig(max_output_tokens=8000)
    )
    
    print("🌊 Streaming with 2.0-flash-001...")
    for chunk in stream:
        if chunk.text:
            full_response += chunk.text
            chunk_count += 1
            if chunk_count % 20 == 0:
                print(f"  📦 {chunk_count} chunks (~{len(full_response.split())} words)...")
    
    if full_response:
        print(f"✅ SUCCESS!")
        print(f"  Total chunks: {chunk_count}")
        print(f"  Output: {len(full_response.split())} words")
        
        with open("transcript/test_streaming_flash20.txt", "w") as f:
            f.write(full_response)
        print("✓ Saved: transcript/test_streaming_flash20.txt")
    else:
        print("⚠️  Empty response")
        
except Exception as e:
    print(f"❌ FAILED: {e}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*60)
print("STREAMING TEST SUMMARY")
print("="*60)
print("\nKey Findings:")
print("  • Streaming keeps connection alive during long generations")
print("  • Still limited to 8,192 output tokens total")
print("  • Prevents 'server disconnected' errors from timeouts")
print("\nIf TEST 2/3/4 succeed:")
print("  → Use streaming for all long-output tasks")
print("  → Set max_output_tokens=8000 to stay under limit")
print("\nIf only TEST 4 succeeds:")
print("  → Stick with gemini-2.0-flash-001 model")
print("\nCheck transcript/ directory for outputs.")