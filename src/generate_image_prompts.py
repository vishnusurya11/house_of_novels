#!/usr/bin/env python3
"""
Generate Image Prompts - Create AI image generation prompts for characters, locations, and scenes.

Takes an existing codex file with story data and generates detailed image prompts
for each character (portrait), location (environment art), and scene (illustration).

Usage:
    # Set your OpenRouter API key
    export OPENROUTER_API_KEY="your-key-here"

    # Generate image prompts for a codex (auto-detect style from genre)
    uv run python src/generate_image_prompts.py output/codex_20260104094417.json

    # With specific art style
    uv run python src/generate_image_prompts.py output/codex.json --style anime
    uv run python src/generate_image_prompts.py output/codex.json --style ultra-realistic
    uv run python src/generate_image_prompts.py output/codex.json --style watercolor

    # With custom model
    uv run python src/generate_image_prompts.py output/codex.json --model "x-ai/grok-4.1-fast"

Available styles:
    ultra-realistic  - Photorealistic, cinematic lighting
    anime           - Japanese anime style
    watercolor      - Soft watercolor painting
    oil-painting    - Classical oil painting style
    concept-art     - Game/movie concept art style
    comic           - Comic book / graphic novel style
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for proper package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.story_agents.image_prompt_agents import (
    CharacterImagePromptAgent,
    LocationImagePromptAgent,
    SceneImagePromptAgent,
    SceneImagePromptCriticAgent,
    # Single poster (fallback)
    StoryPosterPromptAgent,
    StoryPosterCriticAgent,
    # Multi-agent poster system (primary)
    CinematicPosterAgent,
    IllustratedPosterAgent,
    GraphicPosterAgent,
    PosterJurySupervisor,
)
from src.config import DEFAULT_MODEL

# Available art styles for image generation
STYLE_CHOICES = [
    "ultra-realistic",
    "anime",
    "watercolor",
    "oil-painting",
    "concept-art",
    "comic",
    "fantasy",      # Genre-based fallbacks
    "sci-fi",
    "noir",
    "horror",
]


def load_codex(codex_path: Path) -> dict:
    """Load codex JSON file."""
    with open(codex_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_codex(codex: dict, codex_path: Path) -> None:
    """Save codex JSON file."""
    with open(codex_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, indent=2, ensure_ascii=False)


def detect_genre(codex: dict) -> str:
    """
    Detect story genre from codex prompts.

    Args:
        codex: Loaded codex dictionary

    Returns:
        Genre string (fantasy, sci-fi, noir, horror, etc.)
    """
    # Get setting prompt from deck_of_worlds
    setting = codex.get("deck_of_worlds", {}).get("prompts", [{}])
    if setting:
        setting = setting[0].get("prompt", "")
    else:
        setting = ""

    # Also check story engine prompt
    story = codex.get("story_engine", {}).get("prompts", [{}])
    if story:
        story = story[0].get("prompt", "")
    else:
        story = ""

    combined = (setting + " " + story).lower()

    # Genre detection heuristics
    if any(w in combined for w in ["castle", "kingdom", "dragon", "magic", "sword", "wizard", "elf", "dwarf"]):
        return "fantasy"
    elif any(w in combined for w in ["spaceship", "planet", "galaxy", "robot", "cyber", "android", "starship"]):
        return "sci-fi"
    elif any(w in combined for w in ["detective", "murder", "crime", "mystery", "noir", "investigation"]):
        return "noir"
    elif any(w in combined for w in ["ghost", "haunted", "demon", "horror", "vampire", "zombie", "nightmare"]):
        return "horror"
    elif any(w in combined for w in ["romance", "love", "heart", "passion"]):
        return "romance"
    elif any(w in combined for w in ["western", "cowboy", "frontier", "sheriff"]):
        return "western"
    else:
        return "fantasy"  # default


def generate_image_prompts(codex_path: str, model: str = None, style: str = None) -> Path:
    """
    Generate image prompts for all characters and locations in codex.

    Args:
        codex_path: Path to codex JSON file
        model: LLM model to use (default: from config)
        style: Art style for prompts (default: auto-detect from genre)

    Returns:
        Path to updated codex file
    """
    model = model or DEFAULT_MODEL
    codex_path = Path(codex_path)

    if not codex_path.exists():
        raise FileNotFoundError(f"Codex not found: {codex_path}")

    codex = load_codex(codex_path)

    # Check if story exists
    if "story" not in codex:
        raise ValueError("Codex has no 'story' section. Run story builder first.")

    story = codex["story"]
    characters = story.get("characters", [])
    locations = story.get("locations", [])

    if not characters and not locations:
        raise ValueError("No characters or locations found in story.")

    # Use provided style or auto-detect from genre
    if style:
        art_style = style
    else:
        art_style = detect_genre(codex)

    # Count scenes
    narrative = story.get("narrative", {})
    scene_count = sum(len(act.get("scenes", [])) for act in narrative.get("acts", []))

    print("\n" + "#" * 60)
    print("# GENERATE IMAGE PROMPTS")
    print("#" * 60)
    print(f"\n>>> Codex: {codex_path.name}")
    print(f">>> Model: {model}")
    print(f">>> Art Style: {art_style}" + (" (auto-detected)" if not style else ""))
    print(f">>> Characters: {len(characters)}")
    print(f">>> Locations: {len(locations)}")
    print(f">>> Scenes: {scene_count}")

    # Generate character image prompts
    if characters:
        print("\n" + "=" * 50)
        print("GENERATING CHARACTER IMAGE PROMPTS")
        print("=" * 50)

        char_agent = CharacterImagePromptAgent(model=model)

        for i, char in enumerate(characters):
            name = char.get("name", f"Character {i+1}")
            print(f"\n>>> [{i+1}/{len(characters)}] {name}...")

            try:
                image_prompt = char_agent.generate_prompt(char, art_style)
                char["image_prompt"] = image_prompt
                print(f"    Generated {len(image_prompt)} chars")
            except Exception as e:
                print(f"    ERROR: {e}")
                char["image_prompt"] = f"Error generating prompt: {e}"

    # Generate location image prompts
    if locations:
        print("\n" + "=" * 50)
        print("GENERATING LOCATION IMAGE PROMPTS")
        print("=" * 50)

        loc_agent = LocationImagePromptAgent(model=model)

        for i, loc in enumerate(locations):
            name = loc.get("name", f"Location {i+1}")
            print(f"\n>>> [{i+1}/{len(locations)}] {name}...")

            try:
                image_prompt = loc_agent.generate_prompt(loc, art_style)
                loc["image_prompt"] = image_prompt
                print(f"    Generated {len(image_prompt)} chars")
            except Exception as e:
                print(f"    ERROR: {e}")
                loc["image_prompt"] = f"Error generating prompt: {e}"

    # Generate scene image prompts
    narrative = story.get("narrative", {})
    scenes = []
    for act in narrative.get("acts", []):
        scenes.extend(act.get("scenes", []))

    if scenes:
        print("\n" + "=" * 50)
        print("GENERATING SCENE IMAGE PROMPTS")
        print("=" * 50)

        scene_agent = SceneImagePromptAgent(model=model)
        critic_agent = SceneImagePromptCriticAgent(model=model)

        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            print(f"\n>>> [{i+1}/{len(scenes)}] Scene {scene_num}...")

            try:
                # Find location profile for this scene
                loc_name = scene.get("location", "")
                location = next(
                    (loc for loc in locations if loc.get("name") == loc_name),
                    None
                )

                # Generate initial prompt
                print(f"    Generating prompt...")
                image_prompt = scene_agent.generate_prompt(
                    scene, characters, location, art_style
                )

                # Critique the prompt
                print(f"    Critiquing...")
                critique = critic_agent.critique(
                    image_prompt, scene, characters, location
                )

                # Revise if needed (moderate or major severity)
                severity = critique.get("severity", "minor")
                if severity in ["moderate", "major"]:
                    print(f"    Revising ({severity} issues)...")
                    image_prompt = scene_agent.revise_prompt(image_prompt, critique)

                scene["image_prompt"] = image_prompt
                print(f"    Generated {len(image_prompt)} chars (severity: {severity})")

            except Exception as e:
                print(f"    ERROR: {e}")
                scene["image_prompt"] = f"Error generating prompt: {e}"

        # Update narrative with scene prompts
        codex["story"]["narrative"] = narrative

    # Generate story poster prompts (9 candidates, 3 winners via jury voting)
    outline = story.get("outline", {})
    if outline.get("title"):
        print("\n" + "=" * 50)
        print("GENERATING STORY POSTER PROMPTS (Multi-Agent)")
        print("=" * 50)

        print(f"\n>>> Title: '{outline.get('title')}'")

        try:
            # Phase 1: Generate 9 prompts (3 agents × 3 compositions each)
            print("\n>>> Phase 1: Generating 9 poster candidates...")

            cinematic = CinematicPosterAgent(model=model)
            illustrated = IllustratedPosterAgent(model=model)
            graphic = GraphicPosterAgent(model=model)

            all_prompts = []

            print("    CINEMATIC agent generating 3 prompts...")
            cinematic_prompts = cinematic.generate_prompts(
                outline, characters, locations, art_style
            )
            all_prompts.extend(cinematic_prompts)
            print(f"    -> Generated {len(cinematic_prompts)} cinematic prompts")

            print("    ILLUSTRATED agent generating 3 prompts...")
            illustrated_prompts = illustrated.generate_prompts(
                outline, characters, locations, art_style
            )
            all_prompts.extend(illustrated_prompts)
            print(f"    -> Generated {len(illustrated_prompts)} illustrated prompts")

            print("    GRAPHIC agent generating 3 prompts...")
            graphic_prompts = graphic.generate_prompts(
                outline, characters, locations, art_style
            )
            all_prompts.extend(graphic_prompts)
            print(f"    -> Generated {len(graphic_prompts)} graphic prompts")

            print(f"\n    Total candidates: {len(all_prompts)}")

            # Phase 2: Jury voting
            print("\n>>> Phase 2: Jury voting on top 3...")

            jury = PosterJurySupervisor(model=model)
            voting_results = jury.run_voting(all_prompts, outline)

            # Store results
            outline["poster_prompts"] = voting_results["winners"]  # Top 3 winners
            outline["all_poster_candidates"] = voting_results["all_prompts"]  # All 9 prompts
            outline["poster_voting_metadata"] = voting_results["voting_metadata"]
            codex["story"]["outline"] = outline

            print(f"\n    Top 3 selected from {len(all_prompts)} candidates:")
            for i, winner in enumerate(voting_results["winners"], 1):
                score = winner.get("score", 0)
                agent = winner.get("agent", "Unknown")
                comp = winner.get("composition", "unknown")
                print(f"    #{i}: {agent} - {comp} ({score} pts)")

        except Exception as e:
            print(f"\n    ERROR in multi-agent system: {e}")
            print("    Falling back to single poster generation...")

            # Fallback to single poster system
            try:
                poster_agent = StoryPosterPromptAgent(model=model)
                poster_critic = StoryPosterCriticAgent(model=model)

                poster_prompt = poster_agent.generate_prompt(
                    outline, characters, locations, art_style
                )

                critique = poster_critic.critique(poster_prompt, outline, characters)
                severity = critique.get("severity", "minor")

                if severity in ["moderate", "major"]:
                    poster_prompt = poster_agent.revise_prompt(poster_prompt, critique)

                # Store as single-element array for consistency
                outline["poster_prompts"] = [{
                    "agent": "FALLBACK",
                    "composition": "single",
                    "prompt": poster_prompt,
                    "style": art_style,
                    "score": 0
                }]
                codex["story"]["outline"] = outline
                print(f"    Fallback generated {len(poster_prompt)} chars")

            except Exception as fallback_e:
                print(f"    FALLBACK ERROR: {fallback_e}")
                outline["poster_prompts"] = []
                codex["story"]["outline"] = outline

    # Update codex
    codex["story"]["characters"] = characters
    codex["story"]["locations"] = locations
    codex["image_prompts_generated_at"] = datetime.now().isoformat()

    # Save back to same file
    save_codex(codex, codex_path)

    print("\n" + "#" * 60)
    print(f"# Image prompts saved to: {codex_path}")
    print("#" * 60)

    # Print sample prompts
    if characters and characters[0].get("image_prompt"):
        print(f"\n>>> Sample character prompt ({characters[0].get('name', 'Character 1')}):")
        prompt = characters[0]["image_prompt"]
        print(f"    {prompt[:200]}..." if len(prompt) > 200 else f"    {prompt}")

    if locations and locations[0].get("image_prompt"):
        print(f"\n>>> Sample location prompt ({locations[0].get('name', 'Location 1')}):")
        prompt = locations[0]["image_prompt"]
        print(f"    {prompt[:200]}..." if len(prompt) > 200 else f"    {prompt}")

    if scenes and scenes[0].get("image_prompt"):
        print(f"\n>>> Sample scene prompt (Scene {scenes[0].get('scene_number', 1)}):")
        prompt = scenes[0]["image_prompt"]
        print(f"    {prompt[:200]}..." if len(prompt) > 200 else f"    {prompt}")

    if outline.get("poster_prompts"):
        print(f"\n>>> Story poster prompts ({outline.get('title', 'Untitled')}):")
        for i, poster in enumerate(outline["poster_prompts"][:3], 1):
            agent = poster.get("agent", "Unknown")
            comp = poster.get("composition", "unknown")
            score = poster.get("score", 0)
            prompt = poster.get("prompt", "")
            print(f"\n    #{i} [{agent}/{comp}] ({score} pts):")
            print(f"    {prompt[:150]}..." if len(prompt) > 150 else f"    {prompt}")

    return codex_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI image prompts for characters, locations, and scenes in a codex"
    )
    parser.add_argument(
        "codex_path",
        help="Path to codex JSON file"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--style",
        choices=STYLE_CHOICES,
        default="anime",
        help="Art style for image prompts: ultra-realistic, anime, watercolor, oil-painting, concept-art, comic (default: auto-detect from genre)"
    )
    args = parser.parse_args()

    generate_image_prompts(args.codex_path, args.model, args.style)


if __name__ == "__main__":
    main()
