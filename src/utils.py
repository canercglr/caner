"""
Utility functions for Speed-Drawing Explainer Video Generator
"""
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        name: The original filename
        max_length: Maximum length of the filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = sanitized.strip('._')

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized or "untitled"


def generate_project_id(topic: str) -> str:
    """
    Generate a unique project ID based on topic and timestamp.

    Args:
        topic: The video topic

    Returns:
        Unique project ID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
    return f"{sanitize_filename(topic)[:20]}_{timestamp}_{topic_hash}"


def create_project_directory(base_dir: Path, project_id: str) -> Dict[str, Path]:
    """
    Create a project directory structure.

    Args:
        base_dir: Base output directory
        project_id: Unique project identifier

    Returns:
        Dictionary of created directories
    """
    project_dir = base_dir / project_id

    directories = {
        "root": project_dir,
        "scripts": project_dir / "scripts",
        "visuals": project_dir / "visuals",
        "audio": project_dir / "audio",
        "temp": project_dir / "temp",
        "output": project_dir / "output",
    }

    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return directories


def save_json(data: Any, filepath: Path) -> None:
    """Save data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON to {filepath}")


def load_json(filepath: Path) -> Any:
    """Load data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def estimate_duration(text: str, words_per_minute: int = 150) -> float:
    """
    Estimate speaking duration for text.

    Args:
        text: The text to speak
        words_per_minute: Speaking speed

    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    return (word_count / words_per_minute) * 60


def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """
    Split text into chunks for API processing.

    Args:
        text: Text to split
        max_chunk_size: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def format_time(seconds: float) -> str:
    """
    Format seconds as MM:SS or HH:MM:SS.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class ProgressTracker:
    """Track and display progress for multi-step operations."""

    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description

    def update(self, step_name: str = "") -> None:
        """Update progress to next step."""
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        logger.info(f"[{percentage:.0f}%] {self.description}: {step_name}")

    def complete(self) -> None:
        """Mark progress as complete."""
        logger.info(f"[100%] {self.description}: Complete!")
