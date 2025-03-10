#!/usr/bin/env python3
"""
Test script for Reddit to Twitter Video Reposter

This script tests the Reddit API configuration and shows what videos would be downloaded
without actually posting to Twitter.
"""

import os
import json
import logging
import argparse
import praw
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_reddit_config(config_path="config.json"):
    """Test the Reddit API configuration."""
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        reddit_config = config.get("reddit", {})
        subreddits = config.get("subreddits", [])
        
        if not subreddits:
            logger.error("No subreddits specified in config.json")
            return False
        
        # Initialize Reddit client
        try:
            reddit = praw.Reddit(
                client_id=reddit_config.get("client_id"),
                client_secret=reddit_config.get("client_secret"),
                user_agent=reddit_config.get("user_agent", "RedditToTwitter Bot v1.0"),
                username=reddit_config.get("username"),
                password=reddit_config.get("password")
            )
            
            # Test authentication
            username = reddit.user.me().name if reddit.user.me() else "Anonymous"
            logger.info(f"Successfully authenticated with Reddit as: {username}")
            
            # Test subreddit access
            for subreddit_name in subreddits:
                logger.info(f"Testing access to r/{subreddit_name}...")
                subreddit = reddit.subreddit(subreddit_name)
                
                video_count = 0
                for post in subreddit.hot(limit=5):
                    is_video = False
                    
                    # Check if it's a video
                    if hasattr(post, 'is_video') and post.is_video:
                        is_video = True
                    elif any(domain in post.url for domain in ['gfycat.com', 'imgur.com', 'v.redd.it']):
                        is_video = True
                    
                    if is_video:
                        video_count += 1
                        logger.info(f"Found video: {post.title} ({post.url})")
                
                logger.info(f"Found {video_count} videos in r/{subreddit_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Reddit authentication failed: {e}")
            return False
            
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        return False
    except Exception as e:
        logger.error(f"Error testing Reddit configuration: {e}")
        return False

def test_twitter_config(config_path="config.json"):
    """Test the Twitter API configuration (without posting)."""
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        twitter_accounts = config.get("twitter_accounts", [])
        
        if not twitter_accounts:
            logger.error("No Twitter accounts specified in config.json")
            return False
        
        # Check Twitter account configurations
        for account in twitter_accounts:
            name = account.get("name", "Unknown")
            logger.info(f"Checking Twitter account configuration: {name}")
            
            # Check if all required fields are present
            required_fields = ["consumer_key", "consumer_secret", "access_token", "access_token_secret"]
            missing_fields = [field for field in required_fields if not account.get(field)]
            
            if missing_fields:
                logger.error(f"Missing required fields for Twitter account {name}: {', '.join(missing_fields)}")
                return False
            else:
                logger.info(f"Twitter account {name} configuration looks good")
        
        return True
        
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        return False
    except Exception as e:
        logger.error(f"Error testing Twitter configuration: {e}")
        return False

def main():
    """Main function to test the configuration."""
    parser = argparse.ArgumentParser(description="Test Reddit to Twitter Video Reposter Configuration")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    logger.info("Testing Reddit to Twitter Video Reposter configuration...")
    
    # Test Reddit configuration
    logger.info("Testing Reddit API configuration...")
    reddit_ok = test_reddit_config(args.config)
    
    # Test Twitter configuration
    logger.info("Testing Twitter API configuration...")
    twitter_ok = test_twitter_config(args.config)
    
    # Summary
    logger.info("Configuration test summary:")
    logger.info(f"Reddit API: {'OK' if reddit_ok else 'FAILED'}")
    logger.info(f"Twitter API: {'OK' if twitter_ok else 'FAILED'}")
    
    if reddit_ok and twitter_ok:
        logger.info("All configurations look good! You can now run the main script.")
        return 0
    else:
        logger.error("Configuration test failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())