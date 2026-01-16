"""
Transcribe podcast episode 148 using Gemini 3 Flash.
- Uses episode show notes as background context
- Verbatim transcription
- Timestamps at each speaker turn
"""

from google import genai
from keys.creds import GEMINI_API_KEY
from file_manager import get_or_upload_file
import json

# Load episode info
with open("episodes.json", "r", encoding="utf-8") as f:
    episodes = json.load(f)

# Episode 148 is the first one
episode = episodes[0]
print(f"Episode: {episode['title']}")
print(f"Date: {episode['publish_date']}")

# Audio file path (renamed to avoid encoding issues)
AUDIO_FILE = "audio/episode_148.mp3"

# Build prompt with episode context
TRANSCRIPTION_PROMPT = f"""You are a professional transcriptionist. Please transcribe this Chinese podcast episode VERBATIM (word-for-word, exactly as spoken).

## Episode Background
Title: {episode['title']}
Published: {episode['publish_date']}

## Show Notes (for context - names, topics, timestamps mentioned)
{episode['show_notes']}

## Speakers
- 主播 (Host): 程曼祺 (Cheng Manqi), 晚点 LatePost 科技报道负责人
- 嘉宾 (Guest): 陈亦伦 (Chen Yilun), 它石智航创始人兼 CEO

## Transcription Instructions
1. Transcribe VERBATIM - capture every word exactly as spoken, including filler words (嗯, 啊, 那个, etc.)
2. Add TIMESTAMPS at each speaker turn in format [MM:SS] or [HH:MM:SS]
3. Label each speaker clearly: 【程曼祺】 or 【陈亦伦】
4. Preserve natural speech patterns, pauses, and self-corrections
5. Use Chinese punctuation throughout
6. Keep technical terms and English words as spoken

## Output Format Example
[00:00] 【程曼祺】欢迎收听晚点聊...
[00:15] 【陈亦伦】谢谢曼祺，很高兴来到这里...
[00:32] 【程曼祺】那我们今天主要想聊的是...

Now please transcribe the entire audio:
"""

# Initialize client
client = genai.Client(api_key=GEMINI_API_KEY)

# Get the audio file (uses cached upload if available)
print("\n📤 Loading audio file...")
file_obj = get_or_upload_file(AUDIO_FILE)

# Transcription
print("\n📝 Generating verbatim transcript with timestamps...")
print(f"Model: gemini-3-flash-preview")
print(f"Audio: {AUDIO_FILE}")
print(f"This is an 85-minute episode, may take several minutes...\n")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[TRANSCRIPTION_PROMPT, file_obj]
)

# Save the transcript
output_file = f"transcript/episode_148_verbatim.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# {episode['title']}\n")
    f.write(f"# Published: {episode['publish_date']}\n")
    f.write(f"# Transcribed with Gemini 3 Flash\n\n")
    f.write(response.text)

print(f"✅ Transcript saved: {output_file}")
print(f"\n--- Preview (first 1000 chars) ---")
print(response.text[:1000])
