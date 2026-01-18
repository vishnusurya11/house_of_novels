# House of Novels

Digital implementation of the Story Engine and Deck of Worlds for generating story prompts and world-building.

## House of Novels - Complete Pipeline

The modular `house_of_novels.py` is the main entry point for end-to-end novel generation.

### CLI Usage

```bash
# Generate complete novel with defaults (standard scope, all phases)
uv run python -m src.house_of_novels

# Quick flash fiction (~10 min read)
uv run python -m src.house_of_novels --scope flash

# Short story (~20 min read)
uv run python -m src.house_of_novels --scope short

# Long story (~50 min read)
uv run python -m src.house_of_novels --scope long

# Use specific model
uv run python -m src.house_of_novels --model "x-ai/grok-4.1-fast"

# Run only specific phases
uv run python -m src.house_of_novels --phases codex outline characters

# Resume from existing codex (skip codex generation)
uv run python -m src.house_of_novels --codex forge/20260105143022/codex_20260105143022.json --phases narrative images
```

### Programmatic Usage


python -m src.comfyui_trigger


```python
from src.house_of_novels import generate_novel

# Generate with defaults
forge_path = generate_novel()

# Generate flash fiction
forge_path = generate_novel(scope="flash")

# Generate with specific model and scope
forge_path = generate_novel(
    scope="standard",
    model="x-ai/grok-4.1-fast"
)

# Run only first 3 phases
forge_path = generate_novel(
    phases=["codex", "outline", "characters"]
)

# Resume from existing codex
forge_path = generate_novel(
    codex_path="forge/20260105143022/codex_20260105143022.json",
    phases=["narrative", "images"]
)
```

### Output Structure

```
forge/
  20260105143022/                    # Timestamped run folder
    codex_20260105143022.json        # All story data with matching timestamp
```

### Ad-Hoc Phase Execution

Each phase can be run independently using the codex path from a timestamped folder:

```bash
# Phase 0: Generate codex with prompts (creates new folder)
uv run python -m src.phases.phase0_codex
uv run python -m src.phases.phase0_codex --output-dir forge/20260105143022

# Phase 1: Generate story outline (requires codex from Phase 0)
uv run python -m src.phases.phase1_outline forge\20260116191326\codex_20260116191326.json
uv run python -m src.phases.phase1_outline forge/20260105143022/codex_20260105143022.json --scope flash

# Phase 2: Generate characters & locations (requires Phase 1)
uv run python -m src.phases.phase2_characters forge\20260116191326\codex_20260116191326.json
uv run python -m src.phases.phase2_characters forge/20260105143022/codex_20260105143022.json --fix-names

# Phase 3: Write narrative prose (requires Phases 1-2)
uv run python -m src.phases.phase3_narrative forge\20260116191326\codex_20260116191326.json

# Phase 3 with specific steps (act-by-act control)
uv run python -m src.phases.phase3_narrative forge/20260105143022/codex_20260105143022.json --steps 1    # Act 1 only
uv run python -m src.phases.phase3_narrative forge/20260105143022/codex_20260105143022.json --steps 2 3  # Acts 2 & 3
uv run python -m src.phases.phase3_narrative forge/20260105143022/codex_20260105143022.json --steps 4 5  # Critique & revision only

# Phase 3b: Generate storyboard shots (requires Phase 3)
uv run python -m src.phases.phase3b_storyboard forge\20260113222641\codex_20260113222641.json
uv run python -m src.phases.phase3b_storyboard forge/20260105143022/codex_20260105143022.json --max-revisions 3

# Phase 4: Generate image/video prompts (requires Phase 3)
uv run python -m src.phases.phase4_prompts forge/20260116191326/codex_20260116191326.json

# Phase 4 with specific steps (granular control)
uv run python -m src.phases.phase4_prompts forge/20260105143022/codex_20260105143022.json --steps 1    # Characters only
uv run python -m src.phases.phase4_prompts forge/20260105143022/codex_20260105143022.json --steps 1 2  # Characters + Locations
uv run python -m src.phases.phase4_prompts forge/20260105143022/codex_20260105143022.json --steps 3    # Posters only
uv run python -m src.phases.phase4_prompts forge/20260105143022/codex_20260105143022.json --steps 4 5  # Shot frames + Video prompts




# phse 5
uv run python -m src.phases.phase5_generation forge/20260116191326/codex_20260116191326.json


uv run python -m src.phases.phase5_generation forge/20260116191326/codex_20260116191326.json --steps 3



# phase 6



```



**Re-run any phase**: Just pass the same codex path to regenerate that phase with different options:
```bash
# Regenerate outline with different scope
uv run python -m src.phases.phase1_outline forge/20260105143022/codex_20260105143022.json --scope long

# Regenerate specific Phase 4 steps
uv run python -m src.phases.phase4_prompts forge/20260105143022/codex_20260105143022.json --steps 3  # Re-run poster generation
```

### Story Scopes

| Scope | Scenes | Characters | Locations | Read Time |
|-------|--------|------------|-----------|-----------|
| flash | 3-4 | 2 | 1 | ~10 min |
| short | 6-8 | 3 | 2 | ~20 min |
| standard | 12-14 | 5 | 4 | ~35 min |
| long | 18-20 | 8 | 6 | ~50 min |

### Phase 1: Step-Granular Execution (Research-Driven Outline)

Phase 1 supports running individual steps for research-driven story outline generation with web search and multi-agent debate:

**Available Steps**:
1. **High-Level Story Structure** - Research-driven 3-act summary with web search (Hero's Journey, Save the Cat, etc.)
2. **Beat Sheet Generation** - Convert high-level structure into bullet-point beats for each act
3. **Scene-by-Scene Outline** - Expand beats into full scene summaries (act-by-act)
4. **Structure & Pacing Critique** - Multi-agent critique of complete outline
5. **Revision & Final Outline** - Apply critiques and revise outline

**Usage Examples**:
```bash
# Run all steps (default - backward compatible)
uv run python -m src.phases.phase1_outline forge/xxx/codex.json

# Step 1: Generate high-level structure with web research
uv run python -m src.phases.phase1_outline forge/xxx/codex.json --steps 1

# Step 2: Generate beat sheet (requires Step 1)
uv run python -m src.phases.phase1_outline forge/xxx/codex.json --steps 2

# Step 3: Generate full scene-by-scene outline (requires Step 2)
uv run python -m src.phases.phase1_outline forge/xxx/codex.json --steps 3

# Steps 4-5: Critique and revise
uv run python -m src.phases.phase1_outline forge/xxx/codex.json --steps 4 5

# Re-run beat sheet with different research approach
uv run python -m src.phases.phase1_outline forge/xxx/codex.json --steps 2
```

**Benefits**:
- Research-driven approach: Agents search online for story structure best practices
- Preserves plot coherence: High-level structure created BEFORE detailed beats
- Generic character roles: No names committed until Phase 2 (multi-agent name debate)
- Iterative refinement: Can regenerate beats without redoing structure
- Multi-agent debate: Coordinates multiple perspectives on story structure
- Resume from any step if needed

**How It Works**:
- Step 1: Researches Hero's Journey, Save the Cat, needs/wants frameworks → saves to `codex["story"]["outline"]["high_level_structure"]`
- Step 2: Generates bullet-point beats for each act → saves to `codex["story"]["outline"]["beat_sheet"]`
- Step 3: Expands beats into full scenes (Act 1 → Act 2 → Act 3) → saves to `codex["story"]["outline"]["acts"]`
- Steps 4-5: Critique and revision cycles (same as before)
- Each step reads from codex, saves immediately after completion

**Why This Approach?**:
Instead of generating the entire outline in one shot, this research-driven approach:
1. Researches proven story structures online first
2. Creates high-level arc preserving plot coherence
3. Defines beat-by-beat breakdown with story structure expertise
4. Only then generates full scene summaries

This produces better quality outlines while allowing regeneration of individual steps if needed.

### Phase 3: Step-Granular Execution

Phase 3 supports running individual steps for act-by-act narrative control:

**Available Steps**:
1. **Write Act 1 Prose** - Scene-by-scene writing for Act 1 (setup)
2. **Write Act 2 Prose** - Scene-by-scene writing for Act 2 (confrontation)
3. **Write Act 3 Prose** - Scene-by-scene writing for Act 3 (resolution)
4. **Style & Continuity Critique** - Multi-agent critique of complete narrative
5. **Revision & Final Narrative** - Apply critiques and revise narrative

**Usage Examples**:
```bash
# Run all steps (default - backward compatible)
uv run python -m src.phases.phase3_narrative forge/xxx/codex.json

# Write Act 1 only
uv run python -m src.phases.phase3_narrative forge/xxx/codex.json --steps 1

# Write Acts 2 and 3 (after Act 1 is done)
uv run python -m src.phases.phase3_narrative forge/xxx/codex.json --steps 2 3

# Re-run just Act 2 if you want to regenerate it
uv run python -m src.phases.phase3_narrative forge/xxx/codex.json --steps 2

# Run critique and revision only (all 3 acts must be written first)
uv run python -m src.phases.phase3_narrative forge/xxx/codex.json --steps 4 5

# Re-run just revision with different approach
uv run python -m src.phases.phase3_narrative forge/xxx/codex.json --steps 5
```

**Benefits**:
- Write acts independently - regenerate Act 2 without rewriting Acts 1 & 3
- Acts build on each other sequentially with proper continuity
- Run critiques without regenerating prose
- Resume from where you left off if a step fails
- Save time by only regenerating what needs to change

**How It Works**:
- Each step saves to codex immediately after completion
- Act 2 reads Act 1's ending from codex for continuity
- Act 3 reads Act 2's ending from codex for continuity
- Step 4 requires all 3 acts to exist (reads from codex)
- Step 5 requires Step 4 critiques to exist (reads from codex metadata)

### Phase 4: Step-Granular Execution

Phase 4 supports running individual steps for fine-grained control over prompt generation:

**Available Steps**:
1. **Character Prompts** - Detailed portrait prompts for each character
2. **Location Prompts** - Environmental/location image prompts
3. **Poster Prompts** - Multi-agent jury voting on poster/thumbnail designs
4. **Shot Frame Prompts** - First/last frame prompts for video generation
5. **Video Prompts** - LTX screenplay format video prompts

**Usage Examples**:
```bash
# Run all steps (default)
uv run python -m src.phases.phase4_prompts forge/xxx/codex.json

# Run only character prompts
uv run python -m src.phases.phase4_prompts forge/xxx/codex.json --steps 1

# Run characters and locations
uv run python -m src.phases.phase4_prompts forge/xxx/codex.json --steps 1 2

# Run only poster generation (useful for regenerating with different settings)
uv run python -m src.phases.phase4_prompts forge/xxx/codex.json --steps 3

# Run shot frames and video prompts (requires Phase 3b storyboard)
uv run python -m src.phases.phase4_prompts forge/xxx/codex.json --steps 4 5
```

**Benefits**:
- Re-run specific steps without regenerating everything
- Skip steps you don't need (e.g., skip video prompts if only generating images)
- Iterate on poster designs without touching other prompts
- Resume from where you left off if a step fails

---

## ComfyUI Integration

The `trigger_comfy()` function allows you to trigger ComfyUI workflows and wait for completion. This is useful for Phase 5 (image generation).

### Prerequisites

1. **Start ComfyUI**: Ensure ComfyUI is running locally on port 8188 (default)
   ```bash
   # In your ComfyUI directory
   python main.py
   ```

2. **Install Dependencies**: The required dependencies are in pyproject.toml
   ```bash
   uv sync
   ```

### Basic Usage

```python
from src.comfyui_trigger import trigger_comfy

result = trigger_comfy(
    workflow_json_path="workflows/portrait.json",
    replacements={
        "45_text": "A beautiful portrait of a warrior",
        "31_seed": 12345,
        "3_steps": 30
    }
)

print(f"Status: {result['status']}")
print(f"Prompt ID: {result['prompt_id']}")
print(f"Execution time: {result['execution_time']}s")
print(f"Outputs: {len(result['outputs'])} files")
```

### Replacement Format

The `replacements` dict uses the format `"nodeID_parameter": value`:

- `"45_text"` → Updates `workflow["45"]["inputs"]["text"]`
- `"31_seed"` → Updates `workflow["31"]["inputs"]["seed"]`
- `"3_steps"` → Updates `workflow["3"]["inputs"]["steps"]`

To find node IDs and parameters:
1. Open your workflow JSON file
2. Look for nodes like `"45": {"inputs": {"text": "..."}}`
3. Use `nodeID_parameterName` format in replacements

### Custom ComfyUI URL

```python
result = trigger_comfy(
    workflow_json_path="workflows/portrait.json",
    replacements={"45_text": "A warrior"},
    comfyui_url="http://192.168.1.100:8188",  # Remote ComfyUI instance
    timeout=600  # 10 minute timeout
)
```

### Error Handling

```python
try:
    result = trigger_comfy(
        workflow_json_path="workflows/portrait.json",
        replacements={"45_text": "A portrait"}
    )

    if result['status'] == 'completed':
        print(f"Success! Generated {len(result['outputs'])} outputs")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

except FileNotFoundError as e:
    print(f"Workflow file not found: {e}")
except ConnectionError as e:
    print(f"Cannot reach ComfyUI: {e}")
except TimeoutError as e:
    print(f"Workflow execution timeout: {e}")
```

### Integration with Phase 5

```python
# In your phase 5 script
from src.comfyui_trigger import trigger_comfy

# Generate image for a character
character_prompt = "A fierce warrior with silver armor"
result = trigger_comfy(
    workflow_json_path="workflows/character_portrait.json",
    replacements={
        "6_text": character_prompt,  # Main prompt node
        "3_seed": 42,                # Seed for reproducibility
        "3_steps": 25,               # Number of diffusion steps
        "3_cfg": 7.5                 # CFG scale
    }
)

if result['status'] == 'completed':
    # Save outputs to disk
    for i, output_bytes in enumerate(result['outputs']):
        with open(f"output/character_{i}.png", "wb") as f:
            f.write(output_bytes)
```

---

## Legacy Quick Start

```bash
# Install dependencies
uv add langchain langchain-openai langgraph pydantic

# Set OpenRouter API key (for multi-agent mode)
export OPENROUTER_API_KEY="your-key-here"

# Generate story prompts (random)
uv run python src/story_engine_generator.py

# Generate story prompts (multi-agent AI debate)
uv run python src/story_engine_agents.py

# Generate world/microsettings
uv run python src/deck_of_worlds_generator.py

# Run with latest codex file
uv run python src/story_engine_agents.py
uv run python src/story_builder.py

# Run with specific codex
uv run python src/story_builder.py output/codex_20260103160507.json

# Use different model
uv run python src/story_builder.py --model openai/gpt-5-mini

# Standard story (~35 min)
uv run python src/generate_story.py

# Quick flash fiction (~10 min)
uv run python src/generate_story.py --scope flash

# Long story with custom model
uv run python src/generate_story.py --scope long --model "x-ai/grok-4.1-fast"


# Generate image prompts for a codex
uv run python src/generate_image_prompts.py output/codex_20260104174039.json

# With custom model
uv run python src/generate_image_prompts.py output/codex.json --model "x-ai/grok-4.1-fast"

# Auto-detect style from genre (default)
uv run python src/generate_image_prompts.py output/codex.json

# Specify art style
uv run python src/generate_image_prompts.py output/codex.json --style anime
uv run python src/generate_image_prompts.py output/codex.json --style ultra-realistic
uv run python src/generate_image_prompts.py output/codex.json --style watercolor
uv run python src/generate_image_prompts.py output/codex.json --style oil-painting
uv run python src/generate_image_prompts.py output/codex.json --style concept-art
uv run python src/generate_image_prompts.py output/codex.json --style comic


```

Output is printed to console and saved to files (overwrites each run):
- `generated_prompts.txt` - Story Engine output (random)
- `generated_agent_prompts.txt` - Story Engine output (AI debate)
- `generated_worlds.txt` - Deck of Worlds output

## Project Structure

```
house_of_novels/
├── src/
│   ├── story_engine_generator.py     # Random story prompt generator
│   ├── story_engine_agents.py        # Multi-agent AI prompt generator
│   ├── deck_of_worlds_generator.py   # World/microsetting generator
│   ├── config.py                     # API keys and model config
│   ├── agents/                       # AI agent implementations
│   │   ├── base_agent.py             # Base agent with OpenRouter
│   │   ├── card_agents.py            # Placer, Rotator, Critic, Synthesizer
│   │   └── supervisor.py             # Debate orchestrator
│   ├── prompts/                      # Extensible prompt configs
│   │   ├── base_config.py            # Abstract prompt config
│   │   ├── story_seed.py             # Story Seed config
│   │   ├── character_concept.py      # Character Concept config
│   │   └── circle_of_fate.py         # Circle of Fate config
│   └── graph/                        # LangGraph workflow
│       ├── state.py                  # Debate state definitions
│       └── workflow.py               # StateGraph setup
├── files/
│   ├── story_engine_main_deck.json   # Story cards data
│   ├── deck_of_worlds.json           # World cards data
│   ├── story_engine_guide.md         # Story Engine guidebook
│   └── deck_of_worlds_guide.md       # Deck of Worlds guidebook
├── generated_prompts.txt             # Story output (auto-generated)
├── generated_agent_prompts.txt       # AI debate output (auto-generated)
└── generated_worlds.txt              # World output (auto-generated)
```

---

## Multi-Agent Story Engine

The `story_engine_agents.py` uses 4 AI agents to debate and select cards, replicating the collaborative discussion experience of the physical card game.

### Agent Roles

| Agent | Role | Perspective |
|-------|------|-------------|
| **PLACER** | Dramatic advocate | Bold, high-stakes, memorable choices |
| **ROTATOR** | Nuance advocate | Subtle, layered, morally complex choices |
| **CRITIC** | Quality challenger | Identifies clichés, weak combinations |
| **SYNTHESIZER** | Connection finder | Builds cohesion, finds thematic links |

### Debate Flow

1. **Draw** - 4 cards drawn per type (like physical deck's 4 options)
2. **Round 1** - Each agent gives initial opinion
3. **Round 2** - Agents respond/rebut
4. **Vote** - Each agent votes for their choice
5. **Select** - Majority wins (Supervisor breaks ties)

---

## Story Engine

### Card Types

| Type | Description | Count |
|------|-------------|-------|
| **Agents** | Characters who make choices | 144 |
| **Engines** | Motivations and relationships | 72 |
| **Anchors** | Objects, locations, or events | 144 |
| **Conflicts** | Obstacles, consequences, or dilemmas | 72 |
| **Aspects** | Adjectives that describe other cards | 144 |

### Prompt Types

**Simple Prompts:**
- **Story Seed** - Agent + Engine + Anchor + Conflict + Aspect
- **Character Concept** - Deeper character with motivation choices
- **Item/Setting-Driven** - Object-centered story

**Complex Prompts:**
- **Circle of Fate** - Two characters in mutual push-pull
- **Clash of Wills** - Two rivals wanting the same thing
- **Soul Divided** - One character torn between two desires

---

## Deck of Worlds

### Card Types

| Type | Description |
|------|-------------|
| **Regions** | Main terrain/environment (the hub) |
| **Landmarks** | Points of interest / geographic sites |
| **Namesakes** | In-world nicknames/titles |
| **Origins** | Significant events from the past |
| **Attributes** | Present-day features of area/people |
| **Advents** | Future-changing events + story hooks |

### Microsetting Types

**Simple Microsetting:** 1 of each card type

**Complex Microsetting:** Multiple Landmarks, Namesakes, Attributes to choose from

**World Meta:** Global rules (Namesake + Origin + Attribute + Advent) that apply to entire world

**World Map:** Multiple microsettings with shared meta theme
