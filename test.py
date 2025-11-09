# from google import genai
# from google.genai.types import HttpOptions
# import os
# from keys.creds import GEMINI_API_KEY
# import httpx


# GEMINI_TIMEOUT = 10 * 60 * 1000  # 10 minutes = 600,000 ms

# client = genai.Client(
#     api_key=GEMINI_API_KEY, 
#     http_options=HttpOptions(timeout=GEMINI_TIMEOUT)
# )

# # wav_10min = {"name": "wav_10mins", "uri": "files/vqsrli804usc"} 
# # flac_full = {"name": "flac_full", "uri": "files/7uigbl8m7elu"}
# # flac_10min = {"name": "flac_10mins", "uri": "files/nubde0edid4c"}
# # flac_15min = {"name": "flac_15mins", "uri": "files/c87wily1qb5c"}
# # flac_30min = {"name": "flac_30mins", "uri": "files/zrnbtg2qs6le"}
# # flac_45min = {"name": "flac_45mins", "uri": "files/r7zier3wosrj"}
# chunk_1 = {"name": "chunk_1", "uri": "files/anb79vwu95wg", "start": 0.00, "end": 30.00}
# chunk_2 = {"name": "chunk_2", "uri": "files/z9fc27kzeqd8", "start": 29.83, "end": 52.37}

# uploaded_file = 

# try:
#     file_obj = client.files.get(name=uploaded_file["uri"])
# except Exception as e:
#     print(f"Error getting file: {e}")
#     exit(1)

# # Generate transcription with speaker labels
# prompt = """Generate a verbatim English-language transcript of the podcast. Identify the names of the speakers based on the conversation.

# #output format:
# Speaker Name 1:\n[their text]

# Speaker Name 2:\n[their text]

# ...

# #instructions:
# - label each speaker consistently throughout the transcription.
# - only use characters from the English alphabet, unless you believe foreign characters are correct.
# - use the correct words and spell everything correctly. Use the context of the podcast to help.
# - no markdown formatting.

# #background:
# The podcast is produced by Trivium China, a consultancy on China policy. The speakers are usually Andrew Polk, Dinny Macmahon, Kendra Schaefer, and occasionally other guests.
# """


# response_verbatim = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents=[prompt, file_obj]
# )


# with open(f"transcript/{uploaded_file['name']}_verbatim.txt", "w") as f:
#     f.write(response_verbatim.text)
# print(f"verbatim transcript saved")


# # with open(f"transcript/{uploaded_file['name']}_verbatim.txt", "r") as f:
# #     transcript_verbatim = f.read()

# # response_edited = client.models.generate_content(
# #     model="gemini-2.5-flash",
# #     contents=[f"""
# #     #Your goal is to edit the podcast transcript to improve readability

# #     #instructions:
# #     - Remove filler words
# #     - Remove false starts, unnecessary repetitions, and miscellaneous noise
# #     - Keep the same speaker labels and format
# #     - Correct misspellings 
# #     - No markdown formatting
# #     - Make other edits when necessary to improve readability and coherence

# #     #transcript:
# #     {transcript_verbatim}
    
# #     """
# #     ]
# # )

# # with open(f"transcript/{uploaded_file['name']}_edited.txt", "w") as f:
# #     f.write(response_edited.text)
# # print(f"edited transcript saved")





from google import genai
from google.genai.types import HttpOptions
from keys.creds import GEMINI_API_KEY
import time

GEMINI_TIMEOUT = 10 * 60 * 1000  # 10 minutes
MAX_RETRIES = 2  

client = genai.Client(
    api_key=GEMINI_API_KEY, 
    http_options=HttpOptions(timeout=GEMINI_TIMEOUT)
)

# Helper function for retry logic
def retry_api_call(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """
    Retry an API call up to max_retries times.
    Returns: (success: bool, result: Any, error: Exception|None)
    """
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                print(f"🔄 Retrying... (attempt {attempt + 2}/{max_retries + 1})")
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"❌ All {max_retries + 1} attempts failed")
                return False, None, e
    return False, None, Exception("Unexpected retry loop exit")

# Define all chunks
chunks = [
    {"name": "chunk_1", "uri": "files/anb79vwu95wg", "start": 0.00, "end": 30.00},
    {"name": "chunk_2", "uri": "files/z9fc27kzeqd8", "start": 29.83, "end": 52.37},
    # Add more chunks here
]

# Base transcription prompt
base_prompt = """Generate a verbatim English-language transcript of the podcast. Identify the names of the speakers based on the conversation.

#output format:
Speaker Name:\n[their text]

Speaker Name:\n[their text]

...

#instructions:
- label each speaker consistently throughout the transcription.
- only use characters from the English alphabet, unless you believe foreign characters are correct.
- use the correct words and spell everything correctly. Use the context of the podcast to help.
- no markdown formatting.
- transcribe ALL audio in this segment from start to finish.

#background:
The podcast is produced by Trivium China, a consultancy on China policy. The speakers are usually Andrew Polk, Dinny Macmahon, Kendra Schaefer, and occasionally other guests.
"""

# Storage for context between chunks
previous_context = None

# Process each chunk
for i, chunk in enumerate(chunks):
    print(f"\n{'='*60}")
    print(f"Processing {chunk['name']} ({chunk['start']:.2f} - {chunk['end']:.2f} min)")
    print(f"{'='*60}")
    
    # Get file with retry
    success, file_obj, error = retry_api_call(
        client.files.get,
        name=chunk["uri"]
    )
    if not success:
        print(f"❌ Error getting file after retries: {error}")
        continue
    
    # Build prompt based on chunk position
    if i == 0:
        # First chunk - use base prompt
        transcription_prompt = base_prompt
    else:
        # Subsequent chunks - add context from previous segment
        transcription_prompt = f"""{base_prompt}

#IMPORTANT CONTEXT:
- This is chunk {i+1} of the podcast, covering minutes {chunk['start']:.2f} - {chunk['end']:.2f}.
- The first 10 seconds overlap with the previous chunk to ensure continuity.
- Transcribe the ENTIRE audio segment, including the overlapping portion.
- New speakers may appear in this segment - identify them if they do.

#CONTEXT FROM PREVIOUS SEGMENT:
{previous_context}

#YOUR TASK:
Use the above context to maintain speaker name consistency and conversation flow, then transcribe this entire audio segment from beginning to end.
"""
    
    # Step 1: Generate transcript for this chunk
    print(f"📝 Generating transcript for {chunk['name']}...")
    success, response, error = retry_api_call(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=[transcription_prompt, file_obj]
    )
    if not success:
        print(f"❌ Error generating transcript after retries: {error}")
        continue
    
    chunk_transcript = response.text
    
    # Save the chunk transcript
    transcript_filename = f"transcript/{chunk['name']}_verbatim.txt"
    with open(transcript_filename, "w") as f:
        f.write(chunk_transcript)
    print(f"✓ Saved: {transcript_filename}")
    
    # Step 2: Generate context summary for next chunk (if not last chunk)
    if i < len(chunks) - 1:
        print(f"🔄 Generating context summary for next chunk...")
        
        summary_prompt = """You are preparing context for transcribing the next audio segment of this podcast.

#CONTEXT:
- The podcast continues in the next audio chunk
- We need to know WHERE THIS SEGMENT ENDED so the next transcription can continue smoothly
- Focus ONLY on the last several exchanges between the speakers

#YOUR TASK:
1. List all speaker names who appeared in this segment
2. Summarize what EACH speaker was saying in the FINAL exchanges - what were they discussing as this segment ended?

#FORMAT:
Speakers: [list all speaker names]

Where the conversation left off:
Speaker Name A: [what they were saying/discussing at the END]
Speaker Name B: [what they were saying/discussing at the END]
Speaker Name C: [what they were saying/discussing at the END]

#IMPORTANT:
- Focus on the ENDING of the conversation below, not the beginning or middle
- Keep summaries brief (1-2 sentences per speaker)
- This helps the next chunk know where to continue from

#TRANSCRIPT:
""" + chunk_transcript
        
        success, summary_response, error = retry_api_call(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[summary_prompt]
        )
        if success:
            previous_context = summary_response.text.strip()
            print(f"✓ Context summary generated")
            print(f"Preview: {previous_context}")
        else:
            print(f"⚠️  Warning: Could not generate context summary after retries: {error}")
            print(f"⚠️  Continuing without context for next chunk")
            previous_context = "No context available from previous segment."
    
    print(f"✓ Chunk {i+1} complete")

print(f"\n{'='*60}")
print("✅ All chunks processed!")
print(f"{'='*60}")
print("\n📁 Discrete transcripts saved in transcript/ directory")
print("💡 Next step: Compile and edit transcripts (separate script)")


# =============================================================================
# EDITING PHASE: Stitch chunks together and clean up transcript
# =============================================================================

print(f"\n{'='*60}")
print("EDITING PHASE: Combining and cleaning transcripts")
print(f"{'='*60}")

# Read all chunk transcripts
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
        print(f"✓ Loaded: {transcript_filename}")
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

print(f"\n📝 Generating edited transcript...")

# Editing prompt
editing_prompt = f"""Your goal is to edit the podcast transcript to improve readability. The transcript was generated in multiple chunks with markers.

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

try:
    success, response_edited, error = retry_api_call(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=[editing_prompt],
        config=GenerateContentConfig(
            thinking_config={'thinking_budget': 0}  # Disable thinking for Flash
        )
    )
    
    if not success:
        print(f"❌ Error during editing after retries: {error}")
        exit(1)
    
    # Save the final edited transcript
    final_filename = "transcript/full_transcript_edited.txt"
    with open(final_filename, "w") as f:
        f.write(response_edited.text)
    
    print(f"✓ Edited transcript saved: {final_filename}")

    # Also save the combined verbatim (with chunk markers) for reference
    verbatim_filename = "transcript/full_transcript_verbatim.txt"
    with open(verbatim_filename, "w") as f:
        f.write(combined_transcript)
    print(f"✓ Combined verbatim saved: {verbatim_filename}")
    
except Exception as e:
    print(f"❌ Error during editing: {e}")
    exit(1)

print(f"\n{'='*60}")
print("✅ COMPLETE!")
print(f"{'='*60}")
print(f"\n📁 Final outputs:")
print(f"   - transcript/full_transcript_verbatim.txt (combined, unedited)")
print(f"   - transcript/full_transcript_edited.txt (stitched and cleaned)")
print(f"\n💡 Individual chunk transcripts preserved in transcript/chunk_*_verbatim.txt")