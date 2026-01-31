# Phase 1 Revamp Plan: Unified Author-Driven Story Creation

## Goal
Merge Phase 1 (Plotting), Phase 2 (Screenplay), and Phase 3 (Revision) into a single **author-driven Phase 1** with 10 selective sub-steps.

### Input
- Codex from Phase 0 (author, story_structure, story_engine.prompts, deck_of_worlds.prompts)

### Output
- `story.characters` - Character dict with IDs
- `story.locations` - Location dict with IDs
- `story.outline` - Outline with acts, scenes, beats
- `story.narrative` - Full narrative with chapters/scenes/text

---

## Phase 1: 10 Sub-Steps (Author-Driven)

| Step | Name | Description |
|------|------|-------------|
| 1 | **Plotting** | Structure research → Beat sheet → Scene outline |
| 2 | **Characters** | Generate characters, name mapping |
| 3 | **World Building** | Expand setting from DOW + Generate lore/rules + Locations |
| 4 | **Critique & Revise Outline** | Structure/pacing critique → Outline revision |
| 5 | **Complete Narrative** | Write full prose story (Acts 1-3) |
| 6 | **Narrative Revision** | Multi-focus revision (pacing, dialogue, etc.) |
| 7 | **Title Naming** | Book & chapter title naming via 3-agent debate |
| 8 | **Screenplay** | Format narrative for reader presentation |
| 9 | **Final Polish** | Final continuity/prose polish |
| 10 | **Final Output** | Validate and finalize story dict |

---

## Step Details

**Step 1: Plotting**
- Input: story_engine.prompts, deck_of_worlds.prompts, author, story_structure
- Output: story.outline (acts, scenes, beats, title, logline)
- Uses: StructureResearchAgent, BeatSheetAgent, SceneBuilderAgent

**Step 2: Characters**
- Input: story.outline
- Output: story.characters[]
- Uses: Character generation workflow with name debates

**Step 3: World Building (+ Locations)**
- Input: deck_of_worlds.prompts, story.outline, story.characters
- Output: story.world (lore, rules, expanded setting), story.locations[]
- Uses: TBD - world building agent

**Step 4: Critique & Revise Outline**
- Input: story.outline, story.characters, story.world
- Output: Revised story.outline
- Uses: StructureCriticAgent, PacingCriticAgent, ReviserAgent

**Step 5: Complete Narrative**
- Input: story.outline, story.characters, story.locations, story.world
- Output: story.narrative (full prose with acts/scenes/paragraphs/sentences)
- Uses: WriterAgent with author's ScreenplayStyle

**Step 6: Narrative Revision**
- Input: story.narrative
- Output: Revised story.narrative
- Uses: StyleCriticAgent, ContinuityCriticAgent, ReviserAgent
- Passes: TBD (controlled by author's revision_style or CLI flag)

**Step 7: Title Naming**
- Input: story.outline, story.narrative.chapters
- Output: narrative.title, chapters[].chapter_title
- Uses: TitleLiteraryAgent, TitleThematicAgent, TitleCommercialAgent
- Process: 3-agent debate for book title, then each chapter title

**Step 8: Screenplay**
- Input: story.narrative
- Output: story.screenplay (formatted for reader presentation)
- Uses: TBD - formatting agent

**Step 9: Final Polish**
- Input: story.narrative, story.screenplay
- Output: Polished versions
- Uses: Final revision pass

**Step 10: Final Output**
- Validate all story components
- Generate final codex output

---

## Files to Modify

### 1. `src/phases/phase1_plotting.py` → Rename to `phase1_author.py`
- Expand to include all 9 sub-steps
- Absorb Phase 2 (screenplay) logic
- Absorb Phase 3 (revision) logic
- Keep `--steps` flag for selective execution

### 2. `src/phases/phase2_screenplay.py` → DELETE or DEPRECATE
- Move WriterAgent usage into Phase 1 Step 5

### 3. `src/phases/phase3_revision.py` → DELETE or DEPRECATE
- Move revision logic into Phase 1 Steps 6, 8

### 4. `src/story_workflows.py` → UPDATE
- Update workflow to call single unified Phase 1

### 5. `src/story_builder.py` → UPDATE
- Update StoryBuilder to use new Phase 1 structure

---

## New Phase 1 Function Signature

```python
def run_phase1_author(
    codex_path: Path,
    model: str = None,
    scope: str = None,
    steps: list[int] = None,  # 1-10, default all
    revision_passes: int = None,  # For step 6
) -> Phase1Result:
```

---

## Metadata Structure

```json
{
  "metadata": {
    "phase_0": {...},
    "phase_1": {
      "phase": 1,
      "name": "Author-Driven Story Creation",
      "author_id": "author_001",
      "steps_completed": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      "step_timings": {...},
      "plotting": {...},
      "characters": {...},
      "locations": {...},
      "world_building": {...},
      "narrative": {...},
      "revisions": {...}
    }
  }
}
```

---

## Codex Output Structure

```json
{
  "story": {
    "outline": {
      "title": "...",
      "logline": "...",
      "acts": [...]
    },
    "characters": [...],
    "locations": [...],
    "world": {
      "lore": "...",
      "rules": [...],
      "expanded_setting": "..."
    },
    "narrative": {
      "acts": [
        {
          "act_number": 1,
          "scenes": [
            {
              "scene_number": 1,
              "text": "...",
              "paragraphs": [...],
              "sentences": [...]
            }
          ]
        }
      ]
    },
    "screenplay": {
      "formatted_output": "..."
    }
  },
  "metadata": {
    "phase_1": {
      "steps_completed": [1, 2, 3, ..., 10],
      "step_timings": {...}
    }
  }
}
```

---

## Interactive Development Approach

We will build Phase 1 step by step:
1. Start with Step 1 (Plotting) - validate it works
2. Add Step 2 (Characters) - test integration
3. Add Step 3 (World Building + Locations) - test integration
4. Add Step 4 (Critique & Revise) - test integration
5. Add Step 5 (Complete Narrative) - test integration
6. Add Step 6 (Narrative Revision) - test integration
7. Add Step 7 (Title Naming) - test integration
8. Continue adding steps incrementally
9. Each step can be tested independently with `--steps N` flag

---

## CLI Interface

```bash
# Run all steps
uv run python -m src.phases.phase1_author forge/xxx/codex.json

# Run specific steps
uv run python -m src.phases.phase1_author forge/xxx/codex.json --steps 1 2 3

# Run with specific revision passes
uv run python -m src.phases.phase1_author forge/xxx/codex.json --steps 6 --revision-passes 3
```

---

## Author Architecture (Plugin Pattern)

Each author has their own unique way of completing the 9 steps while maintaining the same I/O contract.

### Design Principles
- **Fixed I/O Contract**: Input = Phase 0 codex output, Output = characters[], locations[], outline{}, narrative{}
- **Author Autonomy**: Each author can implement the 9 steps differently (different agents, different story structures, different processes)
- **Self-Contained**: Each author lives in their own folder with all their logic
- **Auto-Discovery**: Authors are discovered automatically at runtime
- **Scalable**: Architecture supports 100+ authors with easy add/remove capability

### Directory Structure

```
src/authors/
├── __init__.py                    # Author registry (auto-discovery)
├── base.py                        # BaseAuthor + BaseAuthorPhase1 interface
├── lyra_shadowmend/
│   ├── __init__.py                # Exports author config + phase1 runner
│   ├── config.py                  # Author identity (name, genres, preferred_structure)
│   └── phase1.py                  # LyraShadowmendPhase1(BaseAuthorPhase1)
├── marcus_steel/
│   ├── __init__.py
│   ├── config.py
│   └── phase1.py
├── elena_nightwood/
│   └── ...
└── _disabled/                     # Disabled authors (ignored by auto-discovery)
    └── old_author/
```

### Base Interface

```python
# src/authors/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Phase1Result:
    """Standard output from any author's Phase 1."""
    codex_path: Path
    outline: dict          # story.outline
    characters: list       # story.characters
    locations: list        # story.locations
    world: dict            # story.world
    narrative: dict        # story.narrative
    screenplay: dict       # story.screenplay (optional)
    success: bool
    error: str = None
    steps_completed: list[int] = None
    step_timings: dict = None

class BaseAuthorPhase1(ABC):
    """Base class all authors must implement for Phase 1."""

    @abstractmethod
    def run(
        self,
        codex_path: Path,
        steps: list[int] = None,
        revision_passes: int = None,
    ) -> Phase1Result:
        """Execute Phase 1 with this author's unique approach."""
        pass

    # Optional: Authors can override individual steps
    def step1_plotting(self, codex: dict) -> dict: ...
    def step2_characters(self, codex: dict) -> dict: ...
    def step3_world_building(self, codex: dict) -> dict: ...
    def step4_critique_revise(self, codex: dict) -> dict: ...
    def step5_narrative(self, codex: dict) -> dict: ...
    def step6_revision(self, codex: dict) -> dict: ...
    def step7_naming(self, codex: dict) -> dict: ...
    def step8_screenplay(self, codex: dict) -> dict: ...
    def step9_polish(self, codex: dict) -> dict: ...
    def step10_finalize(self, codex: dict) -> dict: ...
```

### Author Registry (Auto-Discovery)

```python
# src/authors/__init__.py
def discover_authors() -> dict[str, BaseAuthorPhase1]:
    """Auto-discover all author implementations."""
    authors = {}
    authors_dir = Path(__file__).parent

    for folder in authors_dir.iterdir():
        if folder.is_dir() and not folder.name.startswith(('_', '.')):
            try:
                module = importlib.import_module(f"src.authors.{folder.name}")
                if hasattr(module, 'get_phase1_runner'):
                    authors[folder.name] = module.get_phase1_runner()
            except ImportError:
                pass  # Skip invalid author folders

    return authors

def get_author_phase1(author_id: str) -> BaseAuthorPhase1:
    """Get Phase 1 runner for specific author."""
    authors = discover_authors()
    return authors.get(author_id)
```

### Example Author Implementation

```python
# src/authors/lyra_shadowmend/phase1.py
class LyraShadowmendPhase1(BaseAuthorPhase1):
    """Lyra uses Dan Harmon Story Circle + mystical character naming."""

    def run(self, codex_path: Path, steps: list[int] = None, ...) -> Phase1Result:
        # Lyra's unique implementation
        # - Uses story circle for plotting
        # - Generates mystical character names
        # - Focuses on atmospheric world building
        ...

    def step1_plotting(self, codex: dict) -> dict:
        # Uses DanHarmonStoryCircle structure
        from src.story_structures import get_structure
        structure = get_structure("dan_harmon_story_circle")
        ...
```

### Integration with Phase 1 Runner

```python
# src/phases/phase1_author.py
def run_phase1_author(codex_path: Path, ...) -> Phase1Result:
    codex = load_codex(codex_path)
    author_id = codex["author"]["id"]

    # Get author-specific Phase 1 runner
    phase1_runner = get_author_phase1(author_id)

    if phase1_runner is None:
        raise ValueError(f"Unknown author: {author_id}")

    return phase1_runner.run(codex_path, steps=steps, ...)
```

### Future Scalability Notes

> **Note**: This architecture is designed to support 100+ authors. Future enhancements could include:
> - Performance tracking per author
> - Author comparison metrics
> - Easy enable/disable via `_disabled/` folder
> - Author versioning
> - Hot-reload of author implementations
>
> These are not implemented now but the architecture supports them.
