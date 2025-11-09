from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
from keys.creds import GEMINI_API_KEY
import time


MAX_RETRIES = 2  

client = genai.Client(
    api_key=GEMINI_API_KEY
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
# EDITING PHASE: Clean up each transcript individually
# =============================================================================

print(f"\n{'='*60}")
print("EDITING PHASE: Cleaning individual transcripts")
print(f"{'='*60}")

# Edit each chunk transcript individually
edited_chunks = []
for i, chunk in enumerate(chunks):
    verbatim_filename = f"transcript/{chunk['name']}_verbatim.txt"
    edited_filename = f"transcript/{chunk['name']}_edited.txt"
    
    try:
        with open(verbatim_filename, "r") as f:
            chunk_text = f.read()
        print(f"✓ Loaded: {verbatim_filename}")
    except FileNotFoundError:
        print(f"❌ Missing: {verbatim_filename}")
        exit(1)
    
    # Individual editing prompt
    editing_prompt = f"""Your goal is to edit this podcast transcript chunk to improve readability while maintaining accuracy.

#instructions:
- Remove filler words
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Keep the same speaker labels and format
- Correct misspellings 
- No markdown formatting
- Make other edits when necessary to improve readability and coherence

#TRANSCRIPT TO EDIT:
{chunk_text}
"""
    
    print(f"📝 Editing {chunk['name']}...")
    success, response, error = retry_api_call(
        client.models.generate_content,
        model="gemini-2.5-pro",
        contents=[editing_prompt],
        config=GenerateContentConfig(
            thinking_config={'thinking_budget': 0}
        )
    )
    
    if not success:
        print(f"❌ Error editing {chunk['name']} after retries: {error}")
        exit(1)
    
    edited_text = response.text
    
    # Save edited chunk
    with open(edited_filename, "w") as f:
        f.write(edited_text)
    print(f"✓ Saved: {edited_filename}")
    
    edited_chunks.append({
        "number": i + 1,
        "name": chunk['name'],
        "text": edited_text,
        "start": chunk['start'],
        "end": chunk['end']
    })

print(f"\n✅ All chunks edited individually")

# =============================================================================
# STITCHING PHASE: Combine edited transcripts seamlessly
# =============================================================================

print(f"\n{'='*60}")
print("STITCHING PHASE: Combining edited transcripts")
print(f"{'='*60}")

# Combine edited transcripts with markers for the stitching process
combined_edited = ""
for ct in edited_chunks:
    combined_edited += f"\n\n{'='*60}\n"
    combined_edited += f"CHUNK {ct['number']} (Minutes {ct['start']:.2f} - {ct['end']:.2f})\n"
    combined_edited += f"{'='*60}\n\n"
    combined_edited += ct['text']

print(f"📝 Stitching chunks together...")

# Stitching prompt
stitching_prompt = f"""Your goal is to stitch multiple edited podcast transcript chunks into one seamless, continuous transcript.

#CONTEXT:
The transcript was generated in multiple chunks with markers. The chunks have already been edited for readability.

#instrucitons
- Remove duplicate content from the 10-second overlaps between chunks
- Ensure smooth transitions between chunks
- Fix any speaker inconsistencies across chunks
- Don't make other signficant changes to the transcript unless necessary 

#transcript:
{combined_edited}
"""

success, response_stitched, error = retry_api_call(
    client.models.generate_content,
    model="gemini-2.5-pro",
    contents=[stitching_prompt],
    config=GenerateContentConfig(
        thinking_config={'thinking_budget': 0}
    )
)

if not success:
    print(f"❌ Error during stitching after retries: {error}")
    exit(1)

# Save the final stitched transcript
final_filename = "transcript/full_transcript_edited.txt"
with open(final_filename, "w") as f:
    f.write(response_stitched.text)

print(f"✓ Final stitched transcript saved: {final_filename}")

# Also save the combined verbatim (with chunk markers) for reference
print(f"📝 Creating combined verbatim reference...")
combined_verbatim = ""
for ct in edited_chunks:
    # Read original verbatim versions
    verbatim_filename = f"transcript/{ct['name']}_verbatim.txt"
    with open(verbatim_filename, "r") as f:
        verbatim_text = f.read()
    
    combined_verbatim += f"\n\n{'='*60}\n"
    combined_verbatim += f"CHUNK {ct['number']} (Minutes {ct['start']:.2f} - {ct['end']:.2f})\n"
    combined_verbatim += f"{'='*60}\n\n"
    combined_verbatim += verbatim_text

verbatim_filename = "transcript/full_transcript_verbatim.txt"
with open(verbatim_filename, "w") as f:
    f.write(combined_verbatim)
print(f"✓ Combined verbatim saved: {verbatim_filename}")

print(f"\n{'='*60}")
print("✅ COMPLETE!")
print(f"{'='*60}")
print(f"\n📁 Final outputs:")
print(f"   - transcript/full_transcript_verbatim.txt (combined, unedited)")
print(f"   - transcript/full_transcript_edited.txt (edited & stitched)")
print(f"\n📁 Individual files:")
print(f"   - transcript/chunk_*_verbatim.txt (original transcripts)")
print(f"   - transcript/chunk_*_edited.txt (edited transcripts)")