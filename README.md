# Reddit to Twitter Video Reposter

This script automatically fetches video posts from specified subreddits and reposts them to one or multiple Twitter accounts.

## Features

- Fetch video posts from multiple subreddits
- Include post text content in tweets (optional)
- Support for Reddit-hosted videos, Gfycat, and Imgur
- Post to multiple Twitter accounts
- Configurable scheduling (hourly, daily, weekly)
- Keeps track of posted videos to avoid duplicates
- Detailed logging

## Prerequisites

- Python 3.6+
- Reddit API credentials
- Twitter API credentials

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install praw tweepy requests schedule
```

3. Copy the configuration template and edit it with your credentials:

```bash
cp config.json.template config.json
```

## Setting up Reddit API Credentials

1. Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App" button
3. Fill in the following details:
   - Name: RedditToTwitter (or any name you prefer)
   - App type: Select "script"
   - Description: A bot that reposts Reddit videos to Twitter
   - About URL: (leave blank)
   - Redirect URI: http://localhost:8080
4. Click "Create app" button
5. Note down the following information:
   - Client ID: The string under "personal use script"
   - Client Secret: The string next to "secret"
6. Update the `config.json` file with these credentials

## Setting up Twitter API Credentials

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app
3. Apply for Elevated access to get write permissions
4. Navigate to your app's "Keys and Tokens" tab
5. Generate the following credentials:
   - API Key (Consumer Key)
   - API Key Secret (Consumer Secret)
   - Access Token
   - Access Token Secret
6. Update the `config.json` file with these credentials for each Twitter account

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
- `twitter_accounts`: List of Twitter accounts to post to
- `subreddits`: List of subreddits to fetch videos from
- `posts_per_subreddit`: Number of posts to check per subreddit
- `include_text_content`: Whether to include the post's text content in tweets (true/false)
- `download_dir`: Directory to store downloaded videos
- `schedule`: Scheduling configuration
  - `interval`: "hourly", "daily", or "weekly"
  - `time`: Time to run (for daily and weekly schedules)
  - `day`: Day of the week (for weekly schedule)

## Usage

### Run Once

To run the script once and exit:

```bash
python reddit_to_twitter.py --run-once
```

### Run as a Scheduled Service

To run the script as a scheduled service:

```bash
python reddit_to_twitter.py
```

The script will run according to the schedule specified in the configuration file.

### Using a Custom Configuration File

To use a custom configuration file:

```bash
python reddit_to_twitter.py --config my_config.json
```

## Setting Up as a System Service

### Linux (systemd)

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/reddit-to-twitter.service
```

2. Add the following content (adjust paths as needed):

```
[Unit]
Description=Reddit to Twitter Video Reposter
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/reddit_to_twitter
ExecStart=/usr/bin/python3 /path/to/reddit_to_twitter/reddit_to_twitter.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl enable reddit-to-twitter.service
sudo systemctl start reddit-to-twitter.service
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create a new task
3. Set the trigger according to your schedule
4. Set the action to start a program:
   - Program/script: `python`
   - Arguments: `C:\path\to\reddit_to_twitter\reddit_to_twitter.py`
   - Start in: `C:\path\to\reddit_to_twitter`

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

### Logs

Check the `reddit_to_twitter.log` file for detailed information about the script's operation and any errors that occur.

## License

This project is licensed under the MIT License - see the LICENSE file for details.