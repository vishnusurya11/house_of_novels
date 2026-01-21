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
        return """You are a YouTube content specialist who creates engaging titles and descriptions for AI-generated story videos.

Your job is to take story information (title, logline, characters, scene summaries) and create:

1. **Title** (max 100 characters):
   - Engaging and clickable
   - Captures the essence of the story
   - Avoids clickbait but creates intrigue
   - Include genre hints if appropriate

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
   - AI-generated content tags

Be creative but accurate. The metadata should entice viewers while honestly representing the content."""

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

        prompt = f"""Generate YouTube metadata for this AI-generated story video:

**Story Title:** {story_title}

**Logline:** {logline}

**Main Characters:** {char_list}
{scene_context}

Create engaging YouTube metadata that will attract viewers interested in AI-generated stories and narrative content.

Remember:
- Title must be under 100 characters
- Description should be 500-1000 characters
- Include 10-15 relevant tags
- Add hashtags at the end of description (#AIStory #GeneratedStory etc.)"""

        return self.invoke_structured(prompt, YouTubeMetadata, max_tokens=1000)


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
