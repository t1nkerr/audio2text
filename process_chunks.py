from google import genai
from google.genai.types import GenerateContentConfig
from keys.creds import GEMINI_API_KEY
import time

# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_RETRIES = 2
MODEL = "gemini-2.5-flash"
OVERLAP_SECONDS = 10

# Pre-uploaded chunks - no need to upload again!
chunks = [
    {"name": "chunk_1", "uri": "files/wleu4gmo9xxq", "start": 0.00, "end": 10.00},
    {"name": "chunk_2", "uri": "files/bjqowvih628p", "start": 9.83, "end": 20.00},
    {"name": "chunk_3", "uri": "files/imgz3esivuwx", "start": 19.83, "end": 30.00},
    {"name": "chunk_4", "uri": "files/sbympdxdgo1x", "start": 29.83, "end": 40.00},
    {"name": "chunk_5", "uri": "files/8url2tz1gxly", "start": 39.83, "end": 50.00},
    {"name": "chunk_6", "uri": "files/v6hjo1i4p56m", "start": 49.83, "end": 52.37},
]

client = genai.Client(api_key=GEMINI_API_KEY)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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


def transcribe_and_edit_chunk(chunk, i, previous_context):
    """Transcribe and edit a chunk in one step - generates clean transcript directly."""
    print(f"\n{'='*60}")
    print(f"Processing {chunk['name']} ({chunk['start']:.2f} - {chunk['end']:.2f} min)")
    print(f"{'='*60}")
    
    # Get file
    success, file_obj, error = retry_api_call(client.files.get, name=chunk["uri"])
    if not success:
        print(f"❌ Error getting file: {error}")
        return None
    
    # Combined prompt - transcribe AND edit in one go
    base_prompt = """Generate a English-language transcript of this audio segment. Make the transcript readable and coherent. 

#background:
The podcast is produced by Trivium China, a consultancy on China policy. The speakers are usually Andrew Polk, Dinny Macmahon, Kendra Schaefer, and occasionally other guests.

#instructions:
- Remove filler words (um, uh, like, you know, etc.)
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Correct misspellings
- Make other edits when necessary to improve readability and coherence
- No markdown formatting. Identify speaker names based on the conversation and label them consistently

#output format:
Speaker Name:\n[their text]

Speaker Name:\n[their text]

...

"""
    
    if i > 0 and previous_context:
        prompt = f"""{base_prompt}

#IMPORTANT CONTEXT:
- This is chunk {i+1} of the podcast, covering minutes {chunk['start']:.2f} - {chunk['end']:.2f}
- The first {OVERLAP_SECONDS} seconds overlap with the previous chunk to ensure continuity

#CONTEXT FROM PREVIOUS SEGMENT:
{previous_context}
"""
    else:
        prompt = base_prompt
    
    # Generate clean transcript
    print(f"📝 Generating clean transcript...")
    success, response, error = retry_api_call(
        client.models.generate_content,
        model=MODEL,
        contents=[prompt, file_obj],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    if not success:
        print(f"❌ Error generating transcript: {error}")
        return None
    
    transcript = response.text
    
    # Save transcript
    filename = f"transcript/{chunk['name']}_clean.txt"
    with open(filename, "w") as f:
        f.write(transcript)
    print(f"✓ Saved: {filename}")
    
    return transcript


def generate_context_summary(transcript):
    """Generate context summary for next chunk."""
    print(f"🔄 Generating context summary for next chunk...")
    
    summary_prompt = f"""Prepare context for transcribing the next audio segment of this podcast.

#YOUR TASK:
1. List all speaker names who appeared in this segment
2. Summarize what EACH speaker was saying in the FINAL exchanges

#FORMAT:
Speakers: [list all speaker names]

Where the conversation left off:
Speaker Name A: [what they were saying/discussing at the END]
Speaker Name B: [what they were saying/discussing at the END]

#IMPORTANT:
- Focus on the ENDING of the conversation, not the beginning or middle
- Keep summaries brief (1-2 sentences per speaker)

#TRANSCRIPT:
{transcript}
"""
    
    success, response, error = retry_api_call(
        client.models.generate_content,
        model=MODEL,
        contents=[summary_prompt],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    if success:
        context = response.text.strip()
        print(f"✓ Context summary generated")
        return context
    else:
        print(f"⚠️  Warning: Could not generate context summary: {error}")
        return "No context available from previous segment."


def stitch_transcripts(chunks):
    """Stitch all clean transcripts into final version."""
    print(f"\n{'='*60}")
    print("STITCHING: Combining transcripts")
    print(f"{'='*60}")
    
    # Load all transcripts
    transcripts = []
    for chunk in chunks:
        filename = f"transcript/{chunk['name']}_clean.txt"
        try:
            with open(filename, "r") as f:
                text = f.read()
                transcripts.append({
                    "name": chunk['name'],
                    "text": text,
                    "start": chunk['start'],
                    "end": chunk['end']
                })
            print(f"✓ Loaded: {filename}")
        except FileNotFoundError:
            print(f"❌ Missing: {filename}")
            return False
    
    # Combine with markers
    combined = ""
    for i, t in enumerate(transcripts):
        combined += f"\n\n{'='*60}\n"
        combined += f"CHUNK {i+1} (Minutes {t['start']:.2f} - {t['end']:.2f})\n"
        combined += f"{'='*60}\n\n"
        combined += t['text']
    
    stitching_prompt = f"""Stitch multiple podcast transcript chunks into one seamless, continuous transcript.

#context:
The transcript was generated in overlapping chunks. Each chunk has already been cleaned and edited.

#instructions:
- Remove duplicate content from the {OVERLAP_SECONDS}-second overlaps between chunks
- Keep only ONE version of overlapping content (choose the better one)
- Ensure smooth transitions between chunks
- Fix any speaker name inconsistencies across chunks
- Output one continuous transcript with no chunk markers
- No other significant changes

#transcript:
{combined}
"""
    
    print(f"📝 Stitching chunks together...")
    success, response, error = retry_api_call(
        client.models.generate_content,
        model=MODEL,
        contents=[stitching_prompt],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    if not success:
        print(f"❌ Error during stitching: {error}")
        return False
    
    # Save final transcript
    final_file = "transcript/final_transcript.txt"
    with open(final_file, "w") as f:
        f.write(response.text)
    print(f"✓ Final transcript saved: {final_file}")
    
    # Save combined reference (with markers)
    reference_file = "transcript/combined_reference.txt"
    with open(reference_file, "w") as f:
        f.write(combined)
    print(f"✓ Combined reference saved: {reference_file}")
    
    return True


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("SIMPLIFIED AUDIO TO TEXT PIPELINE")
    print(f"{'='*60}")
    print(f"Processing {len(chunks)} pre-uploaded chunks")
    print(f"Model: {MODEL}")
    
    # Step 1: Process each chunk (transcribe + edit in one step)
    print(f"\n{'='*60}")
    print("STEP 1: Transcribing and editing chunks")
    print(f"{'='*60}")
    
    previous_context = None
    for i, chunk in enumerate(chunks):
        transcript = transcribe_and_edit_chunk(chunk, i, previous_context)
        if transcript is None:
            print(f"❌ Failed to process {chunk['name']}")
            exit(1)
        
        # Generate context for next chunk
        if i < len(chunks) - 1:
            previous_context = generate_context_summary(transcript)
    
    print(f"\n✅ All chunks processed!")
    
    # Step 2: Stitch transcripts
    print(f"\n{'='*60}")
    print("STEP 2: Stitching transcripts")
    print(f"{'='*60}")
    
    if stitch_transcripts(chunks):
        print(f"\n{'='*60}")
        print("✅ PIPELINE COMPLETE!")
        print(f"{'='*60}")
        print(f"\n📁 Outputs:")
        print(f"   - transcript/final_transcript.txt (final stitched version)")
        print(f"   - transcript/combined_reference.txt (with chunk markers)")
        print(f"   - transcript/chunk_*_clean.txt (individual clean transcripts)")
    else:
        print(f"\n❌ Pipeline failed during stitching")

