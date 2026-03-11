"""
YouTube Metadata Agent

Generates optimized YouTube title and description from story codex data.
"""

from pydantic import BaseModel, Field
from .base_story_agent import BaseStoryAgent


class YouTubeMetadata(BaseModel):
    """YouTube video metadata."""
    title: str = Field(description="Engaging YouTube title (max 100 chars)")
    description: str = Field(description="YouTube description with summary, characters, and hashtags")
    tags: list[str] = Field(description="List of relevant keyword tags for SEO")


class YouTubeMetadataAgent(BaseStoryAgent):
    """Agent that generates YouTube metadata from story data."""

    @property
    def name(self) -> str:
        return "YOUTUBE_METADATA"

    @property
    def role(self) -> str:
        return "YouTube content specialist who creates engaging titles and descriptions"

    @property
    def system_prompt(self) -> str:
        return """You are a YouTube content specialist who creates compelling descriptions and metadata for story videos.

Your job is to take story information (title, logline, characters) and create:

1. **Title** (max 100 characters):
   - Use the EXACT story title provided - do NOT modify or change it
   - This is the book's official title and must be used as-is
   - STRICTLY FORBIDDEN: No emojis, no "AI", no "AI-generated", no mentions of artificial intelligence
   - If the title is too long (>100 chars), truncate cleanly with "..."

2. **Description** (500-1000 characters):
   - Brief story summary (2-3 sentences)
   - Main characters mentioned
   - Genre/mood indicators
   - Call to action (subscribe, like)
   - Relevant hashtags at the end

3. **Tags** (10-15 keywords):
   - Story genre tags
   - Character-related tags
   - General storytelling tags

Be accurate and use the provided story title exactly as given."""

    def generate_metadata(
        self,
        story_title: str,
        logline: str,
        characters: list[dict],
        scene_summaries: list[str] = None,
    ) -> YouTubeMetadata:
        """
        Generate YouTube metadata from story data.

        Args:
            story_title: The story's title
            logline: One-line story summary
            characters: List of character dicts with 'name' and optionally 'role'
            scene_summaries: Optional list of scene summaries for context

        Returns:
            YouTubeMetadata with title, description, and tags
        """
        # Build character list
        char_names = [c.get("name", "Unknown") for c in characters[:5]]  # Top 5
        char_list = ", ".join(char_names) if char_names else "Various characters"

        # Build scene context if available
        scene_context = ""
        if scene_summaries:
            # Take first 3 scenes for context
            summaries = scene_summaries[:3]
            scene_context = f"\n\nFirst few scenes:\n" + "\n".join(f"- {s}" for s in summaries)

        prompt = f"""Generate YouTube metadata for this story video:

**Story Title:** {story_title}

**Logline:** {logline}

**Main Characters:** {char_list}
{scene_context}

Create engaging YouTube metadata.

STRICT TITLE RULES:
- Use the EXACT story title: "{story_title}"
- Do NOT modify, change, or create a different title
- This is the official book title and must be used exactly as provided
- Maximum 100 characters (truncate with "..." if needed)
- NO emojis allowed
- NO "AI", "AI-generated", or any AI references

Description should be 500-1000 characters with hashtags at the end (#Story #Fiction #Drama etc.)"""

        return self.invoke_structured(prompt, YouTubeMetadata, max_tokens=8000)


def generate_chapter_youtube_metadata(
    story_title: str,
    logline: str,
    chapter_number: int,
    total_chapters: int,
    chapter_title: str = "",
) -> YouTubeMetadata:
    """Generate YouTube metadata for a single chapter upload (programmatic, no LLM).

    Args:
        story_title: The story's title.
        logline: One-line story summary.
        chapter_number: 1-based chapter number.
        total_chapters: Total number of chapters in the book.
        chapter_title: Optional chapter title for description context.

    Returns:
        YouTubeMetadata with part-numbered title, description, and tags.
    """
    # Title: "Story Title - Part X of Y"
    part_label = f"Part {chapter_number} of {total_chapters}"
    title = f"{story_title} - {part_label}"
    if len(title) > 100:
        # Truncate story title to fit, keep part label
        max_story = 100 - len(f" - {part_label}") - 3
        title = f"{story_title[:max_story]}... - {part_label}"

    # Description
    chapter_info = f" - {chapter_title}" if chapter_title else ""
    description = (
        f"{story_title} | {part_label}{chapter_info}\n\n"
        f"{logline}\n\n"
        f"Listen to the full audiobook by subscribing and following the playlist.\n\n"
        f"#Audiobook #Story #Fiction #ShortStory #Storytelling"
    )

    # Tags
    tags = [
        "audiobook", "story", "fiction", "storytelling", "narrative",
        part_label.lower(), story_title[:30],
    ]

    return YouTubeMetadata(title=title, description=description, tags=tags)


def generate_youtube_metadata(
    story_title: str,
    logline: str,
    characters: list[dict],
    scene_summaries: list[str] = None,
    model: str = None,
) -> YouTubeMetadata:
    """
    Convenience function to generate YouTube metadata.

    Args:
        story_title: The story's title
        logline: One-line story summary
        characters: List of character dicts
        scene_summaries: Optional list of scene summaries
        model: LLM model to use (optional)

    Returns:
        YouTubeMetadata with title, description, and tags
    """
    from src.config import DEFAULT_MODEL
    model = model or DEFAULT_MODEL

    agent = YouTubeMetadataAgent(model=model)
    return agent.generate_metadata(
        story_title=story_title,
        logline=logline,
        characters=characters,
        scene_summaries=scene_summaries,
    )
