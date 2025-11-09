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