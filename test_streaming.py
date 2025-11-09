from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
from keys.creds import GEMINI_API_KEY
import time

GEMINI_TIMEOUT = 10 * 60 * 1000  # 10 minutes

client = genai.Client(
    api_key=GEMINI_API_KEY, 
    http_options=HttpOptions(timeout=GEMINI_TIMEOUT)
)

# Define chunks
chunks = [
    {"name": "chunk_1", "start": 0.00, "end": 30.00},
    {"name": "chunk_2", "start": 29.83, "end": 52.37},
]

print("="*60)
print("STREAMING TEST - Does it bypass output limits?")
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
print(f"\n📊 Combined: {total_words:,} words (~{total_words * 1.3:.0f} input tokens)")
print(f"   Expected output: ~{total_words * 0.95:.0f} words (slightly less after cleanup)")

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
# # TEST 1: gemini-2.5-flash with streaming - NO OUTPUT LIMIT
# # =============================================================================
# print("\n" + "="*60)
# print("TEST 1: gemini-2.5-flash - Streaming, NO limit")
# print("="*60)

# print(f"\n📝 Testing streaming with NO max_output_tokens...")
# try:
#     full_response = ""
#     chunk_count = 0
    
#     stream = client.models.generate_content_stream(
#         model="gemini-2.5-flash",
#         contents=[complex_prompt]
#         # NO config - let it generate as much as possible
#     )
    
#     print("🌊 Streaming started...")
#     for chunk in stream:
#         if chunk.text:
#             full_response += chunk.text
#             chunk_count += 1
#             if chunk_count % 20 == 0:
#                 words_so_far = len(full_response.split())
#                 print(f"  📦 {chunk_count} chunks (~{words_so_far:,} words, ~{words_so_far * 1.3:.0f} tokens)...")
    
#     if full_response:
#         output_words = len(full_response.split())
#         output_tokens = output_words * 1.3
#         print(f"✅ SUCCESS!")
#         print(f"  Total chunks: {chunk_count}")
#         print(f"  Output: {output_words:,} words (~{output_tokens:.0f} tokens)")
        
#         # Check completeness
#         last_line = full_response.strip().split('\n')[-1]
#         if "bye" in full_response.lower()[-200:]:
#             print(f"  🎯 COMPLETE - Found ending!")
#         elif output_words > 9000:
#             print(f"  🎯 COMPLETE - Got expected length!")
#         else:
#             print(f"  ⚠️  TRUNCATED - Only got {output_words:,} of expected ~9,500 words")
#             print(f"  Last line: {last_line[:80]}...")
        
#         with open("transcript/test1_flash25_no_limit.txt", "w") as f:
#             f.write(full_response)
#         print("✓ Saved: transcript/test1_flash25_no_limit.txt")
#     else:
#         print("⚠️  Empty response")
        
# except Exception as e:
#     print(f"❌ FAILED: {e}")

# # =============================================================================
# # TEST 2: gemini-2.5-flash with thinking DISABLED - NO OUTPUT LIMIT
# # =============================================================================
# print("\n" + "="*60)
# print("TEST 2: gemini-2.5-flash - Thinking OFF, NO limit")
# print("="*60)

# print(f"\n📝 Testing with thinking disabled...")
# try:
#     full_response = ""
#     chunk_count = 0
    
#     stream = client.models.generate_content_stream(
#         model="gemini-2.5-flash",
#         contents=[complex_prompt],
#         config=GenerateContentConfig(
#             thinking_config={'thinking_budget': 0}  # Disable thinking for Flash
#         )
#     )
    
#     print("🌊 Streaming with thinking disabled...")
#     for chunk in stream:
#         if chunk.text:
#             full_response += chunk.text
#             chunk_count += 1
#             if chunk_count % 20 == 0:
#                 words_so_far = len(full_response.split())
#                 print(f"  📦 {chunk_count} chunks (~{words_so_far:,} words, ~{words_so_far * 1.3:.0f} tokens)...")
    
#     if full_response:
#         output_words = len(full_response.split())
#         output_tokens = output_words * 1.3
#         print(f"✅ SUCCESS!")
#         print(f"  Total chunks: {chunk_count}")
#         print(f"  Output: {output_words:,} words (~{output_tokens:.0f} tokens)")
        
#         # Check completeness
#         if "bye" in full_response.lower()[-200:]:
#             print(f"  🎯 COMPLETE - Found ending!")
#         elif output_words > 9000:
#             print(f"  🎯 COMPLETE - Got expected length!")
#         else:
#             print(f"  ⚠️  TRUNCATED - Only got {output_words:,} of expected ~9,500 words")
        
#         with open("transcript/test2_flash25_no_thinking.txt", "w") as f:
#             f.write(full_response)
#         print("✓ Saved: transcript/test2_flash25_no_thinking.txt")
#     else:
#         print("⚠️  Empty response")
        
# except Exception as e:
#     print(f"❌ FAILED: {e}")
#     print(f"   (Note: thinking_config may not be supported in this SDK version)")

# # =============================================================================
# # TEST 3: gemini-2.0-flash-001 - NO OUTPUT LIMIT (control)
# # =============================================================================
# print("\n" + "="*60)
# print("TEST 3: gemini-2.0-flash-001 - Streaming, NO limit")
# print("="*60)

# print(f"\n📝 Testing 2.0-flash-001 with no limit (control)...")
# try:
#     full_response = ""
#     chunk_count = 0
    
#     stream = client.models.generate_content_stream(
#         model="gemini-2.0-flash-001",
#         contents=[complex_prompt]
#         # NO config - let it generate as much as possible
#     )
    
#     print("🌊 Streaming with 2.0-flash-001...")
#     for chunk in stream:
#         if chunk.text:
#             full_response += chunk.text
#             chunk_count += 1
#             if chunk_count % 20 == 0:
#                 words_so_far = len(full_response.split())
#                 print(f"  📦 {chunk_count} chunks (~{words_so_far:,} words, ~{words_so_far * 1.3:.0f} tokens)...")
    
#     if full_response:
#         output_words = len(full_response.split())
#         output_tokens = output_words * 1.3
#         print(f"✅ SUCCESS!")
#         print(f"  Total chunks: {chunk_count}")
#         print(f"  Output: {output_words:,} words (~{output_tokens:.0f} tokens)")
        
#         # Check completeness
#         if "bye" in full_response.lower()[-200:]:
#             print(f"  🎯 COMPLETE - Found ending!")
#         elif output_words > 9000:
#             print(f"  🎯 COMPLETE - Got expected length!")
#         else:
#             print(f"  ⚠️  TRUNCATED - Only got {output_words:,} of expected ~9,500 words")
        
#         with open("transcript/test3_flash20_no_limit.txt", "w") as f:
#             f.write(full_response)
#         print("✓ Saved: transcript/test3_flash20_no_limit.txt")
#     else:
#         print("⚠️  Empty response")
        
# except Exception as e:
#     print(f"❌ FAILED: {e}")

# # =============================================================================
# # SUMMARY
# # =============================================================================
# print("\n" + "="*60)
# print("FINAL ANALYSIS")
# print("="*60)
# print("\nThis test determines:")
# print("  1. Can streaming deliver outputs > 8K tokens?")
# print("  2. Is there a free tier hard limit?")
# print("  3. Does disabling thinking help with long outputs?")
# print("\nIf all outputs are ~9,500+ words:")
# print("  → NO hard limit, streaming works!")
# print("\nIf all outputs stop at ~6,000-8,000 words:")
# print("  → Confirmed: 8K free tier limit exists")
# print("\nCheck the saved transcripts to see where they end.")


# =============================================================================
# TEST 4: gemini-2.5-flash - NO streaming, thinking OFF
# =============================================================================
print("\n" + "="*60)
print("TEST 4: gemini-2.5-flash - NO streaming, thinking OFF")
print("="*60)

print(f"\n📝 Testing thinking disabled WITHOUT streaming...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[complex_prompt],
        config=GenerateContentConfig(
            thinking_config={'thinking_budget': 0}  # Disable thinking
        )
    )
    
    if response and response.text:
        output_words = len(response.text.split())
        output_tokens = output_words * 1.3
        print(f"✅ SUCCESS!")
        print(f"  Output: {output_words:,} words (~{output_tokens:.0f} tokens)")
        
        # Check completeness
        if "bye" in response.text.lower()[-200:]:
            print(f"  🎯 COMPLETE - Found ending!")
        elif output_words > 9000:
            print(f"  🎯 COMPLETE - Got expected length!")
        else:
            print(f"  ⚠️  TRUNCATED - Only got {output_words:,} of expected ~9,500 words")
        
        with open("transcript/test4_no_stream_no_thinking.txt", "w") as f:
            f.write(response.text)
        print("✓ Saved: transcript/test4_no_stream_no_thinking.txt")
    else:
        print("⚠️  Empty response")
        
except Exception as e:
    print(f"❌ FAILED: {e}")