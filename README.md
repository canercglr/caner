# Speed-Drawing Explainer Video Generator

Generate whiteboard-style explainer videos from a single topic using AI-generated scripts, visuals, and voiceovers.

## Features

- **AI-Powered Script Generation**: Creates educational, well-structured scripts with visual cues
- **Whiteboard-Style Visuals**: Generates clean, hand-drawn aesthetic illustrations
- **Natural Voiceovers**: High-quality text-to-speech narration
- **Speed-Drawing Animation**: Progressive reveal effect simulating real-time drawing
- **FREE Mode**: Generate videos without any paid APIs using Gemini + PIL + Google TTS
- **Modular Pipeline**: Run individual steps or the complete pipeline

## Quick Start

### Option 1: FREE Mode (Recommended for beginners)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get your FREE Gemini API key
#    Visit: https://aistudio.google.com/app/apikey

# 3. Generate a video (completely FREE!)
python main.py "How Photosynthesis Works" --free --gemini-key YOUR_GEMINI_KEY
```

### Option 2: Premium Mode (OpenAI - higher quality)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your OpenAI API key
export OPENAI_API_KEY="your-openai-key"

# 3. Generate a video
python main.py "How Photosynthesis Works" --duration 5
```

## Usage

### FREE Mode (No cost!)

```bash
# Set Gemini key as environment variable
export GEMINI_API_KEY="your-gemini-key"

# Generate video in free mode
python main.py "Machine Learning Basics" --free

# Or pass key directly
python main.py "Machine Learning Basics" --free --gemini-key YOUR_KEY
```

### Premium Mode (OpenAI)

```bash
# Generate with default settings
python main.py "Your Topic Here"

# Specify duration and voice
python main.py "Machine Learning Basics" --duration 10 --voice echo

# Use Gemini for scripts only (OpenAI for images/voice)
python main.py "Climate Change" --provider gemini --gemini-key YOUR_KEY
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--duration, -d` | Target video duration in minutes | 5 |
| `--voice, -v` | TTS voice (OpenAI: alloy, echo, fable, onyx, nova, shimmer) | nova |
| `--provider, -p` | AI provider (openai, anthropic, gemini) | openai |
| `--free` | **FREE mode** - uses Gemini + PIL + Google TTS | False |
| `--gemini-key` | Gemini API key (or use GEMINI_API_KEY env var) | - |
| `--api-key` | OpenAI API key (or use OPENAI_API_KEY env var) | - |
| `--output, -o` | Custom output directory | ./output |
| `--no-drawing` | Disable speed-drawing animation | False |
| `--skip-script` | Use existing script | False |
| `--skip-visuals` | Use existing visuals | False |
| `--skip-audio` | Use existing audio | False |
| `--skip-video` | Skip video assembly | False |

## Mode Comparison

| Feature | FREE Mode | Premium Mode |
|---------|-----------|--------------|
| Script Generation | Gemini (free) | GPT-4 / Claude |
| Image Generation | PIL-based (free) | DALL-E 3 |
| Voice Generation | Google TTS (free) | OpenAI TTS |
| Cost | $0 | ~$0.40/video |
| Quality | Good | Excellent |
| API Key Required | Gemini (free) | OpenAI (paid) |

## Getting API Keys

### Gemini API Key (FREE)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and use with `--gemini-key` or set `GEMINI_API_KEY`

### OpenAI API Key (Paid)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account and add payment method
3. Generate an API key
4. Set `OPENAI_API_KEY` environment variable

## Project Structure

```
speed-drawing-explainer/
├── main.py                 # Main CLI application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── src/
│   ├── __init__.py
│   ├── script_generator.py    # AI script generation (OpenAI/Gemini/Anthropic)
│   ├── visual_generator.py    # Image generation (DALL-E or PIL)
│   ├── voiceover_generator.py # Text-to-speech (OpenAI or gTTS)
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

Edit `config.py` to customize default settings:

### Video Settings
```python
VIDEO_CONFIG = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "background_color": (255, 255, 255),
}
```

### AI Settings
```python
# Premium mode (OpenAI)
AI_CONFIG = {
    "script_model": "gpt-4o",
    "image_model": "dall-e-3",
    "tts_model": "tts-1-hd",
    "tts_voice": "nova",
}

# Free mode (Gemini)
GEMINI_CONFIG = {
    "script_model": "gemini-1.5-flash",  # Free tier
    "pro_model": "gemini-1.5-pro",
}
```

## Programmatic Usage

```python
from src import ScriptGenerator, VisualGenerator, VoiceoverGenerator, VideoAssembler

# FREE mode example
script_gen = ScriptGenerator(api_key="gemini-key", provider="gemini")
script = script_gen.generate("How DNS Works", duration_minutes=5)

visual_gen = VisualGenerator(free_mode=True)  # PIL-based
for segment in script.segments:
    visual_gen.generate_visual(
        description=segment.visual_description,
        segment_number=segment.segment_number,
        output_dir=Path("./visuals")
    )

voice_gen = VoiceoverGenerator(provider="gtts")  # Free Google TTS
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

## Troubleshooting

### Common Issues

**"Gemini API key required" error**
```bash
export GEMINI_API_KEY="your-key-here"
# or
python main.py "Topic" --free --gemini-key "your-key-here"
```

**"moviepy not found" error**
```bash
pip install moviepy
# Also ensure ffmpeg is installed
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

**Font rendering issues**
```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu

# macOS (fonts usually pre-installed)
brew install fontconfig
```

## Dependencies

- Python 3.8+
- FFmpeg (for video encoding)
- Gemini API key (free) OR OpenAI API key (paid)

## Cost Breakdown

### FREE Mode
| Component | Cost |
|-----------|------|
| Gemini API | $0 (free tier) |
| PIL Images | $0 (local) |
| Google TTS | $0 (free) |
| **Total** | **$0** |

### Premium Mode (~5 min video)
| Component | Cost |
|-----------|------|
| GPT-4 (script) | ~$0.05 |
| DALL-E 3 (5 images) | ~$0.20 |
| OpenAI TTS | ~$0.15 |
| **Total** | **~$0.40** |

## License

MIT License - feel free to use and modify for your projects.

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.
