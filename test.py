from google import genai
from keys.creds import GEMINI_API_KEY
from file_manager import get_or_upload_file
from prompts import SINGLE_PASS_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)

# Get the audio file (uses cached upload if available)
print("Loading audio file...")
file_obj = get_or_upload_file("audio/sample.flac")

# Single-pass transcription
print("\n📝 Generating transcript (single-pass)...")
print(f"Model: gemini-3-pro")
print(f"This may take a few minutes for a ~52 min file...\n")

response = client.models.generate_content(
    model="gemini-3-pro",
    contents=[SINGLE_PASS_PROMPT, file_obj]
)

# Save the transcript
output_file = "transcript/single_pass_test.txt"
with open(output_file, "w") as f:
    f.write(response.text)

print(f"✅ Transcript saved: {output_file}")
print(f"\n--- Preview (first 500 chars) ---")
print(response.text[:500])