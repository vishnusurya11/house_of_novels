# Future: Scene Generation Enhancements

## Multiple Shots Per Scene

Currently each scene generates a single shot (`sh00`). The architecture already supports multiple shots via the `shot_num` parameter in `_run_location_pass()` and `_run_character_pass()`.

### How to add multiple shots

1. The codex `scene_image_prompt` would include a `shots` array instead of (or in addition to) a single `location_layer` + `character_layers`
2. The Step 2 block would add an outer loop over shots:

```python
for shot_idx, shot_data in enumerate(scene_prompt_data.get("shots", [default_shot])):
    state = _run_location_pass(..., shot_num=shot_idx)
    success, gen_data = _run_character_pass(state, ...)
```

3. Naming already includes shot number:
```
api/{ts}/scenes/ch01_sc02_sh00_layer00_loc_00001_.png
api/{ts}/scenes/ch01_sc02_sh00_layer01_char001_00001_.png
api/{ts}/scenes/ch01_sc02_sh01_layer00_loc_00001_.png    <- shot 1
api/{ts}/scenes/ch01_sc02_sh01_layer01_char003_00001_.png
```

4. The `generation` metadata in the codex would store an array of shot results instead of a single result.

### Impact on downstream phases

- **Video generation (Step 4):** Currently reads one `firstframe_path` per scene. Would need to handle multiple frames per scene (one per shot), generating a video segment for each.
- **Editing (Phase 4):** Would need to stitch multiple video segments per scene into the timeline.
- **Phase 2 prompts:** Would need to generate per-shot prompts (camera angles, character positions, etc.).

---

## Validation and Regeneration

Currently, if a layer fails or produces poor quality, the entire scene must be re-run. Future validation would allow targeted regeneration of individual layers.

### How validation could work

1. After each layer completes, a validation step (LLM vision model or CLIP score) checks the output quality.
2. If validation fails, the layer is regenerated (with a new seed) without re-running previous layers.
3. ComfyUI's auto-incrementing counter (`_00002_`, `_00003_`, etc.) naturally handles regeneration — `_find_comfyui_output()` already uses glob to find the latest file by modification time.

### Implementation approach

1. Add a `_validate_layer()` function that takes the output path and validation criteria.
2. Wrap each `_generate_location_layer()` / `_generate_character_layer()` call in a retry loop:

```python
for attempt in range(max_retries):
    success, gen_data = _generate_character_layer(...)
    if success:
        output_path = _find_comfyui_output(prefix)
        if _validate_layer(output_path, criteria):
            break  # good quality, continue to next layer
        print(f"      Validation failed, retrying (attempt {attempt + 1})")
```

3. The `_find_comfyui_output()` glob-based lookup automatically picks up the latest regenerated file.

### Selective re-run from a specific layer

Since each layer's output path is deterministic and recorded in the codex `generation.layers` array, a future `--start-from-layer N` flag could:

1. Read the codex to find which layers already completed
2. Use the last successful layer's output as `current_scene_path`
3. Resume from layer N without re-running layers 0..N-1

---

## Current Architecture Reference

### Two-pass pipeline (Step 2)

```
Pass 1: Location edits    (all scenes, one model load)
Pass 2: Character compositing (all scenes, one model load)
```

### Naming convention

```
ch{NN}_sc{NN}_sh{NN}_layer{NN}_{type}
```

- `type` = `loc` for location edits, `char{NNN}` for character compositing
- Layer numbers are sequential across the full pipeline (location = layer 0, characters = layer 1, 2, ...)

### Key functions in generation.py

| Function | Purpose |
|----------|---------|
| `_find_comfyui_output(prefix)` | Glob-based lookup, returns latest file matching prefix |
| `_generate_location_layer()` | Single-image edit workflow (location modification) |
| `_generate_character_layer()` | Two-image edit workflow (character compositing) |
| `_run_location_pass()` | Orchestrates location edit for one scene, returns state dict |
| `_run_character_pass()` | Orchestrates character layers for one scene using state from location pass |
| `_build_layered_result()` | Builds metadata dict on partial failure |

### Final image tracking

The last layer's output path is stored in `scene["scene_image_prompt"]["generation"]["output_path"]`. Downstream steps (video, editing) read this path directly.
