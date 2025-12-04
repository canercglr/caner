"""
Configuration settings for Speed-Drawing Explainer Video Generator
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# API Keys (loaded from environment variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Video Settings
VIDEO_CONFIG = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "background_color": (255, 255, 255),  # White background (whiteboard)
    "drawing_color": (30, 30, 30),  # Dark gray for drawings
    "accent_colors": [
        (66, 133, 244),   # Blue
        (234, 67, 53),    # Red
        (251, 188, 5),    # Yellow
        (52, 168, 83),    # Green
    ],
    "font_color": (50, 50, 50),
}

# Audio Settings
AUDIO_CONFIG = {
    "sample_rate": 44100,
    "channels": 2,
    "format": "mp3",
    "voice_speed": 1.0,
    "voice_language": "en",
}

# Script Generation Settings
SCRIPT_CONFIG = {
    "max_segments": 10,
    "min_segment_duration": 5,  # seconds
    "max_segment_duration": 30,  # seconds
    "words_per_minute": 150,  # Average speaking speed
}

# Visual Generation Settings
VISUAL_CONFIG = {
    "style": "whiteboard",
    "image_size": "1024x1024",
    "quality": "hd",
    "drawing_speed": 2.0,  # Speed multiplier for drawing animation
}

# Default AI Model Settings
AI_CONFIG = {
    "script_model": "gpt-4o",
    "image_model": "dall-e-3",
    "tts_model": "tts-1-hd",
    "tts_voice": "alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
}
