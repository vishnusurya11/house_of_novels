"""
Scene Narrator — Full scene audio generation with all Qwen3-TTS voice modes
including LoRA fine-tuned adapters.

Extends QwenTTSEngine with LoRA support and provides a complete scene
generation pipeline: load voices -> generate chunks -> stitch with pauses.

Each character can use a different voice mode:
  - custom: Built-in presets (Ryan, Vivian, etc.) with instruct emotion control
  - clone:  Clone from reference audio file
  - design: Generate unique voice from text description, freeze as clone prompt
  - lora:   Fine-tuned LoRA adapter + reference audio for maximum consistency

For LoRA mode, chunks are batched by speaker to avoid repeated adapter swaps.
The narrator uses a CustomVoice preset while character dialogue uses LoRA.

Usage:
    uv run python -m src.tts.scene_narrator --mode design --scene helios  # Sci-fi (3 speakers)
    uv run python -m src.tts.scene_narrator --mode design --scene noir    # Detective (5 speakers)
    uv run python -m src.tts.scene_narrator --mode design --scene noir --style cinematic   # Alt voice style
    uv run python -m src.tts.scene_narrator --mode design --scene noir --style dramatic    # Theater energy
    uv run python -m src.tts.scene_narrator --mode design --scene noir --style intimate    # Audiobook feel
    uv run python -m src.tts.scene_narrator --mode custom --scene noir    # Preset voices
    uv run python -m src.tts.scene_narrator --mode lora   --scene helios  # LoRA adapters
"""

import argparse
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from src.tts.qwen_tts_engine import (
    CloneVoiceConfig,
    CustomVoiceConfig,
    DesignVoiceConfig,
    LoRAVoiceConfig,
    QwenTTSEngine,
    VoiceConfig,
)
from src.tts.voice_consistency_poc import (
    CHARACTERS,
    NARRATOR_CUSTOM_SPEAKER,
    NARRATOR_VOICE_DESC,
    SCENE_SCRIPT,
)

# Lazy imports for heavy dependencies
_PeftModel = None


def _lazy_import_peft():
    """Lazy-import peft to avoid slow startup when not using LoRA."""
    global _PeftModel
    if _PeftModel is None:
        from peft import PeftModel
        _PeftModel = PeftModel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANGUAGE = "English"
OUTPUT_ROOT = Path("forge/tts_poc/scene_narrator")

# Default LoRA adapter paths (from lora_voice_poc Stage 2 output)
LORA_ADAPTER_ROOT = Path("forge/tts_poc/poc3_lora/lora_adapters")


# ---------------------------------------------------------------------------
# Noir scene — Harbor City detective interrogation (5 speakers)
# ---------------------------------------------------------------------------

NOIR_VOICE_DESIGNS = {
    "narrator": "male narrator, rich deep baritone, noir storytelling gravitas, dramatic pacing",
    "elena_cruz": "female alto, sharp commanding edge, clipped professional diction, detective authority",
    "ryan_park": "young male tenor, nervous tremor, slightly breathless, halting speech",
    "marcus_hale": "older male baritone, world-weary rumble, slow unhurried calm, gravel undertone",
    "lila_bennett": "female mezzo-soprano, cool precise clarity, academic measured tone, quiet intensity",
}

# Voice style alternatives — different vocal character for the same 5 speakers
NOIR_VOICE_STYLES: dict[str, dict[str, str]] = {
    "default": NOIR_VOICE_DESIGNS,
    "cinematic": {
        "narrator": "male baritone, commanding cinematic narrator, dynamic storytelling range, polished presence",
        "elena_cruz": "female mezzo-soprano, steady professional authority, controlled calm, measured precision",
        "ryan_park": "young male tenor, anxious undertone, unsteady breath, vulnerable sincerity",
        "marcus_hale": "deep male baritone, warm gravel, patient steadiness, fatherly weight",
        "lila_bennett": "female alto, smooth analytical clarity, detached composure, intellectual poise",
    },
    "dramatic": {
        "narrator": "male bass-baritone, powerful dramatic resonance, theatrical gravitas, commanding presence",
        "elena_cruz": "female mezzo, firm controlled intensity, steely composure, restrained professional edge",
        "ryan_park": "young male tenor, trembling urgency, raw vulnerability, desperate honesty",
        "marcus_hale": "deep male baritone, rumbling wisdom, unhurried gravity, quiet strength",
        "lila_bennett": "female contralto, crystalline precision, surgical calm, penetrating insight",
    },
    "intimate": {
        "narrator": "male baritone, warm intimate narration, close and personal, drawing the listener in",
        "elena_cruz": "female alto, quiet authority, soft-spoken intensity, laser focus",
        "ryan_park": "young male, nervous whisper, intimate vulnerability, confessional tone",
        "marcus_hale": "older male, gentle rumble, soothing patience, grandfatherly warmth",
        "lila_bennett": "female mezzo, soft precise diction, thoughtful pauses, academic calm",
    },
}

NOIR_CUSTOM_SPEAKERS = {
    "narrator": "Ryan",
    "elena_cruz": "Vivian",
    "ryan_park": "Aiden",
    "marcus_hale": "Ryan",
    "lila_bennett": "Vivian",
}

# (speaker_key, text, instruct)
NOIR_SCENE_SCRIPT = [
    (
        "narrator",
        "The rain had been falling all night, turning the streets of Harbor City "
        "into mirrors of broken light. Neon signs flickered in puddles along the "
        "sidewalks while traffic hissed through the wet asphalt. At the corner of "
        "Mercer and Fifth, yellow police tape fluttered weakly in the wind outside "
        "a narrow brick building that smelled faintly of burnt coffee and bad "
        "decisions. Inside, the small diner was dim and mostly empty, the kind of "
        "place that stayed open because no one cared enough to close it. Four "
        "people sat in a booth near the back, the overhead light buzzing faintly "
        "above them.",
        "Rich noir atmosphere, dramatic scene-setting, rain-soaked tension, vivid imagery.",
    ),
    (
        "elena_cruz",
        "Let's start again. Slowly this time.",
        "Sharp command, controlled authority, deliberate emphasis on 'slowly'.",
    ),
    (
        "narrator",
        "Detective Elena Cruz leaned forward across the table, her notebook "
        "resting beside a half-empty cup of coffee. Across from her sat a "
        "nervous young man whose fingers kept tapping the edge of the table "
        "like he was trying to keep time with his own heartbeat.",
        "Engaging character introduction, observational detail, building tension.",
    ),
    (
        "ryan_park",
        "I already told you everything.",
        "Nervous, defensive, voice cracking slightly, wants this to be over.",
    ),
    (
        "narrator",
        "Ryan's voice cracked slightly. He rubbed his hands together and "
        "avoided looking at anyone directly.",
        "Quick character beat, physical nervousness, tight narration.",
    ),
    (
        "elena_cruz",
        "You told us what you think happened.",
        "Sharp correction, emphasizing the distinction, controlled intensity.",
    ),
    (
        "narrator",
        "Cruz's pen hovered above the notebook.",
        "Tense beat, loaded silence, anticipation.",
    ),
    (
        "elena_cruz",
        "Now tell us what you saw.",
        "Direct command, quiet steel, no room for evasion.",
    ),
    (
        "narrator",
        "At the far end of the booth, a broad-shouldered man in a wrinkled gray "
        "suit watched the exchange with tired eyes. Detective Marcus Hale had "
        "the look of someone who had seen too many nights like this one.",
        "Introducing new character, world-weary atmosphere, dramatic observation.",
    ),
    (
        "marcus_hale",
        "Take your time, kid.",
        "Gentle, patient, reassuring, unhurried calm.",
    ),
    (
        "narrator",
        "Marcus folded his arms across his chest.",
        "Brief physical beat, settling in, quiet authority.",
    ),
    (
        "marcus_hale",
        "Nobody here is in a hurry.",
        "Warm reassurance, steady calm, grounding presence.",
    ),
    (
        "narrator",
        "The diner's front door opened briefly as someone stepped inside to "
        "escape the rain. Cold air swept through the room before the door "
        "closed again.",
        "Atmospheric interruption, ambient detail, noir texture.",
    ),
    (
        "ryan_park",
        "I was locking up the register when the lights outside flickered.",
        "Testimony beginning, measured recall, underlying anxiety.",
    ),
    (
        "narrator",
        "Ryan finally looked up.",
        "Pivotal moment, shift in energy, dramatic beat.",
    ),
    (
        "ryan_park",
        "That's when I saw him.",
        "Quiet dread, significant reveal, weight in every word.",
    ),
    (
        "narrator",
        "Cruz lifted her pen.",
        "Sharp reaction beat, alert attention, tension rising.",
    ),
    (
        "elena_cruz",
        "Saw who?",
        "Quick, sharp, leaning forward, professional urgency.",
    ),
    (
        "narrator",
        "Ryan swallowed.",
        "Physical tension, hesitation, dramatic pause.",
    ),
    (
        "ryan_park",
        "The man standing across the street.",
        "Low, careful, each word deliberate, unease building.",
    ),
    (
        "narrator",
        "The diner's cook glanced up from behind the counter but quickly "
        "returned to cleaning a metal tray.",
        "Background detail, ambient life, brief distraction.",
    ),
    (
        "marcus_hale",
        "What was he doing?",
        "Calm follow-up, investigative patience, steady probing.",
    ),
    (
        "ryan_park",
        "Nothing.",
        "Short, stark, the simplicity is what makes it unsettling.",
    ),
    (
        "narrator",
        "Ryan shook his head quickly.",
        "Nervous energy, quick physical gesture, agitation.",
    ),
    (
        "ryan_park",
        "That was the weird part.",
        "Dawning unease, trying to articulate the wrongness.",
    ),
    (
        "narrator",
        "Cruz exchanged a glance with Marcus.",
        "Silent communication between detectives, shared instinct.",
    ),
    (
        "elena_cruz",
        "People stand on sidewalks all the time.",
        "Testing the witness, calm skepticism, measuring reaction.",
    ),
    (
        "ryan_park",
        "Not like this.",
        "Firm, defensive, insistent, he knows what he saw.",
    ),
    (
        "narrator",
        "Ryan leaned forward slightly.",
        "Physical engagement, urgency rising, committing to the story.",
    ),
    (
        "ryan_park",
        "He was just watching the building.",
        "Emphasis on 'watching', unsettled certainty, eerie calm.",
    ),
    (
        "narrator",
        "At the end of the booth, a woman who had been silent until now "
        "shifted slightly. She wore a dark coat that was still wet from "
        "the rain.",
        "New voice entering, understated dramatic entrance, anticipation.",
    ),
    (
        "lila_bennett",
        "Watching the building or watching you?",
        "Precise, incisive question, cool analytical clarity, cutting through.",
    ),
    (
        "narrator",
        "Ryan hesitated.",
        "Weighted pause, the question landing, uncertainty exposed.",
    ),
    (
        "ryan_park",
        "I don't know.",
        "Vulnerable, honest uncertainty, the bravado cracking.",
    ),
    (
        "narrator",
        "Lila Bennett adjusted her glasses and studied him carefully.",
        "Analytical observation, composed scrutiny, clinical attention.",
    ),
    (
        "lila_bennett",
        "Details matter.",
        "Firm, precise, instructive, quiet authority of expertise.",
    ),
    (
        "narrator",
        "The buzzing overhead light flickered again.",
        "Atmospheric punctuation, unease, noir visual detail.",
    ),
    (
        "lila_bennett",
        "Especially tonight.",
        "Weighted emphasis, foreboding, controlled intensity.",
    ),
    (
        "narrator",
        "Marcus leaned forward now.",
        "Physical shift, engagement deepening, gravity increasing.",
    ),
    (
        "marcus_hale",
        "Tell us what happened next.",
        "Gentle prompt, steady patience, encouraging without pushing.",
    ),
    (
        "narrator",
        "Ryan took a deep breath.",
        "Steeling himself, gathering courage, pivotal moment.",
    ),
    (
        "ryan_park",
        "The streetlight went out.",
        "Flat delivery, stating the impossible, quiet shock.",
    ),
    (
        "narrator",
        "Rain rattled harder against the diner windows.",
        "Atmospheric escalation, nature mirroring tension, dramatic underscore.",
    ),
    (
        "ryan_park",
        "Just one second.",
        "Precise timing, measured, the specificity adding dread.",
    ),
    (
        "narrator",
        "Ryan held up a finger.",
        "Physical emphasis, visual punctuation, conviction.",
    ),
    (
        "ryan_park",
        "That's all it was.",
        "Insistent, trying to make them understand the impossibility.",
    ),
    (
        "narrator",
        "Cruz wrote something in her notebook.",
        "Professional documentation, controlled reaction, processing.",
    ),
    (
        "elena_cruz",
        "And when the light came back?",
        "Measured follow-up, leaning in, anticipation in her voice.",
    ),
    (
        "narrator",
        "Ryan looked toward the diner window as if expecting to see the same "
        "figure outside.",
        "Involuntary dread, memory bleeding into present, haunted.",
    ),
    (
        "ryan_park",
        "He was gone.",
        "Simple, stark, the absence more terrifying than presence.",
    ),
    (
        "narrator",
        "The table went quiet for a moment.",
        "Heavy silence, everyone processing, tension at peak.",
    ),
    (
        "marcus_hale",
        "People leave.",
        "Matter-of-fact, offering the rational explanation, gentle.",
    ),
    (
        "ryan_park",
        "Yeah.",
        "Flat agreement, but unconvinced, leading somewhere.",
    ),
    (
        "narrator",
        "Ryan nodded slowly.",
        "Deliberate, building to something, the calm before.",
    ),
    (
        "ryan_park",
        "But the door upstairs opened.",
        "Quiet escalation, the turn, dread in the delivery.",
    ),
    (
        "narrator",
        "Cruz stopped writing.",
        "Freeze reaction, something significant, full attention.",
    ),
    (
        "elena_cruz",
        "Upstairs?",
        "Sharp surprise, breaking composure slightly, single-word question.",
    ),
    (
        "ryan_park",
        "The apartment above the diner.",
        "Clarifying, steady now, committed to the truth.",
    ),
    (
        "narrator",
        "Marcus straightened slightly.",
        "Physical reaction, old instincts firing, alert.",
    ),
    (
        "marcus_hale",
        "The one that's been empty for two years.",
        "Low, grave, the weight of implication, connecting dots.",
    ),
    (
        "ryan_park",
        "That's what I thought too.",
        "Agreement laced with fear, shared knowledge of impossibility.",
    ),
    (
        "narrator",
        "Lila Bennett leaned forward now, her voice calm but precise.",
        "New energy, analytical mind engaging, clinical focus.",
    ),
    (
        "lila_bennett",
        "And that's when you called the police.",
        "Logical assumption, stated as fact, seeking confirmation.",
    ),
    (
        "ryan_park",
        "No.",
        "Single word, defying expectation, the real reveal approaching.",
    ),
    (
        "narrator",
        "Ryan shook his head.",
        "Negation, physical emphasis, building to climax.",
    ),
    (
        "ryan_park",
        "That's when I heard the scream.",
        "Climactic reveal, quiet horror, the words hanging in the air.",
    ),
    (
        "narrator",
        "Outside, thunder rolled across the harbor. Inside the diner, the "
        "overhead light flickered again as the four people at the booth "
        "realized the night's story had only just begun.",
        "Dramatic closing narration, atmospheric crescendo, noir gravitas, the story continues.",
    ),
]


# ---------------------------------------------------------------------------
# Temple scene — Desert archaeology expedition (5 speakers)
# ---------------------------------------------------------------------------

TEMPLE_VOICE_DESIGNS = {
    "narrator": "male baritone, rich cinematic narrator, adventure storytelling gravitas, dynamic range",
    "samuel_carter": "male tenor, warm confident authority, scholarly enthusiasm, steady composure",
    "leila_hassan": "female alto, grounded pragmatism, careful precision, quiet strength",
    "arthur_whitlock": "older male baritone, distinguished scholarly excitement, professorial warmth, eloquent pacing",
    "jonah_price": "male baritone, dry sardonic edge, understated humor, world-weary practicality",
}

TEMPLE_CUSTOM_SPEAKERS = {
    "narrator": "Ryan",
    "samuel_carter": "Aiden",
    "leila_hassan": "Vivian",
    "arthur_whitlock": "Ryan",
    "jonah_price": "Aiden",
}

# (speaker_key, text, instruct)
TEMPLE_SCENE_SCRIPT = [
    (
        "narrator",
        "The desert had a way of swallowing sound. Wind slid across the endless "
        "dunes, lifting thin streams of sand that drifted like ghosts over the "
        "ruins half-buried beneath the earth. At the center of the excavation "
        "site stood the broken remains of a stone temple that had not seen human "
        "footsteps for centuries. Lanterns hung from wooden posts around the dig "
        "site, casting trembling circles of gold against the ancient carvings. "
        "Shadows stretched across the sand as four figures gathered around a "
        "narrow stairway that descended into darkness.",
        "Rich adventure atmosphere, cinematic scene-setting, desert mystery, vivid imagery.",
    ),
    (
        "samuel_carter",
        "According to the inscriptions, this chamber hasn't been opened since "
        "the temple was sealed.",
        "Measured scholarly excitement, controlled awe, professional authority.",
    ),
    (
        "narrator",
        "Dr. Samuel Carter brushed sand from the edge of the stone doorway. "
        "The carved symbols surrounding it were worn with age but still sharp "
        "enough to hint at their original precision.",
        "Character introduction, observational detail, archaeological texture.",
    ),
    (
        "leila_hassan",
        "That usually means there's a reason it stayed sealed.",
        "Dry caution, practical wisdom, guarded skepticism.",
    ),
    (
        "narrator",
        "Leila folded her arms, studying the stairway with a cautious expression.",
        "Brief character beat, physical wariness, measured composure.",
    ),
    (
        "arthur_whitlock",
        "Or it means we are standing on the verge of the most important "
        "discovery of the century.",
        "Grand scholarly excitement, professorial grandeur, barely contained thrill.",
    ),
    (
        "narrator",
        "Professor Whitlock adjusted the brim of his hat as he peered down "
        "the narrow passage.",
        "Character detail, physical anticipation, seasoned explorer.",
    ),
    (
        "jonah_price",
        "Or we're about to release something that should've stayed buried.",
        "Sardonic warning, dry humor masking unease, deadpan delivery.",
    ),
    (
        "narrator",
        "Jonah shifted his weight and glanced toward the dark entrance.",
        "Physical nervousness, understated tension, quick character beat.",
    ),
    (
        "samuel_carter",
        "You've been reading too many adventure novels.",
        "Warm teasing, light dismissal, affectionate humor.",
    ),
    (
        "narrator",
        "Carter smiled faintly as he lifted the lantern from its hook.",
        "Gentle warmth, quiet confidence, transition beat.",
    ),
    (
        "samuel_carter",
        "Temples don't trap curses.",
        "Reassuring authority, matter-of-fact, scientific certainty.",
    ),
    (
        "jonah_price",
        "Statistically speaking, we've opened three ancient tombs together.",
        "Dry factual delivery, deadpan setup, building to a point.",
    ),
    (
        "narrator",
        "Jonah raised three fingers.",
        "Physical punctuation, comedic timing, visual emphasis.",
    ),
    (
        "jonah_price",
        "Two of them collapsed.",
        "Flat deadpan, the humor is in the simplicity, understated dread.",
    ),
    (
        "leila_hassan",
        "And the third one flooded.",
        "Wry addition, dry solidarity with Jonah, shared experience.",
    ),
    (
        "narrator",
        "Carter sighed quietly.",
        "Conceding the point, gentle exasperation, brief beat.",
    ),
    (
        "samuel_carter",
        "Archaeology requires a certain amount of optimism.",
        "Philosophical warmth, steady conviction, gentle leadership.",
    ),
    (
        "narrator",
        "Whitlock leaned closer to the carved doorway, tracing the faded "
        "symbols with a gloved hand.",
        "Scholarly absorption, physical engagement, reverent attention.",
    ),
    (
        "arthur_whitlock",
        "These markings describe a king who believed the gods had given him "
        "something sacred.",
        "Hushed scholarly wonder, reverent translation, building significance.",
    ),
    (
        "leila_hassan",
        "Sacred how?",
        "Sharp follow-up, cutting to the point, practical urgency.",
    ),
    (
        "narrator",
        "Whitlock straightened slowly.",
        "Dramatic pause, weight of implication, deliberate gravity.",
    ),
    (
        "arthur_whitlock",
        "Powerful.",
        "Single word landing with weight, ominous scholarly certainty, loaded pause.",
    ),
    (
        "narrator",
        "The wind howled briefly across the ruins before fading again into silence.",
        "Atmospheric punctuation, nature responding to revelation, eerie stillness.",
    ),
    (
        "jonah_price",
        "I'm starting to dislike that word.",
        "Sardonic understatement, nervous humor, breaking tension.",
    ),
    (
        "narrator",
        "Carter lowered the lantern toward the stairway. The light revealed "
        "narrow stone steps descending into the earth.",
        "Action transition, visual discovery, anticipation building.",
    ),
    (
        "samuel_carter",
        "There's only one way to find out.",
        "Quiet determination, steady resolve, leadership decision.",
    ),
    (
        "narrator",
        "For a moment no one moved. The desert stretched endlessly around them, "
        "silent and watchful beneath the stars.",
        "Suspended tension, vast isolation, cinematic stillness.",
    ),
    (
        "leila_hassan",
        "If we go down there...",
        "Cautious deliberation, trailing off with weight, setting conditions.",
    ),
    (
        "narrator",
        "Leila met Carter's eyes.",
        "Direct connection, unspoken understanding, pivotal beat.",
    ),
    (
        "leila_hassan",
        "...we do it carefully.",
        "Firm insistence, quiet steel, non-negotiable condition.",
    ),
    (
        "samuel_carter",
        "Agreed.",
        "Simple affirmation, respect for her caution, trust.",
    ),
    (
        "narrator",
        "Whitlock adjusted his coat, unable to hide the excitement in his voice.",
        "Physical tell, academic giddiness, anticipation leaking through.",
    ),
    (
        "arthur_whitlock",
        "History rarely waits for the cautious.",
        "Grand professorial pronouncement, adventurous spirit, philosophical flourish.",
    ),
    (
        "narrator",
        "Jonah let out a quiet breath.",
        "Resigned acceptance, steeling himself, brief exhale.",
    ),
    (
        "jonah_price",
        "History also rarely warns you before it bites.",
        "Sardonic retort, dry wisdom, final word of caution.",
    ),
    (
        "narrator",
        "Carter stepped onto the first stone step, the lantern light spilling "
        "into the passage below.",
        "Action moment, descent beginning, light against darkness.",
    ),
    (
        "samuel_carter",
        "Well.",
        "Single word, gathering breath, moment before the plunge.",
    ),
    (
        "narrator",
        "The lantern glow stretched downward into darkness that had remained "
        "untouched for centuries.",
        "Visual poetry, ancient darkness meeting modern light, anticipation.",
    ),
    (
        "samuel_carter",
        "Let's meet the past.",
        "Quiet determination, poetic resolve, the final word before descent.",
    ),
    (
        "narrator",
        "One by one, the four figures began descending into the buried temple, "
        "while the desert wind quietly erased their footprints above.",
        "Dramatic closing narration, cinematic finality, haunting imagery, the journey begins.",
    ),
]


# ---------------------------------------------------------------------------
# Voice config presets per mode
# ---------------------------------------------------------------------------

def _get_scene_data(
    scene: str,
    style: str = "default",
) -> tuple[list[tuple[str, str, str]], dict[str, str], dict[str, str]]:
    """Get scene script, voice designs, and custom speaker assignments.

    Args:
        scene: Scene name (helios, noir)
        style: Voice style profile (default, cinematic, dramatic, intimate).
               Only applies to noir scene in design mode.

    Returns:
        (script, voice_designs, custom_speakers)
    """
    if scene == "helios":
        voice_designs = {
            "narrator": NARRATOR_VOICE_DESC,
            "marcus_reed": CHARACTERS["marcus_reed"]["voice_desc"],
            "aurora_vale": CHARACTERS["aurora_vale"]["voice_desc"],
        }
        custom_speakers = {
            "narrator": NARRATOR_CUSTOM_SPEAKER,
            "marcus_reed": CHARACTERS["marcus_reed"]["custom_speaker"],
            "aurora_vale": CHARACTERS["aurora_vale"]["custom_speaker"],
        }
        return SCENE_SCRIPT, voice_designs, custom_speakers

    elif scene == "noir":
        if style not in NOIR_VOICE_STYLES:
            raise ValueError(
                f"Unknown style '{style}'. Choose from: {', '.join(NOIR_VOICE_STYLES)}"
            )
        voice_designs = NOIR_VOICE_STYLES[style]
        return NOIR_SCENE_SCRIPT, voice_designs, NOIR_CUSTOM_SPEAKERS

    elif scene == "temple":
        return TEMPLE_SCENE_SCRIPT, TEMPLE_VOICE_DESIGNS, TEMPLE_CUSTOM_SPEAKERS

    else:
        raise ValueError(f"Unknown scene: {scene}")


# Sample texts for voice design (first line each character speaks)
_DESIGN_SAMPLE_TEXTS = {
    "narrator": "The observation deck hung in perfect silence above a pale blue planet.",
    "marcus_reed": "Hello, I'm Marcus Reed, mission commander of the Helios.",
    "aurora_vale": "Hello, I'm Aurora Vale, chief science officer aboard the Helios.",
    "elena_cruz": "Let's start again. Slowly this time.",
    "ryan_park": "I already told you everything.",
    "marcus_hale": "Take your time, kid. Nobody here is in a hurry.",
    "lila_bennett": "Details matter. Especially tonight.",
    "samuel_carter": "According to the inscriptions, this chamber hasn't been opened since the temple was sealed.",
    "leila_hassan": "That usually means there's a reason it stayed sealed.",
    "arthur_whitlock": "These markings describe a king who believed the gods had given him something sacred.",
    "jonah_price": "Statistically speaking, we've opened three ancient tombs together.",
}


def _build_voice_map(
    mode: str,
    scene: str = "helios",
    style: str = "default",
) -> dict[str, VoiceConfig]:
    """Build voice map for the given mode and scene.

    Args:
        mode: Voice mode (custom, design, clone, lora)
        scene: Scene to use (helios, noir)
        style: Voice style profile (only affects noir/design mode)

    Returns:
        Dict mapping speaker_key -> VoiceConfig
    """
    _, voice_designs, custom_speakers = _get_scene_data(scene, style=style)

    if mode == "custom":
        return {
            spk: CustomVoiceConfig(preset)
            for spk, preset in custom_speakers.items()
        }

    elif mode == "design":
        return {
            spk: DesignVoiceConfig(
                description=desc,
                sample_text=_DESIGN_SAMPLE_TEXTS.get(spk, f"Hello, my name is {spk}."),
            )
            for spk, desc in voice_designs.items()
        }

    elif mode == "clone":
        voice_map: dict[str, VoiceConfig] = {
            "narrator": CustomVoiceConfig(custom_speakers.get("narrator", "Ryan")),
        }
        for spk in voice_designs:
            if spk != "narrator":
                voice_map[spk] = CloneVoiceConfig(
                    ref_audio=f"audio_inputs/{spk}_ref.wav",
                    ref_text=_DESIGN_SAMPLE_TEXTS.get(spk, ""),
                )
        return voice_map

    elif mode == "lora":
        voice_map = {
            "narrator": CustomVoiceConfig(custom_speakers.get("narrator", "Ryan")),
        }
        for spk in voice_designs:
            if spk != "narrator":
                adapter_dir = LORA_ADAPTER_ROOT / spk
                voice_map[spk] = LoRAVoiceConfig(
                    adapter_path=str(adapter_dir),
                    ref_audio=str(adapter_dir / "ref_sample.wav"),
                    ref_text=_DESIGN_SAMPLE_TEXTS.get(spk, ""),
                )
        return voice_map

    else:
        raise ValueError(f"Unknown mode: {mode}")


# ---------------------------------------------------------------------------
# Audio post-processing
# ---------------------------------------------------------------------------

def _trim_silence(audio: np.ndarray, top_db: float = 40.0) -> np.ndarray:
    if audio.size == 0:
        return audio
    peak = np.max(np.abs(audio))
    if peak < 1e-10:
        return audio
    threshold = 10 ** (-top_db / 20) * peak
    above = np.where(np.abs(audio) > threshold)[0]
    if len(above) == 0:
        return audio
    return audio[above[0]:above[-1] + 1]


def _edge_fade(audio: np.ndarray, sr: int, ms: float = 5.0) -> np.ndarray:
    n = min(int(sr * ms / 1000), len(audio) // 2)
    if n < 2:
        return audio
    audio = audio.copy()
    audio[:n] *= np.linspace(0, 1, n).astype(np.float32)
    audio[-n:] *= np.linspace(1, 0, n).astype(np.float32)
    return audio


def _normalize(audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-10:
        return audio
    return (audio * (10 ** (target_dbfs / 20) / rms)).astype(np.float32)


def _postprocess(wav: np.ndarray, sr: int) -> np.ndarray:
    return _normalize(_edge_fade(_trim_silence(wav), sr))


def _save(audio: np.ndarray, sr: int, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sr)


def _concat_with_pause(segs: list[np.ndarray], sr: int, pause_ms: int = 400) -> np.ndarray:
    pause = np.zeros(int(sr * pause_ms / 1000), dtype=np.float32)
    parts = []
    for i, seg in enumerate(segs):
        if i > 0:
            parts.append(pause)
        parts.append(seg)
    return np.concatenate(parts) if parts else np.array([], dtype=np.float32)


# ---------------------------------------------------------------------------
# Scene Narrator — core generation logic
# ---------------------------------------------------------------------------

class SceneNarrator:
    """Generates full scene audio with support for all voice modes.

    For CustomVoice/Design/Clone modes, delegates to QwenTTSEngine.
    For LoRA mode, handles adapter loading/swapping and batched generation.
    """

    def __init__(
        self,
        device: str = "cuda",
        precision: str = "bfloat16",
        model_size: str = "1.7B",
        pause_cross_speaker_ms: int = 600,
        pause_same_speaker_ms: int = 300,
    ):
        self.device = device
        self.precision = precision
        self.model_size = model_size
        self.pause_cross_ms = pause_cross_speaker_ms
        self.pause_same_ms = pause_same_speaker_ms
        self.sample_rate = 24000

        # Engine for non-LoRA voice modes
        self._engine: QwenTTSEngine | None = None

        # LoRA state
        self._lora_model = None  # Base model with LoRA adapter applied
        self._lora_clone_cache: dict[str, object] = {}  # speaker -> clone prompt
        self._current_lora_speaker: str | None = None

    def _get_engine(self) -> QwenTTSEngine:
        """Lazily create the TTS engine."""
        if self._engine is None:
            self._engine = QwenTTSEngine(
                device=self.device,
                precision=self.precision,
                model_size=self.model_size,
                pause_between_speakers_ms=self.pause_cross_ms,
                pause_within_speaker_ms=self.pause_same_ms,
            )
        return self._engine

    def _has_lora_speakers(self, voice_map: dict[str, VoiceConfig]) -> bool:
        """Check if any speaker uses LoRA."""
        return any(isinstance(v, LoRAVoiceConfig) for v in voice_map.values())

    def _load_lora_for_speaker(
        self,
        speaker: str,
        config: LoRAVoiceConfig,
    ) -> object:
        """Load a LoRA adapter for a speaker and create their clone prompt.

        If this speaker's clone prompt is already cached, returns it directly.
        Otherwise loads the adapter, creates the prompt, and caches it.

        Returns:
            Reusable voice_clone_prompt object
        """
        # Return cached prompt if available
        if speaker in self._lora_clone_cache:
            return self._lora_clone_cache[speaker]

        _lazy_import_peft()
        import torch
        from qwen_tts import Qwen3TTSModel

        adapter_path = Path(config.adapter_path)
        if not (adapter_path / "adapter_config.json").exists():
            raise FileNotFoundError(
                f"No LoRA adapter found at {adapter_path}. "
                f"Run lora_voice_poc.py --stage train first."
            )

        # Load fresh base model (LoRA requires clean base each time)
        if self._lora_model is not None and self._current_lora_speaker != speaker:
            del self._lora_model
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self._lora_model = None

        if self._lora_model is None:
            print(f"        Loading Base model for LoRA ({speaker})...")
            device_map = f"{self.device}:0" if self.device == "cuda" else self.device
            self._lora_model = Qwen3TTSModel.from_pretrained(
                f"Qwen/Qwen3-TTS-12Hz-{self.model_size}-Base",
                device_map=device_map,
                dtype=torch.bfloat16,
            )

            # Apply LoRA adapter (model.model is the inner Qwen3TTS wrapper)
            print(f"        Applying LoRA adapter: {adapter_path.name}")
            self._lora_model.model.talker = _PeftModel.from_pretrained(
                self._lora_model.model.talker, str(adapter_path),
            )
            self._lora_model.model.talker.eval()
            self._current_lora_speaker = speaker

        # Create clone prompt from reference audio
        ref_text = config.ref_text.strip() if config.ref_text else ""
        use_xvec_only = not ref_text
        if use_xvec_only:
            print(f"        [lora-clone] No ref_text — x_vector_only mode")

        clone_prompt = self._lora_model.create_voice_clone_prompt(
            ref_audio=config.ref_audio,
            ref_text=ref_text if not use_xvec_only else None,
            x_vector_only_mode=use_xvec_only,
        )

        self._lora_clone_cache[speaker] = clone_prompt
        return clone_prompt

    def _generate_lora_chunk(
        self,
        text: str,
        speaker: str,
        config: LoRAVoiceConfig,
    ) -> tuple[np.ndarray, int]:
        """Generate a single audio chunk using LoRA-adapted model."""
        clone_prompt = self._load_lora_for_speaker(speaker, config)
        wavs, sr = self._lora_model.generate_voice_clone(
            text=text,
            language=LANGUAGE,
            voice_clone_prompt=clone_prompt,
        )
        return wavs[0], sr

    def generate_scene(
        self,
        script: list[tuple[str, str, str]],
        voice_map: dict[str, VoiceConfig],
        output_dir: Path,
        mode_label: str = "",
    ) -> tuple[bool, float]:
        """Generate full scene audio from a script.

        For scenes with LoRA speakers, chunks are batched by speaker to
        minimize adapter swaps. Non-LoRA speakers are generated inline.

        Args:
            script: List of (speaker_key, text, instruct) tuples
            voice_map: Speaker -> VoiceConfig mapping
            output_dir: Directory for output WAV files
            mode_label: Label for logging

        Returns:
            (success, total_duration_seconds)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        total_chunks = len(script)

        print(f"\n  Generating {total_chunks} chunks ({mode_label})...")

        has_lora = self._has_lora_speakers(voice_map)

        if has_lora:
            return self._generate_scene_batched(script, voice_map, output_dir)
        else:
            return self._generate_scene_sequential(script, voice_map, output_dir)

    def _generate_scene_sequential(
        self,
        script: list[tuple[str, str, str]],
        voice_map: dict[str, VoiceConfig],
        output_dir: Path,
    ) -> tuple[bool, float]:
        """Generate scene sequentially (no LoRA — simple path)."""
        engine = self._get_engine()
        total_chunks = len(script)

        all_segments: list[np.ndarray] = []
        per_speaker: dict[str, list[np.ndarray]] = {}
        prev_speaker = None

        for idx, (speaker_key, text, instruct) in enumerate(script):
            # Add pause
            if prev_speaker is not None:
                pause_ms = self.pause_cross_ms if speaker_key != prev_speaker else self.pause_same_ms
                all_segments.append(np.zeros(int(self.sample_rate * pause_ms / 1000), dtype=np.float32))

            voice_config = voice_map.get(speaker_key, voice_map.get("narrator"))
            print(f"    [{idx + 1:02d}/{total_chunks}] {speaker_key}: {text[:40]}...")
            start = time.time()

            try:
                # Resolve DesignVoiceConfig to clone prompt
                if isinstance(voice_config, DesignVoiceConfig):
                    cache_key = f"design:{speaker_key}"
                    if cache_key not in engine._voice_cache:
                        print(f"        Designing voice for {speaker_key}...")
                        clone_prompt = engine.design_character_voice(
                            description=voice_config.description,
                            sample_text=voice_config.sample_text,
                        )
                        engine._voice_cache[cache_key] = clone_prompt

                    wav, sr = engine._generate_clone_chunk(
                        text=text,
                        clone_prompt=engine._voice_cache[cache_key],
                        language=LANGUAGE,
                    )
                else:
                    wav, sr = engine.generate_chunk(
                        text=text,
                        speaker=speaker_key,
                        instruct=instruct,
                        voice_config=voice_config,
                        language=LANGUAGE,
                    )

                wav = _postprocess(wav, sr)

            except Exception as e:
                print(f"      ERROR: {e}")
                wav = np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)

            all_segments.append(wav)
            per_speaker.setdefault(speaker_key, []).append(wav)
            prev_speaker = speaker_key
            print(f"      -> {len(wav) / self.sample_rate:.1f}s ({time.time() - start:.1f}s)")

        return self._save_scene(all_segments, per_speaker, output_dir)

    def _generate_scene_batched(
        self,
        script: list[tuple[str, str, str]],
        voice_map: dict[str, VoiceConfig],
        output_dir: Path,
    ) -> tuple[bool, float]:
        """Generate scene with LoRA speakers batched to minimize adapter swaps.

        Strategy:
        1. Generate all non-LoRA chunks first (sequential, using engine)
        2. For each LoRA speaker: load adapter -> generate all their chunks -> unload
        3. Stitch all chunks together in original script order with pauses
        """
        engine = self._get_engine()
        total_chunks = len(script)

        # Pre-allocate results array indexed by script position
        chunk_audio: list[np.ndarray | None] = [None] * total_chunks
        per_speaker: dict[str, list[np.ndarray]] = {}

        # --- Pass 1: Generate non-LoRA chunks ---
        non_lora_count = sum(
            1 for spk, _, _ in script
            if not isinstance(voice_map.get(spk), LoRAVoiceConfig)
        )
        if non_lora_count > 0:
            print(f"\n    Pass 1: {non_lora_count} non-LoRA chunks...")

        for idx, (speaker_key, text, instruct) in enumerate(script):
            voice_config = voice_map.get(speaker_key, voice_map.get("narrator"))
            if isinstance(voice_config, LoRAVoiceConfig):
                continue  # Handle in Pass 2

            print(f"    [{idx + 1:02d}/{total_chunks}] {speaker_key}: {text[:40]}...")
            start = time.time()

            try:
                if isinstance(voice_config, DesignVoiceConfig):
                    cache_key = f"design:{speaker_key}"
                    if cache_key not in engine._voice_cache:
                        print(f"        Designing voice for {speaker_key}...")
                        clone_prompt = engine.design_character_voice(
                            description=voice_config.description,
                            sample_text=voice_config.sample_text,
                        )
                        engine._voice_cache[cache_key] = clone_prompt
                    wav, sr = engine._generate_clone_chunk(
                        text=text,
                        clone_prompt=engine._voice_cache[cache_key],
                        language=LANGUAGE,
                    )
                else:
                    wav, sr = engine.generate_chunk(
                        text=text,
                        speaker=speaker_key,
                        instruct=instruct,
                        voice_config=voice_config,
                        language=LANGUAGE,
                    )
                wav = _postprocess(wav, sr)
            except Exception as e:
                print(f"      ERROR: {e}")
                wav = np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)

            chunk_audio[idx] = wav
            per_speaker.setdefault(speaker_key, []).append(wav)
            print(f"      -> {len(wav) / self.sample_rate:.1f}s ({time.time() - start:.1f}s)")

        # --- Pass 2: Generate LoRA chunks, batched by speaker ---
        lora_speakers = {
            spk: cfg for spk, cfg in voice_map.items()
            if isinstance(cfg, LoRAVoiceConfig)
        }

        for speaker_key, lora_config in lora_speakers.items():
            # Collect this speaker's chunks
            speaker_chunks = [
                (idx, text, instruct)
                for idx, (spk, text, instruct) in enumerate(script)
                if spk == speaker_key
            ]
            if not speaker_chunks:
                continue

            print(f"\n    Pass 2: {len(speaker_chunks)} chunks for {speaker_key} (LoRA)...")

            # Load adapter (cached after first call)
            for idx, text, instruct in speaker_chunks:
                combined_instruct = instruct
                if lora_config.character_style:
                    combined_instruct = f"{instruct} {lora_config.character_style}"

                print(f"    [{idx + 1:02d}/{total_chunks}] {speaker_key}: {text[:40]}...")
                start = time.time()

                try:
                    wav, sr = self._generate_lora_chunk(text, speaker_key, lora_config)
                    wav = _postprocess(wav, sr)
                except Exception as e:
                    print(f"      ERROR: {e}")
                    wav = np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)

                chunk_audio[idx] = wav
                per_speaker.setdefault(speaker_key, []).append(wav)
                print(f"      -> {len(wav) / self.sample_rate:.1f}s ({time.time() - start:.1f}s)")

            # Free LoRA model after processing this speaker
            self._unload_lora()

        # --- Stitch all chunks in original order ---
        all_segments: list[np.ndarray] = []
        prev_speaker = None

        for idx, (speaker_key, _, _) in enumerate(script):
            wav = chunk_audio[idx]
            if wav is None:
                wav = np.zeros(int(self.sample_rate * 0.5), dtype=np.float32)

            # Add pause
            if prev_speaker is not None:
                pause_ms = self.pause_cross_ms if speaker_key != prev_speaker else self.pause_same_ms
                all_segments.append(np.zeros(int(self.sample_rate * pause_ms / 1000), dtype=np.float32))

            all_segments.append(wav)
            prev_speaker = speaker_key

        return self._save_scene(all_segments, per_speaker, output_dir)

    def _save_scene(
        self,
        all_segments: list[np.ndarray],
        per_speaker: dict[str, list[np.ndarray]],
        output_dir: Path,
    ) -> tuple[bool, float]:
        """Concatenate segments and save scene + per-speaker audio."""
        if not all_segments:
            return False, 0.0

        # Check for real audio
        real_chunks = sum(1 for seg in all_segments if np.max(np.abs(seg)) > 1e-6)
        if real_chunks == 0:
            print("    All chunks failed — no audio generated")
            return False, 0.0

        # Save full scene
        full = np.concatenate(all_segments)
        duration = len(full) / self.sample_rate
        _save(full, self.sample_rate, output_dir / "scene_full.wav")
        print(f"\n  scene_full.wav: {duration:.1f}s")

        # Save per-speaker extracts
        for spk, segs in per_speaker.items():
            combined = _concat_with_pause(segs, self.sample_rate)
            _save(combined, self.sample_rate, output_dir / f"{spk}_only.wav")
            print(f"  {spk}_only.wav: {len(combined) / self.sample_rate:.1f}s ({len(segs)} chunks)")

        return True, duration

    def _unload_lora(self):
        """Free LoRA model VRAM."""
        if self._lora_model is not None:
            del self._lora_model
            self._lora_model = None
            self._current_lora_speaker = None
            try:
                import torch
                torch.cuda.empty_cache()
            except ImportError:
                pass

    def close(self):
        """Release all models and VRAM."""
        if self._engine is not None:
            self._engine.close()
            self._engine = None
        self._unload_lora()
        self._lora_clone_cache.clear()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scene Narrator — full scene audio with all voice modes")
    parser.add_argument(
        "--mode",
        default="design",
        choices=["custom", "design", "clone", "lora", "all"],
        help="Voice mode for character voices (default: design)",
    )
    parser.add_argument(
        "--scene",
        default="helios",
        choices=["helios", "noir", "temple"],
        help="Scene to narrate: helios (sci-fi, 3), noir (detective, 5), temple (adventure, 5)",
    )
    parser.add_argument(
        "--style",
        default="default",
        choices=list(NOIR_VOICE_STYLES.keys()),
        help="Voice style profile for design mode (default, cinematic, dramatic, intimate)",
    )
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    args = parser.parse_args()

    modes = ["custom", "design", "lora"] if args.mode == "all" else [args.mode]
    scene_script, _, _ = _get_scene_data(args.scene, style=args.style)

    # Count speakers
    speakers = set()
    for spk, _, _ in scene_script:
        speakers.add(spk)

    style_label = f" (style: {args.style})" if args.style != "default" else ""

    print("=" * 60)
    print("Scene Narrator — Full Scene Audio Generation")
    print("=" * 60)
    print(f"  Device:   {args.device}")
    print(f"  Scene:    {args.scene}{style_label}")
    print(f"  Modes:    {', '.join(modes)}")
    print(f"  Speakers: {', '.join(sorted(speakers))}")
    print(f"  Chunks:   {len(scene_script)}")
    print(f"  Output:   {OUTPUT_ROOT.resolve()}")

    narrator = SceneNarrator(device=args.device)

    try:
        for mode in modes:
            print(f"\n{'#' * 60}")
            print(f"# MODE: {mode.upper()} / SCENE: {args.scene.upper()}")
            print(f"{'#' * 60}")

            try:
                voice_map = _build_voice_map(mode, scene=args.scene, style=args.style)
            except Exception as e:
                print(f"  ERROR building voice map: {e}")
                continue

            # Validate LoRA adapters exist before starting
            if mode == "lora":
                missing = []
                for spk, cfg in voice_map.items():
                    if isinstance(cfg, LoRAVoiceConfig):
                        adapter_dir = Path(cfg.adapter_path)
                        if not (adapter_dir / "adapter_config.json").exists():
                            missing.append(spk)
                if missing:
                    print(f"  SKIP: No LoRA adapters for {', '.join(missing)}.")
                    print(f"  Run first: uv run python -m src.tts.lora_voice_poc --stage all")
                    continue

            # Include style in output dir for non-default styles
            mode_suffix = f"{mode}_{args.style}" if args.style != "default" else mode
            out_dir = OUTPUT_ROOT / args.scene / f"mode_{mode_suffix}"
            start = time.time()
            success, duration = narrator.generate_scene(
                script=scene_script,
                voice_map=voice_map,
                output_dir=out_dir,
                mode_label=f"{mode}/{args.scene}",
            )
            elapsed = time.time() - start

            if success:
                print(f"\n  Mode {mode}: {duration:.1f}s audio in {elapsed:.1f}s")
            else:
                print(f"\n  Mode {mode}: FAILED ({elapsed:.1f}s)")

    finally:
        narrator.close()

    # Summary
    print(f"\n{'=' * 60}")
    print("SCENE GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT_ROOT.resolve()}")
    print("\nListen to:")
    for mode in modes:
        mode_suffix = f"{mode}_{args.style}" if args.style != "default" else mode
        d = OUTPUT_ROOT / args.scene / f"mode_{mode_suffix}"
        if d.exists():
            wavs = sorted(d.glob("*.wav"))
            print(f"  {mode_suffix}: {len(wavs)} files in {d}")
    print(f"\nEvaluate ({len(speakers)} speakers):")
    print("  Q1: Can you tell the speakers apart in scene_full.wav?")
    print("  Q2: Does each speaker stay consistent in *_only.wav?")
    if len(modes) > 1:
        print("  Q3: Which mode sounds most natural across the full scene?")


if __name__ == "__main__":
    main()
