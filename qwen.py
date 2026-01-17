"""
Qwen3-ASR transcription for Episode 148 with Gemini post-processing.
"""

import time
import json
import requests
from google import genai
from google.genai.types import GenerateContentConfig
from keys.creds import QWEN_API_KEY, GEMINI_API_KEY
from prompts import build_chinese_prompt

# DashScope API endpoints
API_SUBMIT = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
API_TASK = "https://dashscope.aliyuncs.com/api/v1/tasks/"
MODEL = "qwen3-asr-flash-filetrans"

# Episode 148 audio
AUDIO_URL = "https://media.xyzcdn.net/61933ace1b4320461e91fd55/lghAWJ9Tv9UZb-7BHwiF3RRxmLAo.mp3"


def qwen_transcribe(file_url: str) -> str:
    """Submit transcription job and wait for result."""
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    payload = {
        "model": MODEL,
        "input": {"file_url": file_url},
        "parameters": {
            "channel_id": [0],
            "enable_itn": True,
            "enable_timestamp": True,
            "language_hints": ["zh"]
        }
    }
    
    # Submit job
    print(f"📤 Submitting transcription job...")
    resp = requests.post(API_SUBMIT, headers=headers, json=payload)
    resp.raise_for_status()
    task_id = resp.json()["output"]["task_id"]
    print(f"✅ Task ID: {task_id}")
    
    # Poll for result
    headers_get = {"Authorization": f"Bearer {QWEN_API_KEY}"}
    while True:
        status_resp = requests.get(f"{API_TASK}{task_id}", headers=headers_get)
        status_data = status_resp.json()
        status = status_data["output"]["task_status"]
        print(f"⏳ Status: {status}")
        
        if status == "SUCCEEDED":
            break
        elif status in ("FAILED", "ERROR"):
            raise Exception(f"Failed: {status_data}")
        time.sleep(10)
    
    # Fetch transcription - handle different response formats
    output = status_data["output"]
    
    # Find transcription URL in various response formats
    trans_url = None
    if "result" in output and "transcription_url" in output["result"]:
        trans_url = output["result"]["transcription_url"]
    elif "results" in output and output["results"]:
        trans_url = output["results"][0].get("transcription_url")
    elif "transcription_url" in output:
        trans_url = output["transcription_url"]
    
    if trans_url:
        print(f"📥 Fetching transcript...")
        trans_resp = requests.get(trans_url)
        trans_data = trans_resp.json()
        
        # Extract text from transcripts
        texts = []
        for t in trans_data.get("transcripts", []):
            for s in t.get("sentences", []):
                texts.append(s.get("text", ""))
        
        if texts:
            return "\n".join(texts)
        
        # Fallback: return raw transcription data
        return json.dumps(trans_data, ensure_ascii=False, indent=2)
    
    # Direct text in output
    if "text" in output:
        return output["text"]
    
    # Return raw output for debugging
    return json.dumps(output, ensure_ascii=False, indent=2)


def gemini_format(raw_transcript: str, episode: dict) -> str:
    """Use Gemini to format transcript with speaker labels and timestamps."""
    print("📝 Formatting with Gemini...")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = build_chinese_prompt(episode)
    
    format_prompt = f"""{prompt}

#raw transcript to format:
{raw_transcript}

请根据以上原始转录文本，添加时间戳和说话人标注。保持内容完整，按照指定格式输出。"""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[format_prompt],
        config=GenerateContentConfig(thinking_config={'thinking_budget': 0})
    )
    
    return response.text


if __name__ == "__main__":
    # Load episode info
    with open("episodes.json", "r", encoding="utf-8") as f:
        episode = json.load(f)[0]
    
    print(f"🎙️  {episode['title']}")
    print(f"📅 {episode['publish_date']}\n")
    
    # Step 1: Qwen ASR
    raw_transcript = qwen_transcribe(AUDIO_URL)
    
    # Save raw
    raw_file = "transcript/episode_148_qwen_raw.txt"
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(raw_transcript)
    print(f"✅ Raw saved: {raw_file}")
    
    # Step 2: Gemini formatting with speaker labels
    formatted = gemini_format(raw_transcript, episode)
    
    # Save formatted
    output_file = "transcript/episode_148_qwen.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# {episode['title']}\n")
        f.write(f"# Published: {episode['publish_date']}\n")
        f.write(f"# ASR: {MODEL} | Formatted: gemini-2.5-flash\n\n")
        f.write(formatted)
    
    print(f"\n✅ Formatted saved: {output_file}")
    print(f"\n--- Preview ---\n{formatted[:1500]}")
