#!/usr/bin/env python3
"""
Thumbnail Prompt Generation via Agent Council

Uses 4 specialized agents that debate and vote on the best thumbnail prompts
for YouTube audiobook/story videos. Generates 12 candidates (3 per agent)
and selects top 5 through voting.

Based on pheonix project's generate_image_prompts.py approach.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple

from langchain_openai import ChatOpenAI

from src.config import DEFAULT_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


# =============================================================================
# Genre-specific multi-shot learning examples (Anime/Cartoon style)
# =============================================================================

EXAMPLE_PROMPTS = {
    'fantasy': [
        """Anime style illustration, create a YouTube thumbnail combining 4 iconic fantasy elements: (1) a young woman with flowing silver hair and emerald cloak standing at an ancient stone altar, magical runes glowing beneath her feet, (2) a wise mentor figure in weathered robes watching from twisted oak trees, (3) swirling vortex of golden light erupting from the altar reaching toward a dramatic moonlit sky, (4) mystical forest clearing with mist curling at ground level framing the scene. Use vibrant color palette of deep emerald greens, magical gold, mysterious purples, and cool moonlight blues that pop on mobile screens. Title typography integrates naturally: story title in BOLD mystical display font with magical glow effects, clearly readable. anime art style, cel shaded, vibrant saturated colors, Studio Ghibli inspired, expressive character design, high quality anime""",

        """Cartoon illustration, create a YouTube thumbnail layering 5 adventure elements: (1) heroic protagonist with determined expression wielding glowing sword in dynamic action pose, (2) towering dark castle silhouette against stormy dramatic sky, (3) companion characters in supporting formation - wise wizard, brave warrior, cunning rogue, (4) ancient map and magical artifacts scattered in foreground, (5) swirling dark magic threatening from castle. Bold color scheme of heroic blues, warning reds, magical purples, and golden hope against dark shadows. Title typography: story title in MASSIVE bold fantasy font dominating center with metallic effects. cartoon art style, hand-drawn animation quality, colorful and expressive, bold outlines, professional cartoon art""",
    ],

    'mystery': [
        """Anime style illustration, create a noir-inspired YouTube thumbnail combining 4 mystery elements: (1) detective protagonist in dramatic shadow, only eyes and collar visible, sharp intelligent gaze, (2) scattered clues in foreground - torn photograph, cryptic note, antique key, (3) foggy Victorian street scene with gas lamps casting pools of light, (4) mysterious silhouette watching from window above. Color palette of deep noir blacks, amber lamplight, fog grays, and accent red for danger. Title typography: story title in bold noir display font with dramatic shadow effects. anime art style, cel shaded, dramatic lighting, expressive character design, high quality anime""",
    ],

    'romance': [
        """Anime style illustration, create an emotional YouTube thumbnail combining 4 romance elements: (1) two protagonists in meaningful glance, expressive eyes conveying unspoken feelings, (2) symbolic flowers - roses, cherry blossoms - creating soft frame, (3) dreamy background of sunset or starlit sky with warm glow, (4) subtle visual metaphors - intertwined paths, matching jewelry, symbolic objects. Warm romantic palette of soft pinks, warm sunset oranges, dreamy purples, and heart reds. Title typography: story title in beautiful flowing display font with subtle sparkle effects. anime art style, cel shaded, soft romantic lighting, beautiful character design, shoujo manga inspired, high quality anime""",
    ],

    'adventure': [
        """Cartoon illustration, create an action-packed YouTube thumbnail combining 5 adventure elements: (1) hero in mid-action leap or dramatic pose showing determination, (2) exotic dangerous location - jungle ruins, mountain peaks, ocean waves, (3) companion team showing diverse skills and personalities, (4) treasure or goal visible in background creating clear objective, (5) obstacles and dangers surrounding scene. Vibrant adventure palette of jungle greens, treasure golds, danger reds, sky blues, and earth browns. Title typography: story title in MASSIVE action display font with dynamic effects. cartoon art style, hand-drawn animation quality, dynamic action poses, bold outlines, professional cartoon art""",
    ],

    'drama': [
        """Anime style illustration, create an emotionally impactful YouTube thumbnail combining 4 drama elements: (1) protagonist in moment of emotional intensity - determination, grief, hope, (2) symbolic imagery representing the story's core conflict or theme, (3) supporting characters reflecting different perspectives or relationships, (4) environment that reinforces emotional tone - storm, sunset, empty space. Dramatic palette of emotional blues, passionate reds, contemplative grays, and hope-filled golds. Title typography: story title in powerful dramatic display font, bold and readable. anime art style, cel shaded, emotional lighting, expressive faces, character-driven composition, high quality anime""",
    ],
}


def select_relevant_examples(genre: str) -> List[str]:
    """Select relevant example prompts based on story genre."""
    genre_lower = genre.lower()
    selected = []

    if any(word in genre_lower for word in ['fantasy', 'magic', 'supernatural']):
        selected.extend(EXAMPLE_PROMPTS.get('fantasy', []))

    if any(word in genre_lower for word in ['mystery', 'thriller', 'detective', 'crime']):
        selected.extend(EXAMPLE_PROMPTS.get('mystery', []))

    if any(word in genre_lower for word in ['romance', 'love', 'relationship']):
        selected.extend(EXAMPLE_PROMPTS.get('romance', []))

    if any(word in genre_lower for word in ['adventure', 'action', 'quest']):
        selected.extend(EXAMPLE_PROMPTS.get('adventure', []))

    if any(word in genre_lower for word in ['drama', 'literary', 'emotional']):
        selected.extend(EXAMPLE_PROMPTS.get('drama', []))

    # Default: use fantasy + adventure examples
    if not selected:
        selected = EXAMPLE_PROMPTS.get('fantasy', [])[:1] + EXAMPLE_PROMPTS.get('adventure', [])[:1]

    return selected[:3]  # Max 3 examples


# =============================================================================
# Agent Council Definitions
# =============================================================================

THUMBNAIL_AGENT_ROLES = {
    'visual_director': {
        'name': 'Visual Composition Director',
        'prompt': """You are a Visual Composition Director specializing in {style_name} YouTube thumbnail composition.

STORY CONTEXT:
- Title: "{title}"
- Logline: {logline}
- Characters: {char_descriptions}
- Key Moments: {key_moments}

VISUAL STYLE: {style_name}
- Prefix (START prompts with this): "{style_prefix}"
- Suffix (END prompts with this): "{style_suffix}"

REFERENCE EXAMPLES:
{examples}

YOUR TASK: Generate exactly 3 thumbnail prompts that:
1. START with: "{style_prefix}"
2. COMBINE 3-5 iconic story elements in ONE {style_name} composition
3. Focus on VISUAL IMPACT, composition balance, and clear focal points
4. Include TITLE typography: "{title}" in BOLD expressive display font integrated into composition
5. Specify COLORS that pop on YouTube (list specific colors)
6. END with: "{style_suffix}"

OUTPUT FORMAT:
- Generate exactly 3 prompts
- Each prompt: 150-200 words, single paragraph
- Each prompt starts with the style prefix
- No numbering, no headers, just 3 paragraphs separated by blank lines"""
    },

    'story_specialist': {
        'name': 'Story Visual Specialist',
        'prompt': """You are a Story Visual Specialist who captures key narrative moments in {style_name} style.

STORY CONTEXT:
- Title: "{title}"
- Logline: {logline}
- Characters: {char_descriptions}
- Key Moments: {key_moments}

VISUAL STYLE: {style_name}
- Prefix: "{style_prefix}"
- Suffix: "{style_suffix}"

REFERENCE EXAMPLES:
{examples}

YOUR TASK: Generate exactly 3 thumbnail prompts that:
1. START with: "{style_prefix}"
2. Capture the EMOTIONAL CORE of the story
3. Show character dynamics and key relationships visually
4. Include recognizable plot elements fans would identify
5. Include TITLE typography: "{title}" in BOLD expressive display font integrated into composition
6. END with: "{style_suffix}"

OUTPUT FORMAT:
- Generate exactly 3 prompts
- Each prompt: 150-200 words, single paragraph
- Each prompt starts with the style prefix
- No numbering, no headers, just 3 paragraphs separated by blank lines"""
    },

    'engagement_expert': {
        'name': 'Engagement Psychology Expert',
        'prompt': """You are an Engagement Psychology Expert optimizing {style_name} thumbnails for maximum YouTube clicks.

STORY CONTEXT:
- Title: "{title}"
- Logline: {logline}
- Characters: {char_descriptions}
- Key Moments: {key_moments}

VISUAL STYLE: {style_name}
- Prefix: "{style_prefix}"
- Suffix: "{style_suffix}"

REFERENCE EXAMPLES:
{examples}

YOUR TASK: Generate exactly 3 thumbnail prompts that:
1. START with: "{style_prefix}"
2. MAXIMIZE click-through with curiosity triggers and emotional hooks
3. Use BOLD, SATURATED colors that pop against YouTube's white interface
4. Create clear visual hierarchy optimized for mobile (320px width)
5. Include TITLE typography: "{title}" in MASSIVE attention-grabbing display font
6. END with: "{style_suffix}"

OUTPUT FORMAT:
- Generate exactly 3 prompts
- Each prompt: 150-200 words, single paragraph
- Each prompt starts with the style prefix
- No numbering, no headers, just 3 paragraphs separated by blank lines"""
    },

    'genre_master': {
        'name': 'Genre Visual Master',
        'prompt': """You are a Genre Visual Master creating {style_name} thumbnails that match story genre expectations.

STORY CONTEXT:
- Title: "{title}"
- Logline: {logline}
- Genre: {genre}
- Characters: {char_descriptions}
- Key Moments: {key_moments}

VISUAL STYLE: {style_name}
- Prefix: "{style_prefix}"
- Suffix: "{style_suffix}"

REFERENCE EXAMPLES:
{examples}

YOUR TASK: Generate exactly 3 thumbnail prompts that:
1. START with: "{style_prefix}"
2. Match {genre} genre visual conventions and expectations
3. Balance familiar genre elements with book-specific unique details
4. Include genre-appropriate mood, atmosphere, and color palette
5. Include TITLE typography: "{title}" in genre-appropriate BOLD display font
6. END with: "{style_suffix}"

OUTPUT FORMAT:
- Generate exactly 3 prompts
- Each prompt: 150-200 words, single paragraph
- Each prompt starts with the style prefix
- No numbering, no headers, just 3 paragraphs separated by blank lines"""
    }
}


VOTING_PROMPT = """You are a thumbnail quality evaluator. Score each thumbnail prompt on these criteria (1-10 each):

1. VISUAL IMPACT: Does it grab attention instantly? Clear focal point? Bold composition?
2. STORY CAPTURE: Does it represent the story's essence? Recognizable to fans?
3. STYLE CONSISTENCY: Does it properly use the {style_name} style prefix/suffix?
4. TITLE INTEGRATION: Is the title integrated as bold, readable typography?
5. MOBILE CLARITY: Will it work at small thumbnail size (320px)?
6. COLOR EFFECTIVENESS: Are colors bold and YouTube-optimized?

PROMPTS TO EVALUATE:
{prompts}

For each prompt, provide:
- Scores for each criterion (1-10)
- Total score (sum of all criteria, max 60)
- One sentence explaining your top pick

OUTPUT FORMAT (JSON):
{{
    "scores": [
        {{"prompt_index": 0, "visual": 8, "story": 7, "style": 9, "typography": 8, "mobile": 7, "color": 8, "total": 47}},
        ...
    ],
    "top_pick_index": 2,
    "top_pick_reason": "Best captures the emotional core while maintaining mobile clarity"
}}"""


# =============================================================================
# Agent Functions
# =============================================================================

def extract_prompts_from_response(response_text: str) -> List[str]:
    """Extract individual prompts from agent response."""
    prompts = []

    # Clean the response
    text = response_text.strip()

    # Remove markdown formatting
    text = re.sub(r'^#+\s*.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*.*?\*\*\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+[\.\)]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-•]\s*', '', text, flags=re.MULTILINE)

    # Split by double newlines
    paragraphs = re.split(r'\n\s*\n', text)

    for para in paragraphs:
        para = para.strip()
        # Valid prompts are long and contain style keywords
        if len(para) > 100 and any(kw in para.lower() for kw in ['anime', 'cartoon', 'illustration', 'thumbnail']):
            prompts.append(para)

    return prompts[:3]  # Max 3 per agent


def run_single_agent(
    agent_key: str,
    agent_info: dict,
    context: dict,
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
) -> List[str]:
    """Run a single agent to generate thumbnail prompts."""

    if verbose:
        print(f"    >>> {agent_info['name']} generating prompts...")

    # Format the agent prompt with context
    prompt_text = agent_info['prompt'].format(**context)

    # Create LLM
    llm = ChatOpenAI(model=model, temperature=0.8, api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

    # Generate
    response = llm.invoke(prompt_text)

    # Extract prompts
    prompts = extract_prompts_from_response(response.content)

    if verbose:
        print(f"        Generated {len(prompts)} prompts")

    return prompts


def vote_on_prompts(
    all_prompts: List[str],
    style_name: str,
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
) -> List[Tuple[int, float]]:
    """Have agents vote on all prompts. Returns list of (index, score) tuples."""

    if verbose:
        print(f"\n>>> Council voting on {len(all_prompts)} candidates...")

    # Format prompts for voting
    prompts_text = "\n\n".join([
        f"[Prompt {i}]\n{p}" for i, p in enumerate(all_prompts)
    ])

    voting_prompt = VOTING_PROMPT.format(
        style_name=style_name,
        prompts=prompts_text
    )

    # Use a more analytical model for voting
    llm = ChatOpenAI(model=model, temperature=0.3, api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

    try:
        response = llm.invoke(voting_prompt)

        # Try to parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response.content)
        if json_match:
            result = json.loads(json_match.group())
            scores = result.get('scores', [])

            # Build score list
            score_list = []
            for score_item in scores:
                idx = score_item.get('prompt_index', 0)
                total = score_item.get('total', 0)
                score_list.append((idx, total))

            if verbose:
                print(f"    Voting complete. Top score: {max(s[1] for s in score_list) if score_list else 0}")

            return score_list

    except Exception as e:
        if verbose:
            print(f"    Voting parse error: {e}")

    # Fallback: equal scores
    return [(i, 30) for i in range(len(all_prompts))]


# =============================================================================
# Main Orchestration
# =============================================================================

def generate_thumbnail_prompts_via_council(
    codex: dict,
    model: str = DEFAULT_MODEL,
    verbose: bool = True,
) -> dict:
    """
    Generate thumbnail prompts using agent council debate and voting.

    Returns:
        dict with:
        - prompts: Top 5 ranked prompts
        - all_candidates: All 12 generated prompts
        - voting_results: Scores and rankings
        - style: Visual style used
        - metadata: Generation metadata
    """

    if verbose:
        print("\n" + "=" * 60)
        print("THUMBNAIL GENERATION: Agent Council")
        print("=" * 60)

    # Get visual_style from codex (set in Phase 0)
    visual_style = codex.get("config", {}).get("visual_style", {})
    style_prefix = visual_style.get("prefix", "Anime style illustration,")
    style_suffix = visual_style.get("suffix", "anime art style, cel shaded, vibrant saturated colors, high quality anime")
    style_name = visual_style.get("name", "Anime")
    style_description = visual_style.get("description", "Japanese anime style")

    if verbose:
        print(f"\n>>> Visual Style: {style_name}")

    # Extract story context
    story = codex.get("story", {})
    outline = story.get("outline", {})
    chapters_data = story.get("chapters", {})

    # Get title from chapters_data (Step 7 naming) OR fallback to outline
    title = chapters_data.get("title") or outline.get("title", "Untitled Story")
    logline = outline.get("logline", "A compelling story unfolds.")
    genre = codex.get("config", {}).get("genre", "fantasy")

    # Character descriptions
    characters = story.get("characters", [])
    char_descriptions = []
    for c in characters:
        phys = c.get("physical", {})
        desc = f"{c.get('name', 'Unknown')} ({c.get('role_in_story', 'unknown')}): {phys.get('hair', 'unknown')} hair, {phys.get('eyes', 'unknown')} eyes, {phys.get('clothing', 'typical attire')}"
        char_descriptions.append(desc)

    # Key moments from chapters
    chapters = chapters_data.get("chapters", [])
    key_moments = []
    for chapter in chapters:
        for scene in chapter.get("scenes", []):
            # Use prose snippet as summary if no explicit summary
            summary = scene.get("summary", "")
            if not summary:
                prose = scene.get("prose", "")
                summary = prose[:200] + "..." if len(prose) > 200 else prose
            if summary:
                key_moments.append(summary)
    key_moments = key_moments[:5]  # Max 5 moments

    # Select genre examples
    examples = select_relevant_examples(genre)
    examples_text = "\n\n".join(examples) if examples else "No specific examples available."

    # Build context for agents
    context = {
        'title': title,
        'logline': logline,
        'genre': genre,
        'char_descriptions': "\n".join(char_descriptions) if char_descriptions else "Characters not yet defined.",
        'key_moments': "\n".join(f"- {m}" for m in key_moments) if key_moments else "Story moments not yet defined.",
        'style_name': style_name,
        'style_prefix': style_prefix,
        'style_suffix': style_suffix,
        'style_description': style_description,
        'examples': examples_text,
    }

    # STEP 1: Each agent generates 3 prompts (12 total)
    if verbose:
        print(f"\n>>> Step 1: Agents generating prompts...")

    all_prompts = []
    agent_contributions = {}

    for agent_key, agent_info in THUMBNAIL_AGENT_ROLES.items():
        prompts = run_single_agent(agent_key, agent_info, context, model, verbose)
        all_prompts.extend(prompts)
        agent_contributions[agent_key] = len(prompts)

    if verbose:
        print(f"\n>>> Total candidates: {len(all_prompts)}")

    if not all_prompts:
        # Fallback if no prompts generated
        fallback_prompt = f"{style_prefix} YouTube thumbnail for \"{title}\", featuring main characters in dramatic {genre} scene composition with bold colors and clear focal point, {style_suffix}"
        return {
            "prompts": [fallback_prompt],
            "all_candidates": [fallback_prompt],
            "voting_results": [],
            "style": visual_style,
            "metadata": {"error": "No prompts generated, using fallback"},
        }

    # STEP 2: Voting round
    if verbose:
        print(f"\n>>> Step 2: Council voting...")

    vote_results = vote_on_prompts(all_prompts, style_name, model, verbose)

    # STEP 3: Rank and select top 5
    if verbose:
        print(f"\n>>> Step 3: Selecting top 5...")

    # Sort by score descending
    indexed_prompts = [(all_prompts[i], score) for i, score in vote_results if i < len(all_prompts)]
    if not indexed_prompts:
        indexed_prompts = [(p, 30) for p in all_prompts]  # Fallback equal scores

    ranked = sorted(indexed_prompts, key=lambda x: x[1], reverse=True)
    top_5 = [p for p, s in ranked[:5]]

    if verbose:
        print(f"\n>>> Selected {len(top_5)} top prompts")
        print("=" * 60)

    return {
        "prompts": top_5,
        "all_candidates": all_prompts,
        "voting_results": vote_results,
        "style": visual_style,
        "metadata": {
            "title": title,
            "genre": genre,
            "total_candidates": len(all_prompts),
            "agent_contributions": agent_contributions,
        },
    }


# =============================================================================
# Standalone execution
# =============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python -m src.story_agents.thumbnail_agents <codex_path>")
        sys.exit(1)

    codex_path = Path(sys.argv[1])

    with open(codex_path, 'r', encoding='utf-8') as f:
        codex = json.load(f)

    result = generate_thumbnail_prompts_via_council(codex, verbose=True)

    print("\n" + "=" * 60)
    print("TOP 5 THUMBNAIL PROMPTS:")
    print("=" * 60)
    for i, prompt in enumerate(result["prompts"], 1):
        print(f"\n--- Prompt {i} ---")
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)