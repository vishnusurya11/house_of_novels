"""
House of Novels - Modular Phase System

Each phase can be run independently or orchestrated via house_of_novels.py.

Phases:
    0. codex      - Generate story prompts via multi-agent debate
    1. outline    - Create 3-act story structure
    2. characters - Build character & location profiles
    3. narrative  - Write scene-by-scene prose
    4. prompts    - Generate AI image prompts (characters, locations, scenes)
    5. generation - Generate images/media using ComfyUI
    6. editing    - Combine shot videos into final video
"""

from src.phases.phase0_codex import run_phase0_codex, Phase0Result
from src.phases.phase1_outline import run_phase1_outline, Phase1Result
from src.phases.phase2_characters import run_phase2_characters, Phase2Result
from src.phases.phase3_narrative import run_phase3_narrative, Phase3Result
from src.phases.phase4_prompts import run_phase4_prompts, Phase4PromptsResult
from src.phases.phase5_generation import run_phase5_generation, Phase5GenerationResult
from src.phases.phase6_editing import run_phase6_editing, Phase6EditingResult

__all__ = [
    "run_phase0_codex", "Phase0Result",
    "run_phase1_outline", "Phase1Result",
    "run_phase2_characters", "Phase2Result",
    "run_phase3_narrative", "Phase3Result",
    "run_phase4_prompts", "Phase4PromptsResult",
    "run_phase5_generation", "Phase5GenerationResult",
    "run_phase6_editing", "Phase6EditingResult",
]
