"""
Visual Generator Module

Generates whiteboard-style illustrations and drawings for explainer videos.
Uses AI image generation and image processing to create sketch-like visuals.
"""
import io
import logging
import requests
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import base64

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
except ImportError:
    Image = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


@dataclass
class GeneratedVisual:
    """Represents a generated visual/image."""
    segment_number: int
    image_path: Path
    description: str
    width: int
    height: int


class VisualGenerator:
    """
    Generates whiteboard-style visuals for explainer videos.

    Supports:
    - AI image generation (DALL-E, etc.)
    - Image-to-sketch conversion
    - Text overlay rendering
    """

    WHITEBOARD_PROMPT_PREFIX = """
Create a clean whiteboard-style educational illustration with the following characteristics:
- White or light cream background (like a whiteboard)
- Simple black or dark gray line drawings
- Hand-drawn sketch aesthetic
- Clear, educational diagram style
- No shadows or 3D effects
- Minimal color accents (blue, red, green highlights only if needed)
- Include simple icons, diagrams, arrows, and hand-written style text labels
- Professional but approachable educational style

Illustration content: """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "dall-e-3",
        image_size: str = "1792x1024"
    ):
        """
        Initialize the visual generator.

        Args:
            api_key: OpenAI API key
            model: Image generation model
            image_size: Output image size
        """
        if OpenAI is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        if Image is None:
            raise ImportError("Pillow package not installed. Run: pip install Pillow")

        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = model
        self.image_size = image_size

        logger.info(f"Initialized VisualGenerator with {model}")

    def generate_visual(
        self,
        description: str,
        segment_number: int,
        output_dir: Path,
        style: str = "whiteboard"
    ) -> GeneratedVisual:
        """
        Generate a visual for a script segment.

        Args:
            description: Visual description from script
            segment_number: Segment number for naming
            output_dir: Directory to save the image
            style: Visual style ("whiteboard", "sketch", "diagram")

        Returns:
            GeneratedVisual object with image details
        """
        # Construct the prompt
        if style == "whiteboard":
            prompt = self.WHITEBOARD_PROMPT_PREFIX + description
        else:
            prompt = f"Educational {style} illustration: {description}"

        # Ensure prompt isn't too long
        prompt = prompt[:4000]

        logger.info(f"Generating visual for segment {segment_number}")

        try:
            # Generate image using DALL-E
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.image_size,
                quality="hd" if self.model == "dall-e-3" else "standard",
                n=1,
                response_format="url"
            )

            image_url = response.data[0].url

            # Download the image
            image_response = requests.get(image_url)
            image = Image.open(io.BytesIO(image_response.content))

            # Apply whiteboard post-processing
            if style == "whiteboard":
                image = self._apply_whiteboard_effect(image)

            # Save the image
            output_path = output_dir / f"segment_{segment_number:02d}.png"
            image.save(output_path, "PNG")

            logger.info(f"Visual saved to {output_path}")

            return GeneratedVisual(
                segment_number=segment_number,
                image_path=output_path,
                description=description,
                width=image.width,
                height=image.height
            )

        except Exception as e:
            logger.error(f"Failed to generate visual: {e}")
            # Create a placeholder image
            return self._create_placeholder(segment_number, description, output_dir)

    def generate_all_visuals(
        self,
        visual_descriptions: List[Dict[str, Any]],
        output_dir: Path,
        style: str = "whiteboard"
    ) -> List[GeneratedVisual]:
        """
        Generate visuals for all script segments.

        Args:
            visual_descriptions: List of dicts with segment_number and description
            output_dir: Directory to save images
            style: Visual style

        Returns:
            List of GeneratedVisual objects
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        visuals = []

        for item in visual_descriptions:
            visual = self.generate_visual(
                description=item["description"],
                segment_number=item["segment_number"],
                output_dir=output_dir,
                style=style
            )
            visuals.append(visual)

        return visuals

    def _apply_whiteboard_effect(self, image: Image.Image) -> Image.Image:
        """
        Apply whiteboard-style effects to an image.

        Args:
            image: Input PIL Image

        Returns:
            Processed image with whiteboard effect
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Increase brightness and contrast for whiteboard look
        from PIL import ImageEnhance

        # Increase brightness
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)

        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)

        # Optional: Apply slight smoothing for cleaner lines
        image = image.filter(ImageFilter.SMOOTH)

        return image

    def _create_placeholder(
        self,
        segment_number: int,
        description: str,
        output_dir: Path
    ) -> GeneratedVisual:
        """Create a placeholder image when generation fails."""
        width, height = 1920, 1080

        # Create white background
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Add placeholder text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except (IOError, OSError):
            font = ImageFont.load_default()
            small_font = font

        # Draw segment title
        title = f"Segment {segment_number}"
        draw.text((width // 2, height // 3), title, fill=(100, 100, 100), font=font, anchor="mm")

        # Draw description (truncated)
        desc_short = description[:100] + "..." if len(description) > 100 else description
        draw.text((width // 2, height // 2), desc_short, fill=(150, 150, 150), font=small_font, anchor="mm")

        # Draw border
        draw.rectangle([10, 10, width - 10, height - 10], outline=(200, 200, 200), width=2)

        output_path = output_dir / f"segment_{segment_number:02d}.png"
        image.save(output_path, "PNG")

        return GeneratedVisual(
            segment_number=segment_number,
            image_path=output_path,
            description=description,
            width=width,
            height=height
        )

    def create_title_card(
        self,
        title: str,
        subtitle: Optional[str] = None,
        output_path: Path = None,
        width: int = 1920,
        height: int = 1080
    ) -> Path:
        """
        Create a title card image.

        Args:
            title: Main title text
            subtitle: Optional subtitle
            output_path: Where to save the image
            width: Image width
            height: Image height

        Returns:
            Path to the created image
        """
        # Create white background
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Try to load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except (IOError, OSError):
            title_font = ImageFont.load_default()
            subtitle_font = title_font

        # Draw title
        draw.text(
            (width // 2, height // 2 - 50),
            title,
            fill=(50, 50, 50),
            font=title_font,
            anchor="mm"
        )

        # Draw subtitle if provided
        if subtitle:
            draw.text(
                (width // 2, height // 2 + 50),
                subtitle,
                fill=(100, 100, 100),
                font=subtitle_font,
                anchor="mm"
            )

        # Draw decorative line
        line_y = height // 2 + 100
        draw.line([(width // 4, line_y), (3 * width // 4, line_y)], fill=(66, 133, 244), width=3)

        if output_path:
            image.save(output_path, "PNG")
            return output_path

        return None

    def create_end_card(
        self,
        text: str = "Thanks for watching!",
        output_path: Path = None,
        width: int = 1920,
        height: int = 1080
    ) -> Path:
        """
        Create an end card image.

        Args:
            text: End card text
            output_path: Where to save the image
            width: Image width
            height: Image height

        Returns:
            Path to the created image
        """
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        except (IOError, OSError):
            font = ImageFont.load_default()

        draw.text(
            (width // 2, height // 2),
            text,
            fill=(50, 50, 50),
            font=font,
            anchor="mm"
        )

        if output_path:
            image.save(output_path, "PNG")
            return output_path

        return None


class SketchConverter:
    """
    Converts images to sketch/whiteboard style using image processing.
    Useful for converting existing images to whiteboard aesthetic.
    """

    @staticmethod
    def to_sketch(
        image: Image.Image,
        blur_radius: int = 5,
        threshold: int = 200
    ) -> Image.Image:
        """
        Convert an image to a pencil sketch style.

        Args:
            image: Input PIL Image
            blur_radius: Blur radius for edge detection
            threshold: Threshold for line darkness

        Returns:
            Sketch-style image
        """
        if np is None:
            raise ImportError("NumPy required for sketch conversion")

        # Convert to grayscale
        gray = image.convert('L')

        # Invert
        inverted = ImageOps.invert(gray)

        # Apply Gaussian blur
        blurred = inverted.filter(ImageFilter.GaussianBlur(blur_radius))

        # Dodge blend
        gray_arr = np.array(gray, dtype=np.float32)
        blur_arr = np.array(blurred, dtype=np.float32)

        # Avoid division by zero
        blur_arr = np.where(blur_arr == 0, 1, blur_arr)

        # Color dodge blend
        result = (gray_arr * 256) / (256 - blur_arr)
        result = np.clip(result, 0, 255).astype(np.uint8)

        # Apply threshold to clean up
        result = np.where(result > threshold, 255, result)

        return Image.fromarray(result)

    @staticmethod
    def to_whiteboard(image: Image.Image) -> Image.Image:
        """
        Convert an image to whiteboard style.

        Args:
            image: Input PIL Image

        Returns:
            Whiteboard-style image
        """
        # First convert to sketch
        sketch = SketchConverter.to_sketch(image)

        # Create white background
        whiteboard = Image.new('RGB', sketch.size, (255, 255, 255))

        # Convert sketch to RGB
        sketch_rgb = sketch.convert('RGB')

        # Composite (dark lines only)
        if np is not None:
            sketch_arr = np.array(sketch_rgb)
            white_arr = np.array(whiteboard)

            # Only show lines darker than white
            mask = sketch_arr < 250
            result = np.where(mask, sketch_arr, white_arr)

            return Image.fromarray(result.astype(np.uint8))

        return sketch_rgb
