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
    - Free mode (PIL-based whiteboard generation)
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
        image_size: str = "1792x1024",
        free_mode: bool = False
    ):
        """
        Initialize the visual generator.

        Args:
            api_key: OpenAI API key (not needed for free_mode)
            model: Image generation model
            image_size: Output image size
            free_mode: Use free PIL-based generation (no API needed)
        """
        if Image is None:
            raise ImportError("Pillow package not installed. Run: pip install Pillow")

        self.free_mode = free_mode
        self.model = model
        self.image_size = image_size
        self.client = None

        if not free_mode:
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
            logger.info(f"Initialized VisualGenerator with {model}")
        else:
            logger.info("Initialized VisualGenerator in FREE mode (PIL-based)")

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
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Generating visual for segment {segment_number}")

        # Use free mode if enabled
        if self.free_mode:
            return self._generate_free_whiteboard(segment_number, description, output_dir)

        # Construct the prompt for AI generation
        if style == "whiteboard":
            prompt = self.WHITEBOARD_PROMPT_PREFIX + description
        else:
            prompt = f"Educational {style} illustration: {description}"

        # Ensure prompt isn't too long
        prompt = prompt[:4000]

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

    def _generate_free_whiteboard(
        self,
        segment_number: int,
        description: str,
        output_dir: Path
    ) -> GeneratedVisual:
        """
        Generate a whiteboard-style image using PIL (free, no API needed).

        Creates a professional-looking whiteboard with:
        - Key points extracted from description
        - Simple shapes and icons
        - Clean typography
        """
        width, height = 1920, 1080

        # Create white background with slight texture
        image = Image.new('RGB', (width, height), (252, 252, 250))
        draw = ImageDraw.Draw(image)

        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except (IOError, OSError):
            title_font = ImageFont.load_default()
            body_font = title_font
            small_font = title_font

        # Colors for whiteboard style
        dark_gray = (50, 50, 50)
        blue = (66, 133, 244)
        red = (234, 67, 53)
        green = (52, 168, 83)
        light_gray = (200, 200, 200)

        # Draw subtle border
        draw.rectangle([20, 20, width - 20, height - 20], outline=light_gray, width=2)

        # Extract key points from description
        key_points = self._extract_key_points(description)

        # Draw segment indicator
        draw.text((60, 40), f"#{segment_number}", fill=blue, font=small_font)

        # Draw main content area
        content_y = 100

        # Draw a title derived from description
        title = self._extract_title(description)
        draw.text((width // 2, content_y), title, fill=dark_gray, font=title_font, anchor="mm")
        content_y += 80

        # Draw decorative line under title
        draw.line([(width // 4, content_y), (3 * width // 4, content_y)], fill=blue, width=3)
        content_y += 50

        # Draw key points with bullet points and icons
        colors = [blue, red, green, blue, red, green]
        for i, point in enumerate(key_points[:6]):
            point_y = content_y + i * 120

            # Draw bullet circle
            bullet_x = 100
            draw.ellipse([bullet_x - 15, point_y - 15, bullet_x + 15, point_y + 15],
                        fill=colors[i % len(colors)])

            # Draw connecting line
            if i < len(key_points) - 1:
                draw.line([(bullet_x, point_y + 20), (bullet_x, point_y + 100)],
                         fill=light_gray, width=2)

            # Draw point text
            # Wrap text if too long
            wrapped_point = self._wrap_text(point, 60)
            draw.text((bullet_x + 40, point_y), wrapped_point, fill=dark_gray, font=body_font, anchor="lm")

            # Draw simple icon/shape on the right
            icon_x = width - 200
            self._draw_simple_icon(draw, icon_x, point_y, i, colors[i % len(colors)])

        # Draw decorative elements
        self._draw_decorative_elements(draw, width, height, light_gray)

        # Save image
        output_path = output_dir / f"segment_{segment_number:02d}.png"
        image.save(output_path, "PNG")

        logger.info(f"Free whiteboard visual saved to {output_path}")

        return GeneratedVisual(
            segment_number=segment_number,
            image_path=output_path,
            description=description,
            width=width,
            height=height
        )

    def _extract_key_points(self, description: str) -> List[str]:
        """Extract key points from description text."""
        import re

        # Try to find bullet points or numbered items
        points = re.findall(r'[-•*]\s*([^-•*\n]+)', description)
        if points:
            return [p.strip() for p in points if len(p.strip()) > 5]

        # Split by sentences and take key ones
        sentences = re.split(r'[.!?]', description)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        # Take first 5 meaningful sentences
        return sentences[:5] if sentences else [description[:100]]

    def _extract_title(self, description: str) -> str:
        """Extract or generate a title from description."""
        # Take first sentence or first 50 chars
        import re
        first_sentence = re.split(r'[.!?]', description)[0].strip()
        if len(first_sentence) > 50:
            return first_sentence[:47] + "..."
        return first_sentence or "Key Concepts"

    def _wrap_text(self, text: str, max_chars: int) -> str:
        """Wrap text to fit within max characters per line."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines[:2])  # Max 2 lines

    def _draw_simple_icon(self, draw: ImageDraw, x: int, y: int, index: int, color: Tuple):
        """Draw a simple icon based on index."""
        icon_size = 40

        if index % 6 == 0:
            # Circle
            draw.ellipse([x - icon_size, y - icon_size, x + icon_size, y + icon_size],
                        outline=color, width=3)
        elif index % 6 == 1:
            # Square
            draw.rectangle([x - icon_size, y - icon_size, x + icon_size, y + icon_size],
                          outline=color, width=3)
        elif index % 6 == 2:
            # Triangle
            draw.polygon([(x, y - icon_size), (x - icon_size, y + icon_size),
                         (x + icon_size, y + icon_size)], outline=color, width=3)
        elif index % 6 == 3:
            # Star (simplified as asterisk shape)
            for angle in range(0, 360, 60):
                import math
                rad = math.radians(angle)
                x2 = x + int(icon_size * math.cos(rad))
                y2 = y + int(icon_size * math.sin(rad))
                draw.line([(x, y), (x2, y2)], fill=color, width=3)
        elif index % 6 == 4:
            # Arrow right
            draw.line([(x - icon_size, y), (x + icon_size, y)], fill=color, width=3)
            draw.line([(x + icon_size - 15, y - 15), (x + icon_size, y)], fill=color, width=3)
            draw.line([(x + icon_size - 15, y + 15), (x + icon_size, y)], fill=color, width=3)
        else:
            # Checkmark
            draw.line([(x - icon_size, y), (x - icon_size // 2, y + icon_size // 2)],
                     fill=color, width=3)
            draw.line([(x - icon_size // 2, y + icon_size // 2), (x + icon_size, y - icon_size)],
                     fill=color, width=3)

    def _draw_decorative_elements(self, draw: ImageDraw, width: int, height: int, color: Tuple):
        """Draw subtle decorative elements."""
        # Corner decorations
        corner_size = 30

        # Top-left corner
        draw.line([(40, 40), (40, 40 + corner_size)], fill=color, width=2)
        draw.line([(40, 40), (40 + corner_size, 40)], fill=color, width=2)

        # Top-right corner
        draw.line([(width - 40, 40), (width - 40, 40 + corner_size)], fill=color, width=2)
        draw.line([(width - 40, 40), (width - 40 - corner_size, 40)], fill=color, width=2)

        # Bottom-left corner
        draw.line([(40, height - 40), (40, height - 40 - corner_size)], fill=color, width=2)
        draw.line([(40, height - 40), (40 + corner_size, height - 40)], fill=color, width=2)

        # Bottom-right corner
        draw.line([(width - 40, height - 40), (width - 40, height - 40 - corner_size)], fill=color, width=2)
        draw.line([(width - 40, height - 40), (width - 40 - corner_size, height - 40)], fill=color, width=2)

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
