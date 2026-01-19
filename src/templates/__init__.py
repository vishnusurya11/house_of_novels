"""
House of Novels - Template Registry

Templates define how media is generated and edited for the final output.
All templates inherit from BaseTemplate and implement run_generation() and run_editing().

Usage:
    from src.templates import get_template, set_template, TEMPLATES

    # Get the current/default template
    template = get_template()

    # Use a specific template
    template = get_template("static_audio")

    # Set the active template for the session
    set_template("static_audio")

    # List available templates
    print(TEMPLATES.keys())
"""

from typing import Type

from .base_template import BaseTemplate, GenerationResult, EditingResult
from .template_1_static_audio.template import StaticAudioTemplate


# Registry of available templates
TEMPLATES: dict[str, Type[BaseTemplate]] = {
    "static_audio": StaticAudioTemplate,
    "template_1": StaticAudioTemplate,  # Alias for backward compatibility
}

# Default template name
DEFAULT_TEMPLATE = "static_audio"

# Currently active template instance
_current_template: BaseTemplate | None = None


def get_template(name: str = None) -> BaseTemplate:
    """
    Get a template instance by name.

    Args:
        name: Template name (default: uses DEFAULT_TEMPLATE)

    Returns:
        Template instance

    Raises:
        ValueError: If template name is not found
    """
    global _current_template
    name = name or DEFAULT_TEMPLATE

    if name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template: {name}. Available: {available}")

    # Return existing instance if same template
    if _current_template is not None and _current_template.name == name:
        return _current_template

    # Create new instance
    _current_template = TEMPLATES[name]()
    return _current_template


def set_template(name: str) -> BaseTemplate:
    """
    Set the active template for the session.

    Args:
        name: Template name

    Returns:
        Template instance

    Raises:
        ValueError: If template name is not found
    """
    global _current_template

    if name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template: {name}. Available: {available}")

    _current_template = TEMPLATES[name]()
    return _current_template


def list_templates() -> list[dict]:
    """
    List all available templates with their descriptions.

    Returns:
        List of dicts with name and description
    """
    result = []
    for name, template_class in TEMPLATES.items():
        # Skip aliases (same class with different name)
        instance = template_class()
        if instance.name == name:  # Only include if name matches (not alias)
            result.append({
                "name": instance.name,
                "description": instance.description,
            })
    return result


__all__ = [
    "BaseTemplate",
    "GenerationResult",
    "EditingResult",
    "TEMPLATES",
    "DEFAULT_TEMPLATE",
    "get_template",
    "set_template",
    "list_templates",
]
