import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup


PODCAST_ID = "61933ace1b4320461e91fd55"


def fetch_podcast_episodes(podcast_id: str) -> list[dict]:
    url = f"https://www.xiaoyuzhoufm.com/podcast/{podcast_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Page status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the __NEXT_DATA__ script tag
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    
    if not script_tag:
        print("Could not find __NEXT_DATA__ script tag")
        return []
    
    try:
        data = json.loads(script_tag.string)
        
        # Navigate to episodes: props.pageProps.podcast.episodes
        podcast_data = data.get("props", {}).get("pageProps", {}).get("podcast", {})
        episodes_raw = podcast_data.get("episodes", [])
        
        print(f"Found {len(episodes_raw)} episodes in __NEXT_DATA__")
        
        episodes = []
        for ep in episodes_raw:
            episode = parse_episode(ep)
            if episode:
                episodes.append(episode)
        
        return episodes
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return []


def parse_episode(ep: dict) -> dict | None:
    """Parse episode data from __NEXT_DATA__ JSON."""
    try:
        episode_id = ep.get("eid")
        title = ep.get("title")
        description = ep.get("description", "")  # Show notes
        
        # pubDate is in ISO format like "2026-01-16T00:15:00.000Z"
        pub_date_raw = ep.get("pubDate")
        
        if pub_date_raw:
            # Parse ISO format and convert to readable format
            try:
                dt = datetime.fromisoformat(pub_date_raw.replace("Z", "+00:00"))
                pub_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pub_date = pub_date_raw
        else:
            pub_date = "Unknown"
        
        if episode_id and title:
            return {
                "title": title,
                "url": f"https://www.xiaoyuzhoufm.com/episode/{episode_id}",
                "publish_date": pub_date,
                "episode_id": episode_id,
                "show_notes": description
            }
    except Exception as e:
        print(f"Error parsing episode: {e}")
    
    return None


def main():
    print("=" * 60)
    print("Xiaoyuzhou FM Podcast Scraper")
    print("=" * 60)
    print(f"\nPodcast ID: {PODCAST_ID}")
    print(f"URL: https://www.xiaoyuzhoufm.com/podcast/{PODCAST_ID}\n")
    
    episodes = fetch_podcast_episodes(PODCAST_ID)
    
    if episodes:
        print(f"\n{'=' * 60}")
        print(f"Found {len(episodes)} episodes:")
        print("=" * 60)
        for i, ep in enumerate(episodes, 1):
            print(f"\n{i}. {ep['title']}")
            print(f"   URL: {ep['url']}")
            print(f"   Date: {ep['publish_date']}")
            # Show first 200 chars of show notes
            notes_preview = ep['show_notes'][:200] + "..." if len(ep['show_notes']) > 200 else ep['show_notes']
            print(f"   Notes: {notes_preview}")
        
        # Save to JSON file
        with open("episodes.json", "w", encoding="utf-8") as f:
            json.dump(episodes, f, ensure_ascii=False, indent=2)
        print(f"\n\nSaved episodes to episodes.json")
    else:
        print("\nCouldn't extract episodes.")


if __name__ == "__main__":
    main()
