# from google import genai
# from google.genai.types import HttpOptions, GenerateContentConfig
# import os
# from keys.creds import GEMINI_API_KEY
# import httpx


# GEMINI_TIMEOUT = 10 * 60 * 1000  # 10 minutes = 600,000 ms

# client = genai.Client(
#     api_key=GEMINI_API_KEY, 
#     http_options=HttpOptions(timeout=GEMINI_TIMEOUT)
# )

# # wav_10min = {"name": "wav_10mins", "uri": "files/vqsrli804usc"} 
# flac_full = {"name": "flac_full", "uri": "files/7uigbl8m7elu"}
# # flac_10min = {"name": "flac_10mins", "uri": "files/nubde0edid4c"}
# # flac_15min = {"name": "flac_15mins", "uri": "files/c87wily1qb5c"}
# # flac_30min = {"name": "flac_30mins", "uri": "files/zrnbtg2qs6le"}
# # flac_45min = {"name": "flac_45mins", "uri": "files/r7zier3wosrj"}
# # chunk_1 = {"name": "chunk_1", "uri": "files/anb79vwu95wg", "start": 0.00, "end": 30.00}
# # chunk_2 = {"name": "chunk_2", "uri": "files/z9fc27kzeqd8", "start": 29.83, "end": 52.37}

# uploaded_file = flac_full

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
#     contents=[prompt, file_obj],
#     config=GenerateContentConfig(
#         thinking_config={'thinking_budget': 0}  # Disable thinking for Flash
#     )
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




# from pydub import AudioSegment

# # Load the audio file
# audio = AudioSegment.from_wav("audio/sample.wav")

# # Extract first 10 minutes (10 * 60 * 1000 milliseconds)
# first_10_mins = audio[:10 * 60 * 1000]

# # Export the trimmed audio
# first_10_mins.export("audio/sample_10mins.wav", format="wav")




# from pydub import AudioSegment

# # Load WAV
# audio = AudioSegment.from_wav("audio/sample.wav")

# # Export as FLAC (lossless compression)
# audio.export("audio/sample.flac", format="flac")

# print("✓ Converted to FLAC")




# from google import genai
# from keys.creds import GEMINI_API_KEY

# client = genai.Client(api_key=GEMINI_API_KEY)

# print("📁 Your uploaded files:\n")

# files = list(client.files.list())

# if not files:
#     print("No files found.")
# else:
#     for file in files:
#         print(f"Name: {file.name}")
#         print(f"Display name: {file.display_name}")
#         print(f"Size: {file.size_bytes / (1024*1024):.2f} MB")
#         print(f"Created: {file.create_time}")
#         print(f"Expires: {file.expiration_time}")
#         print(f"URI: {file.uri}")
#         print("-" * 50)


# from google import genai
# from keys.creds import GEMINI_API_KEY

# client = genai.Client(api_key=GEMINI_API_KEY)

# uploaded_file = client.files.upload(file="audio/sample_10mins.flac")
# print(f"File uploaded: {uploaded_file.name}")






from pydub import AudioSegment
from google import genai
from keys.creds import GEMINI_API_KEY

# Load the full audio file
print("Loading audio file...")
audio = AudioSegment.from_file("audio/sample.flac", format="flac")

# Get duration
duration_ms = len(audio)
duration_minutes = duration_ms / (60 * 1000)
print(f"Full audio duration: {duration_minutes:.2f} minutes ({duration_ms / 1000:.2f} seconds)")

# Settings
chunk_duration_ms = 30 * 60 * 1000  # 30 minutes in milliseconds
buffer_ms = 10 * 1000  # 10 seconds buffer

# Calculate number of chunks needed
num_chunks = (duration_ms + chunk_duration_ms - 1) // chunk_duration_ms  # ceiling division
print(f"\nSplitting into {num_chunks} chunks with 10-second overlap...")

chunks_info = []

for i in range(num_chunks):
    # Calculate start and end times
    if i == 0:
        start_ms = 0
    else:
        # Start 10 seconds before the previous chunk ended
        start_ms = (i * chunk_duration_ms) - buffer_ms
    
    end_ms = min((i + 1) * chunk_duration_ms, duration_ms)
    
    # Extract chunk
    chunk = audio[start_ms:end_ms]
    
    # Calculate human-readable times
    start_min = start_ms / (60 * 1000)
    end_min = end_ms / (60 * 1000)
    chunk_min = len(chunk) / (60 * 1000)
    
    # Export
    filename = f"audio/sample_chunk{i+1}.flac"
    print(f"\nChunk {i+1}: {start_min:.2f}min - {end_min:.2f}min (duration: {chunk_min:.2f}min)")
    chunk.export(filename, format="flac")
    print(f"✓ Exported: {filename}")
    
    chunks_info.append({
        "number": i + 1,
        "filename": filename,
        "start_min": start_min,
        "end_min": end_min,
        "duration_min": chunk_min
    })

print("\n" + "="*60)
print("📤 Uploading chunks to Gemini...")
print("="*60)

client = genai.Client(api_key=GEMINI_API_KEY)

uploaded_chunks = []

for chunk_info in chunks_info:
    print(f"\nUploading chunk {chunk_info['number']}...")
    uploaded_file = client.files.upload(file=chunk_info['filename'])
    
    chunk_data = {
        "number": chunk_info['number'],
        "name": f"chunk_{chunk_info['number']}",
        "uri": uploaded_file.uri,
        "start_min": chunk_info['start_min'],
        "end_min": chunk_info['end_min'],
        "duration_min": chunk_info['duration_min']
    }
    uploaded_chunks.append(chunk_data)
    
    print(f"✓ Uploaded: {uploaded_file.name}")
    print(f"  URI: {uploaded_file.uri}")
    print(f"  Time range: {chunk_info['start_min']:.2f} - {chunk_info['end_min']:.2f} min")

print("\n" + "="*60)
print("✅ All chunks uploaded successfully!")
print("="*60)
print("\n📋 Add these to test.py:\n")

for chunk in uploaded_chunks:
    print(f'chunk_{chunk["number"]} = {{"name": "{chunk["name"]}", "uri": "{chunk["uri"]}", "start": {chunk["start_min"]:.2f}, "end": {chunk["end_min"]:.2f}}}')

print("\n# To process all chunks:")
print("chunks = [chunk_1, chunk_2, ...]  # Add all chunks here")
