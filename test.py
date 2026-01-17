from google import genai
from keys.creds import GEMINI_API_KEY
from file_manager import get_or_upload_file
import json
from prompts import CHINESE_PROMPT

# Load episode info
with open("episodes.json", "r", encoding="utf-8") as f:
    episodes = json.load(f)

# Episode 148 is the first one
episode = episodes[0]
print(f"Episode: {episode['title']}")
print(f"Date: {episode['publish_date']}")

# Audio file path (renamed to avoid encoding issues)
AUDIO_FILE = "audio/episode_148.mp3"

# Initialize client
client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.5-flash"

# Get the audio file (uses cached upload if available)
print("\n📤 Loading audio file...")
file_obj = get_or_upload_file(AUDIO_FILE)

# Transcription
print("\n📝 Generating verbatim transcript with timestamps...")
print(f"Model: {model}")
print(f"Audio: {AUDIO_FILE}")
print(f"This is an 85-minute episode, may take several minutes...\n")

response = client.models.generate_content(
    model=model,
    contents=[CHINESE_PROMPT, file_obj]
)

# Save the transcript
output_file = f"transcript/episode_148_verbatim.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# {episode['title']}\n")
    f.write(f"# Published: {episode['publish_date']}\n")
    f.write(f"# Transcribed with {model}\n\n")
    f.write(response.text)

print(f"✅ Transcript saved: {output_file}")
print(f"\n--- Preview (first 1000 chars) ---")
print(response.text[:1000])
