#!/bin/bash

# AI Podcast Producer Runner Script
# This script activates the virtual environment and runs the main application

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the main application with any provided arguments
python main.py "$@" 