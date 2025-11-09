from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
from keys.creds import GEMINI_API_KEY
from pydub import AudioSegment
import time

CHUNK_DURATION_MINUTES = 10  # Duration of each chunk in minutes
OVERLAP_SECONDS = 10         # Overlap between chunks in seconds
MAX_RETRIES = 2
MODEL_TRANSCRIBE = "gemini-2.5-flash"
MODEL_EDIT = "gemini-2.5-flash"
MODEL_STITCH = "gemini-2.5-flash"
AUDIO_FILE = "audio/sample.flac"


client = genai.Client(api_key=GEMINI_API_KEY)


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


def chunk_and_upload_audio(audio_file, chunk_duration_min, overlap_sec):
    """Split audio file into chunks and upload to Gemini."""
    print(f"\n{'='*60}")
    print("STEP 1: Loading and chunking audio")
    print(f"{'='*60}")
    
    # Load audio
    print(f"Loading {audio_file}...")
    audio = AudioSegment.from_file(audio_file)
    duration_ms = len(audio)
    duration_min = duration_ms / (60 * 1000)
    print(f"✓ Audio duration: {duration_min:.2f} minutes")
    
    # Calculate chunks
    chunk_duration_ms = chunk_duration_min * 60 * 1000
    overlap_ms = overlap_sec * 1000
    num_chunks = (duration_ms + chunk_duration_ms - 1) // chunk_duration_ms
    print(f"✓ Splitting into {num_chunks} chunks ({chunk_duration_min}min each, {overlap_sec}s overlap)")
    
    # Extract and upload chunks
    chunks = []
    for i in range(num_chunks):
        start_ms = 0 if i == 0 else (i * chunk_duration_ms) - overlap_ms
        end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
        
        chunk = audio[start_ms:end_ms]
        start_min = start_ms / (60 * 1000)
        end_min = end_ms / (60 * 1000)
        
        # Save temporary chunk file
        temp_filename = f"audio/temp_chunk{i+1}.flac"
        chunk.export(temp_filename, format="flac")
        print(f"\n📤 Uploading chunk {i+1} ({start_min:.2f}-{end_min:.2f} min)...")
        
        # Upload to Gemini
        uploaded_file = client.files.upload(file=temp_filename)
        
        chunks.append({
            "name": f"chunk_{i+1}",
            "uri": uploaded_file.uri,
            "start": start_min,
            "end": end_min
        })
        print(f"✓ Uploaded: {uploaded_file.uri}")
    
    return chunks


def transcribe_chunk(chunk, i, previous_context):
    """Transcribe a single audio chunk."""
    print(f"\n{'='*60}")
    print(f"Processing {chunk['name']} ({chunk['start']:.2f} - {chunk['end']:.2f} min)")
    print(f"{'='*60}")
    
    # Get file
    success, file_obj, error = retry_api_call(client.files.get, name=chunk["uri"])
    if not success:
        print(f"❌ Error getting file: {error}")
        return None, None
    
    # Build prompt
    base_prompt = """
        Generate a verbatim English-language transcript of the podcast. Identify the names of the speakers based on the conversation.

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
    
    if i > 0 and previous_context:
        prompt = f"""
            {base_prompt}

            #IMPORTANT CONTEXT:
            - This is chunk {i+1} of the podcast, covering minutes {chunk['start']:.2f} - {chunk['end']:.2f}.
            - The first {OVERLAP_SECONDS} seconds overlap with the previous chunk to ensure continuity.
            - Transcribe the ENTIRE audio segment, including the overlapping portion.

            #CONTEXT FROM PREVIOUS SEGMENT:
            {previous_context}

            #YOUR TASK:
            Use the above context to maintain speaker name consistency and conversation flow, then transcribe this entire audio segment from beginning to end.
        """
    else:
        prompt = base_prompt
    
    # Generate transcript
    print(f"📝 Generating transcript...")
    success, response, error = retry_api_call(
        client.models.generate_content,
        model=MODEL_TRANSCRIBE,
        contents=[prompt, file_obj],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    if not success:
        print(f"❌ Error generating transcript: {error}")
        return None, None
    
    transcript = response.text
    
    # Save transcript
    filename = f"transcript/{chunk['name']}_verbatim.txt"
    with open(filename, "w") as f:
        f.write(transcript)
    print(f"✓ Saved: {filename}")
    
    return transcript, filename


def generate_context_summary(transcript, chunk_number, total_chunks):
    """Generate context summary for next chunk."""
    if chunk_number >= total_chunks:
        return None
    
    print(f"🔄 Generating context summary for next chunk...")
    
    summary_prompt = f"""
        You are preparing context for transcribing the next audio segment of this podcast.

        #YOUR TASK:
        1. List all speaker names who appeared in this segment
        2. Summarize what EACH speaker was saying in the FINAL exchanges - what were they discussing as this segment ended?

        #FORMAT:
        Speakers: [list all speaker names]

        Where the conversation left off:
        Speaker Name A: [what they were saying/discussing at the END]
        Speaker Name B: [what they were saying/discussing at the END]

        #IMPORTANT:
        - Focus on the ENDING of the conversation below, not the beginning or middle
        - Keep summaries brief (1-2 sentences per speaker)

        #TRANSCRIPT:
        {transcript}
    """
    
    success, response, error = retry_api_call(
        client.models.generate_content,
        model=MODEL_TRANSCRIBE,
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


def edit_chunk(chunk):
    """Edit a single chunk transcript for readability."""
    verbatim_file = f"transcript/{chunk['name']}_verbatim.txt"
    edited_file = f"transcript/{chunk['name']}_edited.txt"
    
    try:
        with open(verbatim_file, "r") as f:
            chunk_text = f.read()
        print(f"✓ Loaded: {verbatim_file}")
    except FileNotFoundError:
        print(f"❌ Missing: {verbatim_file}")
        return None
    
    editing_prompt = f"""
        Your goal is to edit this podcast transcript chunk to improve readability and coherence.

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
        model=MODEL_EDIT,
        contents=[editing_prompt],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    if not success:
        print(f"❌ Error editing {chunk['name']}: {error}")
        return None
    
    edited_text = response.text
    with open(edited_file, "w") as f:
        f.write(edited_text)
    print(f"✓ Saved: {edited_file}")
    
    return {
        "number": chunk['name'].split('_')[1],
        "name": chunk['name'],
        "text": edited_text,
        "start": chunk['start'],
        "end": chunk['end']
    }


def stitch_transcripts(edited_chunks):
    """Stitch edited chunks into final transcript."""
    print(f"\n{'='*60}")
    print("STITCHING PHASE: Combining edited transcripts")
    print(f"{'='*60}")
    
    # Combine with markers
    combined = ""
    for ct in edited_chunks:
        combined += f"\n\n{'='*60}\n"
        combined += f"CHUNK {ct['number']} (Minutes {ct['start']:.2f} - {ct['end']:.2f})\n"
        combined += f"{'='*60}\n\n"
        combined += ct['text']
    
    stitching_prompt = f"""
        Your goal is to stitch multiple edited podcast transcript chunks into one seamless, continuous transcript.

        #context:
        The transcript was generated in multiple chunks with markers. The chunks have already been edited for readability.

        #instructions
        - Remove duplicate content from the {OVERLAP_SECONDS}-second overlaps between chunks
        - Ensure smooth transitions between chunks
        - Fix any speaker inconsistencies across chunks
        - Don't make other significant changes to the transcript unless necessary 

        #transcript:
        {combined}
    """
    
    print(f"📝 Stitching chunks together...")
    success, response, error = retry_api_call(
        client.models.generate_content,
        model=MODEL_STITCH,
        contents=[stitching_prompt],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    if not success:
        print(f"❌ Error during stitching: {error}")
        return False
    
    # Save final transcript
    final_file = "transcript/full_transcript_edited.txt"
    with open(final_file, "w") as f:
        f.write(response.text)
    print(f"✓ Final transcript saved: {final_file}")
    
    # Save combined verbatim reference
    verbatim_file = "transcript/full_transcript_verbatim.txt"
    with open(verbatim_file, "w") as f:
        f.write(combined)
    print(f"✓ Combined verbatim saved: {verbatim_file}")
    
    return True


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("AUDIO TO TEXT PIPELINE")
    print(f"{'='*60}")
    print(f"Configuration:")
    print(f"  - Chunk duration: {CHUNK_DURATION_MINUTES} minutes")
    print(f"  - Overlap: {OVERLAP_SECONDS} seconds")
    print(f"  - Audio file: {AUDIO_FILE}")
    
    # Step 1: Chunk and upload audio
    chunks = chunk_and_upload_audio(AUDIO_FILE, CHUNK_DURATION_MINUTES, OVERLAP_SECONDS)
    
    # Step 2: Transcribe chunks
    print(f"\n{'='*60}")
    print("STEP 2: Transcribing chunks")
    print(f"{'='*60}")
    
    previous_context = None
    for i, chunk in enumerate(chunks):
        transcript, _ = transcribe_chunk(chunk, i, previous_context)
        if transcript is None:
            print(f"❌ Failed to transcribe {chunk['name']}")
            return
        
        # Generate context for next chunk
        if i < len(chunks) - 1:
            previous_context = generate_context_summary(transcript, i + 1, len(chunks))
    
    print(f"\n✅ All chunks transcribed!")
    
    # Step 3: Edit chunks
    print(f"\n{'='*60}")
    print("STEP 3: Editing individual transcripts")
    print(f"{'='*60}")
    
    edited_chunks = []
    for chunk in chunks:
        edited = edit_chunk(chunk)
        if edited:
            edited_chunks.append(edited)
    
    print(f"\n✅ All chunks edited!")
    
    # Step 4: Stitch transcripts
    if stitch_transcripts(edited_chunks):
        print(f"\n{'='*60}")
        print("✅ PIPELINE COMPLETE!")
        print(f"{'='*60}")
        print(f"\n📁 Final outputs:")
        print(f"   - transcript/full_transcript_edited.txt (final)")
        print(f"   - transcript/full_transcript_verbatim.txt (reference)")
        print(f"   - transcript/chunk_*_verbatim.txt (raw)")
        print(f"   - transcript/chunk_*_edited.txt (edited)")
    else:
        print(f"\n❌ Pipeline failed during stitching")