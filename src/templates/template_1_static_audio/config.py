"""
Template 1 Configuration: Static Audio

Configuration specific to the static images + audio template.
"""

# Template metadata
TEMPLATE_NAME = "static_audio"
TEMPLATE_DESCRIPTION = "Static images with narrated audio (Template 1)"

# Generation steps for this template
# Position: 0=characters, 1=locations, 2=scenes, 3=thumbnails, 4=chapter_cards, 5=audio, 6=video
# Value: 1=run, 0=skip
GENERATION_STEPS = "1111110"  # characters + locations + scenes + thumbnails + chapter_cards + audio (skip video)

# ComfyUI workflows for this template
COMFYUI_WORKFLOWS = {
    "image": "workflows/z_image_turbo_example.json",
    "audio": "workflows/Vibevoice_Single-Speaker.json",
}

# Default steps to run for generation phase
DEFAULT_GENERATION_STEPS = [0, 1, 2, 3, 4, 5]  # characters, locations, scenes, thumbnails, chapter_cards, audio

# Default steps to run for editing phase
DEFAULT_EDITING_STEPS = [1, 2, 3]  # combine audio, scene videos, final video
