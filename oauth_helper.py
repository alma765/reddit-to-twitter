#!/usr/bin/env python3
"""
OAuth Helper for Social Media to Twitter Video Reposter

This module handles OAuth authentication for Reddit, Twitter, and Telegram.
"""

import os
import json
import webbrowser
import time
import random
import string
import logging
import asyncio
from urllib.parse import urlencode, parse_qs
from flask import Flask, request, redirect
from requests_oauthlib import OAuth2Session
import tweepy
from telethon import TelegramClient
import pyperclip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oauth_helper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = "config.json"
REDIRECT_URI = "http://localhost:8000/callback"
SESSION_FILE = "social_media_to_twitter_session"

# Flask app for handling OAuth callbacks
app = Flask(__name__)
oauth_data = {}

def generate_random_state():
    """Generate a random state string for OAuth security."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

def load_config():
    """Load configuration from the config file."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        else:
            # Create a new config file with empty sections
            config = {
                "reddit": {},
                "twitter_accounts": [],
                "telegram": {},
                "subreddits": [],
                "posts_per_subreddit": 10,
                "messages_per_channel": 10,
                "download_dir": "downloads",
                "include_text_content": True,
                "schedule": {
                    "interval": "daily",
                    "time": "12:00",
                    "day": "monday"
                }
            }
            save_config(config)
            return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def save_config(config):
    """Save configuration to the config file."""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

# Reddit OAuth
def setup_reddit_oauth():
    """Set up Reddit OAuth."""
    print("\n=== Reddit OAuth Setup ===")
    print("1. Go to https://www.reddit.com/prefs/apps")
    print("2. Click 'Create App' or 'Create Another App' button")
    print("3. Fill in the following details:")
    print("   - Name: SocialMediaToTwitter (or any name you prefer)")
    print("   - App type: Select 'web app'")
    print("   - Description: A bot that reposts social media videos to Twitter")
    print("   - Redirect URI: http://localhost:8000/callback")
    print("4. Click 'Create app' button")
    
    client_id = input("\nEnter your Reddit Client ID: ")
    client_secret = input("Enter your Reddit Client Secret: ")
    
    # Save credentials to config first
    config = load_config()
    config["reddit"] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_agent": "SocialMediaToTwitter Bot v1.0"
    }
    save_config(config)
    
    # Set up OAuth session
    reddit_oauth = OAuth2Session(client_id, redirect_uri=REDIRECT_URI)
    
    # Build authorization URL manually to avoid scope list issue
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "identity read",
        "duration": "permanent",
        "state": generate_random_state()
    }
    authorization_url = "https://www.reddit.com/api/v1/authorize?" + urlencode(auth_params)
    state = auth_params["state"]
    
    # Save state for verification
    oauth_data["reddit_state"] = state
    
    # Open browser for authorization
    print(f"\nOpening browser for Reddit authorization...")
    webbrowser.open(authorization_url)
    
    # Start Flask app to handle callback
    app.config["SERVICE"] = "reddit"
    app.run(host="localhost", port=8000)
    
    # After callback is handled, oauth_data will contain the access token
    if "reddit_token" in oauth_data:
        config = load_config()
        config["reddit"]["refresh_token"] = oauth_data["reddit_token"]
        save_config(config)
        print("\nReddit OAuth setup completed successfully!")
        return True
    else:
        print("\nReddit OAuth setup failed.")
        return False

# Twitter OAuth
def setup_twitter_oauth():
    """Set up Twitter OAuth."""
    print("\n=== Twitter OAuth Setup ===")
    print("1. Go to https://developer.twitter.com/en/portal/dashboard")
    print("2. Create a new project and app (if you haven't already)")
    print("3. In your app settings, add http://localhost:8000/callback as a callback URL")
    print("4. Make sure your app has read and write permissions")
    
    consumer_key = input("\nEnter your Twitter API Key (Consumer Key): ")
    consumer_secret = input("Enter your Twitter API Key Secret (Consumer Secret): ")
    
    # Initialize Tweepy OAuth handler
    auth = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret,
        callback=REDIRECT_URI
    )
    
    try:
        # Get authorization URL
        auth_url = auth.get_authorization_url()
        
        # Save auth handler for later
        oauth_data["twitter_auth"] = auth
        
        # Open browser for authorization
        print(f"\nOpening browser for Twitter authorization...")
        webbrowser.open(auth_url)
        
        # Start Flask app to handle callback
        app.config["SERVICE"] = "twitter"
        app.run(host="localhost", port=8000)
        
        # After callback is handled, oauth_data will contain the access token
        if "twitter_tokens" in oauth_data:
            config = load_config()
            
            # Add a new Twitter account
            account_name = input("\nEnter a name for this Twitter account: ")
            account = {
                "name": account_name,
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "access_token": oauth_data["twitter_tokens"][0],
                "access_token_secret": oauth_data["twitter_tokens"][1]
            }
            
            # Check if account already exists
            account_exists = False
            for i, existing_account in enumerate(config["twitter_accounts"]):
                if existing_account["name"] == account_name:
                    config["twitter_accounts"][i] = account
                    account_exists = True
                    break
            
            if not account_exists:
                config["twitter_accounts"].append(account)
            
            save_config(config)
            print("\nTwitter OAuth setup completed successfully!")
            return True
        else:
            print("\nTwitter OAuth setup failed.")
            return False
    except Exception as e:
        logger.error(f"Twitter OAuth setup failed: {e}")
        print(f"\nTwitter OAuth setup failed: {e}")
        return False

# Telegram Authentication
async def setup_telegram_auth():
    """Set up Telegram authentication."""
    print("\n=== Telegram Authentication Setup ===")
    print("1. Go to https://my.telegram.org/apps")
    print("2. Log in with your phone number")
    print("3. Fill in the form to create a new application")
    
    api_id = input("\nEnter your Telegram API ID: ")
    api_hash = input("Enter your Telegram API Hash: ")
    phone = input("Enter your phone number (with country code, e.g., +12345678901): ")
    
    # Create Telegram client
    client = TelegramClient(SESSION_FILE, api_id, api_hash)
    
    # Connect to Telegram
    await client.connect()
    
    # Check if already authorized
    if await client.is_user_authorized():
        print("\nAlready authenticated with Telegram.")
    else:
        # Send code request
        await client.send_code_request(phone)
        code = input("\nEnter the code you received on Telegram: ")
        
        try:
            # Sign in with code
            await client.sign_in(phone, code)
            print("\nTelegram authentication successful!")
        except Exception as e:
            print(f"\nTelegram authentication failed: {e}")
            await client.disconnect()
            return False
    
    # Get user info
    me = await client.get_me()
    username = me.username if me.username else me.first_name
    
    # Disconnect
    await client.disconnect()
    
    # Save to config
    config = load_config()
    config["telegram"] = {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone,
        "username": username,
        "channels": config.get("telegram", {}).get("channels", [])
    }
    save_config(config)
    
    # Add Telegram channels
    add_channels = input("\nDo you want to add Telegram channels now? (y/n): ").lower()
    if add_channels == 'y':
        await add_telegram_channels()
    
    return True

async def add_telegram_channels():
    """Add Telegram channels to the configuration."""
    config = load_config()
    channels = config.get("telegram", {}).get("channels", [])
    
    while True:
        channel_name = input("\nEnter a name for the channel (or leave empty to finish): ")
        if not channel_name:
            break
        
        channel_username = input("Enter the channel username or ID: ")
        
        # Check if channel already exists
        channel_exists = False
        for i, existing_channel in enumerate(channels):
            if existing_channel["name"] == channel_name:
                channels[i] = {"name": channel_name, "username": channel_username}
                channel_exists = True
                break
        
        if not channel_exists:
            channels.append({"name": channel_name, "username": channel_username})
    
    config["telegram"]["channels"] = channels
    save_config(config)
    print("\nTelegram channels updated successfully!")

# Flask routes for OAuth callbacks
@app.route('/callback')
def oauth_callback():
    """Handle OAuth callbacks."""
    service = app.config.get("SERVICE")
    
    if service == "reddit":
        code = request.args.get('code')
        state = request.args.get('state')
        
        # Verify state
        if state != oauth_data.get("reddit_state"):
            return "State verification failed. Please try again."
        
        # Exchange code for token
        client_id = load_config().get("reddit", {}).get("client_id")
        client_secret = load_config().get("reddit", {}).get("client_secret")
        
        if not client_id or not client_secret:
            return "Client ID or Client Secret not found in config. Please try again."
        
        token_url = "https://www.reddit.com/api/v1/access_token"
        auth = (client_id, client_secret)
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        
        try:
            import requests
            response = requests.post(token_url, auth=auth, data=data)
            response.raise_for_status()  # Raise an exception for bad status codes
            tokens = response.json()
            
            if 'refresh_token' in tokens:
                oauth_data["reddit_token"] = tokens['refresh_token']
                return "Reddit authentication successful! You can close this window and return to the terminal."
            else:
                logger.error(f"Token response missing refresh_token: {tokens}")
                return "Failed to get Reddit refresh token. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return f"Failed to exchange code for token: {str(e)}. Please try again."
    
    elif service == "twitter":
        # Get OAuth verifier from callback
        oauth_verifier = request.args.get('oauth_verifier')
        oauth_token = request.args.get('oauth_token')
        
        logger.info(f"Twitter callback received - verifier: {oauth_verifier}, token: {oauth_token}")
        
        if not oauth_verifier:
            logger.error("No OAuth verifier received in callback")
            return "Failed to get OAuth verifier. Please try again."
        
        # Get the auth handler from oauth_data
        auth = oauth_data.get("twitter_auth")
        
        if not auth:
            logger.error("Twitter auth handler not found in oauth_data")
            return "Authentication handler not found. Please try again."
        
        # Get access token
        try:
            auth.get_access_token(oauth_verifier)
            oauth_data["twitter_tokens"] = (auth.access_token, auth.access_token_secret)
            logger.info("Successfully obtained Twitter access tokens")
            return "Twitter authentication successful! You can close this window and return to the terminal."
        except Exception as e:
            logger.error(f"Twitter token exchange failed: {e}")
            return f"Failed to get Twitter access token: {e}. Please try again."
    
    return "Unknown service. Please try again."

def main_menu():
    """Display the main menu and handle user choices."""
    while True:
        print("\n=== Social Media to Twitter OAuth Helper ===")
        print("1. Set up Reddit OAuth")
        print("2. Set up Twitter OAuth")
        print("3. Set up Telegram Authentication")
        print("4. Add Telegram Channels")
        print("5. View Current Configuration")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            setup_reddit_oauth()
        elif choice == '2':
            setup_twitter_oauth()
        elif choice == '3':
            asyncio.run(setup_telegram_auth())
        elif choice == '4':
            asyncio.run(add_telegram_channels())
        elif choice == '5':
            config = load_config()
            print("\n=== Current Configuration ===")
            
            # Reddit
            if "client_id" in config.get("reddit", {}):
                print("\nReddit: Configured")
            else:
                print("\nReddit: Not configured")
            
            # Twitter
            if config.get("twitter_accounts"):
                print(f"\nTwitter Accounts: {len(config['twitter_accounts'])} configured")
                for account in config["twitter_accounts"]:
                    print(f"  - {account['name']}")
            else:
                print("\nTwitter Accounts: None configured")
            
            # Telegram
            if "api_id" in config.get("telegram", {}):
                print("\nTelegram: Configured")
                if config.get("telegram", {}).get("channels"):
                    print(f"Telegram Channels: {len(config['telegram']['channels'])} configured")
                    for channel in config["telegram"]["channels"]:
                        print(f"  - {channel['name']} ({channel['username']})")
                else:
                    print("Telegram Channels: None configured")
            else:
                print("\nTelegram: Not configured")
            
            # Subreddits
            if config.get("subreddits"):
                print(f"\nSubreddits: {len(config['subreddits'])} configured")
                for subreddit in config["subreddits"]:
                    print(f"  - {subreddit}")
            else:
                print("\nSubreddits: None configured")
        elif choice == '6':
            print("\nExiting OAuth Helper. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()