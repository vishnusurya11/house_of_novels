"""
Chapter Title Card Agents — Generate a shared template prompt for chapter title cards.

Architecture (matching E3):
1. Generate ONE reusable template prompt with placeholder text ("CHAPTER I" / "CHAPTER TITLE")
2. Per-chapter edit prompts are generated programmatically (simple f-string replacement)
3. Phase 3 generates ONE template image, then Qwen Edit per chapter

Design informed by film title card conventions (HBO prestige TV, Netflix originals)
and audiobook production standards. Font recommendations sourced from professional
typography research: Cinzel (fantasy), Bebas Neue (thriller), Playfair Display (romance).

Workflow:
1. ChapterTitleCardComposerAgent — generates ONE template background prompt
2. ChapterTitleCardCriticAgent — validates atmosphere, text space, genre fit
3. Composer revises based on critique (up to max_revisions rounds)
4. Per-chapter edit prompts generated programmatically via _roman_numeral()
"""

from src.story_agents.base_story_agent import BaseStoryAgent
from src.story_schemas import ChapterTitleCardPromptSchema, ChapterTitleCardCritiqueSchema
from src.config import DEFAULT_MODEL


# Genre → font style mapping for title card text
GENRE_FONT_STYLES = {
    "fantasy": {
        "font": "Cinzel Decorative serif",
        "color": "gold with subtle warm glow",
        "palette": "deep midnight blue, royal purple, gold accents",
        "atmosphere": "ancient mystical, volumetric fog, candlelight or starlight",
    },
    "sci-fi": {
        "font": "geometric sans-serif like Bebas Neue",
        "color": "ice blue with holographic shimmer",
        "palette": "deep teal, electric blue, dark cyan, black void",
        "atmosphere": "futuristic, holographic elements, deep space nebula",
    },
    "noir": {
        "font": "bold condensed sans-serif like Futura Bold",
        "color": "stark white with sharp shadow",
        "palette": "near-black, deep charcoal, isolated crimson accent",
        "atmosphere": "rain-slicked streets, harsh shadows, neon glow, film noir",
    },
    "horror": {
        "font": "distressed irregular serif",
        "color": "bone white with cracked texture",
        "palette": "pure black, deep crimson, sickly green undertone",
        "atmosphere": "thick fog, decay, ominous shadows, desaturated",
    },
    "romance": {
        "font": "elegant serif like Playfair Display",
        "color": "warm cream with soft glow",
        "palette": "warm amber, muted rose, golden hour tones",
        "atmosphere": "soft bokeh, golden hour light, dreamy warmth",
    },
    "western": {
        "font": "weathered slab serif",
        "color": "burnt sienna on dusty parchment",
        "palette": "desert ochre, burnt orange, dusty brown, pale sky",
        "atmosphere": "desert heat haze, dust motes, frontier sunset",
    },
}

DEFAULT_FONT_STYLE = {
    "font": "elegant Cinzel serif",
    "color": "gold with subtle glow",
    "palette": "dark atmospheric tones, deep blue, warm gold accents",
    "atmosphere": "cinematic, moody, volumetric lighting",
}


def _roman_numeral(n: int) -> str:
    """Convert integer to Roman numeral."""
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for val, numeral in vals:
        while n >= val:
            result += numeral
            n -= val
    return result


class ChapterTitleCardComposerAgent(BaseStoryAgent):
    """Generates cinematic chapter title card background prompts.

    Uses genre-aware font and color mapping to produce atmospheric backgrounds
    with centered placeholder text. The prompt instructs the image model to
    render text in a specific font style so Qwen Edit can maintain visual
    consistency when replacing the placeholder with the actual chapter title.

    References: Film title card conventions (HBO, Netflix), Cinzel/Bebas Neue
    typography research, prestige audiobook production standards.
    """

    @property
    def name(self) -> str:
        return "CHAPTER_TITLE_CARD_COMPOSER"

    @property
    def role(self) -> str:
        return "Chapter Title Card Composer"

    @property
    def system_prompt(self) -> str:
        return """You are an expert cinematic title card designer specializing in chapter cards for premium audiobook video productions.

Your task: generate an atmospheric background image prompt with placeholder chapter text centered in the frame.

## COMPOSITION RULES

1. The CENTER of the image must contain placeholder text (e.g., "CHAPTER I") rendered in the specified font style
2. The center area must remain VISUALLY CLEAN so the text is clearly readable
3. World details, atmosphere, and visual interest should appear AROUND THE EDGES of the frame
4. Use dark vignette at edges to draw the eye toward the center text
5. The scene should hint at the WORLD and LORE of the book, not recreate a specific scene
6. Focus on mood, symbolism, and atmosphere — iconic objects, recognizable locations, environmental storytelling

## PROMPT STRUCTURE

Your background_prompt must describe:
1. COMPOSITION: "Cinematic wide shot, symmetrical composition, centered text area"
2. ENVIRONMENT: Atmospheric scene from the book's world around the edges
3. TEXT: The placeholder text in the specified font style, centered, with the exact font description
4. LIGHTING: Moody, cinematic lighting that supports text readability (dark backgrounds)
5. ATMOSPHERE: Genre-appropriate mood (fog, particles, glow effects)
6. QUALITY: "8K, cinematic, film grain, professional title card"

## QWEN EDIT PROMPT

Your qwen_edit_prompt must be a clear instruction like:
"Replace the text 'CHAPTER I' in the center of the image with 'Chapter 1' in the same font style, and below it in slightly larger font write 'The Awakening'"

## CONSTRAINTS
- Prompt: 150-250 words, single flowing paragraph
- The placeholder text MUST be in quotes in the prompt so the image model renders it
- Background should be dark enough for text to be readable
- Do NOT reference specific scenes or spoil plot points
- Use the book's world elements (artifacts, environments, symbols) for atmosphere"""

    def compose_template(
        self,
        genre: str,
        visual_style: dict,
        book_title: str,
        setting_context: str = "",
        revision_context: str = "",
    ) -> ChapterTitleCardPromptSchema:
        """Generate a reusable template prompt for ALL chapter title cards.

        Creates ONE background prompt with "CHAPTER I" / "CHAPTER TITLE" placeholder
        text. Per-chapter edits are done programmatically, not by LLM.

        Args:
            genre: Detected genre (fantasy, sci-fi, noir, etc.)
            visual_style: Visual style dict with name, prefix, suffix
            book_title: The book's title for context
            setting_context: Setting/world description from deck_of_worlds
            revision_context: Critic feedback for revision (empty on first call)

        Returns:
            ChapterTitleCardPromptSchema with template background prompt
        """
        font_style = GENRE_FONT_STYLES.get(genre, DEFAULT_FONT_STYLE)

        style_name = visual_style.get("name", "Cinematic") if visual_style else "Cinematic"
        style_prefix = visual_style.get("prefix", "") if visual_style else ""
        style_suffix = visual_style.get("suffix", "") if visual_style else ""

        user_prompt = f"""Generate a REUSABLE chapter title card template prompt for:

BOOK: "{book_title}"
GENRE: {genre}
WORLD/SETTING: {setting_context[:500] if setting_context else "N/A"}

This is a TEMPLATE image — it will be reused for ALL chapters. Actual chapter
titles will be overlaid via AI image editing in post-production.

FONT STYLE REQUIREMENTS:
- Font: {font_style['font']}
- Text color: {font_style['color']}
- Color palette: {font_style['palette']}
- Atmosphere: {font_style['atmosphere']}

PLACEHOLDER TEXT: "CHAPTER I" on one line, "CHAPTER TITLE" below in larger font
(This placeholder will be replaced per-chapter by Qwen Image Edit)

VISUAL STYLE: {style_name}
{"STYLE PREFIX (START your prompt with EXACTLY this): " + style_prefix if style_prefix else ""}
{"STYLE SUFFIX (END your prompt with EXACTLY this): " + style_suffix if style_suffix else ""}

Generate:
1. background_prompt: atmospheric scene from the book's world with "CHAPTER I" and
   "CHAPTER TITLE" placeholder text centered in {font_style['font']}, {font_style['color']} color.
   World elements around the edges. Heavy dark vignette. 150-250 words, single paragraph.
2. placeholder_text: "CHAPTER I"
3. font_style_description: describe the font rendering style for consistency
4. qwen_edit_prompt: "Replace 'CHAPTER I' with 'CHAPTER I' and 'CHAPTER TITLE' with 'CHAPTER TITLE' in the same font style"
5. mood: the overall mood
6. color_palette: dominant colors
{revision_context}"""

        return self.invoke_structured(
            user_prompt,
            ChapterTitleCardPromptSchema,
            max_tokens=2000,
        )


class ChapterTitleCardCriticAgent(BaseStoryAgent):
    """Critiques chapter title card prompts for quality and genre fit.

    Validates that the background prompt creates appropriate atmosphere,
    leaves clean center space for text, and matches the story's visual style.

    Scoring: atmosphere (evocative scene), text_space (clean center),
    style_consistency (matches visual style), genre_fit (suits the genre).
    """

    @property
    def name(self) -> str:
        return "CHAPTER_TITLE_CARD_CRITIC"

    @property
    def role(self) -> str:
        return "Chapter Title Card Critic"

    @property
    def system_prompt(self) -> str:
        return """You are a critical reviewer of chapter title card image prompts for premium audiobook productions.

## EVALUATION CRITERIA (Score 1-10 each):

1. ATMOSPHERE (1-10): Is the background evocative and cinematic? Does it create mood?
   - 10: Stunning atmospheric scene with world-building elements
   - 5: Generic or bland background
   - 1: No atmosphere, flat description

2. TEXT_SPACE (1-10): Does the composition leave clean center space for text?
   - 10: Clear center area, visual interest at edges, dark vignette
   - 5: Some clutter in center but readable
   - 1: Center is busy and text would be unreadable

3. STYLE_CONSISTENCY (1-10): Does it match the visual style?
   - 10: Perfect style adherence with correct prefix/suffix
   - 5: Partial style match
   - 1: Completely wrong style

4. GENRE_FIT (1-10): Does the design suit the story genre?
   - 10: Perfect genre atmosphere (dark for thriller, magical for fantasy, etc.)
   - 5: Generic, could be any genre
   - 1: Wrong genre aesthetic

## DECISION RULES
- If ANY score is below 7, set needs_revision = true
- Provide SPECIFIC suggestions for improvement
- Check that placeholder text is described with proper font style
- Verify the qwen_edit_prompt is clear and actionable"""

    def critique(
        self,
        prompt_schema: ChapterTitleCardPromptSchema,
        visual_style: dict,
        book_title: str = "",
    ) -> ChapterTitleCardCritiqueSchema:
        """Evaluate a template title card prompt for quality.

        Args:
            prompt_schema: The template prompt to critique
            visual_style: Visual style dict
            book_title: Book title for context

        Returns:
            ChapterTitleCardCritiqueSchema with scores and suggestions
        """
        style_name = visual_style.get("name", "Cinematic") if visual_style else "Cinematic"
        style_prefix = visual_style.get("prefix", "") if visual_style else ""

        user_prompt = f"""Critically evaluate this chapter title card TEMPLATE prompt.
This is a reusable template for all chapters — not chapter-specific.

## PROMPT TO EVALUATE:
Background: {prompt_schema.background_prompt}
Placeholder: {prompt_schema.placeholder_text}
Font Style: {prompt_schema.font_style_description}
Mood: {prompt_schema.mood}
Colors: {prompt_schema.color_palette}

## BOOK: "{book_title}"

## VISUAL STYLE: {style_name}
Expected prefix: {style_prefix}

Score each criterion 1-10 and provide specific improvement suggestions.
Set needs_revision=true if any score is below 7."""

        return self.invoke_structured(
            user_prompt,
            ChapterTitleCardCritiqueSchema,
            max_tokens=1500,
        )


def generate_chapter_card_template_prompt(
    codex: dict,
    visual_style: dict,
    genre: str,
    model: str = DEFAULT_MODEL,
    max_revisions: int = 2,
) -> dict:
    """Generate ONE shared template prompt for all chapter title cards.

    Matching E3's architecture: one template image, per-chapter Qwen Edits.

    Args:
        codex: Full codex with story data
        visual_style: Visual style dict with name, prefix, suffix
        genre: Detected genre (fantasy, sci-fi, noir, etc.)
        model: LLM model to use
        max_revisions: Maximum revision cycles

    Returns:
        Dict with template prompt fields + revision_count, final_scores, critique_history
    """
    composer = ChapterTitleCardComposerAgent(model=model)
    critic = ChapterTitleCardCriticAgent(model=model, temperature=0.3)

    # Extract book-level context
    story = codex.get("story", {})
    outline = story.get("outline", {})
    book_title = (
        outline.get("title")
        or codex.get("story_engine", {}).get("rich_plot", {}).get("winning_plot", {}).get("title", "Untitled")
    )

    dow_prompts = codex.get("deck_of_worlds", {}).get("prompts", [])
    setting_context = dow_prompts[0].get("prompt", "") if dow_prompts else ""

    font_style = GENRE_FONT_STYLES.get(genre, DEFAULT_FONT_STYLE)

    print(f"      Composing shared chapter card template for \"{book_title}\"...")

    # Step 1: Initial composition
    current = composer.compose_template(
        genre=genre,
        visual_style=visual_style,
        book_title=book_title,
        setting_context=setting_context,
    )
    critique_history = []
    revision_count = 0

    # Step 2: Critic + revision loop
    for i in range(max_revisions):
        print(f"        Critique round {i + 1}...")
        critique = critic.critique(current, visual_style, book_title=book_title)
        critique_history.append({
            "round": i + 1,
            "scores": {
                "atmosphere": critique.atmosphere_score,
                "text_space": critique.text_space_score,
                "style_consistency": critique.style_consistency_score,
                "genre_fit": critique.genre_fit_score,
            },
            "needs_revision": critique.needs_revision,
            "suggestions": critique.suggestions,
        })

        if not critique.needs_revision:
            avg = (critique.atmosphere_score + critique.text_space_score +
                   critique.style_consistency_score + critique.genre_fit_score) / 4
            print(f"        Passed critique (avg: {avg:.1f}/10)")
            break

        print(f"        Revising (atmos={critique.atmosphere_score}, space={critique.text_space_score}, "
              f"style={critique.style_consistency_score}, genre={critique.genre_fit_score})...")

        suggestions_text = "\n".join(f"- {s}" for s in critique.suggestions)
        revision_ctx = (
            f"\n\nREVISION CONTEXT:\n"
            f"ORIGINAL PROMPT:\n{current.background_prompt}\n\n"
            f"CRITIC SUGGESTIONS:\n{suggestions_text}\n\n"
            f"Improve the prompt while maintaining the template composition and font style."
        )
        current = composer.compose_template(
            genre=genre,
            visual_style=visual_style,
            book_title=book_title,
            setting_context=setting_context,
            revision_context=revision_ctx,
        )
        revision_count += 1

    # Build final scores
    final_critique = critique_history[-1] if critique_history else {}
    final_scores = final_critique.get("scores", {
        "atmosphere": 7.0,
        "text_space": 7.0,
        "style_consistency": 7.0,
        "genre_fit": 7.0,
    })
    scores = list(final_scores.values())
    final_scores["overall"] = sum(scores) / len(scores) if scores else 7.0

    return {
        "background_prompt": current.background_prompt,
        "placeholder_text": current.placeholder_text,
        "font_style_description": current.font_style_description,
        "font_style": font_style,
        "mood": current.mood,
        "color_palette": current.color_palette,
        "revision_count": revision_count,
        "final_scores": final_scores,
        "critique_history": critique_history,
    }


def generate_per_chapter_edit_prompts(chapters: list[dict]) -> list[dict]:
    """Generate programmatic Qwen Edit prompts for each chapter.

    Matching E3: simple f-string replacement, no LLM needed.

    Args:
        chapters: List of chapter dicts with chapter_number, chapter_title

    Returns:
        List of dicts with chapter_number, chapter_title, qwen_edit_prompt
    """
    results = []
    for ch in chapters:
        ch_num = ch.get("chapter_number", 1)
        ch_title = ch.get("chapter_title", f"Chapter {ch_num}")
        roman = _roman_numeral(ch_num)

        edit_prompt = (
            f"Replace 'CHAPTER I' with 'CHAPTER {roman}' and "
            f"'CHAPTER TITLE' with '{ch_title}' in the same font style"
        )

        results.append({
            "chapter_number": ch_num,
            "chapter_title": ch_title,
            "qwen_edit_prompt": edit_prompt,
        })

    return results
