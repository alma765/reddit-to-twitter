#!/usr/bin/env python3
"""
Reddit to Twitter Video Reposter

This script automatically fetches video posts from specified subreddits and reposts them
to one or multiple Twitter accounts.
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
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reddit_to_twitter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditToTwitter:
    def __init__(self, config_path="config.json"):
        """Initialize the Reddit to Twitter reposter with the given configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self.reddit = self._init_reddit()
        self.twitter_clients = self._init_twitter_clients()
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
                user_agent=reddit_config.get("user_agent", "RedditToTwitter Bot v1.0"),
                username=reddit_config.get("username"),
                password=reddit_config.get("password")
            )
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise

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

    def post_to_twitter(self, video_path, post, account_name):
        """Post a video to a Twitter account."""
        try:
            if account_name not in self.twitter_clients:
                logger.error(f"Twitter account not found: {account_name}")
                return False
            
            twitter_api = self.twitter_clients[account_name]["api"]
            twitter_client = self.twitter_clients[account_name]["client"]
            
            # Create tweet text
            tweet_text = f"{post.title}\n\nSource: https://reddit.com{post.permalink}"
            
            # Upload media
            media = twitter_api.media_upload(filename=str(video_path))
            
            # Post tweet with media
            twitter_client.create_tweet(
                text=tweet_text[:280],  # Twitter character limit
                media_ids=[media.media_id]
            )
            
            logger.info(f"Posted to Twitter account {account_name}: {post.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            return False

    def process_subreddit(self, subreddit_name, limit=10):
        """Process videos from a subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts from the subreddit
            for post in subreddit.hot(limit=limit):
                # Skip if already posted
                if post.id in self.posted_videos:
                    continue
                
                # Skip if not a video
                if not (hasattr(post, 'is_video') and post.is_video) and not any(
                    domain in post.url for domain in ['gfycat.com', 'imgur.com', 'v.redd.it']
                ):
                    continue
                
                # Download the video
                video_path = self.download_video(post)
                if not video_path:
                    continue
                
                # Post to each Twitter account
                posted_accounts = []
                for account_name in self.twitter_clients.keys():
                    if self.post_to_twitter(video_path, post, account_name):
                        posted_accounts.append(account_name)
                
                # Mark as posted if posted to at least one account
                if posted_accounts:
                    self.posted_videos[post.id] = {
                        "title": post.title,
                        "url": post.url,
                        "posted_at": datetime.now().isoformat(),
                        "posted_to": posted_accounts
                    }
                    self._save_posted_videos()
                
                # Respect rate limits
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Error processing subreddit {subreddit_name}: {e}")

    def run(self):
        """Run the Reddit to Twitter reposter."""
        subreddits = self.config.get("subreddits", [])
        limit = self.config.get("posts_per_subreddit", 10)
        
        for subreddit in subreddits:
            logger.info(f"Processing subreddit: {subreddit}")
            self.process_subreddit(subreddit, limit)

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
    """Main function to run the Reddit to Twitter reposter."""
    parser = argparse.ArgumentParser(description="Reddit to Twitter Video Reposter")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    
    try:
        reposter = RedditToTwitter(config_path=args.config)
        
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