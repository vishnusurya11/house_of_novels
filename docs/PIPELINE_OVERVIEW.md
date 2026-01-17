# House of Novels - Pipeline Overview

A multi-phase AI story generation pipeline that creates complete stories with characters, locations, and visual media.

---

## Data Flow

```
User Input → Phase 0 (Codex) → Phase 1 (Outline) → Phase 2 (Characters)
          → Phase 3 (Narrative) → Phase 3b (Storyboard) → Phase 4 (Prompts)
          → Phase 5 (Generation) → Complete Story + Media
```

**Central Data Store**: `codex_{timestamp}.json` - All phases read from and write to this file.

---

## Phase 0: Codex Creation

**Purpose**: Generate the foundational story concept through multi-agent debate.

**Input**: User preferences (genre, tone, themes) or random selection
**Output**: `codex_{timestamp}.json` with story seed, microsetting, character concepts

### How It Works
1. **Deck of Worlds** agents draw "cards" (genre, catalyst, theme, conflict, tone)
2. Multi-agent debate synthesizes cards into a cohesive concept
3. Generates: story seed, microsetting, protagonist concept, antagonist concept

**Key Files**: `phase0_codex.py`, `codex_generator.py`, `deck_of_worlds_agents.py`

---

## Phase 1: Outline Generation

**Purpose**: Create a 3-act story structure with scene breakdowns.

**Input**: Codex with story seed and microsetting
**Output**: Codex updated with acts, scenes, and poster prompts

### Steps

| Step | Name | Input | Output |
|------|------|-------|--------|
| 1 | Act Summaries | Story seed, scope config | 3 act summaries with emotional arcs |
| 2 | Scene Breakdowns | Act summaries | Individual scenes per act |
| 3 | Scene Merging | Scene breakdowns | Combined scene list |
| 4 | Outline Critique | Full outline | Style and continuity critiques |
| 5 | Poster Prompts | Outline, critique | 3 marketing poster prompts |

**Key Files**: `phase1_outline.py`, `outline_agents.py`

---

## Phase 2: Characters & Locations

**Purpose**: Generate detailed characters and locations with unique names.

**Input**: Codex with outline
**Output**: Codex updated with full character profiles and location details

### How It Works
1. **Character Generation**: Creates detailed profiles from concepts
   - Physical appearance, personality, backstory, motivations
   - Multi-agent name debate (3 rounds of critique/revision)

2. **Location Generation**: Creates vivid location descriptions
   - Sensory details, atmosphere, narrative significance

**Key Files**: `phase2_characters.py`, `character_agents.py`, `name_agents.py`

---

## Phase 3: Narrative Prose

**Purpose**: Write the actual story prose for each scene.

**Input**: Codex with outline, characters, locations
**Output**: Codex updated with full narrative prose

### Steps

| Step | Name | Input | Output |
|------|------|-------|--------|
| 1 | Act 1 Prose | Outline, characters | Prose for all Act 1 scenes |
| 2 | Act 2 Prose | Act 1 + outline | Prose for all Act 2 scenes |
| 3 | Act 3 Prose | Acts 1-2 + outline | Prose for all Act 3 scenes |
| 4 | Critique | Full narrative | Style & continuity critiques |
| 5 | Revision | Narrative + critiques | Polished final narrative |

**Word Counts by Scope**:
- Flash: 400-500 words/scene
- Short: 500-600 words/scene
- Standard: 600-800 words/scene
- Long: 800-1000 words/scene

**Key Files**: `phase3_narrative.py`, `narrative_agents.py`, `reviser_agent.py`

---

## Phase 3b: Storyboard

**Purpose**: Break scenes into camera shots for video generation.

**Input**: Codex with narrative prose
**Output**: Codex updated with shot breakdowns per scene

### Shot Structure
Each shot contains:
- `shot_number`: Sequential number within scene
- `shot_type`: Camera angle (wide, medium, close-up, etc.)
- `duration_seconds`: Shot length (2-8 seconds typically)
- `characters_in_frame`: List of character names
- `action_description`: What happens visually
- `dialogue`: Any spoken lines
- `camera_movement`: Pan, tilt, zoom, static, etc.

**Key Files**: `phase3b_storyboard.py`, `storyboard_agents.py`

---

## Phase 4: Prompt Generation

**Purpose**: Generate AI image/video prompts for all visual assets.

**Input**: Codex with narrative and storyboard
**Output**: Codex updated with generation prompts

### Steps

| Step | Name | Input | Output |
|------|------|-------|--------|
| 1 | Character Prompts | Character profiles | Portrait image prompts |
| 2 | Location Prompts | Location details | Environment image prompts |
| 3 | Shot Frame Prompts | Storyboard shots | First/last frame prompts per shot |
| 4 | Video Prompts | Shots + frame prompts | Motion/action video prompts |
| 5 | Poster Prompts | Outline poster concepts | Detailed poster image prompts |

**Prompt Format**: 300-500 word detailed descriptions including:
- Visual composition and framing
- Lighting and atmosphere
- Color palette and style
- Character positioning and expressions

**Key Files**: `phase4_prompts.py`, `image_prompt_agents.py`, `video_prompt_agents.py`

---

## Phase 5: Media Generation

**Purpose**: Generate actual images and videos using ComfyUI.

**Input**: Codex with all prompts
**Output**: Generated media files + codex updated with output paths

### Steps

| Step | Name | Input | Output |
|------|------|-------|--------|
| 1 | Static Images | Character/location/poster prompts | PNG files for portraits, locations, posters |
| 2 | Shot Frames | First/last frame prompts | PNG files for each shot's start/end frames |
| 3 | Videos | Video prompts + first frames | MP4 files using LTX 2.0 i2v |
| 4 | Audio | (Future) | Audio files |

### Output Paths
```
ComfyUI/output/api/{timestamp}/
├── characters/       # Character portraits
├── locations/        # Location images
├── posters/          # Marketing posters
├── firstframes/      # Shot first frames
│   └── act{N}/scene{N}/shot{N}/
├── lastframes/       # Shot last frames
│   └── act{N}/scene{N}/shot{N}/
└── videos/           # Generated videos
    └── act{N}/scene{N}/shot{N}/
```

### Generation Metadata
Each generated asset gets metadata stored in codex:
```json
{
  "generation": {
    "prompt_id": "abc123",
    "status": "completed",
    "execution_time": 12.5,
    "output_path": "api/.../image_00001_.png",
    "seed": 264854736453334,
    "generated_at": "2026-01-15T20:12:45"
  }
}
```

**Timeouts**:
- Images: 5 minutes (300s)
- Videos: 30 minutes (1800s)

**Key Files**: `phase5_generation.py`, `comfyui_trigger.py`

---

## Configuration

### Story Scopes (`src/config.py`)

| Scope | Scenes | Characters | Locations | Words/Scene |
|-------|--------|------------|-----------|-------------|
| flash | 3-4 | 2 | 1 | 400-500 |
| short | 6-8 | 3 | 2 | 500-600 |
| standard | 12-14 | 5 | 4 | 600-800 |
| long | 18-20 | 8 | 6 | 800-1000 |

### Key Configuration Values
- `DEFAULT_MODEL`: `openai/gpt-4o-mini`
- `DEBATE_ROUNDS`: 2
- `NAME_DEBATE_ROUNDS`: 2
- `DEFAULT_COMFYUI_URL`: `http://127.0.0.1:8188`
- `VIDEO_GENERATION_TIMEOUT`: 1800s (30 min)

---

## Running the Pipeline

### Full Pipeline
```bash
uv run python -m src.house_of_novels
```

### Individual Phases
```bash
# Phase 0: Create codex
uv run python -m src.phases.phase0_codex

# Phase 1: Generate outline
uv run python -m src.phases.phase1_outline forge/{timestamp}/codex_{timestamp}.json

# Phase 2: Generate characters
uv run python -m src.phases.phase2_characters forge/{timestamp}/codex_{timestamp}.json

# Phase 3: Write narrative
uv run python -m src.phases.phase3_narrative forge/{timestamp}/codex_{timestamp}.json

# Phase 3b: Create storyboard
uv run python -m src.phases.phase3b_storyboard forge/{timestamp}/codex_{timestamp}.json

# Phase 4: Generate prompts
uv run python -m src.phases.phase4_prompts forge/{timestamp}/codex_{timestamp}.json

# Phase 5: Generate media (specific steps)
uv run python -m src.phases.phase5_generation forge/{timestamp}/codex_{timestamp}.json --steps 1 2 3
```

---

## Codex Structure Overview

```json
{
  "metadata": { "timestamp": "...", "version": "..." },
  "story": {
    "title": "Story Title",
    "seed": { "genre": "...", "theme": "...", "conflict": "..." },
    "microsetting": { "name": "...", "description": "..." },
    "characters": [
      {
        "id": "char_001",
        "name": "Character Name",
        "role": "protagonist",
        "character_prompt": { "prompt": "...", "generation": {...} }
      }
    ],
    "locations": [
      {
        "id": "loc_001",
        "name": "Location Name",
        "location_prompt": { "prompt": "...", "generation": {...} }
      }
    ],
    "outline": {
      "acts": [...],
      "poster_prompts": [...]
    },
    "narrative": {
      "acts": [
        {
          "act_number": 1,
          "scenes": [
            {
              "scene_number": 1,
              "prose": "...",
              "shots": [
                {
                  "shot_number": 1,
                  "firstframe_prompt": "...",
                  "lastframe_prompt": "...",
                  "video_prompt": "...",
                  "firstframe_generation": {...},
                  "lastframe_generation": {...},
                  "video_generation": {...}
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```