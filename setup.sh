#!/bin/bash

# Configuration and Environment Setup Script for Manhwa Video Generator
# Author: Jatin Mudiraj (via Antigravity AI)

# Color Codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Starting Environment Setup for Manhwa Generator ---${NC}"

# ... (rest of setup.sh)
if ! command -v ffmpeg &> /dev/null
then
    echo -e "${RED}Error: FFmpeg is not installed.${NC} Please install it."
    exit 1
fi

if ! command -v python3 &> /dev/null
then
    echo -e "${RED}Error: Python3 is not installed.${NC}"
    exit 1
fi

if [ ! -d "audio_env" ]; then
    echo "Creating virtual environment 'audio_env'..."
    python3 -m venv audio_env
fi

source audio_env/bin/activate

pip install --upgrade pip
if [ -f "requirements_audio.txt" ]; then
    pip install -r requirements_audio.txt
else
    pip install pydub requests assemblyai edge-tts
fi

mkdir -p clips
mkdir -p generated_audio
mkdir -p video_generated
mkdir -p temp_assembly
mkdir -p audio_sample

echo -e "${GREEN}--- Setup Complete! ---${NC}"
echo "To begin generating videos, run:"
echo -e "${GREEN}source audio_env/bin/activate${NC}"
echo "Then update your story_config.json and run:"
echo -e "${GREEN}python video_maker_v2.py${NC}"
echo -e "\n${RED}NOTE:${NC} Ensure this folder is a sibling of your 'image_gen' folder for image-sync features to work correctly."
