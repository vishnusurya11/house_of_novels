"""
Template 1 Configuration: Static Audio

Configuration specific to the static images + audio template.
"""

# Template metadata
TEMPLATE_NAME = "static_audio"
TEMPLATE_DESCRIPTION = "Static images with narrated audio (Template 1)"

# Generation steps for this template
# Position: 0=audio, 1=static_images, 2=scene_images, 3=videos, 4=editing
# Value: 1=run, 0=skip
GENERATION_STEPS = "11101"  # audio + static_images + scene_images + editing (skip videos)

# ComfyUI workflows for this template
COMFYUI_WORKFLOWS = {
    "image": "workflows/z_image_turbo_example.json",
    "audio": "workflows/Vibevoice_Single-Speaker.json",
}

# Default steps to run for generation phase
DEFAULT_GENERATION_STEPS = [1, 2, 3]  # audio, static images, scene images

# Default steps to run for editing phase
DEFAULT_EDITING_STEPS = [1, 2, 3]  # combine audio, scene videos, final video
