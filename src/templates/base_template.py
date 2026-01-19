"""
Base Template Class for House of Novels

All output templates must inherit from BaseTemplate and implement
the run_generation() and run_editing() methods.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class GenerationResult:
    """Result of template generation phase."""
    codex_path: Path
    poster_count: int
    character_portrait_count: int
    location_image_count: int
    scene_image_count: int
    shot_frame_count: int
    video_count: int
    audio_count: int
    success: bool
    error: Optional[str] = None
    step_timings: dict = field(default_factory=dict)


@dataclass
class EditingResult:
    """Result of template editing phase."""
    codex_path: Path
    scene_audio_count: int
    scene_video_count: int
    video_output_path: Optional[Path]
    video_duration: float
    success: bool
    error: Optional[str] = None
    step_timings: dict = field(default_factory=dict)


class BaseTemplate(ABC):
    """
    Abstract base class for all output templates.

    Templates define how media is generated and edited for the final output.
    Phases 0-4 (narrative generation) are shared across all templates.
    Templates handle Phases 5-6 (media generation and editing).
    """

    name: str = "base"
    description: str = "Base template"

    @abstractmethod
    def run_generation(
        self,
        codex_path: Path,
        comfyui_url: str = None,
        workflow_path: str = None,
        steps: list[int] = None,
        timeout: int = None,
        **kwargs
    ) -> GenerationResult:
        """
        Run media generation phase (Phase 5 equivalent).

        Args:
            codex_path: Path to codex.json
            comfyui_url: ComfyUI API URL
            workflow_path: Path to ComfyUI workflow JSON
            steps: List of step numbers to run
            timeout: Timeout in seconds per generation

        Returns:
            GenerationResult with counts and status
        """
        pass

    @abstractmethod
    def run_editing(
        self,
        codex_path: Path,
        steps: list[int] = None,
        comfyui_output_dir: str = None,
        **kwargs
    ) -> EditingResult:
        """
        Run media editing phase (Phase 6 equivalent).

        Args:
            codex_path: Path to codex.json
            steps: List of step numbers to run
            comfyui_output_dir: ComfyUI output directory

        Returns:
            EditingResult with output paths and status
        """
        pass

    def get_default_generation_steps(self) -> list[int]:
        """Return default generation steps for this template."""
        return [1, 2, 3]

    def get_default_editing_steps(self) -> list[int]:
        """Return default editing steps for this template."""
        return [1, 2, 3]

    def validate_codex(self, codex_path: Path) -> bool:
        """Validate codex has required data for this template."""
        import json
        with open(codex_path, "r", encoding="utf-8") as f:
            codex = json.load(f)

        # Check for required narrative structure
        story = codex.get("story", {})
        if not story.get("narrative", {}).get("acts"):
            return False
        if not story.get("characters"):
            return False
        return True
