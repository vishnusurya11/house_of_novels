"""
House of Novels - Modular Phase System

Each phase can be run independently or orchestrated via house_of_novels.py.

Pipeline:
    0. codex      - Generate story prompts + select author
    1. author     - 10-step author-driven story creation (plotting, characters, narrative, revision, etc.)
    2. prompts    - Generate AI image prompts (thumbnails, chapter images)
    3. generation - Generate images/audio using ComfyUI
    4. editing    - Combine media into final video
    5. upload     - Upload to YouTube
"""

from src.phases.phase0_codex import run_phase0_codex, Phase0Result
from src.phases.phase1_author import run_phase1_author
from src.phases.phase2_prompts import run_phase2_prompts, Phase2PromptsResult
from src.phases.phase3_generation import run_phase3_generation, Phase3GenerationResult
from src.phases.phase4_editing import run_phase4_editing, Phase4EditingResult
from src.phases.phase5_upload import run_phase5_upload, Phase5UploadResult

__all__ = [
    "run_phase0_codex", "Phase0Result",
    "run_phase1_author",
    "run_phase2_prompts", "Phase2PromptsResult",
    "run_phase3_generation", "Phase3GenerationResult",
    "run_phase4_editing", "Phase4EditingResult",
    "run_phase5_upload", "Phase5UploadResult",
]
