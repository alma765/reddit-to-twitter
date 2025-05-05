#!/usr/bin/env python3
"""
Social Media to Twitter Video Reposter

This script automatically fetches video posts from specified subreddits and Telegram channels
and reposts them to one or multiple Twitter accounts.
"""

import os
import json
import time
import logging
import argparse
import requests
import schedule
from datetime import datetime
import praw
import tweepy
import urllib.parse
import asyncio
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, MessageMediaWebPage
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("social_media_to_twitter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SocialMediaToTwitter:
    def __init__(self, config_path="config.json"):
        """Initialize the Social Media to Twitter reposter with the given configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self.reddit = self._init_reddit()
        self.twitter_clients = self._init_twitter_clients()
        self.telegram = self._init_telegram()
        self.download_dir = Path(self.config.get("download_dir", "downloads"))
        self.download_dir.mkdir(exist_ok=True)
        self.posted_videos = self._load_posted_videos()

    def _load_config(self):
        """Load configuration from the config file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise

    def _init_reddit(self):
        """Initialize the Reddit API client."""
        try:
            reddit_config = self.config.get("reddit", {})
            return praw.Reddit(
                client_id=reddit_config.get("client_id"),
                client_secret=reddit_config.get("client_secret"),
                user_agent=reddit_config.get("user_agent", "SocialMediaToTwitter Bot v1.0"),
                username=reddit_config.get("username"),
                password=reddit_config.get("password")
            )
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise

    def _init_telegram(self):
        """Initialize the Telegram client."""
        try:
            telegram_config = self.config.get("telegram", {})
            if not telegram_config or not telegram_config.get("api_id") or not telegram_config.get("api_hash"):
                logger.warning("Telegram configuration not found or incomplete. Telegram functionality will be disabled.")
                return None
            
            # Create the client but don't connect yet (we'll do that asynchronously when needed)
            client = TelegramClient(
                'social_media_to_twitter_session',
                telegram_config.get("api_id"),
                telegram_config.get("api_hash")
            )
            
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return None

    def _init_twitter_clients(self):
        """Initialize Twitter API clients for each account."""
        twitter_clients = {}
        twitter_accounts = self.config.get("twitter_accounts", [])
        
        for account in twitter_accounts:
            try:
                client = tweepy.Client(
                    consumer_key=account.get("consumer_key"),
                    consumer_secret=account.get("consumer_secret"),
                    access_token=account.get("access_token"),
                    access_token_secret=account.get("access_token_secret")
                )
                # Create auth for media upload
                auth = tweepy.OAuth1UserHandler(
                    account.get("consumer_key"),
                    account.get("consumer_secret"),
                    account.get("access_token"),
                    account.get("access_token_secret")
                )
                api = tweepy.API(auth)
                
                twitter_clients[account.get("name")] = {
                    "client": client,
                    "api": api
                }
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client for {account.get('name')}: {e}")
        
        return twitter_clients

    def _load_posted_videos(self):
        """Load the list of already posted videos."""
        posted_file = Path("posted_videos.json")
        if posted_file.exists():
            try:
                with open(posted_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load posted videos: {e}")
                return {}
        return {}

    def _save_posted_videos(self):
        """Save the list of posted videos."""
        try:
            with open("posted_videos.json", 'w') as f:
                json.dump(self.posted_videos, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save posted videos: {e}")

    def download_video(self, post):
        """Download a video from a Reddit post."""
        try:
            # Handle different types of Reddit video posts
            video_url = None
            
            # Direct video hosted on Reddit
            if hasattr(post, 'is_video') and post.is_video:
                if hasattr(post, 'media') and post.media:
                    video_url = post.media['reddit_video']['fallback_url']
            
            # External video (e.g., YouTube, Vimeo)
            elif post.domain.startswith(('youtube.com', 'youtu.be', 'vimeo.com')):
                logger.info(f"External video from {post.domain} not supported yet")
                return None
            
            # Gfycat
            elif 'gfycat.com' in post.url:
                gfycat_id = post.url.split('/')[-1]
                gfycat_api_url = f"https://api.gfycat.com/v1/gfycats/{gfycat_id}"
                response = requests.get(gfycat_api_url)
                if response.status_code == 200:
                    data = response.json()
                    video_url = data['gfyItem']['mp4Url']
            
            # Imgur
            elif 'imgur.com' in post.url and ('.gifv' in post.url or '.mp4' in post.url):
                video_url = post.url.replace('.gifv', '.mp4')
            
            if not video_url:
                logger.info(f"No video URL found for post: {post.id}")
                return None
            
            # Download the video
            video_path = self.download_dir / f"{post.id}.mp4"
            response = requests.get(video_url, stream=True)
            
            if response.status_code == 200:
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Downloaded video: {video_path}")
                return video_path
            else:
                logger.error(f"Failed to download video: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None

    async def download_telegram_video(self, message, channel_name):
        """Download a video from a Telegram message."""
        try:
            # Check if the message contains a video
            if not message.media:
                return None
            
            is_video = False
            
            # Check for different types of media
            if isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                for attr in document.attributes:
                    if hasattr(attr, 'round_message') or hasattr(attr, 'supports_streaming'):
                        is_video = True
                        break
            elif isinstance(message.media, MessageMediaWebPage) and hasattr(message.media.webpage, 'document'):
                document = message.media.webpage.document
                for attr in document.attributes:
                    if hasattr(attr, 'round_message') or hasattr(attr, 'supports_streaming'):
                        is_video = True
                        break
            
            if not is_video:
                return None
            
            # Generate a unique ID for the message
            message_id = f"telegram_{channel_name}_{message.id}"
            video_path = self.download_dir / f"{message_id}.mp4"
            
            # Download the media
            await self.telegram.download_media(message, file=str(video_path))
            
            if video_path.exists():
                logger.info(f"Downloaded Telegram video: {video_path}")
                return video_path, message_id
            else:
                logger.error(f"Failed to download Telegram video")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading Telegram video: {e}")
            return None

    def post_to_twitter(self, video_path, post, account_name):
        """Post a video to a Twitter account."""
        try:
            if account_name not in self.twitter_clients:
                logger.error(f"Twitter account not found: {account_name}")
                return False
            
            twitter_api = self.twitter_clients[account_name]["api"]
            twitter_client = self.twitter_clients[account_name]["client"]
            
            # Create tweet text with post title
            tweet_text = f"{post.title}"
            
            # Add post text content if available and enabled in config
            include_text_content = self.config.get("include_text_content", False)
            if include_text_content and hasattr(post, 'selftext') and post.selftext:
                # Truncate selftext if it's too long
                max_selftext_length = 150  # Reasonable length for tweet
                selftext = post.selftext.strip()
                if len(selftext) > max_selftext_length:
                    selftext = selftext[:max_selftext_length] + "..."
                
                tweet_text += f"\n\n{selftext}"
            
            tweet_text += f"\n\nSource: https://reddit.com{post.permalink}"
            
            # Upload media
            try:
                logger.info(f"Uploading media to Twitter for post {post.id}...")
                media = twitter_api.media_upload(
                    filename=str(video_path),
                    media_category='tweet_video'
                )
                logger.info(f"Media uploaded successfully, media_id: {media.media_id}")
                
                # Wait for media processing
                logger.info("Waiting for media processing...")
                time.sleep(5)  # Wait for initial processing
                
                # Check media status
                status = twitter_api.get_media_upload_status(media.media_id)
                while status.processing_info and status.processing_info['state'] in ['pending', 'in_progress']:
                    logger.info(f"Media still processing: {status.processing_info['state']}")
                    time.sleep(5)
                    status = twitter_api.get_media_upload_status(media.media_id)
                
                if status.processing_info and status.processing_info['state'] == 'failed':
                    logger.error(f"Media processing failed: {status.processing_info.get('error', {}).get('message', 'Unknown error')}")
                    return False
                
                logger.info("Media processing completed successfully")
                
            except Exception as e:
                logger.error(f"Failed to upload media to Twitter: {e}")
                return False
            
            # Post tweet with media
            try:
                logger.info(f"Creating tweet for post {post.id}...")
                response = twitter_client.create_tweet(
                    text=tweet_text[:280],  # Twitter character limit
                    media_ids=[media.media_id]
                )
                if response and hasattr(response, 'data') and response.data:
                    logger.info(f"Successfully posted to Twitter account {account_name}: {post.id}")
                    logger.info(f"Tweet URL: https://twitter.com/user/status/{response.data['id']}")
                    return True
                else:
                    logger.error(f"Tweet creation response missing data: {response}")
                    return False
            except Exception as e:
                logger.error(f"Failed to create tweet: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            return False

    def post_telegram_to_twitter(self, video_path, message, message_id, channel_name, account_name):
        """Post a Telegram video to a Twitter account."""
        try:
            if account_name not in self.twitter_clients:
                logger.error(f"Twitter account not found: {account_name}")
                return False
            
            twitter_api = self.twitter_clients[account_name]["api"]
            twitter_client = self.twitter_clients[account_name]["client"]
            
            # Create tweet text with message text or a default message
            tweet_text = message.text if message.text else f"Video from {channel_name}"
            
            # Truncate if too long
            if len(tweet_text) > 250:
                tweet_text = tweet_text[:250] + "..."
            
            # Add source
            tweet_text += f"\n\nSource: Telegram channel {channel_name}"
            
            # Upload media
            media = twitter_api.media_upload(filename=str(video_path))
            
            # Post tweet with media
            twitter_client.create_tweet(
                text=tweet_text[:280],  # Twitter character limit
                media_ids=[media.media_id]
            )
            
            logger.info(f"Posted Telegram video to Twitter account {account_name}: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting Telegram video to Twitter: {e}")
            return False

    def process_subreddit(self, subreddit_name, limit=10):
        """Process videos from a subreddit."""
        try:
            logger.info(f"Starting to process subreddit: {subreddit_name}")
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts from the subreddit
            posts_processed = 0
            videos_found = 0
            videos_downloaded = 0
            videos_posted = 0
            
            for post in subreddit.hot(limit=limit):
                posts_processed += 1
                logger.info(f"Processing post {posts_processed}/{limit}: {post.id} - {post.title}")
                
                # Skip if already posted
                if post.id in self.posted_videos:
                    logger.info(f"Post {post.id} already posted, skipping")
                    continue
                
                # Check if it's a video
                is_video = (hasattr(post, 'is_video') and post.is_video) or any(
                    domain in post.url for domain in ['gfycat.com', 'imgur.com', 'v.redd.it']
                )
                
                if not is_video:
                    logger.info(f"Post {post.id} is not a video, skipping")
                    continue
                
                videos_found += 1
                logger.info(f"Found video post: {post.id} - {post.title}")
                
                # Download the video
                video_path = self.download_video(post)
                if not video_path:
                    logger.error(f"Failed to download video for post {post.id}")
                    continue
                
                videos_downloaded += 1
                logger.info(f"Successfully downloaded video for post {post.id}")
                
                # Post to each Twitter account
                posted_accounts = []
                for account_name in self.twitter_clients.keys():
                    logger.info(f"Attempting to post to Twitter account: {account_name}")
                    if self.post_to_twitter(video_path, post, account_name):
                        posted_accounts.append(account_name)
                        videos_posted += 1
                        logger.info(f"Successfully posted to Twitter account {account_name}")
                    else:
                        logger.error(f"Failed to post to Twitter account {account_name}")
                
                # Mark as posted if posted to at least one account
                if posted_accounts:
                    self.posted_videos[post.id] = {
                        "title": post.title,
                        "url": post.url,
                        "posted_at": datetime.now().isoformat(),
                        "posted_to": posted_accounts
                    }
                    self._save_posted_videos()
                    logger.info(f"Marked post {post.id} as posted to accounts: {posted_accounts}")
                else:
                    logger.error(f"Post {post.id} was not posted to any Twitter accounts")
                
                # Respect rate limits
                time.sleep(5)
            
            logger.info(f"Subreddit {subreddit_name} processing complete:")
            logger.info(f"Posts processed: {posts_processed}")
            logger.info(f"Videos found: {videos_found}")
            logger.info(f"Videos downloaded: {videos_downloaded}")
            logger.info(f"Videos posted: {videos_posted}")
                
        except Exception as e:
            logger.error(f"Error processing subreddit {subreddit_name}: {e}")
            logger.exception("Full traceback:")

    async def process_telegram_channel(self, channel_info, limit=10):
        """Process videos from a Telegram channel."""
        try:
            if not self.telegram:
                logger.warning("Telegram client not initialized. Skipping Telegram processing.")
                return
            
            channel_name = channel_info.get("name")
            channel_username = channel_info.get("username")
            
            if not channel_username:
                logger.error(f"No username provided for channel: {channel_name}")
                return
            
            # Connect to Telegram if not already connected
            if not self.telegram.is_connected():
                await self.telegram.connect()
                
                # Check if authorization is required
                if not await self.telegram.is_user_authorized():
                    telegram_config = self.config.get("telegram", {})
                    phone = telegram_config.get("phone")
                    if not phone:
                        logger.error("Phone number not provided in config. Cannot authenticate with Telegram.")
                        return
                    
                    # Send code request
                    await self.telegram.send_code_request(phone)
                    logger.warning(f"Telegram authentication required. A code has been sent to {phone}.")
                    logger.warning("Please run the script again with the --telegram-code option to provide the code.")
                    return
            
            # Get messages from the channel
            messages = await self.telegram.get_messages(channel_username, limit=limit)
            
            for message in messages:
                # Skip if already posted
                message_id = f"telegram_{channel_name}_{message.id}"
                if message_id in self.posted_videos:
                    continue
                
                # Download the video
                download_result = await self.download_telegram_video(message, channel_name)
                if not download_result:
                    continue
                
                video_path, message_id = download_result
                
                # Post to each Twitter account
                posted_accounts = []
                for account_name in self.twitter_clients.keys():
                    if self.post_telegram_to_twitter(video_path, message, message_id, channel_name, account_name):
                        posted_accounts.append(account_name)
                
                # Mark as posted if posted to at least one account
                if posted_accounts:
                    self.posted_videos[message_id] = {
                        "text": message.text if message.text else "",
                        "channel": channel_name,
                        "posted_at": datetime.now().isoformat(),
                        "posted_to": posted_accounts
                    }
                    self._save_posted_videos()
                
                # Respect rate limits
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error processing Telegram channel {channel_info.get('name')}: {e}")

    async def process_all_telegram_channels(self):
        """Process all configured Telegram channels."""
        if not self.telegram:
            return
            
        telegram_config = self.config.get("telegram", {})
        channels = telegram_config.get("channels", [])
        limit = self.config.get("messages_per_channel", 10)
        
        for channel in channels:
            logger.info(f"Processing Telegram channel: {channel.get('name')}")
            await self.process_telegram_channel(channel, limit)
        
        # Disconnect from Telegram when done
        if self.telegram and self.telegram.is_connected():
            await self.telegram.disconnect()

    def run(self):
        """Run the Social Media to Twitter reposter."""
        subreddits = self.config.get("subreddits", [])
        limit = self.config.get("posts_per_subreddit", 10)
        
        # Process Reddit subreddits
        for subreddit in subreddits:
            logger.info(f"Processing subreddit: {subreddit}")
            self.process_subreddit(subreddit, limit)
        
        # Process Telegram channels
        if self.telegram:
            asyncio.run(self.process_all_telegram_channels())

def setup_scheduler(reposter, schedule_config):
    """Set up the scheduler based on configuration."""
    interval = schedule_config.get("interval", "daily")
    time_str = schedule_config.get("time", "12:00")
    
    if interval == "hourly":
        schedule.every().hour.do(reposter.run)
    elif interval == "daily":
        schedule.every().day.at(time_str).do(reposter.run)
    elif interval == "weekly":
        day = schedule_config.get("day", "monday")
        schedule.every().week.days(day).at(time_str).do(reposter.run)
    
    logger.info(f"Scheduler set up: {interval} at {time_str}")

def main():
    """Main function to run the Social Media to Twitter reposter."""
    parser = argparse.ArgumentParser(description="Social Media to Twitter Video Reposter")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--telegram-code", help="Telegram authentication code")
    parser.add_argument("--setup", action="store_true", help="Run the OAuth setup helper")
    args = parser.parse_args()
    
    try:
        # Run OAuth setup if requested
        if args.setup:
            try:
                # Check if oauth_helper.py exists
                if not os.path.exists("oauth_helper.py"):
                    logger.error("OAuth helper not found. Please make sure oauth_helper.py is in the current directory.")
                    return 1
                
                # Import and run the OAuth helper
                spec = importlib.util.spec_from_file_location("oauth_helper", "oauth_helper.py")
                oauth_helper = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(oauth_helper)
                oauth_helper.main_menu()
                return 0
            except Exception as e:
                logger.error(f"Error running OAuth helper: {e}")
                return 1
        
        reposter = SocialMediaToTwitter(config_path=args.config)
        
        # Handle Telegram authentication if code is provided
        if args.telegram_code and reposter.telegram:
            asyncio.run(reposter.telegram.connect())
            if not asyncio.run(reposter.telegram.is_user_authorized()):
                telegram_config = reposter.config.get("telegram", {})
                phone = telegram_config.get("phone")
                if phone:
                    asyncio.run(reposter.telegram.sign_in(phone, args.telegram_code))
                    logger.info("Successfully authenticated with Telegram")
                else:
                    logger.error("Phone number not provided in config. Cannot authenticate with Telegram.")
            else:
                logger.info("Already authenticated with Telegram")
            asyncio.run(reposter.telegram.disconnect())
        
        if args.run_once:
            reposter.run()
        else:
            # Set up scheduler
            schedule_config = reposter.config.get("schedule", {"interval": "daily", "time": "12:00"})
            setup_scheduler(reposter, schedule_config)
            
            # Run scheduler
            logger.info("Starting scheduler...")
            while True:
                schedule.run_pending()
                time.sleep(60)
                
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())