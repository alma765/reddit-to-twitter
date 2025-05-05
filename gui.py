#!/usr/bin/env python3
"""
Web GUI for Social Media to Twitter Video Reposter

This module provides a web-based GUI for the Social Media to Twitter Video Reposter.
"""

import os
import json
import time
import logging
import threading
import subprocess
import webbrowser
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = "config.json"
SCRIPT_PATH = "social_media_to_twitter.py"
OAUTH_HELPER_PATH = "oauth_helper.py"
PORT = 8080

# Flask app
app = Flask(__name__)

# Global variables
process = None
log_buffer = []
is_running = False

def load_config():
    """Load configuration from the config file."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
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
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def run_script(args=None):
    """Run the script with the given arguments."""
    global process, is_running, log_buffer
    
    if is_running:
        return False
    
    is_running = True
    log_buffer = []
    
    cmd = ["python", SCRIPT_PATH]
    if args:
        cmd.extend(args)
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Start a thread to read the output
        def read_output():
            for line in iter(process.stdout.readline, ''):
                log_buffer.append(line)
                logger.info(line.strip())
            process.stdout.close()
            process.wait()
            global is_running
            is_running = False
        
        threading.Thread(target=read_output, daemon=True).start()
        return True
    except Exception as e:
        logger.error(f"Failed to run script: {e}")
        is_running = False
        return False

def run_oauth_helper():
    """Run the OAuth helper script."""
    global process, is_running, log_buffer
    
    if is_running:
        return False
    
    is_running = True
    log_buffer = []
    
    try:
        process = subprocess.Popen(
            ["python", OAUTH_HELPER_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Start a thread to read the output
        def read_output():
            for line in iter(process.stdout.readline, ''):
                log_buffer.append(line)
                logger.info(line.strip())
            process.stdout.close()
            process.wait()
            global is_running
            is_running = False
        
        threading.Thread(target=read_output, daemon=True).start()
        return True
    except Exception as e:
        logger.error(f"Failed to run OAuth helper: {e}")
        is_running = False
        return False

def create_template():
    """Create the template directory and files if they don't exist."""
    os.makedirs("templates", exist_ok=True)
    
    # Create index.html
    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Social Media to Twitter Video Reposter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .section h2 {
            margin-top: 0;
            color: #444;
        }
        .btn {
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 16px;
        }
        .btn:hover {
            background-color: #45a049;
        }
        .btn-secondary {
            background-color: #2196F3;
        }
        .btn-secondary:hover {
            background-color: #0b7dda;
        }
        .btn-danger {
            background-color: #f44336;
        }
        .btn-danger:hover {
            background-color: #d32f2f;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"], select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .log-container {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .status {
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .status-running {
            background-color: #e7f3fe;
            border-left: 6px solid #2196F3;
        }
        .status-idle {
            background-color: #f1f1f1;
            border-left: 6px solid #ccc;
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            border-radius: 4px 4px 0 0;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 16px;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #ccc;
        }
        .tabcontent {
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 4px 4px;
        }
        .visible {
            display: block;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .action-buttons {
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Social Media to Twitter Video Reposter</h1>
        
        <div class="status" id="status-container">
            <div id="status-message">Status: Idle</div>
        </div>
        
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'dashboard')">Dashboard</button>
            <button class="tablinks" onclick="openTab(event, 'config')">Configuration</button>
            <button class="tablinks" onclick="openTab(event, 'credentials')">API Credentials</button>
            <button class="tablinks" onclick="openTab(event, 'logs')">Logs</button>
        </div>
        
        <div id="dashboard" class="tabcontent visible">
            <div class="section">
                <h2>Actions</h2>
                <button class="btn" onclick="runScript(['--run-once'])">Run Once</button>
                <button class="btn btn-secondary" onclick="runScript([])">Run Scheduled</button>
                <button class="btn btn-secondary" onclick="runOAuthHelper()">Setup OAuth</button>
                <button class="btn btn-danger" onclick="stopScript()" id="stop-btn" disabled>Stop</button>
            </div>
            
            <div class="section">
                <h2>Status</h2>
                <div id="dashboard-status">
                    <p>The script is currently not running.</p>
                </div>
            </div>
        </div>
        
        <div id="config" class="tabcontent">
            <div class="section">
                <h2>Configuration</h2>
                <div id="config-content">Loading configuration...</div>
            </div>
        </div>
        
        <div id="credentials" class="tabcontent">
            <div class="section">
                <h2>Reddit API Credentials</h2>
                <form id="reddit-form">
                    <div class="form-group">
                        <label for="reddit-client-id">Client ID:</label>
                        <input type="text" id="reddit-client-id" name="client_id" placeholder="Reddit Client ID">
                    </div>
                    <div class="form-group">
                        <label for="reddit-client-secret">Client Secret:</label>
                        <input type="text" id="reddit-client-secret" name="client_secret" placeholder="Reddit Client Secret">
                    </div>
                    <div class="form-group">
                        <label for="reddit-username">Username:</label>
                        <input type="text" id="reddit-username" name="username" placeholder="Reddit Username">
                    </div>
                    <div class="form-group">
                        <label for="reddit-password">Password:</label>
                        <input type="password" id="reddit-password" name="password" placeholder="Reddit Password">
                    </div>
                    <div class="form-group">
                        <label for="reddit-user-agent">User Agent:</label>
                        <input type="text" id="reddit-user-agent" name="user_agent" value="SocialMediaToTwitter Bot v1.0">
                    </div>
                    <button type="button" class="btn" onclick="saveRedditCredentials()">Save Reddit Credentials</button>
                </form>
            </div>
            
            <div class="section">
                <h2>Twitter API Credentials</h2>
                <form id="twitter-form">
                    <div class="form-group">
                        <label for="twitter-account-name">Account Name:</label>
                        <input type="text" id="twitter-account-name" name="name" placeholder="Twitter Account Name">
                    </div>
                    <div class="form-group">
                        <label for="twitter-consumer-key">Consumer Key:</label>
                        <input type="text" id="twitter-consumer-key" name="consumer_key" placeholder="Twitter Consumer Key">
                    </div>
                    <div class="form-group">
                        <label for="twitter-consumer-secret">Consumer Secret:</label>
                        <input type="text" id="twitter-consumer-secret" name="consumer_secret" placeholder="Twitter Consumer Secret">
                    </div>
                    <div class="form-group">
                        <label for="twitter-access-token">Access Token:</label>
                        <input type="text" id="twitter-access-token" name="access_token" placeholder="Twitter Access Token">
                    </div>
                    <div class="form-group">
                        <label for="twitter-access-token-secret">Access Token Secret:</label>
                        <input type="text" id="twitter-access-token-secret" name="access_token_secret" placeholder="Twitter Access Token Secret">
                    </div>
                    <button type="button" class="btn" onclick="saveTwitterCredentials()">Save Twitter Account</button>
                </form>
                
                <div id="twitter-accounts-list" style="margin-top: 20px;">
                    <h3>Configured Twitter Accounts</h3>
                    <div id="twitter-accounts-container">Loading...</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Telegram API Credentials</h2>
                <form id="telegram-form">
                    <div class="form-group">
                        <label for="telegram-api-id">API ID:</label>
                        <input type="text" id="telegram-api-id" name="api_id" placeholder="Telegram API ID">
                    </div>
                    <div class="form-group">
                        <label for="telegram-api-hash">API Hash:</label>
                        <input type="text" id="telegram-api-hash" name="api_hash" placeholder="Telegram API Hash">
                    </div>
                    <div class="form-group">
                        <label for="telegram-phone">Phone Number:</label>
                        <input type="text" id="telegram-phone" name="phone" placeholder="Phone Number (with country code)">
                    </div>
                    <button type="button" class="btn" onclick="saveTelegramCredentials()">Save Telegram Credentials</button>
                </form>
                
                <div id="telegram-channels" style="margin-top: 20px;">
                    <h3>Telegram Channels</h3>
                    <form id="telegram-channel-form">
                        <div class="form-group">
                            <label for="telegram-channel-name">Channel Name:</label>
                            <input type="text" id="telegram-channel-name" name="name" placeholder="Channel Name">
                        </div>
                        <div class="form-group">
                            <label for="telegram-channel-username">Channel Username/ID:</label>
                            <input type="text" id="telegram-channel-username" name="username" placeholder="Channel Username or ID">
                        </div>
                        <button type="button" class="btn" onclick="addTelegramChannel()">Add Channel</button>
                    </form>
                    
                    <div id="telegram-channels-container" style="margin-top: 20px;">Loading...</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Subreddits</h2>
                <form id="subreddit-form">
                    <div class="form-group">
                        <label for="subreddit-name">Subreddit Name:</label>
                        <input type="text" id="subreddit-name" name="name" placeholder="Subreddit Name (without r/)">
                    </div>
                    <button type="button" class="btn" onclick="addSubreddit()">Add Subreddit</button>
                </form>
                
                <div id="subreddits-container" style="margin-top: 20px;">Loading...</div>
            </div>
            
            <div class="section">
                <h2>General Settings</h2>
                <form id="settings-form">
                    <div class="form-group">
                        <label for="posts-per-subreddit">Posts per Subreddit:</label>
                        <input type="number" id="posts-per-subreddit" name="posts_per_subreddit" min="1" max="100" value="10">
                    </div>
                    <div class="form-group">
                        <label for="messages-per-channel">Messages per Channel:</label>
                        <input type="number" id="messages-per-channel" name="messages_per_channel" min="1" max="100" value="10">
                    </div>
                    <div class="form-group">
                        <label for="include-text-content">Include Text Content:</label>
                        <select id="include-text-content" name="include_text_content">
                            <option value="true">Yes</option>
                            <option value="false">No</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="download-dir">Download Directory:</label>
                        <input type="text" id="download-dir" name="download_dir" value="downloads">
                    </div>
                    <div class="form-group">
                        <label for="schedule-interval">Schedule Interval:</label>
                        <select id="schedule-interval" name="interval">
                            <option value="hourly">Hourly</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="schedule-time">Schedule Time:</label>
                        <input type="text" id="schedule-time" name="time" value="12:00">
                    </div>
                    <div class="form-group" id="schedule-day-group">
                        <label for="schedule-day">Schedule Day:</label>
                        <select id="schedule-day" name="day">
                            <option value="monday">Monday</option>
                            <option value="tuesday">Tuesday</option>
                            <option value="wednesday">Wednesday</option>
                            <option value="thursday">Thursday</option>
                            <option value="friday">Friday</option>
                            <option value="saturday">Saturday</option>
                            <option value="sunday">Sunday</option>
                        </select>
                    </div>
                    <button type="button" class="btn" onclick="saveSettings()">Save Settings</button>
                </form>
            </div>
        </div>
        
        <div id="logs" class="tabcontent">
            <div class="section">
                <h2>Log Output</h2>
                <div class="log-container" id="log-output"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab functionality
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
        
        // Run script
        function runScript(args) {
            fetch('/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ args: args }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('status-container').className = 'status status-running';
                    document.getElementById('status-message').textContent = 'Status: Running';
                    document.getElementById('dashboard-status').innerHTML = '<p>The script is currently running...</p>';
                    document.getElementById('stop-btn').disabled = false;
                    
                    // Start polling for logs
                    startLogPolling();
                }
            });
        }
        
        // Run OAuth helper
        function runOAuthHelper() {
            fetch('/run-oauth', {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('status-container').className = 'status status-running';
                    document.getElementById('status-message').textContent = 'Status: Running OAuth Helper';
                    document.getElementById('dashboard-status').innerHTML = '<p>The OAuth helper is currently running...</p>';
                    document.getElementById('stop-btn').disabled = false;
                    
                    // Start polling for logs
                    startLogPolling();
                }
            });
        }
        
        // Stop script
        function stopScript() {
            fetch('/stop', {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('status-container').className = 'status status-idle';
                    document.getElementById('status-message').textContent = 'Status: Idle';
                    document.getElementById('dashboard-status').innerHTML = '<p>The script has been stopped.</p>';
                    document.getElementById('stop-btn').disabled = true;
                }
            });
        }
        
        // Load configuration
        function loadConfig() {
            fetch('/config')
            .then(response => response.json())
            .then(data => {
                let configHtml = '<div class="form-group">';
                
                // Reddit section
                configHtml += '<h3>Reddit</h3>';
                if (data.reddit && data.reddit.client_id) {
                    configHtml += '<p>✅ Reddit is configured</p>';
                } else {
                    configHtml += '<p>❌ Reddit is not configured</p>';
                }
                
                // Twitter section
                configHtml += '<h3>Twitter Accounts</h3>';
                if (data.twitter_accounts && data.twitter_accounts.length > 0) {
                    configHtml += '<table><tr><th>Name</th><th>Status</th></tr>';
                    data.twitter_accounts.forEach(account => {
                        configHtml += `<tr><td>${account.name}</td><td>✅ Configured</td></tr>`;
                    });
                    configHtml += '</table>';
                } else {
                    configHtml += '<p>❌ No Twitter accounts configured</p>';
                }
                
                // Telegram section
                configHtml += '<h3>Telegram</h3>';
                if (data.telegram && data.telegram.api_id) {
                    configHtml += '<p>✅ Telegram is configured</p>';
                    
                    // Telegram channels
                    configHtml += '<h4>Telegram Channels</h4>';
                    if (data.telegram.channels && data.telegram.channels.length > 0) {
                        configHtml += '<table><tr><th>Name</th><th>Username/ID</th></tr>';
                        data.telegram.channels.forEach(channel => {
                            configHtml += `<tr><td>${channel.name}</td><td>${channel.username}</td></tr>`;
                        });
                        configHtml += '</table>';
                    } else {
                        configHtml += '<p>❌ No Telegram channels configured</p>';
                    }
                } else {
                    configHtml += '<p>❌ Telegram is not configured</p>';
                }
                
                // Subreddits section
                configHtml += '<h3>Subreddits</h3>';
                if (data.subreddits && data.subreddits.length > 0) {
                    configHtml += '<ul>';
                    data.subreddits.forEach(subreddit => {
                        configHtml += `<li>${subreddit}</li>`;
                    });
                    configHtml += '</ul>';
                } else {
                    configHtml += '<p>❌ No subreddits configured</p>';
                }
                
                // Schedule section
                configHtml += '<h3>Schedule</h3>';
                configHtml += `<p>Interval: ${data.schedule.interval}</p>`;
                configHtml += `<p>Time: ${data.schedule.time}</p>`;
                if (data.schedule.interval === 'weekly') {
                    configHtml += `<p>Day: ${data.schedule.day}</p>`;
                }
                
                // Other settings
                configHtml += '<h3>Other Settings</h3>';
                configHtml += `<p>Posts per subreddit: ${data.posts_per_subreddit}</p>`;
                configHtml += `<p>Messages per channel: ${data.messages_per_channel}</p>`;
                configHtml += `<p>Include text content: ${data.include_text_content ? 'Yes' : 'No'}</p>`;
                configHtml += `<p>Download directory: ${data.download_dir}</p>`;
                
                configHtml += '</div>';
                
                document.getElementById('config-content').innerHTML = configHtml;
            });
        }
        
        // Save Reddit credentials
        function saveRedditCredentials() {
            const form = document.getElementById('reddit-form');
            const data = {
                client_id: form.elements.client_id.value,
                client_secret: form.elements.client_secret.value,
                username: form.elements.username.value,
                password: form.elements.password.value,
                user_agent: form.elements.user_agent.value
            };
            
            fetch('/save-reddit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Reddit credentials saved successfully!');
                    loadConfig();
                } else {
                    alert('Failed to save Reddit credentials.');
                }
            });
        }
        
        // Save Twitter credentials
        function saveTwitterCredentials() {
            const form = document.getElementById('twitter-form');
            const data = {
                name: form.elements.name.value,
                consumer_key: form.elements.consumer_key.value,
                consumer_secret: form.elements.consumer_secret.value,
                access_token: form.elements.access_token.value,
                access_token_secret: form.elements.access_token_secret.value
            };
            
            fetch('/save-twitter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Twitter account saved successfully!');
                    loadConfig();
                    loadTwitterAccounts();
                    
                    // Clear form
                    form.reset();
                } else {
                    alert('Failed to save Twitter account.');
                }
            });
        }
        
        // Save Telegram credentials
        function saveTelegramCredentials() {
            const form = document.getElementById('telegram-form');
            const data = {
                api_id: form.elements.api_id.value,
                api_hash: form.elements.api_hash.value,
                phone: form.elements.phone.value
            };
            
            fetch('/save-telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Telegram credentials saved successfully!');
                    loadConfig();
                } else {
                    alert('Failed to save Telegram credentials.');
                }
            });
        }
        
        // Add Telegram channel
        function addTelegramChannel() {
            const form = document.getElementById('telegram-channel-form');
            const data = {
                name: form.elements.name.value,
                username: form.elements.username.value
            };
            
            fetch('/add-telegram-channel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Telegram channel added successfully!');
                    loadConfig();
                    loadTelegramChannels();
                    
                    // Clear form
                    form.reset();
                } else {
                    alert('Failed to add Telegram channel.');
                }
            });
        }
        
        // Add subreddit
        function addSubreddit() {
            const form = document.getElementById('subreddit-form');
            const data = {
                name: form.elements.name.value
            };
            
            fetch('/add-subreddit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Subreddit added successfully!');
                    loadConfig();
                    loadSubreddits();
                    
                    // Clear form
                    form.reset();
                } else {
                    alert('Failed to add subreddit.');
                }
            });
        }
        
        // Save settings
        function saveSettings() {
            const form = document.getElementById('settings-form');
            const data = {
                posts_per_subreddit: parseInt(form.elements.posts_per_subreddit.value),
                messages_per_channel: parseInt(form.elements.messages_per_channel.value),
                include_text_content: form.elements.include_text_content.value === 'true',
                download_dir: form.elements.download_dir.value,
                schedule: {
                    interval: form.elements.interval.value,
                    time: form.elements.time.value,
                    day: form.elements.day.value
                }
            };
            
            fetch('/save-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Settings saved successfully!');
                    loadConfig();
                } else {
                    alert('Failed to save settings.');
                }
            });
        }
        
        // Load Twitter accounts
        function loadTwitterAccounts() {
            fetch('/config')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('twitter-accounts-container');
                
                if (data.twitter_accounts && data.twitter_accounts.length > 0) {
                    let html = '<table><tr><th>Name</th><th>Actions</th></tr>';
                    
                    data.twitter_accounts.forEach(account => {
                        html += `<tr>
                            <td>${account.name}</td>
                            <td>
                                <button class="btn btn-danger" onclick="removeTwitterAccount('${account.name}')">Remove</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</table>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<p>No Twitter accounts configured</p>';
                }
            });
        }
        
        // Load Telegram channels
        function loadTelegramChannels() {
            fetch('/config')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('telegram-channels-container');
                
                if (data.telegram && data.telegram.channels && data.telegram.channels.length > 0) {
                    let html = '<table><tr><th>Name</th><th>Username/ID</th><th>Actions</th></tr>';
                    
                    data.telegram.channels.forEach(channel => {
                        html += `<tr>
                            <td>${channel.name}</td>
                            <td>${channel.username}</td>
                            <td>
                                <button class="btn btn-danger" onclick="removeTelegramChannel('${channel.name}')">Remove</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</table>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<p>No Telegram channels configured</p>';
                }
            });
        }
        
        // Load subreddits
        function loadSubreddits() {
            fetch('/config')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('subreddits-container');
                
                if (data.subreddits && data.subreddits.length > 0) {
                    let html = '<table><tr><th>Name</th><th>Actions</th></tr>';
                    
                    data.subreddits.forEach(subreddit => {
                        html += `<tr>
                            <td>${subreddit}</td>
                            <td>
                                <button class="btn btn-danger" onclick="removeSubreddit('${subreddit}')">Remove</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</table>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<p>No subreddits configured</p>';
                }
            });
        }
        
        // Remove Twitter account
        function removeTwitterAccount(name) {
            if (confirm(`Are you sure you want to remove Twitter account "${name}"?`)) {
                fetch('/remove-twitter-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Twitter account removed successfully!');
                        loadConfig();
                        loadTwitterAccounts();
                    } else {
                        alert('Failed to remove Twitter account.');
                    }
                });
            }
        }
        
        // Remove Telegram channel
        function removeTelegramChannel(name) {
            if (confirm(`Are you sure you want to remove Telegram channel "${name}"?`)) {
                fetch('/remove-telegram-channel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Telegram channel removed successfully!');
                        loadConfig();
                        loadTelegramChannels();
                    } else {
                        alert('Failed to remove Telegram channel.');
                    }
                });
            }
        }
        
        // Remove subreddit
        function removeSubreddit(name) {
            if (confirm(`Are you sure you want to remove subreddit "${name}"?`)) {
                fetch('/remove-subreddit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Subreddit removed successfully!');
                        loadConfig();
                        loadSubreddits();
                    } else {
                        alert('Failed to remove subreddit.');
                    }
                });
            }
        }
        
        // Show/hide schedule day based on interval
        function updateScheduleDayVisibility() {
            const interval = document.getElementById('schedule-interval').value;
            const dayGroup = document.getElementById('schedule-day-group');
            
            if (interval === 'weekly') {
                dayGroup.style.display = 'block';
            } else {
                dayGroup.style.display = 'none';
            }
        }
        
        // Poll for status and logs
        function startLogPolling() {
            const logInterval = setInterval(() => {
                fetch('/status')
                .then(response => response.json())
                .then(data => {
                    // Update logs
                    const logOutput = document.getElementById('log-output');
                    logOutput.innerHTML = data.logs.join('');
                    logOutput.scrollTop = logOutput.scrollHeight;
                    
                    // Check if script is still running
                    if (!data.running) {
                        clearInterval(logInterval);
                        document.getElementById('status-container').className = 'status status-idle';
                        document.getElementById('status-message').textContent = 'Status: Idle';
                        document.getElementById('dashboard-status').innerHTML = '<p>The script has completed.</p>';
                        document.getElementById('stop-btn').disabled = true;
                        
                        // Reload config after script completes
                        loadConfig();
                    }
                });
            }, 1000);
        }
        
        // Initial load
        document.addEventListener('DOMContentLoaded', function() {
            loadConfig();
            loadTwitterAccounts();
            loadTelegramChannels();
            loadSubreddits();
            
            // Set up event listeners
            document.getElementById('schedule-interval').addEventListener('change', updateScheduleDayVisibility);
            updateScheduleDayVisibility();
            
            // Check initial status
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.running) {
                    document.getElementById('status-container').className = 'status status-running';
                    document.getElementById('status-message').textContent = 'Status: Running';
                    document.getElementById('dashboard-status').innerHTML = '<p>The script is currently running...</p>';
                    document.getElementById('stop-btn').disabled = false;
                    startLogPolling();
                }
            });
        });
    </script>
</body>
</html>""")

# Flask routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run():
    """Run the script."""
    data = request.json
    args = data.get('args', [])
    success = run_script(args)
    return jsonify({'success': success})

@app.route('/run-oauth', methods=['POST'])
def run_oauth():
    """Run the OAuth helper."""
    success = run_oauth_helper()
    return jsonify({'success': success})

@app.route('/stop', methods=['POST'])
def stop():
    """Stop the script."""
    global process, is_running
    if process and is_running:
        process.terminate()
        is_running = False
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/status')
def status():
    """Get the status of the script."""
    global is_running, log_buffer
    return jsonify({
        'running': is_running,
        'logs': log_buffer
    })

@app.route('/config')
def config():
    """Get the configuration."""
    config = load_config()
    # Mask passwords and secrets
    if 'reddit' in config and 'password' in config['reddit']:
        config['reddit']['password'] = '********' if config['reddit']['password'] else ''
    if 'reddit' in config and 'client_secret' in config['reddit']:
        config['reddit']['client_secret'] = '********' if config['reddit']['client_secret'] else ''
    if 'telegram' in config and 'api_hash' in config['telegram']:
        config['telegram']['api_hash'] = '********' if config['telegram']['api_hash'] else ''
    for account in config.get('twitter_accounts', []):
        if 'consumer_secret' in account:
            account['consumer_secret'] = '********' if account['consumer_secret'] else ''
        if 'access_token_secret' in account:
            account['access_token_secret'] = '********' if account['access_token_secret'] else ''
    return jsonify(config)

@app.route('/save-reddit', methods=['POST'])
def save_reddit():
    """Save Reddit credentials."""
    data = request.json
    config = load_config()
    config['reddit'] = data
    save_config(config)
    return jsonify({'success': True})

@app.route('/save-twitter', methods=['POST'])
def save_twitter():
    """Save Twitter credentials."""
    data = request.json
    config = load_config()
    
    # Check if account already exists
    account_exists = False
    for i, account in enumerate(config.get('twitter_accounts', [])):
        if account.get('name') == data.get('name'):
            config['twitter_accounts'][i] = data
            account_exists = True
            break
    
    if not account_exists:
        if 'twitter_accounts' not in config:
            config['twitter_accounts'] = []
        config['twitter_accounts'].append(data)
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/save-telegram', methods=['POST'])
def save_telegram():
    """Save Telegram credentials."""
    data = request.json
    config = load_config()
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['api_id'] = data.get('api_id')
    config['telegram']['api_hash'] = data.get('api_hash')
    config['telegram']['phone'] = data.get('phone')
    
    if 'channels' not in config['telegram']:
        config['telegram']['channels'] = []
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/add-telegram-channel', methods=['POST'])
def add_telegram_channel():
    """Add a Telegram channel."""
    data = request.json
    config = load_config()
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    if 'channels' not in config['telegram']:
        config['telegram']['channels'] = []
    
    # Check if channel already exists
    channel_exists = False
    for i, channel in enumerate(config['telegram']['channels']):
        if channel.get('name') == data.get('name'):
            config['telegram']['channels'][i] = data
            channel_exists = True
            break
    
    if not channel_exists:
        config['telegram']['channels'].append(data)
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/add-subreddit', methods=['POST'])
def add_subreddit():
    """Add a subreddit."""
    data = request.json
    config = load_config()
    
    if 'subreddits' not in config:
        config['subreddits'] = []
    
    subreddit = data.get('name')
    if subreddit and subreddit not in config['subreddits']:
        config['subreddits'].append(subreddit)
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/save-settings', methods=['POST'])
def save_settings():
    """Save general settings."""
    data = request.json
    config = load_config()
    
    config['posts_per_subreddit'] = data.get('posts_per_subreddit', 10)
    config['messages_per_channel'] = data.get('messages_per_channel', 10)
    config['include_text_content'] = data.get('include_text_content', True)
    config['download_dir'] = data.get('download_dir', 'downloads')
    config['schedule'] = data.get('schedule', {
        'interval': 'daily',
        'time': '12:00',
        'day': 'monday'
    })
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/remove-twitter-account', methods=['POST'])
def remove_twitter_account():
    """Remove a Twitter account."""
    data = request.json
    config = load_config()
    
    if 'twitter_accounts' in config:
        config['twitter_accounts'] = [account for account in config['twitter_accounts'] if account.get('name') != data.get('name')]
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/remove-telegram-channel', methods=['POST'])
def remove_telegram_channel():
    """Remove a Telegram channel."""
    data = request.json
    config = load_config()
    
    if 'telegram' in config and 'channels' in config['telegram']:
        config['telegram']['channels'] = [channel for channel in config['telegram']['channels'] if channel.get('name') != data.get('name')]
    
    save_config(config)
    return jsonify({'success': True})

@app.route('/remove-subreddit', methods=['POST'])
def remove_subreddit():
    """Remove a subreddit."""
    data = request.json
    config = load_config()
    
    if 'subreddits' in config:
        config['subreddits'] = [subreddit for subreddit in config['subreddits'] if subreddit != data.get('name')]
    
    save_config(config)
    return jsonify({'success': True})

def main():
    """Main function to start the GUI."""
    # Create template directory and files
    create_template()
    
    # Open browser
    webbrowser.open(f'http://localhost:{PORT}')
    
    # Start Flask app
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()