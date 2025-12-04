"""
Voiceover Generator Module

Generates text-to-speech voiceovers for explainer videos.
Supports multiple TTS providers including OpenAI and Google TTS.
"""
import io
import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass
import tempfile

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

logger = logging.getLogger(__name__)


@dataclass
class GeneratedAudio:
    """Represents a generated audio file."""
    segment_number: int
    audio_path: Path
    duration: float  # in seconds
    text: str


class VoiceoverGenerator:
    """
    Generates text-to-speech voiceovers for video narration.

    Supports:
    - OpenAI TTS (high quality)
    - Google TTS (free alternative)
    """

    # OpenAI TTS voices
    OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai",
        voice: str = "nova",
        model: str = "tts-1-hd"
    ):
        """
        Initialize the voiceover generator.

        Args:
            api_key: API key for OpenAI (if using OpenAI provider)
            provider: TTS provider ("openai" or "gtts")
            voice: Voice to use (OpenAI: alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (OpenAI: tts-1, tts-1-hd)
        """
        self.provider = provider.lower()
        self.voice = voice
        self.model = model
        self.client = None

        if self.provider == "openai":
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
            if voice not in self.OPENAI_VOICES:
                logger.warning(f"Unknown voice '{voice}', using 'nova'")
                self.voice = "nova"
        elif self.provider == "gtts":
            if gTTS is None:
                raise ImportError("gTTS package not installed. Run: pip install gtts")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        if AudioSegment is None:
            logger.warning("pydub not installed. Audio duration detection may be limited.")

        logger.info(f"Initialized VoiceoverGenerator with {provider} ({voice})")

    def generate_voiceover(
        self,
        text: str,
        segment_number: int,
        output_dir: Path,
        speed: float = 1.0
    ) -> GeneratedAudio:
        """
        Generate voiceover audio for a text segment.

        Args:
            text: Text to convert to speech
            segment_number: Segment number for naming
            output_dir: Directory to save audio
            speed: Speech speed multiplier (OpenAI only)

        Returns:
            GeneratedAudio object with audio details
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"segment_{segment_number:02d}.mp3"

        logger.info(f"Generating voiceover for segment {segment_number}")

        try:
            if self.provider == "openai":
                self._generate_openai(text, output_path, speed)
            else:
                self._generate_gtts(text, output_path)

            # Get audio duration
            duration = self._get_audio_duration(output_path)

            logger.info(f"Voiceover saved to {output_path} (duration: {duration:.1f}s)")

            return GeneratedAudio(
                segment_number=segment_number,
                audio_path=output_path,
                duration=duration,
                text=text
            )

        except Exception as e:
            logger.error(f"Failed to generate voiceover: {e}")
            raise

    def generate_all_voiceovers(
        self,
        segments: List[Dict[str, Any]],
        output_dir: Path,
        speed: float = 1.0
    ) -> List[GeneratedAudio]:
        """
        Generate voiceovers for all script segments.

        Args:
            segments: List of dicts with segment_number and text
            output_dir: Directory to save audio files
            speed: Speech speed multiplier

        Returns:
            List of GeneratedAudio objects
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        audios = []

        for segment in segments:
            audio = self.generate_voiceover(
                text=segment["text"],
                segment_number=segment["segment_number"],
                output_dir=output_dir,
                speed=speed
            )
            audios.append(audio)

        return audios

    def _generate_openai(self, text: str, output_path: Path, speed: float = 1.0) -> None:
        """Generate audio using OpenAI TTS."""
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            speed=speed
        )

        # Stream to file
        response.stream_to_file(str(output_path))

    def _generate_gtts(self, text: str, output_path: Path) -> None:
        """Generate audio using Google TTS."""
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(str(output_path))

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file in seconds."""
        if AudioSegment is not None:
            try:
                audio = AudioSegment.from_file(str(audio_path))
                return len(audio) / 1000.0  # Convert ms to seconds
            except Exception as e:
                logger.warning(f"Could not get audio duration with pydub: {e}")

        # Fallback: estimate based on file size (rough approximation)
        # MP3 at ~128kbps = ~16KB per second
        file_size = audio_path.stat().st_size
        return file_size / 16000  # Rough estimate

    def concatenate_audio(
        self,
        audio_files: List[Path],
        output_path: Path,
        pause_between: float = 0.5
    ) -> Path:
        """
        Concatenate multiple audio files with pauses between.

        Args:
            audio_files: List of audio file paths
            output_path: Output path for combined audio
            pause_between: Pause duration between segments (seconds)

        Returns:
            Path to the combined audio file
        """
        if AudioSegment is None:
            raise ImportError("pydub required for audio concatenation")

        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=int(pause_between * 1000))

        for i, audio_path in enumerate(audio_files):
            audio = AudioSegment.from_file(str(audio_path))
            combined += audio
            if i < len(audio_files) - 1:
                combined += silence

        combined.export(str(output_path), format="mp3")
        logger.info(f"Combined audio saved to {output_path}")

        return output_path


class AudioProcessor:
    """
    Additional audio processing utilities.
    """

    @staticmethod
    def adjust_speed(audio_path: Path, speed: float, output_path: Path) -> Path:
        """
        Adjust the playback speed of an audio file.

        Args:
            audio_path: Input audio file
            speed: Speed multiplier (e.g., 1.5 for 50% faster)
            output_path: Output path

        Returns:
            Path to adjusted audio
        """
        if AudioSegment is None:
            raise ImportError("pydub required for audio processing")

        audio = AudioSegment.from_file(str(audio_path))

        # Change speed by altering frame rate
        # This will also change pitch - for speed without pitch change,
        # additional processing would be needed
        new_frame_rate = int(audio.frame_rate * speed)
        adjusted = audio._spawn(audio.raw_data, overrides={
            "frame_rate": new_frame_rate
        })

        # Convert back to standard frame rate
        adjusted = adjusted.set_frame_rate(audio.frame_rate)

        adjusted.export(str(output_path), format="mp3")
        return output_path

    @staticmethod
    def add_background_music(
        voiceover_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float = -20  # dB reduction
    ) -> Path:
        """
        Add background music to a voiceover.

        Args:
            voiceover_path: Main voiceover audio
            music_path: Background music file
            output_path: Output path
            music_volume: Volume reduction for music (dB)

        Returns:
            Path to combined audio
        """
        if AudioSegment is None:
            raise ImportError("pydub required for audio processing")

        voiceover = AudioSegment.from_file(str(voiceover_path))
        music = AudioSegment.from_file(str(music_path))

        # Adjust music volume
        music = music + music_volume

        # Loop music if shorter than voiceover
        while len(music) < len(voiceover):
            music = music + music

        # Trim music to voiceover length
        music = music[:len(voiceover)]

        # Overlay
        combined = voiceover.overlay(music)

        combined.export(str(output_path), format="mp3")
        return output_path

    @staticmethod
    def normalize_audio(audio_path: Path, output_path: Path, target_dbfs: float = -20) -> Path:
        """
        Normalize audio to a target volume level.

        Args:
            audio_path: Input audio file
            output_path: Output path
            target_dbfs: Target volume in dBFS

        Returns:
            Path to normalized audio
        """
        if AudioSegment is None:
            raise ImportError("pydub required for audio processing")

        audio = AudioSegment.from_file(str(audio_path))

        change_in_dbfs = target_dbfs - audio.dBFS
        normalized = audio.apply_gain(change_in_dbfs)

        normalized.export(str(output_path), format="mp3")
        return output_path
