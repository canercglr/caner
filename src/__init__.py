"""
Speed-Drawing Explainer Video Generator

A system for creating whiteboard-style explainer videos from a single topic
using AI-generated scripts, visuals, and voiceovers.
"""

from .script_generator import ScriptGenerator
from .visual_generator import VisualGenerator
from .voiceover_generator import VoiceoverGenerator
from .video_assembler import VideoAssembler

__version__ = "1.0.0"
__all__ = [
    "ScriptGenerator",
    "VisualGenerator",
    "VoiceoverGenerator",
    "VideoAssembler",
]
