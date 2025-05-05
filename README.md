# Social Media to Twitter Video Reposter

This script automatically fetches video posts from specified subreddits and Telegram channels and reposts them to one or multiple Twitter accounts.

## Features

- Fetch video posts from multiple subreddits
- Fetch video messages from Telegram channels
- Include post text content in tweets (optional)
- Support for Reddit-hosted videos, Gfycat, and Imgur
- Post to multiple Twitter accounts
- Configurable scheduling (hourly, daily, weekly)
- Keeps track of posted videos to avoid duplicates
- OAuth setup helper for easy authentication with Reddit, Twitter, and Telegram
- Web-based GUI for easy management
- Detailed logging

## Prerequisites

- Python 3.6+
- Reddit API credentials
- Telegram API credentials (optional, for Telegram functionality)
- Twitter API credentials

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install praw tweepy requests schedule telethon
```

3. Set up your API credentials using the OAuth helper:

```bash
python social_media_to_twitter.py --setup
```

This will guide you through the process of setting up API credentials for Reddit, Twitter, and Telegram using OAuth authentication in your web browser.

## Manual Setup (Alternative)

If you prefer to set up your API credentials manually, follow these steps:

1. Copy the configuration template:

```bash
cp config.json.template config.json
```

2. Edit the config.json file with your credentials.

### Setting up Reddit API Credentials

1. Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App" button
3. Fill in the following details:
   - Name: RedditToTwitter (or any name you prefer)
   - App type: Select "web app"
   - Description: A bot that reposts Reddit videos to Twitter
   - About URL: (leave blank)
   - Redirect URI: http://localhost:8000/callback
4. Click "Create app" button
5. Note down the following information:
   - Client ID: The string under "personal use script"
   - Client Secret: The string next to "secret"
6. Update the `config.json` file with these credentials

### Setting up Telegram API Credentials

1. Go to [Telegram's API Development Tools](https://my.telegram.org/apps)
2. Log in with your phone number
3. Fill in the form to create a new application:
   - App title: RedditToTwitter (or any name you prefer)
   - Short name: RedditToTwitter (or any name you prefer)
   - Platform: Other
   - Description: A bot that reposts Telegram videos to Twitter
4. Click "Create application"
5. Note down the following information:
   - API ID: The numeric ID provided
   - API Hash: The string provided
6. Update the `config.json` file with these credentials

### Setting up Twitter API Credentials

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app
3. Apply for Elevated access to get write permissions
4. Navigate to your app's "Keys and Tokens" tab
5. Generate the following credentials:
   - API Key (Consumer Key)
   - API Key Secret (Consumer Secret)
   - Access Token
   - Access Token Secret
6. In your app settings, set the callback URL to: http://localhost:8000/callback
7. Update the `config.json` file with these credentials for each Twitter account

## Configuration

Edit the `config.json` file to customize the script's behavior:

```json
{
  "reddit": {
    "client_id": "YOUR_REDDIT_CLIENT_ID",
    "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
    "username": "YOUR_REDDIT_USERNAME",
    "password": "YOUR_REDDIT_PASSWORD",
    "user_agent": "RedditToTwitter Bot v1.0"
  },
  "telegram": {
    "api_id": "YOUR_TELEGRAM_API_ID",
    "api_hash": "YOUR_TELEGRAM_API_HASH",
    "phone": "YOUR_PHONE_NUMBER",
    "channels": [
      {
        "name": "channel1",
        "username": "channel_username_or_id"
      }
    ]
  },
  "twitter_accounts": [
    {
      "name": "account1",
      "consumer_key": "YOUR_TWITTER_CONSUMER_KEY",
      "consumer_secret": "YOUR_TWITTER_CONSUMER_SECRET",
      "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
      "access_token_secret": "YOUR_TWITTER_ACCESS_TOKEN_SECRET"
    }
  ],
  "subreddits": [
    "videos",
    "gifs",
    "funny"
  ],
  "posts_per_subreddit": 10,
  "messages_per_channel": 10,
  "download_dir": "downloads",
  "include_text_content": true,
  "schedule": {
    "interval": "daily",
    "time": "12:00",
    "day": "monday"
  }
}
```

### Configuration Options

- `reddit`: Reddit API credentials
- `telegram`: Telegram API credentials and channel configuration (optional)
  - `api_id`: Your Telegram API ID
  - `api_hash`: Your Telegram API hash
  - `phone`: Your phone number in international format (e.g., +12345678901)
  - `channels`: List of Telegram channels to fetch videos from
    - `name`: A name for the channel (for reference)
    - `username`: The username or ID of the channel
- `twitter_accounts`: List of Twitter accounts to post to
- `subreddits`: List of subreddits to fetch videos from
- `posts_per_subreddit`: Number of posts to check per subreddit
- `messages_per_channel`: Number of messages to check per Telegram channel
- `include_text_content`: Whether to include the post's text content in tweets (true/false)
- `download_dir`: Directory to store downloaded videos
- `schedule`: Scheduling configuration
  - `interval`: "hourly", "daily", or "weekly"
  - `time`: Time to run (for daily and weekly schedules)
  - `day`: Day of the week (for weekly schedule)

## Usage

### Web GUI

The easiest way to use the script is through the web-based GUI:

```bash
python gui.py
```

This will open a web browser with a user-friendly interface where you can:
- Set up OAuth authentication for Reddit, Twitter, and Telegram
- View and manage your configuration
- Run the script once or as a scheduled service
- Monitor logs in real-time

### OAuth Setup

To set up your API credentials using the OAuth helper:

```bash
python social_media_to_twitter.py --setup
```

This interactive tool will guide you through:
1. Setting up Reddit OAuth
2. Setting up Twitter OAuth
3. Setting up Telegram Authentication
4. Adding Telegram Channels
5. Viewing your current configuration

### Run Once

To run the script once and exit:

```bash
python social_media_to_twitter.py --run-once
```

### Telegram Authentication

When using Telegram functionality for the first time, you'll need to authenticate:

1. Run the script:
```bash
python social_media_to_twitter.py --run-once
```

2. The script will send an authentication code to your phone number
3. Run the script again with the code:
```bash
python social_media_to_twitter.py --telegram-code YOUR_CODE
```

After successful authentication, the script will create a session file and you won't need to authenticate again.

### Run as a Scheduled Service

To run the script as a scheduled service:

```bash
python social_media_to_twitter.py
```

The script will run according to the schedule specified in the configuration file.

### Using a Custom Configuration File

To use a custom configuration file:

```bash
python social_media_to_twitter.py --config my_config.json
```

## Setting Up as a System Service

### Linux (systemd)

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/social-media-to-twitter.service
```

2. Add the following content (adjust paths as needed):

```
[Unit]
Description=Social Media to Twitter Video Reposter
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/social_media_to_twitter
ExecStart=/usr/bin/python3 /path/to/social_media_to_twitter/social_media_to_twitter.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl enable social-media-to-twitter.service
sudo systemctl start social-media-to-twitter.service
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create a new task
3. Set the trigger according to your schedule
4. Set the action to start a program:
   - Program/script: `python`
   - Arguments: `C:\path\to\social_media_to_twitter\social_media_to_twitter.py`
   - Start in: `C:\path\to\social_media_to_twitter`

## Troubleshooting

### Common Issues

1. **Reddit API Rate Limiting**
   - Error: "Too many requests"
   - Solution: Decrease the number of posts per subreddit or increase the sleep time between requests

2. **Twitter API Rate Limiting**
   - Error: "Rate limit exceeded"
   - Solution: Decrease the frequency of posts or distribute posts across more Twitter accounts

3. **Video Download Failures**
   - Error: "Failed to download video"
   - Solution: Check if the video URL is accessible and if the script has permission to write to the download directory

4. **Telegram Authentication Issues**
   - Error: "Phone number invalid" or "Code invalid"
   - Solution: Make sure you're using the correct phone number format (with country code) and the correct authentication code

### Logs

Check the `social_media_to_twitter.log` file for detailed information about the script's operation and any errors that occur.

## License

This project is licensed under the MIT License - see the LICENSE file for details.