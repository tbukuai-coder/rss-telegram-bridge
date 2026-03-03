# 📰 RSS to Telegram Bridge

Automatically publish RSS feed updates to a Telegram channel or group. Runs on GitHub Actions — no server needed.

## Features

- 🔄 Polls multiple RSS feeds on a schedule
- 📱 Posts to Telegram with clean formatting
- 🚫 Deduplication — never posts the same article twice
- ⚙️ Configurable feeds, message format, and limits
- 🆓 Runs entirely on GitHub Actions (free tier friendly)

## Quick Start

### 1. Fork or Use This Template

Click "Use this template" or fork this repository.

### 2. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Save the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3. Get Your Chat ID

**For a channel:**
1. Add your bot as an admin to the channel
2. The chat ID is `@yourchannel` or the numeric ID (e.g., `-1001234567890`)

**For a group:**
1. Add your bot to the group
2. Send a message in the group
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find the `chat.id` in the response

**For personal messages:**
1. Message your bot
2. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find your `chat.id`

### 4. Configure GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `TELEGRAM_BOT_TOKEN` — Your bot token from BotFather
- `TELEGRAM_CHAT_ID` — Your channel/group/chat ID

### 5. Configure Feeds

Edit `config.yaml` to add your RSS feeds:

```yaml
feeds:
  - name: "Hacker News"
    url: "https://hnrss.org/frontpage"
    enabled: true
  
  - name: "Your Favorite Site"
    url: "https://example.com/feed.xml"
    enabled: true
```

### 6. Enable GitHub Actions

Go to Actions tab → Enable workflows

The bridge will run every 30 minutes automatically.

## Configuration

### config.yaml

```yaml
feeds:
  - name: "Feed Name"       # Display name (for logs)
    url: "https://..."      # RSS/Atom feed URL
    enabled: true           # true/false to enable/disable

settings:
  max_articles_per_run: 5   # Limit posts per feed per run
  include_summary: true     # Include article summary
  summary_max_length: 280   # Truncate long summaries
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Yes | Target channel/group/chat ID |
| `MESSAGE_TEMPLATE` | No | Custom message format |

### Custom Message Template

Set `MESSAGE_TEMPLATE` environment variable:

```
📰 *{title}*

{summary}

🔗 {link}
```

Available placeholders: `{title}`, `{link}`, `{summary}`

## Schedule

Default: Every 30 minutes (`*/30 * * * *`)

Edit `.github/workflows/rss-bridge.yml` to change:

```yaml
schedule:
  - cron: '0 * * * *'  # Every hour
  - cron: '0 */6 * * *'  # Every 6 hours
  - cron: '0 8 * * *'  # Daily at 8 AM UTC
```

## Manual Run

Go to Actions → RSS to Telegram Bridge → Run workflow

## Local Development

```bash
# Clone the repo
git clone https://github.com/yourusername/rss-telegram-bridge
cd rss-telegram-bridge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
python main.py
```

## License

MIT — do whatever you want with it.
