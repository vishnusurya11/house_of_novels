"""
House of Novels - Modular Phase System

Each phase can be run independently or orchestrated via house_of_novels.py.

Pipeline (with Author Phases):
    0. codex      - Generate story prompts + select author
    1. plotting   - Outline + Characters + Locations (merged)
    2. screenplay - Write scene-by-scene prose (author-styled)
    3. revision   - Multi-pass editing (author's revision style)
    4. storyboard - Break scenes into shots
    5. prompts    - Generate AI image prompts
    6. generation - Generate images/audio using ComfyUI
    7. editing    - Combine media into final video
    8. upload     - Upload to YouTube
"""

from src.phases.phase0_codex import run_phase0_codex, Phase0Result
from src.phases.phase1_plotting import run_phase1_plotting, Phase1Result
from src.phases.phase2_screenplay import run_phase2_screenplay, Phase2Result
from src.phases.phase3_revision import run_phase3_revision, Phase3Result
from src.phases.phase4_storyboard import run_phase4_storyboard
from src.phases.phase5_prompts import run_phase5_prompts
from src.phases.phase6_generation import run_phase6_generation
from src.phases.phase7_editing import run_phase7_editing
from src.phases.phase8_upload import run_phase8_upload

__all__ = [
    "run_phase0_codex", "Phase0Result",
    "run_phase1_plotting", "Phase1Result",
    "run_phase2_screenplay", "Phase2Result",
    "run_phase3_revision", "Phase3Result",
    "run_phase4_storyboard",
    "run_phase5_prompts",
    "run_phase6_generation",
    "run_phase7_editing",
    "run_phase8_upload",
]
