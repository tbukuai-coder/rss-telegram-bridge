#!/usr/bin/env python3
"""
RSS to Telegram Bridge
Fetches RSS feeds and posts new articles to a Telegram channel/group.
"""

import os
import json
import hashlib
import html
import re
from pathlib import Path
from datetime import datetime, timezone

import feedparser
import httpx
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MESSAGE_TEMPLATE = os.getenv(
    "MESSAGE_TEMPLATE",
    "📰 *{title}*\n\n{summary}\n\n🔗 [Read more]({link})"
)

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
POSTED_PATH = SCRIPT_DIR / "posted.json"


def load_config() -> dict:
    """Load feed configuration from YAML file."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_posted() -> set:
    """Load set of already-posted article IDs."""
    if POSTED_PATH.exists():
        with open(POSTED_PATH, "r") as f:
            data = json.load(f)
            return set(data.get("posted", []))
    return set()


def save_posted(posted: set) -> None:
    """Save posted article IDs."""
    with open(POSTED_PATH, "w") as f:
        json.dump({"posted": list(posted), "updated": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def get_article_id(entry: dict) -> str:
    """Generate a unique ID for an article."""
    # Use entry ID if available, otherwise hash the link
    identifier = entry.get("id") or entry.get("link", "")
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    clean = html.unescape(clean)
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def truncate(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3].rsplit(' ', 1)[0] + "..."


def escape_markdown(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    # Characters that need escaping in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_message(entry: dict, settings: dict) -> str:
    """Format an article into a Telegram message."""
    title = clean_html(entry.get("title", "No title"))
    link = entry.get("link", "")
    
    # Get summary
    summary = ""
    if settings.get("include_summary", True):
        summary_raw = entry.get("summary") or entry.get("description", "")
        summary = clean_html(summary_raw)
        max_len = settings.get("summary_max_length", 280)
        summary = truncate(summary, max_len)
    
    # Format message (using Markdown for Telegram)
    message = MESSAGE_TEMPLATE.format(
        title=title,
        link=link,
        summary=summary if summary else "No summary available"
    )
    
    return message


def send_telegram_message(text: str) -> bool:
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False


def fetch_feed(url: str) -> list:
    """Fetch and parse an RSS feed."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            print(f"⚠️ Feed parsing issue: {feed.bozo_exception}")
            return []
        return feed.entries
    except Exception as e:
        print(f"❌ Failed to fetch feed: {e}")
        return []


def process_feeds() -> None:
    """Main function to process all feeds."""
    print(f"🚀 Starting RSS to Telegram Bridge - {datetime.now(timezone.utc).isoformat()}")
    
    # Validate configuration
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Missing required environment variables!")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return
    
    # Load configuration
    config = load_config()
    feeds = config.get("feeds", [])
    settings = config.get("settings", {})
    max_per_run = settings.get("max_articles_per_run", 5)
    
    # Load already-posted articles
    posted = load_posted()
    initial_count = len(posted)
    
    total_posted = 0
    
    for feed_config in feeds:
        if not feed_config.get("enabled", True):
            continue
        
        feed_name = feed_config.get("name", "Unknown")
        feed_url = feed_config.get("url")
        
        if not feed_url:
            continue
        
        print(f"\n📡 Fetching: {feed_name}")
        entries = fetch_feed(feed_url)
        
        if not entries:
            print(f"   No entries found")
            continue
        
        print(f"   Found {len(entries)} entries")
        
        # Process new articles (newest first, limited)
        new_count = 0
        for entry in entries:
            if new_count >= max_per_run:
                break
            
            article_id = get_article_id(entry)
            
            if article_id in posted:
                continue
            
            # Format and send
            message = format_message(entry, settings)
            title = clean_html(entry.get("title", ""))[:50]
            
            if send_telegram_message(message):
                print(f"   ✅ Posted: {title}...")
                posted.add(article_id)
                new_count += 1
                total_posted += 1
            else:
                print(f"   ❌ Failed: {title}...")
    
    # Save state
    save_posted(posted)
    
    print(f"\n📊 Summary:")
    print(f"   Articles posted this run: {total_posted}")
    print(f"   Total tracked articles: {len(posted)} (+{len(posted) - initial_count})")
    print("✅ Done!")


if __name__ == "__main__":
    process_feeds()
