"""
Prompt templates for audio transcription pipeline.
Import and use directly in your scripts.

Usage:
    from prompts import TRANSCRIBE_EDIT_PROMPT, STITCH_PROMPT
"""

# =============================================================================
# BACKGROUND CONTEXT (reusable across prompts)
# =============================================================================

PODCAST_BACKGROUND = """The podcast is produced by Trivium China, a consultancy on China policy. The speakers are usually Andrew Polk, Dinny Macmahon, Kendra Schaefer, and occasionally other guests."""


# =============================================================================
# APPROACH 1: COMBINED TRANSCRIPTION + EDITING (process_chunks.py)
# =============================================================================

TRANSCRIBE_EDIT_PROMPT = f"""Generate a English-language transcript of this audio segment. Make the transcript readable and coherent. 

#background:
{PODCAST_BACKGROUND}

#instructions:
- Remove filler words (um, uh, like, you know, etc.)
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Correct misspellings
- Make other edits when necessary to improve readability and coherence
- No markdown formatting. Identify speaker names based on the conversation and label them consistently

#output format:
Speaker Name:
[their text]

Speaker Name:
[their text]

...
"""

def get_transcribe_edit_prompt_with_context(chunk_num: int, start_min: float, end_min: float, overlap_sec: int, previous_context: str) -> str:
    """Get transcription+editing prompt with context from previous chunk."""
    return f"""{TRANSCRIBE_EDIT_PROMPT}

#IMPORTANT CONTEXT:
- This is chunk {chunk_num} of the podcast, covering minutes {start_min:.2f} - {end_min:.2f}
- The first {overlap_sec} seconds overlap with the previous chunk to ensure continuity

#CONTEXT FROM PREVIOUS SEGMENT:
{previous_context}
"""


# =============================================================================
# CONTEXT SUMMARY (for passing between chunks)
# =============================================================================

def get_context_summary_prompt(transcript: str) -> str:
    """Generate prompt for creating context summary for next chunk."""
    return f"""Prepare context for transcribing the next audio segment of this podcast.

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


# =============================================================================
# STITCHING (combine multiple chunks)
# =============================================================================

def get_stitch_prompt(combined_transcript: str, overlap_sec: int) -> str:
    """Generate prompt for stitching multiple chunks together."""
    return f"""Stitch multiple podcast transcript chunks into one seamless, continuous transcript.

#context:
The transcript was generated in overlapping chunks. Each chunk has already been cleaned and edited.

#instructions:
- Remove duplicate content from the {overlap_sec}-second overlaps between chunks
- Keep only ONE version of overlapping content (choose the better one)
- Ensure smooth transitions between chunks
- Fix any speaker name inconsistencies across chunks
- Output one continuous transcript with no chunk markers
- No other significant changes

#transcript:
{combined_transcript}
"""


# =============================================================================
# APPROACH 2: TWO-STEP (VERBATIM + EDIT) - from main.py
# =============================================================================

VERBATIM_TRANSCRIBE_PROMPT = f"""Generate a verbatim English-language transcript of the podcast. Identify the names of the speakers based on the conversation.

#output format:
Speaker Name:
[their text]

Speaker Name:
[their text]

...

#instructions:
- label each speaker consistently throughout the transcription.
- only use characters from the English alphabet, unless you believe foreign characters are correct.
- use the correct words and spell everything correctly. Use the context of the podcast to help.
- no markdown formatting.
- transcribe ALL audio in this segment from start to finish.

#background:
{PODCAST_BACKGROUND}
"""

def get_verbatim_prompt_with_context(chunk_num: int, start_min: float, end_min: float, overlap_sec: int, previous_context: str) -> str:
    """Get verbatim transcription prompt with context from previous chunk."""
    return f"""{VERBATIM_TRANSCRIBE_PROMPT}

#IMPORTANT CONTEXT:
- This is chunk {chunk_num} of the podcast, covering minutes {start_min:.2f} - {end_min:.2f}.
- The first {overlap_sec} seconds overlap with the previous chunk to ensure continuity.
- Transcribe the ENTIRE audio segment, including the overlapping portion.

#CONTEXT FROM PREVIOUS SEGMENT:
{previous_context}

#YOUR TASK:
Use the above context to maintain speaker name consistency and conversation flow, then transcribe this entire audio segment from beginning to end.
"""


def get_edit_prompt(transcript: str) -> str:
    """Generate prompt for editing a verbatim transcript."""
    return f"""Your goal is to edit this podcast transcript chunk to improve readability and coherence.

#instructions:
- Remove filler words
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Keep the same speaker labels and format
- Correct misspellings 
- No markdown formatting
- Make other edits when necessary to improve readability and coherence

#TRANSCRIPT TO EDIT:
{transcript}
"""


# =============================================================================
# FUTURE: SINGLE-PASS FULL AUDIO (Gemini 3)
# =============================================================================

SINGLE_PASS_PROMPT = f"""Generate a clean, readable English-language transcript of this entire podcast episode.

#background:
{PODCAST_BACKGROUND}

#instructions:
- Identify speaker names based on the conversation and label them consistently throughout
- Remove filler words (um, uh, like, you know, etc.)
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Correct misspellings
- Make edits when necessary to improve readability and coherence
- No markdown formatting

#output format:
Speaker Name:
[their text]

Speaker Name:
[their text]

...
"""
