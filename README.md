# House of Novels

AI-powered novel generation pipeline — creates complete stories with audio, images, and video, then uploads to YouTube.

## Quick Start

```bash
uv sync
export OPENROUTER_API_KEY="your-key-here"
uv run python -m src.house_of_novels --scope flash
```

Output: `forge/<timestamp>/codex_<timestamp>.json` with all story data and generated media.

---

## Pipeline Overview

```
Phase 0 (Codex)  →  Phase 1 (Author)  →  Phase 2 (Prompts)  →  Phase 3 (Generation)  →  Phase 4 (Editing)  →  Phase 5 (Upload)
  Story seed         10-step story         Image/video           ComfyUI media            Audio/video            YouTube
  + author pick      creation              prompt gen            generation               compositing            publish
```

| Phase | Module | Description |
|-------|--------|-------------|
| 0 | `phase0_codex` | Generate story seed prompts + select author persona |
| 1 | `phase1_author` | 10-step author pipeline: theme → plot → characters → world → scenes → prose → revision → titles |
| 2 | `phase2_prompts` | Generate image prompts: characters, locations, posters, scene images, thumbnails |
| 3 | `phase3_generation` | Generate media via ComfyUI: audio (TTS), static images, scene images |
| 4 | `phase4_editing` | Combine audio → scene videos → final video |
| 5 | `phase5_upload` | Upload to YouTube with AI-generated metadata |

---

## CLI Usage

### Full Pipeline

```bash
# Standard scope (default, all phases)
uv run python -m src.house_of_novels

# Flash fiction (~10 min read, cheapest)
uv run python -m src.house_of_novels --scope flash

# Other scopes
uv run python -m src.house_of_novels --scope short     # ~20 min
uv run python -m src.house_of_novels --scope standard   # ~35 min
uv run python -m src.house_of_novels --scope long       # ~50 min

# Custom model
uv run python -m src.house_of_novels --model "x-ai/grok-4.1-fast"

# Resume from existing codex
uv run python -m src.house_of_novels --codex forge/<ts>/codex_<ts>.json --phases prompts generation
```

### Individual Phases

Each phase runs independently. Pass the codex path from a previous run:

```bash
# Phase 0: Generate codex (creates new timestamped folder)
uv run python -m src.phases.phase0_codex

# Phase 1: Author pipeline (requires Phase 0 codex)
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json --steps 0 1 2 3  # specific steps

# Phase 2: Prompt generation (requires Phase 1)
uv run python -m src.phases.phase2_prompts forge/<ts>/codex_<ts>.json
uv run python -m src.phases.phase2_prompts forge/<ts>/codex_<ts>.json --steps 1 2      # specific steps

# Phase 3: Media generation via ComfyUI (requires Phase 2)
uv run python -m src.phases.phase3_generation forge/<ts>/codex_<ts>.json

# Phase 4: Audio/video editing (requires Phase 3)
uv run python -m src.phases.phase4_editing forge/<ts>/codex_<ts>.json

# Phase 5: YouTube upload (requires Phase 4)
uv run python -m src.phases.phase5_upload forge/<ts>/codex_<ts>.json --privacy unlisted
```

### Testing & Maintenance

```bash
uv sync                                                    # Install dependencies
uv run pytest tests/ -v                                    # Run tests
uv run python -m py_compile src/story_agents/<file>.py     # Syntax check
```

---

## Phase 1: Author Pipeline (10 Steps)

The core story creation engine. Each step uses multi-agent debate (propose → cross-critique → vote → synthesize).

| Step | Name | Description |
|------|------|-------------|
| 0 | Theme Foundation | Thematic square, character perspectives, central question |
| 1 | Plotting | Structure research → beat sheet → scene outline |
| 2 | Characters | Generate characters + multi-agent name debate |
| 3 | World Building | Setting expansion → lore/rules → locations |
| 4 | Critique & Revise | Structure/pacing critique → outline revision |
| 5 | Complete Narrative | Write full prose (5-agent debate per scene) |
| 6 | Narrative Revision | 5-critic revision (prose, voice, continuity, pacing, emotion) |
| 7 | Screenplay | Format narrative for presentation |
| 8 | Final Polish | Continuity + prose polish pass |
| 9 | Final Output | Validate and finalize story dict |

**5-Critic Revision System (Step 6):**
- **ProsePolishCritic**: Filter words, cliches, show-don't-tell
- **CharacterVoiceCritic**: Dialogue authenticity + differentiation
- **ContinuityCritic**: Consistency with codex
- **PacingTensionCritic**: Scene structure + ticking clock
- **EmotionalResonanceCritic**: Emotional beats + micro-tension

```bash
# Run all steps
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json

# Run specific steps
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json --steps 0        # Theme only
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json --steps 0 1 2 3  # Through world building
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json --steps 5        # Prose only
uv run python -m src.phases.phase1_author forge/<ts>/codex_<ts>.json --steps 6        # Revision only
```

---

## Phase 2: Prompt Generation (5 Steps)

Generates AI image generation prompts for all visual assets.

| Step | Name | Description |
|------|------|-------------|
| 1 | Character Prompts | Detailed portrait prompts per character |
| 2 | Location Prompts | Environment/location image prompts |
| 3 | Poster Prompts | Multi-agent jury voting on poster designs |
| 4 | Scene Image Prompts | Layered prompts per scene (location + character layers) |
| 5 | Thumbnail Prompts | YouTube thumbnail via agent council debate |

```bash
uv run python -m src.phases.phase2_prompts forge/<ts>/codex_<ts>.json
uv run python -m src.phases.phase2_prompts forge/<ts>/codex_<ts>.json --steps 1 2    # Characters + Locations
uv run python -m src.phases.phase2_prompts forge/<ts>/codex_<ts>.json --steps 4      # Scene images only
```

---

## Story Scopes

| Scope | Scenes | Characters | Locations | Words/Scene | Read Time |
|-------|--------|------------|-----------|-------------|-----------|
| flash | 3-4 | 2 | 1 | 400-500 | ~10 min |
| short | 6-8 | 3 | 2 | 500-600 | ~20 min |
| standard | 12-14 | 5 | 4 | 600-800 | ~35 min |
| long | 18-20 | 8 | 6 | 800-1000 | ~50 min |

---

## Architecture

### Key Files

```
src/
├── house_of_novels.py               # Main orchestrator (runs all phases)
├── phases/                           # 6 phase orchestrators
│   ├── phase0_codex.py               #   Codex generation
│   ├── phase1_author.py              #   10-step author pipeline
│   ├── phase2_prompts.py             #   Prompt generation
│   ├── phase3_generation.py          #   Media generation (ComfyUI)
│   ├── phase4_editing.py             #   Audio/video editing
│   └── phase5_upload.py              #   YouTube upload
├── authors/
│   ├── base_phase1.py                # Base Phase 1 implementation (10 steps)
│   ├── registry.py                   # Author registry
│   └── personas/                     # Custom author implementations
├── story_agents/                     # 38 specialized LLM agents
│   ├── base_story_agent.py           #   Base class (invoke_structured, retry, cache)
│   ├── character_agents.py           #   Character generation
│   ├── narrative_writing_agents.py   #   Prose writing
│   ├── scene_image_prompt_agents.py  #   Scene image prompts (layered)
│   └── ...                           #   36 more agent files
├── story_schemas.py                  # All Pydantic schemas (~3,800 lines)
├── config.py                         # Config helpers, environment detection
├── visual_styles.py                  # Visual style definitions
├── comfyui_trigger.py                # ComfyUI workflow execution
└── templates/
    └── template_1_static_audio/      # Default template (static images + audio)
        ├── generation.py             #   Media generation logic
        └── editing.py                #   Video editing logic

config.yaml                           # Models, temperatures, token limits, parallelism
```

### Agent Pattern

All 38 agents extend `BaseStoryAgent`:
- **Structured output** via `invoke_structured(schema)` with Pydantic validation
- **Automatic model fallback** chain (primary → fallback models)
- **Disk cache** for expensive LLM calls
- **Thread-based parallelism** (25 concurrent workers, configurable per step)
- **Token tracking** per agent, per step

### Multi-Agent Debate Pattern

Used throughout Phase 1 for high-quality story decisions:

```
5 Agents Propose  →  Cross-Critique  →  Vote  →  Synthesize Best
```

---

## ComfyUI Integration

Phase 3 uses ComfyUI for image generation. Start ComfyUI before running:

```bash
# Start ComfyUI (in your ComfyUI directory)
python main.py

# Then run Phase 3
uv run python -m src.phases.phase3_generation forge/<ts>/codex_<ts>.json
```

### Programmatic Usage

```python
from src.comfyui_trigger import trigger_comfy

result = trigger_comfy(
    workflow_json_path="workflows/portrait.json",
    replacements={
        "45_text": "A portrait of a warrior",  # nodeID_parameter format
        "31_seed": 12345,
        "3_steps": 30
    }
)
```

The `replacements` dict uses `"nodeID_parameter": value` format, mapping to `workflow[nodeID]["inputs"][parameter]`.

---

## Configuration

All config lives in `config.yaml`. Never hardcode models, temperatures, or token limits.

```yaml
# Global defaults
default_model: "openai/gpt-4.1-nano"
fallback_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"]
max_concurrent: 25

# Per-step config (example)
step5_chapter_scene_breakdown:
  model: "openai/gpt-4.1-nano"
  temperature: 0.7
  token_limits:
    prose_proposal: 16000
    prose_critique: 12000
  parallel_processing:
    enabled: true
    max_workers: 6
```
