"""
Video Assembler Module

Combines visuals, audio, and animations into final explainer videos.
Creates speed-drawing style animations with progressive reveal effects.
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import tempfile
import shutil

try:
    from moviepy.editor import (
        ImageClip, AudioFileClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip, TextClip,
        CompositeAudioClip, VideoFileClip
    )
    from moviepy.video.fx.all import fadein, fadeout, resize
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw
    import numpy as np
except ImportError:
    Image = None
    np = None

logger = logging.getLogger(__name__)


@dataclass
class VideoSegment:
    """Represents a video segment to be assembled."""
    segment_number: int
    visual_path: Path
    audio_path: Path
    duration: float
    title: Optional[str] = None


class VideoAssembler:
    """
    Assembles final explainer videos from visuals and audio.

    Features:
    - Speed-drawing reveal animations
    - Smooth transitions between segments
    - Title cards and end screens
    - Progress indicators
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ):
        """
        Initialize the video assembler.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            background_color: Background color (RGB)
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("moviepy not installed. Run: pip install moviepy")

        self.width = width
        self.height = height
        self.fps = fps
        self.background_color = background_color

        logger.info(f"Initialized VideoAssembler ({width}x{height} @ {fps}fps)")

    def assemble_video(
        self,
        segments: List[VideoSegment],
        output_path: Path,
        title: Optional[str] = None,
        include_title_card: bool = True,
        include_end_card: bool = True,
        drawing_effect: bool = True,
        transition_duration: float = 0.5
    ) -> Path:
        """
        Assemble the final video from segments.

        Args:
            segments: List of VideoSegment objects
            output_path: Path for output video
            title: Video title for title card
            include_title_card: Whether to add title card
            include_end_card: Whether to add end card
            drawing_effect: Whether to add speed-drawing reveal effect
            transition_duration: Duration of transitions between segments

        Returns:
            Path to the output video
        """
        logger.info(f"Assembling video with {len(segments)} segments")

        clips = []

        # Add title card
        if include_title_card and title:
            title_clip = self._create_title_card_clip(title, duration=3.0)
            title_clip = fadein(title_clip, 0.5)
            title_clip = fadeout(title_clip, 0.5)
            clips.append(title_clip)

        # Process each segment
        for segment in segments:
            logger.info(f"Processing segment {segment.segment_number}")

            # Create the segment clip
            if drawing_effect:
                segment_clip = self._create_drawing_clip(
                    segment.visual_path,
                    segment.audio_path,
                    segment.duration
                )
            else:
                segment_clip = self._create_simple_clip(
                    segment.visual_path,
                    segment.audio_path,
                    segment.duration
                )

            # Add transitions
            if clips:  # Not the first clip
                segment_clip = fadein(segment_clip, transition_duration)

            clips.append(segment_clip)

        # Add end card
        if include_end_card:
            end_clip = self._create_end_card_clip(duration=3.0)
            end_clip = fadein(end_clip, 0.5)
            end_clip = fadeout(end_clip, 0.5)
            clips.append(end_clip)

        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")

        # Write output
        logger.info(f"Writing video to {output_path}")
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(output_path.parent / 'temp_audio.m4a'),
            remove_temp=True,
            logger=None  # Suppress moviepy's verbose output
        )

        # Clean up
        final_video.close()
        for clip in clips:
            clip.close()

        logger.info(f"Video assembled successfully: {output_path}")
        return output_path

    def _create_simple_clip(
        self,
        visual_path: Path,
        audio_path: Path,
        duration: float
    ) -> CompositeVideoClip:
        """Create a simple clip with static image and audio."""
        # Load image and audio
        image_clip = ImageClip(str(visual_path)).set_duration(duration)
        audio_clip = AudioFileClip(str(audio_path))

        # Resize image to fit video dimensions
        image_clip = image_clip.resize((self.width, self.height))

        # Set audio
        image_clip = image_clip.set_audio(audio_clip)

        return image_clip

    def _create_drawing_clip(
        self,
        visual_path: Path,
        audio_path: Path,
        duration: float
    ) -> CompositeVideoClip:
        """
        Create a clip with speed-drawing reveal effect.

        The image progressively reveals from left to right or
        top to bottom, simulating a hand drawing on whiteboard.
        """
        # Load audio first to get accurate duration
        audio_clip = AudioFileClip(str(audio_path))
        actual_duration = audio_clip.duration

        # Load image
        img = Image.open(visual_path).convert('RGBA')
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        img_array = np.array(img)

        # Create reveal animation frames
        def make_frame(t):
            # Calculate reveal progress (0 to 1)
            # Use first 70% of duration for drawing, rest for showing complete image
            draw_duration = actual_duration * 0.7
            progress = min(1.0, t / draw_duration)

            # Create mask for progressive reveal
            mask = np.zeros((self.height, self.width), dtype=np.float32)

            # Reveal from left to right with some vertical variation
            reveal_x = int(progress * self.width)

            # Add slight wave effect for more natural look
            for y in range(self.height):
                wave_offset = int(20 * np.sin(y * 0.02 + t * 2))
                x_pos = min(self.width, max(0, reveal_x + wave_offset))
                mask[y, :x_pos] = 1.0

            # Apply soft edge
            edge_width = 50
            for x in range(max(0, reveal_x - edge_width), min(self.width, reveal_x + edge_width)):
                edge_progress = (x - (reveal_x - edge_width)) / (2 * edge_width)
                for y in range(self.height):
                    if mask[y, x] < edge_progress:
                        mask[y, x] = edge_progress

            # Create frame with white background
            frame = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255

            # Apply mask to reveal image
            mask_3d = np.stack([mask, mask, mask], axis=-1)
            frame = (frame * (1 - mask_3d) + img_array[:, :, :3] * mask_3d).astype(np.uint8)

            return frame

        # Create video clip from frames
        from moviepy.editor import VideoClip
        video_clip = VideoClip(make_frame, duration=actual_duration)
        video_clip = video_clip.set_audio(audio_clip)

        return video_clip

    def _create_title_card_clip(
        self,
        title: str,
        duration: float = 3.0,
        subtitle: Optional[str] = None
    ) -> CompositeVideoClip:
        """Create a title card clip."""
        # Create background
        bg = ColorClip(
            size=(self.width, self.height),
            color=self.background_color,
            duration=duration
        )

        # Create title text
        try:
            title_clip = TextClip(
                title,
                fontsize=70,
                color='gray',
                font='DejaVu-Sans-Bold',
                size=(self.width - 200, None),
                method='caption'
            ).set_position('center').set_duration(duration)

            clips = [bg, title_clip]

            if subtitle:
                subtitle_clip = TextClip(
                    subtitle,
                    fontsize=36,
                    color='darkgray',
                    font='DejaVu-Sans',
                    size=(self.width - 200, None),
                    method='caption'
                ).set_position(('center', self.height // 2 + 80)).set_duration(duration)
                clips.append(subtitle_clip)

            return CompositeVideoClip(clips)

        except Exception as e:
            logger.warning(f"Could not create text clip: {e}. Using simple title card.")
            # Fallback: create a simple image-based title card
            return self._create_image_title_card(title, duration)

    def _create_image_title_card(self, title: str, duration: float) -> ImageClip:
        """Create a title card as an image (fallback method)."""
        if Image is None:
            raise ImportError("Pillow required for image-based title cards")

        img = Image.new('RGB', (self.width, self.height), self.background_color)
        draw = ImageDraw.Draw(img)

        try:
            from PIL import ImageFont
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except (IOError, OSError):
            from PIL import ImageFont
            font = ImageFont.load_default()

        # Get text size and center it
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        draw.text((x, y), title, fill=(80, 80, 80), font=font)

        # Convert to numpy array
        img_array = np.array(img)

        return ImageClip(img_array).set_duration(duration)

    def _create_end_card_clip(
        self,
        duration: float = 3.0,
        text: str = "Thanks for watching!"
    ) -> CompositeVideoClip:
        """Create an end card clip."""
        return self._create_title_card_clip(text, duration)


class DrawingAnimator:
    """
    Creates drawing animation effects for whiteboard videos.

    Generates frame-by-frame animations that simulate
    hand-drawing on a whiteboard.
    """

    @staticmethod
    def create_reveal_mask(
        width: int,
        height: int,
        progress: float,
        style: str = "left_to_right"
    ) -> np.ndarray:
        """
        Create a reveal mask for animation.

        Args:
            width: Image width
            height: Image height
            progress: Animation progress (0 to 1)
            style: Reveal style

        Returns:
            Numpy array mask (0-1 float values)
        """
        if np is None:
            raise ImportError("NumPy required for animations")

        mask = np.zeros((height, width), dtype=np.float32)

        if style == "left_to_right":
            reveal_x = int(progress * width)
            mask[:, :reveal_x] = 1.0

        elif style == "top_to_bottom":
            reveal_y = int(progress * height)
            mask[:reveal_y, :] = 1.0

        elif style == "radial":
            center_x, center_y = width // 2, height // 2
            max_radius = np.sqrt(center_x**2 + center_y**2)
            current_radius = progress * max_radius

            y, x = np.ogrid[:height, :width]
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            mask = (dist <= current_radius).astype(np.float32)

        elif style == "scatter":
            # Random scatter reveal
            np.random.seed(42)  # Consistent randomness
            reveal_count = int(progress * width * height)
            indices = np.random.permutation(width * height)[:reveal_count]
            flat_mask = np.zeros(width * height, dtype=np.float32)
            flat_mask[indices] = 1.0
            mask = flat_mask.reshape((height, width))

        return mask

    @staticmethod
    def apply_drawing_effect(
        image: np.ndarray,
        progress: float,
        style: str = "left_to_right",
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> np.ndarray:
        """
        Apply drawing effect to an image.

        Args:
            image: Input image array
            progress: Animation progress (0 to 1)
            style: Reveal style
            background_color: Background color

        Returns:
            Image with drawing effect applied
        """
        height, width = image.shape[:2]
        mask = DrawingAnimator.create_reveal_mask(width, height, progress, style)

        # Create background
        bg = np.ones_like(image)
        for i, c in enumerate(background_color):
            bg[:, :, i] = c

        # Apply mask
        mask_3d = np.stack([mask, mask, mask], axis=-1)
        result = (bg * (1 - mask_3d) + image * mask_3d).astype(np.uint8)

        return result


def assemble_from_project(
    project_dir: Path,
    output_filename: str = "final_video.mp4"
) -> Path:
    """
    Convenience function to assemble video from a project directory.

    Expects the following structure:
    - project_dir/scripts/script.json
    - project_dir/visuals/segment_XX.png
    - project_dir/audio/segment_XX.mp3

    Args:
        project_dir: Project directory path
        output_filename: Name of output file

    Returns:
        Path to the assembled video
    """
    import json

    project_dir = Path(project_dir)

    # Load script
    script_path = project_dir / "scripts" / "script.json"
    with open(script_path, 'r') as f:
        script_data = json.load(f)

    # Build segments list
    segments = []
    visuals_dir = project_dir / "visuals"
    audio_dir = project_dir / "audio"

    for i, seg_data in enumerate(script_data.get("segments", []), start=1):
        visual_path = visuals_dir / f"segment_{i:02d}.png"
        audio_path = audio_dir / f"segment_{i:02d}.mp3"

        if visual_path.exists() and audio_path.exists():
            # Get audio duration
            audio_clip = AudioFileClip(str(audio_path))
            duration = audio_clip.duration
            audio_clip.close()

            segments.append(VideoSegment(
                segment_number=i,
                visual_path=visual_path,
                audio_path=audio_path,
                duration=duration,
                title=seg_data.get("title")
            ))

    # Assemble video
    assembler = VideoAssembler()
    output_path = project_dir / "output" / output_filename

    return assembler.assemble_video(
        segments=segments,
        output_path=output_path,
        title=script_data.get("topic", "Explainer Video")
    )
