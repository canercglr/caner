#!/usr/bin/env python3
"""
Speed-Drawing Explainer Video Generator

Generate whiteboard-style explainer videos from a single topic using
AI-generated scripts, visuals, and voiceovers.

Usage:
    python main.py "Your Topic Here" [options]

Example:
    python main.py "How Machine Learning Works" --duration 5 --voice nova
"""
import sys
import logging
from pathlib import Path
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Please install required packages: pip install click rich")
    sys.exit(1)

from config import (
    OUTPUT_DIR, OPENAI_API_KEY, ANTHROPIC_API_KEY,
    VIDEO_CONFIG, AUDIO_CONFIG, SCRIPT_CONFIG, AI_CONFIG
)
from src.utils import create_project_directory, generate_project_id, save_json, format_time
from src.script_generator import ScriptGenerator
from src.visual_generator import VisualGenerator
from src.voiceover_generator import VoiceoverGenerator
from src.video_assembler import VideoAssembler, VideoSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


class ExplainerVideoGenerator:
    """
    Main class for generating explainer videos.

    Orchestrates the entire pipeline from topic to final video.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai",
        voice: str = "nova"
    ):
        """
        Initialize the video generator.

        Args:
            api_key: API key for AI services
            provider: AI provider ("openai" or "anthropic")
            voice: TTS voice to use
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.provider = provider
        self.voice = voice

        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def generate(
        self,
        topic: str,
        duration_minutes: int = 5,
        output_dir: Optional[Path] = None,
        skip_script: bool = False,
        skip_visuals: bool = False,
        skip_audio: bool = False,
        skip_video: bool = False,
        drawing_effect: bool = True
    ) -> Path:
        """
        Generate a complete explainer video.

        Args:
            topic: The topic to explain
            duration_minutes: Target video duration
            output_dir: Custom output directory
            skip_script: Skip script generation (use existing)
            skip_visuals: Skip visual generation
            skip_audio: Skip audio generation
            skip_video: Skip video assembly
            drawing_effect: Include speed-drawing animation

        Returns:
            Path to the generated video
        """
        # Create project directory
        project_id = generate_project_id(topic)
        dirs = create_project_directory(output_dir or OUTPUT_DIR, project_id)

        console.print(Panel(
            f"[bold blue]Generating Explainer Video[/bold blue]\n\n"
            f"Topic: [green]{topic}[/green]\n"
            f"Duration: [yellow]{duration_minutes} minutes[/yellow]\n"
            f"Project ID: [dim]{project_id}[/dim]",
            title="Speed-Drawing Explainer"
        ))

        script = None
        visuals = []
        audios = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:

            # Step 1: Generate Script
            if not skip_script:
                task = progress.add_task("[cyan]Generating script...", total=100)
                script = self._generate_script(topic, duration_minutes, dirs)
                progress.update(task, completed=100)
                console.print("[green]✓[/green] Script generated")
            else:
                script = self._load_existing_script(dirs)

            if script is None:
                raise ValueError("No script available. Cannot continue.")

            # Step 2: Generate Visuals
            if not skip_visuals:
                task = progress.add_task(
                    "[cyan]Generating visuals...",
                    total=len(script.segments) + 2  # +2 for title and end cards
                )
                visuals = self._generate_visuals(script, dirs, progress, task)
                console.print("[green]✓[/green] Visuals generated")
            else:
                visuals = self._load_existing_visuals(script, dirs)

            # Step 3: Generate Voiceovers
            if not skip_audio:
                task = progress.add_task(
                    "[cyan]Generating voiceovers...",
                    total=len(script.segments) + 2  # intro + segments + conclusion
                )
                audios = self._generate_voiceovers(script, dirs, progress, task)
                console.print("[green]✓[/green] Voiceovers generated")
            else:
                audios = self._load_existing_audio(script, dirs)

            # Step 4: Assemble Video
            if not skip_video:
                task = progress.add_task("[cyan]Assembling video...", total=100)
                output_path = self._assemble_video(
                    script, visuals, audios, dirs, drawing_effect
                )
                progress.update(task, completed=100)
                console.print("[green]✓[/green] Video assembled")
            else:
                output_path = dirs["output"] / "final_video.mp4"

        # Display summary
        self._display_summary(script, output_path, dirs)

        return output_path

    def _generate_script(self, topic: str, duration: int, dirs: dict):
        """Generate the video script."""
        generator = ScriptGenerator(
            api_key=self.api_key,
            model=AI_CONFIG["script_model"],
            provider=self.provider
        )

        script = generator.generate(topic, duration_minutes=duration)
        generator.save_script(script, dirs["scripts"] / "script.json")

        return script

    def _load_existing_script(self, dirs: dict):
        """Load existing script from project directory."""
        script_path = dirs["scripts"] / "script.json"
        if script_path.exists():
            generator = ScriptGenerator.__new__(ScriptGenerator)
            return generator.load_script(script_path)
        return None

    def _generate_visuals(self, script, dirs: dict, progress, task):
        """Generate visuals for all segments."""
        generator = VisualGenerator(
            api_key=self.api_key,
            model=AI_CONFIG["image_model"]
        )

        visuals = []

        # Create title card
        title_path = dirs["visuals"] / "title_card.png"
        generator.create_title_card(script.topic, output_path=title_path)
        visuals.append({"type": "title", "path": title_path})
        progress.update(task, advance=1)

        # Generate segment visuals
        for segment in script.segments:
            visual = generator.generate_visual(
                description=segment.visual_description,
                segment_number=segment.segment_number,
                output_dir=dirs["visuals"]
            )
            visuals.append({
                "type": "segment",
                "segment_number": segment.segment_number,
                "path": visual.image_path
            })
            progress.update(task, advance=1)

        # Create end card
        end_path = dirs["visuals"] / "end_card.png"
        generator.create_end_card(output_path=end_path)
        visuals.append({"type": "end", "path": end_path})
        progress.update(task, advance=1)

        return visuals

    def _load_existing_visuals(self, script, dirs: dict):
        """Load existing visuals from project directory."""
        visuals = []
        visuals_dir = dirs["visuals"]

        title_path = visuals_dir / "title_card.png"
        if title_path.exists():
            visuals.append({"type": "title", "path": title_path})

        for segment in script.segments:
            path = visuals_dir / f"segment_{segment.segment_number:02d}.png"
            if path.exists():
                visuals.append({
                    "type": "segment",
                    "segment_number": segment.segment_number,
                    "path": path
                })

        end_path = visuals_dir / "end_card.png"
        if end_path.exists():
            visuals.append({"type": "end", "path": end_path})

        return visuals

    def _generate_voiceovers(self, script, dirs: dict, progress, task):
        """Generate voiceovers for narration."""
        generator = VoiceoverGenerator(
            api_key=self.api_key,
            provider="openai",
            voice=self.voice,
            model=AI_CONFIG["tts_model"]
        )

        audios = []

        # Generate intro audio
        intro_audio = generator.generate_voiceover(
            text=script.introduction,
            segment_number=0,
            output_dir=dirs["audio"]
        )
        audios.append({
            "type": "intro",
            "path": intro_audio.audio_path,
            "duration": intro_audio.duration
        })
        progress.update(task, advance=1)

        # Generate segment audios
        for segment in script.segments:
            audio = generator.generate_voiceover(
                text=segment.narration,
                segment_number=segment.segment_number,
                output_dir=dirs["audio"]
            )
            audios.append({
                "type": "segment",
                "segment_number": segment.segment_number,
                "path": audio.audio_path,
                "duration": audio.duration
            })
            progress.update(task, advance=1)

        # Generate conclusion audio
        conclusion_audio = generator.generate_voiceover(
            text=script.conclusion,
            segment_number=len(script.segments) + 1,
            output_dir=dirs["audio"]
        )
        audios.append({
            "type": "conclusion",
            "path": conclusion_audio.audio_path,
            "duration": conclusion_audio.duration
        })
        progress.update(task, advance=1)

        return audios

    def _load_existing_audio(self, script, dirs: dict):
        """Load existing audio from project directory."""
        from pydub import AudioSegment

        audios = []
        audio_dir = dirs["audio"]

        # Intro
        intro_path = audio_dir / "segment_00.mp3"
        if intro_path.exists():
            audio = AudioSegment.from_file(str(intro_path))
            audios.append({
                "type": "intro",
                "path": intro_path,
                "duration": len(audio) / 1000
            })

        # Segments
        for segment in script.segments:
            path = audio_dir / f"segment_{segment.segment_number:02d}.mp3"
            if path.exists():
                audio = AudioSegment.from_file(str(path))
                audios.append({
                    "type": "segment",
                    "segment_number": segment.segment_number,
                    "path": path,
                    "duration": len(audio) / 1000
                })

        # Conclusion
        conclusion_path = audio_dir / f"segment_{len(script.segments) + 1:02d}.mp3"
        if conclusion_path.exists():
            audio = AudioSegment.from_file(str(conclusion_path))
            audios.append({
                "type": "conclusion",
                "path": conclusion_path,
                "duration": len(audio) / 1000
            })

        return audios

    def _assemble_video(self, script, visuals, audios, dirs: dict, drawing_effect: bool):
        """Assemble the final video."""
        assembler = VideoAssembler(
            width=VIDEO_CONFIG["width"],
            height=VIDEO_CONFIG["height"],
            fps=VIDEO_CONFIG["fps"]
        )

        # Build video segments
        segments = []

        # Match visuals with audios for segments
        visual_map = {v.get("segment_number"): v for v in visuals if v["type"] == "segment"}
        audio_map = {a.get("segment_number"): a for a in audios if a["type"] == "segment"}

        for segment_num in sorted(visual_map.keys()):
            if segment_num in audio_map:
                visual = visual_map[segment_num]
                audio = audio_map[segment_num]

                segments.append(VideoSegment(
                    segment_number=segment_num,
                    visual_path=visual["path"],
                    audio_path=audio["path"],
                    duration=audio["duration"]
                ))

        output_path = dirs["output"] / "final_video.mp4"

        return assembler.assemble_video(
            segments=segments,
            output_path=output_path,
            title=script.topic,
            include_title_card=True,
            include_end_card=True,
            drawing_effect=drawing_effect
        )

    def _display_summary(self, script, output_path: Path, dirs: dict):
        """Display generation summary."""
        table = Table(title="Generation Summary")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Topic", script.topic)
        table.add_row("Segments", str(len(script.segments)))
        table.add_row("Est. Duration", format_time(script.total_duration))
        table.add_row("Output", str(output_path))
        table.add_row("Project Dir", str(dirs["root"]))

        console.print("\n")
        console.print(table)
        console.print("\n[bold green]Video generation complete![/bold green]")


@click.command()
@click.argument('topic')
@click.option('--duration', '-d', default=5, help='Target video duration in minutes')
@click.option('--voice', '-v', default='nova',
              type=click.Choice(['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']),
              help='TTS voice to use')
@click.option('--provider', '-p', default='openai',
              type=click.Choice(['openai', 'anthropic']),
              help='AI provider for script generation')
@click.option('--output', '-o', type=click.Path(), help='Custom output directory')
@click.option('--no-drawing', is_flag=True, help='Disable speed-drawing animation')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
@click.option('--skip-script', is_flag=True, help='Skip script generation (use existing)')
@click.option('--skip-visuals', is_flag=True, help='Skip visual generation')
@click.option('--skip-audio', is_flag=True, help='Skip audio generation')
@click.option('--skip-video', is_flag=True, help='Skip video assembly')
def main(
    topic: str,
    duration: int,
    voice: str,
    provider: str,
    output: Optional[str],
    no_drawing: bool,
    api_key: Optional[str],
    skip_script: bool,
    skip_visuals: bool,
    skip_audio: bool,
    skip_video: bool
):
    """
    Generate a whiteboard-style explainer video from a topic.

    TOPIC: The subject to explain in the video.

    Example:
        python main.py "How Blockchain Works" --duration 5 --voice nova
    """
    try:
        generator = ExplainerVideoGenerator(
            api_key=api_key,
            provider=provider,
            voice=voice
        )

        output_path = generator.generate(
            topic=topic,
            duration_minutes=duration,
            output_dir=Path(output) if output else None,
            skip_script=skip_script,
            skip_visuals=skip_visuals,
            skip_audio=skip_audio,
            skip_video=skip_video,
            drawing_effect=not no_drawing
        )

        console.print(f"\n[bold]Output video:[/bold] {output_path}")

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        logger.exception("Generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
