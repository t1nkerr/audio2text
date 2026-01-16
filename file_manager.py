"""
File manager for Gemini API uploads.
Tracks uploaded files and handles expiration.

Usage:
    from file_manager import get_or_upload_file
    
    file_obj = get_or_upload_file("audio/sample.flac")
    # Returns a Gemini file object ready to use
"""

from google import genai
from keys.creds import GEMINI_API_KEY
import json
import os
from datetime import datetime, timezone

JOBS_FILE = "jobs.json"

client = genai.Client(api_key=GEMINI_API_KEY)


def load_jobs() -> dict:
    """Load jobs registry from JSON file."""
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_jobs(jobs: dict):
    """Save jobs registry to JSON file."""
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def is_expired(job: dict) -> bool:
    """Check if a job's file has expired."""
    if "expires_at" not in job:
        return True
    
    expires_at = datetime.fromisoformat(job["expires_at"])
    now = datetime.now(timezone.utc)
    return now >= expires_at


def upload_file(file_path: str) -> dict:
    """Upload a file to Gemini and return job info."""
    print(f"📤 Uploading {file_path}...")
    
    uploaded = client.files.upload(file=file_path)
    
    # Get file info including expiration
    file_info = client.files.get(name=uploaded.name)
    
    job = {
        "file_path": file_path,
        "name": uploaded.name,
        "uri": uploaded.uri,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": file_info.expiration_time.isoformat() if file_info.expiration_time else None,
        "size_bytes": file_info.size_bytes,
    }
    
    print(f"✓ Uploaded: {uploaded.name}")
    print(f"  URI: {uploaded.uri}")
    if job["expires_at"]:
        print(f"  Expires: {job['expires_at']}")
    
    return job


def get_or_upload_file(file_path: str, force_upload: bool = False):
    """
    Get a file object, uploading if necessary.
    
    Args:
        file_path: Path to the audio file
        force_upload: If True, always upload (ignore cache)
    
    Returns:
        Gemini file object ready to use with generate_content()
    """
    jobs = load_jobs()
    
    # Check if we have a valid cached upload
    if file_path in jobs and not force_upload:
        job = jobs[file_path]
        
        if not is_expired(job):
            print(f"✓ Using cached file: {job['name']}")
            try:
                file_obj = client.files.get(name=job["name"])
                return file_obj
            except Exception as e:
                print(f"⚠️ Cached file not found on server: {e}")
                print("  Re-uploading...")
        else:
            print(f"⏰ File expired, re-uploading...")
    
    # Upload the file
    job = upload_file(file_path)
    
    # Save to registry
    jobs[file_path] = job
    save_jobs(jobs)
    
    # Return file object
    return client.files.get(name=job["name"])


def list_jobs():
    """List all tracked jobs and their status."""
    jobs = load_jobs()
    
    if not jobs:
        print("No files in registry.")
        return
    
    print(f"\n{'='*60}")
    print("REGISTERED FILES")
    print(f"{'='*60}")
    
    for file_path, job in jobs.items():
        expired = is_expired(job)
        status = "❌ EXPIRED" if expired else "✓ ACTIVE"
        
        print(f"\n{file_path}")
        print(f"  Name: {job.get('name', 'N/A')}")
        print(f"  URI: {job.get('uri', 'N/A')}")
        print(f"  Status: {status}")
        if job.get("expires_at"):
            print(f"  Expires: {job['expires_at']}")
        if job.get("size_bytes"):
            size_mb = job["size_bytes"] / (1024 * 1024)
            print(f"  Size: {size_mb:.2f} MB")


def clear_expired():
    """Remove expired entries from registry."""
    jobs = load_jobs()
    active_jobs = {k: v for k, v in jobs.items() if not is_expired(v)}
    removed = len(jobs) - len(active_jobs)
    save_jobs(active_jobs)
    print(f"Removed {removed} expired entries.")
    return removed


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python file_manager.py upload <file_path>  - Upload a file")
        print("  python file_manager.py list                - List all registered files")
        print("  python file_manager.py clear               - Remove expired entries")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "upload" and len(sys.argv) >= 3:
        file_path = sys.argv[2]
        get_or_upload_file(file_path)
    elif command == "list":
        list_jobs()
    elif command == "clear":
        clear_expired()
    else:
        print(f"Unknown command: {command}")
