"""
Script Generator Module

Generates educational scripts for whiteboard explainer videos using AI.
The script is structured into segments, each with narration text and
visual scene descriptions.
"""
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .utils import estimate_duration, save_json

logger = logging.getLogger(__name__)


@dataclass
class ScriptSegment:
    """Represents a segment of the video script."""
    segment_number: int
    title: str
    narration: str
    visual_description: str
    key_points: List[str]
    estimated_duration: float  # in seconds

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VideoScript:
    """Complete video script with all segments."""
    topic: str
    total_duration: float
    introduction: str
    segments: List[ScriptSegment]
    conclusion: str
    visual_style_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "total_duration": self.total_duration,
            "introduction": self.introduction,
            "segments": [s.to_dict() for s in self.segments],
            "conclusion": self.conclusion,
            "visual_style_notes": self.visual_style_notes,
        }

    def get_full_narration(self) -> str:
        """Get complete narration text."""
        parts = [self.introduction]
        for segment in self.segments:
            parts.append(segment.narration)
        parts.append(self.conclusion)
        return "\n\n".join(parts)


class ScriptGenerator:
    """
    Generates educational video scripts using AI.

    Supports OpenAI GPT, Anthropic Claude, and Google Gemini models.
    """

    SCRIPT_PROMPT_TEMPLATE = """
You are an expert educational content creator specializing in whiteboard explainer videos.
Create a comprehensive, engaging script for a whiteboard-style explainer video on the topic: "{topic}"

Target duration: {duration} minutes

Requirements:
1. The script should be educational, clear, and engaging
2. Break down complex concepts into simple, digestible parts
3. Use analogies and real-world examples
4. Structure content for visual representation (things that can be drawn)
5. Include natural pauses for visual transitions

Please provide the script in the following JSON format:
{{
    "topic": "{topic}",
    "introduction": "Opening narration (30-45 seconds worth of content)",
    "segments": [
        {{
            "segment_number": 1,
            "title": "Segment title",
            "narration": "The spoken narration for this segment",
            "visual_description": "Detailed description of what should be drawn/shown during this segment. Include specific elements like diagrams, icons, text labels, arrows, etc.",
            "key_points": ["Key point 1", "Key point 2", "Key point 3"]
        }}
    ],
    "conclusion": "Closing narration summarizing key takeaways (30-45 seconds)",
    "visual_style_notes": "Overall visual style recommendations for the whiteboard animation"
}}

Create {num_segments} segments that progressively build understanding of the topic.
Each segment should be {segment_duration} seconds of narration.
Make the visual descriptions specific and drawable - describe actual shapes, diagrams, icons, and text to be shown.
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        provider: str = "openai"
    ):
        """
        Initialize the script generator.

        Args:
            api_key: API key for the AI provider
            model: Model name to use
            provider: AI provider ("openai", "anthropic", or "gemini")
        """
        self.model = model
        self.provider = provider.lower()
        self.client = None

        if self.provider == "openai":
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        elif self.provider == "anthropic":
            if anthropic is None:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        elif self.provider == "gemini":
            if genai is None:
                raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model or "gemini-1.5-flash")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"Initialized ScriptGenerator with {provider} ({model})")

    def generate(
        self,
        topic: str,
        duration_minutes: int = 5,
        num_segments: Optional[int] = None,
        custom_instructions: Optional[str] = None
    ) -> VideoScript:
        """
        Generate a video script for the given topic.

        Args:
            topic: The topic to explain
            duration_minutes: Target video duration in minutes
            num_segments: Number of segments (auto-calculated if not provided)
            custom_instructions: Additional instructions for script generation

        Returns:
            VideoScript object with complete script
        """
        # Calculate segments based on duration
        if num_segments is None:
            num_segments = max(3, min(10, duration_minutes))

        segment_duration = (duration_minutes * 60 - 60) // num_segments  # Reserve 60s for intro/outro

        prompt = self.SCRIPT_PROMPT_TEMPLATE.format(
            topic=topic,
            duration=duration_minutes,
            num_segments=num_segments,
            segment_duration=segment_duration
        )

        if custom_instructions:
            prompt += f"\n\nAdditional instructions:\n{custom_instructions}"

        logger.info(f"Generating script for topic: {topic}")
        logger.info(f"Target duration: {duration_minutes} minutes, {num_segments} segments")

        # Generate script using AI
        script_data = self._call_ai(prompt)

        # Parse and validate the response
        script = self._parse_script(script_data, topic)

        logger.info(f"Generated script with {len(script.segments)} segments")
        logger.info(f"Estimated total duration: {script.total_duration:.1f} seconds")

        return script

    def _call_ai(self, prompt: str) -> Dict[str, Any]:
        """Call the AI API to generate script."""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert educational content creator. Always respond with valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                return json.loads(content)

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                    system="You are an expert educational content creator. Always respond with valid JSON only, no additional text."
                )
                content = response.content[0].text
                # Extract JSON from response
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content.strip())

            elif self.provider == "gemini":
                full_prompt = f"""You are an expert educational content creator. Always respond with valid JSON only, no additional text or markdown formatting.

{prompt}"""
                response = self.client.generate_content(full_prompt)
                content = response.text.strip()
                # Extract JSON from response (Gemini might wrap in markdown)
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("AI response was not valid JSON")
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            raise

    def _parse_script(self, data: Dict[str, Any], topic: str) -> VideoScript:
        """Parse AI response into VideoScript object."""
        segments = []
        total_duration = 0

        # Parse introduction duration
        intro_duration = estimate_duration(data.get("introduction", ""))
        total_duration += intro_duration

        # Parse segments
        for seg_data in data.get("segments", []):
            narration = seg_data.get("narration", "")
            duration = estimate_duration(narration)
            total_duration += duration

            segment = ScriptSegment(
                segment_number=seg_data.get("segment_number", len(segments) + 1),
                title=seg_data.get("title", f"Segment {len(segments) + 1}"),
                narration=narration,
                visual_description=seg_data.get("visual_description", ""),
                key_points=seg_data.get("key_points", []),
                estimated_duration=duration
            )
            segments.append(segment)

        # Parse conclusion duration
        conclusion_duration = estimate_duration(data.get("conclusion", ""))
        total_duration += conclusion_duration

        return VideoScript(
            topic=topic,
            total_duration=total_duration,
            introduction=data.get("introduction", ""),
            segments=segments,
            conclusion=data.get("conclusion", ""),
            visual_style_notes=data.get("visual_style_notes", "")
        )

    def save_script(self, script: VideoScript, filepath: Path) -> None:
        """Save script to a JSON file."""
        save_json(script.to_dict(), filepath)
        logger.info(f"Script saved to {filepath}")

    def load_script(self, filepath: Path) -> VideoScript:
        """Load script from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        segments = [
            ScriptSegment(**seg) for seg in data.get("segments", [])
        ]

        return VideoScript(
            topic=data.get("topic", ""),
            total_duration=data.get("total_duration", 0),
            introduction=data.get("introduction", ""),
            segments=segments,
            conclusion=data.get("conclusion", ""),
            visual_style_notes=data.get("visual_style_notes", "")
        )
