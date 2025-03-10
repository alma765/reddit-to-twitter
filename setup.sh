#!/bin/bash
# Setup script for Reddit to Twitter Video Reposter

echo "Setting up Reddit to Twitter Video Reposter..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

# Create config.json if it doesn't exist
if [ ! -f config.json ]; then
    echo "Creating config.json from template..."
    cp config.json.template config.json
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create config.json."
        exit 1
    fi
    echo "Please edit config.json with your Reddit and Twitter API credentials."
fi

# Create downloads directory
echo "Creating downloads directory..."
mkdir -p downloads

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your Reddit and Twitter API credentials"
echo "2. Run the script with: python reddit_to_twitter.py"
echo ""
echo "For more information, see README.md"