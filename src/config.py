"""
Configuration for the Multi-Agent Story Engine.

Environment variables:
- OPENROUTER_API_KEY: Your OpenRouter API key
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Project root directory (for resolving relative paths)
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file from project root
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

# Load YAML configuration
CONFIG_YAML_PATH = PROJECT_ROOT / "config.yaml"
try:
    with open(CONFIG_YAML_PATH) as f:
        YAML_CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Warning: config.yaml not found at {CONFIG_YAML_PATH}, using defaults")
    YAML_CONFIG = {"global": {}, "steps": {}}

# Export config sections
GLOBAL_CONFIG = YAML_CONFIG.get("global", {})
STEPS_CONFIG = YAML_CONFIG.get("steps", {})


# Helper functions for accessing step-level config
def get_step_config(step_name: str) -> dict:
    """Get config for a specific step."""
    return STEPS_CONFIG.get(step_name, {})


def get_token_limit(step_name: str, limit_type: str = "general") -> int:
    """Get token limit for step and type."""
    step = get_step_config(step_name)
    return step.get("token_limits", {}).get(limit_type, GLOBAL_CONFIG.get("default_token_limit", 2000))


def get_step_model(step_name: str) -> str:
    """Get model for a specific step."""
    return get_step_config(step_name).get("model", GLOBAL_CONFIG.get("default_model", "openai/gpt-5-nano"))


# === ENVIRONMENT DETECTION ===
def detect_environment() -> str:
    """Detect environment from folder path or HOUSE_OF_NOVELS_ENV variable.

    Priority:
    1. HOUSE_OF_NOVELS_ENV environment variable if set
    2. Path-based detection (looks for 'alpha' or 'prod' in PROJECT_ROOT path)
    3. Default to 'alpha' if unclear
    """
    env_override = os.environ.get("HOUSE_OF_NOVELS_ENV")
    if env_override in ("alpha", "prod"):
        return env_override

    path_str = str(PROJECT_ROOT).lower()
    if "\\prod\\" in path_str or "/prod/" in path_str:
        return "prod"
    elif "\\alpha\\" in path_str or "/alpha/" in path_str:
        return "alpha"

    return "alpha"  # Default


ENVIRONMENT = detect_environment()

# Environment-specific configuration
ENV_CONFIG = {
    "alpha": {
        # Channel: @DigitalDaVinci-ViSuRAI
        "playlist_id": "PLDErTZAi9nWzqR8WZg070oJAGNhkYa-5N",
        # ComfyUI output path for alpha
        "comfyui_output_dir": r"D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\output",
    },
    "prod": {
        # Channel: @TheKeepersLantern
        "playlist_id": "PLr_5rpnSabhkDGfXp_G5ORgHhZY2m8hD6",
        # ComfyUI output path for prod (using alpha for now, change when prod ComfyUI is set up)
        "comfyui_output_dir": r"D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\output",
    },
}

_env_config = ENV_CONFIG[ENVIRONMENT]


# OpenRouter Configuration
# Supports both OPENROUTER_API_KEY and OPR_ROUTER_API_KEY
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPR_ROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default model for all agents (loaded from config.yaml)
DEFAULT_MODEL = GLOBAL_CONFIG.get("default_model", "openai/gpt-5-nano")

# Fallback models for automatic recovery (loaded from config.yaml)
FALLBACK_MODELS = GLOBAL_CONFIG.get("fallback_models", [
    "qwen/qwen-turbo",
    "mistralai/mistral-7b-instruct",
    "deepseek/deepseek-chat-v3"
])

# Step 6 narrative prose generation model (loaded from config.yaml)
# Can be changed in config.yaml: steps.step6_prose_generation.model
STEP6_PROSE_MODEL = get_step_model("step6_prose_generation")

# Alternative models with tool calling support
SUPPORTED_MODELS = [
    "openai/gpt-5-nano",     # Ultra-cheap, 128K output, 400K context
    "openai/gpt-4o-mini",    # Reliable, fast
    "openai/gpt-5-mini",     # Latest OpenAI
    "x-ai/grok-4.1-fast",    # 1.8M context, excels at tools
    "deepseek/deepseek-v3.2", # Improved function calling
    "openai/gpt-oss-120b",   # Native tool use
]

# Debate configuration
DEBATE_ROUNDS = 2  # Initial opinions + rebuttals, then vote
NAME_DEBATE_ROUNDS = 2  # Critique rounds per character name

# Card draw configuration (like physical deck's 4 options)
CARDS_PER_DRAW = 4

# Story scope configurations
# Controls story length, character/location limits, and prose depth
STORY_SCOPES = {
    "flash": {
        "scene_range": (3, 4),
        "max_characters": 2,  # Protagonist + 1 other
        "max_locations": 1,
        "words_per_scene_min": 400,
        "words_per_scene_max": 500,
        "paragraphs_per_scene": 2,
        "description": "Flash fiction (~10 min read)",
    },
    "short": {
        "scene_range": (6, 8),
        "max_characters": 3,  # Protagonist, antagonist, 1 supporting
        "max_locations": 2,
        "words_per_scene_min": 500,
        "words_per_scene_max": 600,
        "paragraphs_per_scene": 3,
        "description": "Short story (~20 min read)",
    },
    "standard": {
        "scene_range": (12, 14),
        "max_characters": 5,  # Reduced from 8
        "max_locations": 4,   # Reduced from 6
        "words_per_scene_min": 600,
        "words_per_scene_max": 800,
        "paragraphs_per_scene": 4,
        "description": "Standard story (~35 min read)",
    },
    "long": {
        "scene_range": (18, 20),
        "max_characters": 8,  # Reduced from 12
        "max_locations": 6,   # Reduced from 10
        "words_per_scene_min": 800,
        "words_per_scene_max": 1000,
        "paragraphs_per_scene": 5,
        "description": "Long story (~50 min read)",
    },
}

DEFAULT_STORY_SCOPE = "standard"

# Phase configuration for House of Novels modular system
# Streamlined pipeline with author-driven phases:
# Phase 0: Codex (story seed + author selection)
# Phase 1: Author (10-step creation: plotting, characters, narrative, revision)
# Phase 2: Prompts (character, location, scene, poster, thumbnail)
# Phase 3: Generation (audio + images via ComfyUI)
# Phase 4: Editing (combine audio, create videos)
# Phase 5: Upload (YouTube)
PHASE_NAMES = [
    "codex",      # 0 - Story seed generation + author selection
    "author",     # 1 - 10-step author-driven creation (plotting, characters, narrative, revision)
    "prompts",    # 2 - Image/video prompts
    "generation", # 3 - Media generation (audio + images)
    "editing",    # 4 - Video editing
    "upload",     # 5 - YouTube upload
]
DEFAULT_FORGE_DIR = "forge"

# Author Configuration
DEFAULT_AUTHOR = None  # None = random selection
AUTHOR_SELECTION_MODE = "random"  # "random" | "specific" | "genre_match"
DEFAULT_STRUCTURE = "three_act"  # Default story structure if author doesn't specify

# ComfyUI Configuration for Phase 5 (Media Generation)
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"
DEFAULT_COMFYUI_TIMEOUT = 1800  # 30 minutes per generation

# ComfyUI workflow paths (relative to project root) — one per generation step
COMFYUI_WORKFLOWS = {
    "character": "workflows/z_image_turbo_characters.json",  # 1024x1024 square portraits
    "location": "workflows/z_image_turbo_locations.json",     # 1280x720 landscape
    "scene": "workflows/z_image_turbo_example.json",         # 1280x720 landscape (flat prompt fallback)
    "scene_location_edit": "workflows/image_qwen_image_edit_location.json",        # single-image location edit
    "scene_character_edit": "workflows/image_qwen_image_edit_2511_two_images.json", # two-image character composite
    "thumbnail": "workflows/z_image_turbo_example.json",     # 1280x720 landscape
    "audio": "workflows/Qwen_tts_voice_clone.json",
    "video": "workflows/video_ltx2_i2v_distilled.json",
}

# ComfyUI output directory (where images/videos are saved)
# This is used to construct full paths for input images in video generation
COMFYUI_OUTPUT_DIR = _env_config["comfyui_output_dir"]

# Video generation timeout (30 minutes - videos take much longer than images)
VIDEO_GENERATION_TIMEOUT = 1800  # seconds

# Generation step control (binary string)
# Position: 0=characters, 1=locations, 2=scenes, 3=thumbnails, 4=audio, 5=video
# Value: 1=run, 0=skip
# Examples:
#   "111110" = Run everything except video (default)
#   "100000" = Only character portraits
#   "011000" = Locations + scene images
#   "000010" = Only audio generation
#   "111111" = Run everything including video
GENERATION_STEPS = "111110"

# Audio generation timeout (30 minutes per generation)
AUDIO_GENERATION_TIMEOUT = 1800  # seconds

# YouTube Configuration for Phase 7 (Upload)
YOUTUBE_CLIENT_SECRETS_FILE = PROJECT_ROOT / "client_secrets.json"
YOUTUBE_TOKEN_FILE = PROJECT_ROOT / ".youtube_token.json"
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
DEFAULT_YOUTUBE_CATEGORY = "24"  # Entertainment
DEFAULT_YOUTUBE_PRIVACY = "public"  # public by default
DEFAULT_YOUTUBE_PLAYLIST = _env_config["playlist_id"]


def get_workflow_path(workflow_type: str) -> Path:
    """Get absolute path to a ComfyUI workflow file.

    Args:
        workflow_type: Type of workflow ("image", "video", or "audio")

    Returns:
        Absolute Path to the workflow JSON file

    Raises:
        ValueError: If workflow_type is not found in COMFYUI_WORKFLOWS
    """
    relative_path = COMFYUI_WORKFLOWS.get(workflow_type)
    if not relative_path:
        raise ValueError(f"Unknown workflow type: {workflow_type}. Available: {list(COMFYUI_WORKFLOWS.keys())}")
    return PROJECT_ROOT / relative_path


def get_max_character_layers() -> int:
    """Max characters with individual layers in layered scene prompts.

    Excess characters beyond this limit become background figures
    noted in the last character layer's prompt.
    """
    return YAML_CONFIG.get("phase2_scene_prompts", {}).get("max_character_layers", 3)


def get_shot_selection_config() -> dict:
    """Get shot selection config for Phase 2 scene image prompts.

    Returns dict with 'enabled' (bool) and 'force_shot_type' (str | None).
    """
    return YAML_CONFIG.get("phase2_scene_prompts", {}).get(
        "shot_selection", {"enabled": True, "force_shot_type": None}
    )


def should_run_step(step_index: int) -> bool:
    """Check if a generation step should run based on GENERATION_STEPS config.

    Args:
        step_index: 0=characters, 1=locations, 2=scenes, 3=thumbnails, 4=audio, 5=video

    Returns:
        True if the step should run, False otherwise
    """
    if step_index < 0 or step_index >= len(GENERATION_STEPS):
        return False
    return GENERATION_STEPS[step_index] == "1"
