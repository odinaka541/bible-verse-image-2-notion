# YouVersion to Notion Daily Sync

Automatically sync the YouVersion Bible Verse of the Day (with image!) to your Notion page every morning.

## Features

- Fetches the daily verse with official YouVersion images
- Multiple fallback strategies for maximum reliability
- Beautiful Notion formatting with callout blocks
- Automated daily execution via GitHub Actions
- Zero-maintenance once set up

## Architecture

```
+-----------------+
|  YouVersion     |
|  Bible.com      |
|  Life.Church    |
+--------+--------+
         | Fetch verse + image
         v
+-----------------+
|  Python Script  |
|  (Multi-source  |
|   fallback)     |
+--------+--------+
         | Upload
         v
+-----------------+
|  Notion Page    |
|  (Your daily    |
|   devotional)   |
+-----------------+
```

## Quick Start

### Prerequisites

1. Python 3.11+ installed on your machine
2. Notion account (free tier works!)
3. GitHub account (for automated daily sync)

### Step 1: Set Up Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Name it: `YouVersion Sync`
4. Select the workspace where you want the verse to appear
5. Click "Submit"
6. Copy the Internal Integration Token (starts with `secret_`)

### Step 2: Get Your Notion Page ID

1. Open the Notion page where you want verses to appear
2. Click "Share" in the top right
3. Click "Invite" and add your integration (`YouVersion Sync`)
4. Copy the page URL. It looks like:
   ```
   https://www.notion.so/My-Devotional-a1b2c3d4e5f6...
   ```
5. The Page ID is everything after the last dash: `a1b2c3d4e5f6...`

### Step 3: Local Setup

```bash
# clone this repository
git clone <your-repo-url>
cd youversion-notion-sync

# install dependencies
pip install -r requirements.txt

# create .env file
cp .env.template .env

# edit .env and add your credentials
nano .env  # or use your favorite editor
```

Your `.env` should look like:
```env
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=a1b2c3d4e5f6789012345678901234
CLEAR_DAILY=false
```

### Step 4: Test It Out

```bash
python youversion_sync_enhanced.py
```

You should see:
```
==================================================
YouVersion -> Notion Sync
==================================================
Successfully fetched using: _strategy_lifechurch_image
Verse: Psalm 23:4 (NLT)
Text: Even when I walk through the darkest valley...
Image: https://d347bo4ltvvnaz.cloudfront.net/images/...
Successfully uploaded to Notion!
```

### Step 5: Set Up Automated Daily Sync

#### Option A: GitHub Actions (Recommended)

1. Push this code to a GitHub repository
2. Go to your repo's Settings -> Secrets and variables -> Actions
3. Add two secrets:
   - `NOTION_TOKEN` = your Notion integration token
   - `NOTION_PAGE_ID` = your page ID
4. The workflow will run automatically every day at 6 AM UTC

To test immediately:
- Go to Actions tab
- Click "Daily YouVersion Sync"
- Click "Run workflow"

#### Option B: Cron Job (Linux/Mac)

```bash
# edit your crontab
crontab -e

# add this line (runs at 6 AM daily)
0 6 * * * cd /path/to/youversion-notion-sync && /usr/bin/python3 youversion_sync_enhanced.py
```

#### Option C: Windows Task Scheduler

1. Open Task Scheduler
2. Create a new task
3. Set trigger: Daily at 6:00 AM
4. Action: Run `python.exe` with argument `C:\path\to\youversion_sync_enhanced.py`

## Project Structure

```
youversion-notion-sync/
├── youversion_sync_enhanced.py   # main script (multi-fallback)
├── youversion_notion_sync.py     # alternative simpler version
├── run.py                        # user-friendly wrapper
├── test_sync.py                  # debug tool
├── requirements.txt              # python dependencies
├── .env.template                 # environment variables template
├── setup.sh                      # linux/mac setup script
├── setup.bat                     # windows setup script
├── .github/
│   └── workflows/
│       └── daily-sync.yml        # github actions workflow
└── README.md                     # this file
```

## How It Works

### Multi-Strategy Fetching

The script tries multiple methods to get the verse image:

1. **Life.Church CDN** (Primary) - Most reliable
   - Official images published by YouVersion's parent org
   - Available for dates up to 90 days in advance

2. **Bible.com Scraping** (Secondary)
   - Directly from the VOTD page
   - Always has today's verse

3. **Unofficial APIs** (Fallback)
   - Community-built APIs
   - May not always have images

### Notion Block Structure

Each day creates a beautiful block with:
- Date header (Heading 2)
- Callout with verse citation and text (blue background)
- Full-resolution verse image

## Customization

### Change the Time

Edit `.github/workflows/daily-sync.yml`:
```yaml
schedule:
  - cron: '0 6 * * *'  # change to your preferred time (UTC)
```

Use crontab.guru to generate cron expressions.

### Clear Page Daily

To replace yesterday's verse instead of appending:
```env
CLEAR_DAILY=true
```

### Change Notion Formatting

Edit the `add_verse_with_image` method in `youversion_sync_enhanced.py` to customize:
- Heading styles
- Callout colors
- Block order
- Additional content

## Troubleshooting

### "Missing environment variables"
- Ensure `.env` file exists with correct values
- For GitHub Actions, check repository secrets

### "Notion API Error: 401"
- Your integration token is invalid
- Regenerate it from notion.so/my-integrations

### "Notion API Error: 404"
- Page ID is incorrect
- Integration wasn't invited to the page
- Make sure you shared the page with your integration

### "All strategies failed to fetch verse"
- Check your internet connection
- Bible.com or Life.Church might be down temporarily
- Try running again in a few minutes

### Images not displaying in Notion
- The image URL might be blocked by Notion's proxy
- Life.Church images should work reliably
- Try the `youversion_notion_sync.py` alternative script

## Security Notes

- Never commit your `.env` file to Git (it's in `.gitignore`)
- Use GitHub Secrets for automation
- Notion tokens can be regenerated if compromised
- Rate limits: YouVersion has generous limits, but be respectful

## License

MIT License - Feel free to use, modify, and distribute.

## Acknowledgments

- YouVersion (https://www.youversion.com) - For the amazing Bible app
- Life.Church (https://www.life.church) - For publishing verse images
- Notion (https://www.notion.so) - For the fantastic API

---

*"Your word is a lamp to my feet and a light to my path." - Psalm 119:105*
