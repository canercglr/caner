# Speed-Drawing Explainer Video Generator

Generate whiteboard-style explainer videos from a single topic using AI-generated scripts, visuals, and voiceovers.

## Features

- **AI-Powered Script Generation**: Creates educational, well-structured scripts with visual cues
- **Whiteboard-Style Visuals**: Generates clean, hand-drawn aesthetic illustrations using DALL-E 3
- **Natural Voiceovers**: High-quality text-to-speech using OpenAI TTS
- **Speed-Drawing Animation**: Progressive reveal effect simulating real-time drawing
- **Modular Pipeline**: Run individual steps or the complete pipeline

## Quick Start

### 1. Installation

```bash
# Clone and navigate to the project
cd speed-drawing-explainer

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 2. Generate a Video

```bash
python main.py "How Photosynthesis Works" --duration 5
```

This will generate:
- A structured script explaining the topic
- Whiteboard-style illustrations for each segment
- Professional voiceover narration
- A complete video with speed-drawing animations

## Usage

### Basic Usage

```bash
# Generate a 5-minute explainer video
python main.py "Your Topic Here"

# Specify duration
python main.py "Machine Learning Basics" --duration 10

# Choose a different voice
python main.py "Climate Change" --voice echo
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--duration, -d` | Target video duration in minutes | 5 |
| `--voice, -v` | TTS voice (alloy, echo, fable, onyx, nova, shimmer) | nova |
| `--provider, -p` | AI provider for scripts (openai, anthropic) | openai |
| `--output, -o` | Custom output directory | ./output |
| `--no-drawing` | Disable speed-drawing animation | False |
| `--api-key` | OpenAI API key (or use env var) | - |
| `--skip-script` | Use existing script | False |
| `--skip-visuals` | Use existing visuals | False |
| `--skip-audio` | Use existing audio | False |
| `--skip-video` | Skip video assembly | False |

### Examples

```bash
# Full video with custom settings
python main.py "Blockchain Technology" -d 7 -v onyx

# Use Anthropic for script generation
python main.py "Quantum Computing" --provider anthropic

# Regenerate only video from existing assets
python main.py "Previous Topic" --skip-script --skip-visuals --skip-audio

# Static images (no drawing animation)
python main.py "Solar System" --no-drawing
```

## Project Structure

```
speed-drawing-explainer/
├── main.py                 # Main CLI application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── src/
│   ├── __init__.py
│   ├── script_generator.py    # AI script generation
│   ├── visual_generator.py    # Image generation & processing
│   ├── voiceover_generator.py # Text-to-speech
│   ├── video_assembler.py     # Video assembly & animation
│   └── utils.py               # Utility functions
├── templates/
│   └── prompts/              # AI prompt templates
├── output/                   # Generated videos
└── assets/                   # Static assets
```

## Output Structure

Each generated video creates a project folder:

```
output/{project_id}/
├── scripts/
│   └── script.json         # Generated script with visual cues
├── visuals/
│   ├── title_card.png
│   ├── segment_01.png
│   ├── segment_02.png
│   └── end_card.png
├── audio/
│   ├── segment_00.mp3      # Introduction
│   ├── segment_01.mp3
│   ├── segment_02.mp3
│   └── segment_XX.mp3      # Conclusion
└── output/
    └── final_video.mp4     # Final assembled video
```

## Configuration

Edit `config.py` to customize:

### Video Settings
```python
VIDEO_CONFIG = {
    "width": 1920,          # Video width
    "height": 1080,         # Video height
    "fps": 30,              # Frames per second
    "background_color": (255, 255, 255),  # White background
}
```

### AI Settings
```python
AI_CONFIG = {
    "script_model": "gpt-4o",        # Script generation model
    "image_model": "dall-e-3",       # Image generation model
    "tts_model": "tts-1-hd",         # Text-to-speech model
    "tts_voice": "nova",             # Default voice
}
```

## API Requirements

### OpenAI API
- **Required** for image generation (DALL-E 3)
- **Required** for high-quality TTS
- **Optional** for script generation (can use Anthropic instead)

### Anthropic API
- **Optional** alternative for script generation
- Set `ANTHROPIC_API_KEY` in your `.env` file

## Programmatic Usage

```python
from src import ScriptGenerator, VisualGenerator, VoiceoverGenerator, VideoAssembler

# Generate script
script_gen = ScriptGenerator(api_key="your-key")
script = script_gen.generate("How DNS Works", duration_minutes=5)

# Generate visuals
visual_gen = VisualGenerator(api_key="your-key")
for segment in script.segments:
    visual_gen.generate_visual(
        description=segment.visual_description,
        segment_number=segment.segment_number,
        output_dir=Path("./visuals")
    )

# Generate voiceovers
voice_gen = VoiceoverGenerator(api_key="your-key", voice="nova")
for segment in script.segments:
    voice_gen.generate_voiceover(
        text=segment.narration,
        segment_number=segment.segment_number,
        output_dir=Path("./audio")
    )

# Assemble video
assembler = VideoAssembler()
assembler.assemble_video(segments, output_path=Path("./output.mp4"))
```

## Customization

### Custom Visual Styles

Modify `src/visual_generator.py` to change the whiteboard prompt:

```python
WHITEBOARD_PROMPT_PREFIX = """
Create a clean whiteboard-style illustration...
Your custom style instructions here...
"""
```

### Custom TTS Voices

Available OpenAI voices:
- `alloy` - Neutral, balanced
- `echo` - Warm, conversational
- `fable` - Expressive, storytelling
- `onyx` - Deep, authoritative
- `nova` - Friendly, professional (default)
- `shimmer` - Clear, energetic

### Animation Styles

The video assembler supports multiple reveal styles:
- `left_to_right` - Standard whiteboard reveal
- `top_to_bottom` - Top-down reveal
- `radial` - Center-out circular reveal
- `scatter` - Random pixel reveal

## Troubleshooting

### Common Issues

**"API key required" error**
```bash
export OPENAI_API_KEY="your-key-here"
# or
python main.py "Topic" --api-key "your-key-here"
```

**"moviepy not found" error**
```bash
pip install moviepy
# Also ensure ffmpeg is installed on your system
```

**Font rendering issues**
```bash
# On Ubuntu/Debian
sudo apt-get install fonts-dejavu

# On macOS (fonts usually pre-installed)
brew install fontconfig
```

## Dependencies

- Python 3.8+
- OpenAI API access
- FFmpeg (for video encoding)

## License

MIT License - feel free to use and modify for your projects.

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.
