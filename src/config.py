"""
Configuration for the Multi-Agent Story Engine.

Environment variables:
- OPENROUTER_API_KEY: Your OpenRouter API key
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory (for resolving relative paths)
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file from project root
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

# OpenRouter Configuration
# Supports both OPENROUTER_API_KEY and OPR_ROUTER_API_KEY
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPR_ROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default model for all agents (supports tool calling)
DEFAULT_MODEL = "openai/gpt-4o-mini"

# Alternative models with tool calling support
SUPPORTED_MODELS = [
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
PHASE_NAMES = ["codex", "outline", "characters", "narrative", "storyboard", "prompts", "generation", "editing", "upload"]
DEFAULT_FORGE_DIR = "forge"

# ComfyUI Configuration for Phase 5 (Media Generation)
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"
DEFAULT_COMFYUI_TIMEOUT = 1800  # 30 minutes per generation

# ComfyUI workflow paths (relative to project root)
COMFYUI_WORKFLOWS = {
    "image": "workflows/z_image_turbo_example.json",
    "video": "workflows/video_ltx2_i2v_distilled.json",
    "audio": "workflows/Vibevoice_Single-Speaker.json",
}

# ComfyUI output directory (where images/videos are saved)
# This is used to construct full paths for input images in video generation
COMFYUI_OUTPUT_DIR = r"D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\output"

# Video generation timeout (30 minutes - videos take much longer than images)
VIDEO_GENERATION_TIMEOUT = 1800  # seconds

# Generation step control (binary string)
# Position: 0=audio, 1=static_images, 2=scene_images, 3=videos, 4=editing
# Value: 1=run, 0=skip
# Examples:
#   "11111" = Run everything (default)
#   "11100" = Audio + static images + scene images (current default)
#   "01100" = Static + scene images (skip audio)
#   "10000" = Only audio generation
#   "00100" = Only scene images
#   "00001" = Only editing (assume media exists)
GENERATION_STEPS = "11101"

# Audio generation timeout (30 minutes per generation)
AUDIO_GENERATION_TIMEOUT = 1800  # seconds

# YouTube Configuration for Phase 7 (Upload)
YOUTUBE_CLIENT_SECRETS_FILE = PROJECT_ROOT / "client_secrets.json"
YOUTUBE_TOKEN_FILE = PROJECT_ROOT / ".youtube_token.json"
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
DEFAULT_YOUTUBE_CATEGORY = "24"  # Entertainment
DEFAULT_YOUTUBE_PRIVACY = "public"  # public by default
DEFAULT_YOUTUBE_PLAYLIST = "PLr_5rpnSabhkDGfXp_G5ORgHhZY2m8hD6"  # House of Novels playlist


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


def should_run_step(step_index: int) -> bool:
    """Check if a generation step should run based on GENERATION_STEPS config.

    Args:
        step_index: 0=audio, 1=static_images, 2=shot_frames, 3=videos, 4=editing

    Returns:
        True if the step should run, False otherwise
    """
    if step_index < 0 or step_index >= len(GENERATION_STEPS):
        return False
    return GENERATION_STEPS[step_index] == "1"
