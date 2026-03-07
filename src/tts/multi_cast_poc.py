"""
POC 2: Multi-Cast Audiobook — Different CustomVoice presets per character,
with character_style appended to every instruct (Alexandria pattern).

Each character gets a distinct preset voice. The character_style field adds
persistent personality traits to every line's emotional instruct.

Run:
    uv run python -m src.tts.multi_cast_poc
    uv run python -m src.tts.multi_cast_poc --step 2   # Scene only
"""

import argparse
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from src.tts.qwen_tts_engine import QwenTTSEngine


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANGUAGE = "English"
OUTPUT_ROOT = Path("forge/tts_poc/poc2_multi_cast")

# Each character gets a DIFFERENT preset + persistent character_style
VOICE_MAP = {
    "narrator": {
        "speaker": "Ryan",
        "character_style": "Commanding narrator, rich baritone, dynamic pacing with dramatic emphasis.",
    },
    "marcus_reed": {
        "speaker": "Aiden",
        "character_style": "Gruff military commander, deep deliberate authority.",
    },
    "aurora_vale": {
        "speaker": "Vivian",
        "character_style": "Precise analytical scientist, crisp clear diction.",
    },
}

# ---------------------------------------------------------------------------
# Emotion test lines (Step 1)
# ---------------------------------------------------------------------------

EMOTION_LINES = [
    ("I didn't realize anyone was keeping track.",
     "Calm, measured, neutral delivery. Quiet composure.", "01_neutral"),
    ("Natural interference doesn't repeat the same pattern every forty-three seconds.",
     "Tense, low intensity, controlled worry. Deliberate emphasis.", "02_tense"),
    ("We didn't come all this way to ignore the most interesting discovery in the system.",
     "Commanding authority, firm conviction, rising energy.", "03_commanding"),
    ("The crew doesn't have to like it. They just have to be ready.",
     "Cold resolve, quiet steel, finality.", "04_resolve"),
    ("Those are the only kind worth finding.",
     "Warm amusement, quiet laugh, genuine lightness.", "05_amused"),
    ("That planet was supposed to be empty.",
     "Hushed disbelief, dawning unease, edge of fear.", "06_uneasy"),
]

# ---------------------------------------------------------------------------
# Scene script (Step 2) — same as POC 1 for A/B comparison
# ---------------------------------------------------------------------------

SCENE_SCRIPT = [
    ("narrator",
     "The observation deck of the research vessel Helios hung in perfect "
     "silence above a pale blue planet. Through the massive viewing window, "
     "storms drifted slowly across the planet's oceans like swirling "
     "brushstrokes of white paint. Beyond that world stretched the quiet "
     "darkness of deep space, scattered with distant stars that barely "
     "shimmered against the black. Marcus Reed stood near the glass with "
     "his hands clasped behind his back, watching the slow rotation of "
     "the planet below. From this distance it looked peaceful—almost "
     "fragile—but Marcus knew the instruments buried throughout the ship "
     "told a different story.",
     "Expansive scene-setting, deliberate gravitas, building wonder."),
    ("aurora_vale", "You've been standing here for an hour.",
     "Casual observation, slight concern, matter-of-fact."),
    ("narrator",
     "Marcus didn't turn at first. He watched a lightning storm flash "
     "faintly along the planet's night side.",
     "Crisp observational beat, understated."),
    ("marcus_reed", "I didn't realize anyone was keeping track.",
     "Calm, dry, distracted. Not dismissive, just absorbed."),
    ("narrator",
     "Aurora stepped onto the deck behind him, the metal floor humming "
     "softly beneath her boots as the ship adjusted its orbit. She paused "
     "beside a console, glancing at the glowing data streaming across its "
     "surface.",
     "Grounded narration, precise physical detail, ambient texture."),
    ("aurora_vale", "Someone has to. You stopped answering messages from the bridge.",
     "Direct, slightly reproachful, professional concern."),
    ("narrator", "Marcus finally looked over his shoulder.",
     "Sharp transition beat."),
    ("marcus_reed", "I was thinking.", "Simple, quiet, reflective."),
    ("narrator",
     "Aurora crossed the room and joined him at the window. The reflection "
     "of the planet shimmered faintly across the glass, painting both of "
     "them in pale blue light.",
     "Vivid imagery, cinematic sweep, drawing the listener in."),
    ("aurora_vale", "That's never a comforting phrase coming from a mission commander.",
     "Light sarcasm, warmth underneath, conversational."),
    ("narrator", "Marcus gave a faint smile that didn't quite reach his eyes.",
     "Intimate character beat, loaded subtext."),
    ("marcus_reed", "It depends on what I'm thinking about.",
     "Guarded, slight deflection, hint of humor."),
    ("narrator", "Aurora followed his gaze down to the planet again.",
     "Smooth transition, purposeful movement."),
    ("aurora_vale", "Let me guess. The signal.",
     "Knowing, resigned, cutting to the point."),
    ("narrator", "Marcus nodded.", "Tight beat. Let the silence land."),
    ("marcus_reed", "It's still repeating.",
     "Low, serious, weighted. Quiet intensity."),
    ("narrator",
     "Somewhere deep within the ship, scanners clicked and hummed as they "
     "continued their quiet work.",
     "Low ominous undercurrent, machinery alive in the dark."),
    ("aurora_vale", "The science team thinks it's natural interference.",
     "Measured, professional, offering the rational explanation."),
    ("narrator", "Marcus rested a hand against the cold glass.",
     "Deliberate physical action, tension in the stillness."),
    ("marcus_reed",
     "Natural interference doesn't repeat the same pattern every forty-three seconds.",
     "Firm, deliberate, controlled intensity. Making a point."),
    ("narrator",
     "Aurora didn't respond immediately. The two of them watched the "
     "planet spin slowly beneath them.",
     "Taut silence, tension coiling, the weight of unspoken truth."),
    ("aurora_vale", "You think someone is sending it.",
     "Hushed realization, guarded, testing the thought aloud."),
    ("marcus_reed", "I think something is.",
     "Quiet, ominous emphasis. Letting the distinction land."),
    ("narrator",
     "Far below them, lightning flared again across the planet's dark hemisphere.",
     "Dramatic visual punctuation, foreboding edge."),
    ("aurora_vale", "That planet was supposed to be empty.",
     "Disbelief, dawning unease, edge of fear."),
    ("narrator", "Marcus nodded slowly.", "Heavy beat, gravity in the simplicity."),
    ("marcus_reed", "That's what the survey drones said.",
     "Dry, skeptical, implied distrust."),
    ("aurora_vale", "And you trust drones?",
     "Sharp, challenging, raising an eyebrow."),
    ("narrator", "Marcus turned to look at her more fully now.",
     "Decisive physical shift, the scene pivots."),
    ("marcus_reed", "I trust them more than coincidence.",
     "Steady conviction, measured, final."),
    ("narrator", "Aurora folded her arms and leaned lightly against the railing.",
     "Grounded posture, bracing for what comes next."),
    ("aurora_vale", "So what's the plan?",
     "Direct, practical, bracing herself."),
    ("narrator", "Marcus hesitated.", "Loaded pause, the decision hanging."),
    ("marcus_reed", "The signal originates somewhere on the surface.",
     "Matter-of-fact, laying groundwork for the hard ask."),
    ("aurora_vale", "Of course it does.",
     "Dry resignation, she saw this coming."),
    ("narrator", "Marcus met her eyes.", "Direct, unflinching beat. Gravity."),
    ("marcus_reed", "Which means we'll have to go down there.",
     "Quiet command, slight reluctance, accepting the inevitable."),
    ("narrator", "Aurora stared at him for a long moment.",
     "Charged silence, the stakes crystallizing."),
    ("aurora_vale", "You're serious.",
     "Flat disbelief, searching his face for doubt."),
    ("narrator", "Marcus turned back toward the planet.",
     "Resolute withdrawal, commander gazing into the unknown."),
    ("marcus_reed",
     "We didn't come all this way to ignore the most interesting discovery in the system.",
     "Rising conviction, commander's authority, quiet fire."),
    ("narrator",
     "The ship shifted slightly as thrusters fired to stabilize its orbit.",
     "Mechanical punctuation, grounding the drama in physical reality."),
    ("aurora_vale", "Interesting discoveries are usually the dangerous ones.",
     "Warning, concern, pragmatic caution."),
    ("narrator", "Marcus allowed himself a quiet laugh.",
     "Flash of warmth, tension cracking for a breath."),
    ("marcus_reed", "Those are the only kind worth finding.",
     "Warm amusement, genuine lightness, conviction."),
    ("narrator", "Aurora pushed herself away from the railing.",
     "Kinetic shift, decision made, momentum building."),
    ("aurora_vale", "The crew isn't going to like this.",
     "Pragmatic warning, accepting the decision, moving forward."),
    ("narrator", "Marcus glanced toward the glowing world below.",
     "Final contemplative gaze, the weight of command settling."),
    ("marcus_reed", "The crew doesn't have to like it.",
     "Cold resolve, quiet steel, command authority."),
    ("narrator",
     "The lightning storms continued to ripple across the planet's "
     "atmosphere, silent from this distance.",
     "Vast cinematic close, cosmic silence, the enormity landing."),
    ("marcus_reed", "They just have to be ready.",
     "Final quiet authority, settling weight, end of discussion."),
    ("narrator",
     "For a long moment neither of them spoke. The planet turned slowly "
     "beneath their ship, carrying its hidden signal around the curve of "
     "its horizon again and again. Somewhere down there, something was "
     "calling into the void—and for the first time since the mission "
     "began, Marcus Reed felt certain the call had been meant for them.",
     "Grand closing narration, building emotional crescendo, awe and foreboding."),
]


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


def _concat_with_pause(segs: list[np.ndarray], sr: int, pause_ms: int = 600) -> np.ndarray:
    pause = np.zeros(int(sr * pause_ms / 1000), dtype=np.float32)
    parts = []
    for i, seg in enumerate(segs):
        if i > 0:
            parts.append(pause)
        parts.append(seg)
    return np.concatenate(parts) if parts else np.array([], dtype=np.float32)


def _build_instruct(speaker_key: str, line_instruct: str) -> str:
    """Combine line-level instruct with persistent character_style."""
    style = VOICE_MAP.get(speaker_key, {}).get("character_style", "")
    if style:
        return f"{line_instruct} {style}"
    return line_instruct


def _get_speaker(speaker_key: str) -> str:
    """Get CustomVoice preset for a speaker."""
    return VOICE_MAP.get(speaker_key, VOICE_MAP["narrator"])["speaker"]


# ---------------------------------------------------------------------------
# Step 1: Emotion range per character (different presets)
# ---------------------------------------------------------------------------

def run_step1(engine: QwenTTSEngine) -> None:
    print("\n" + "#" * 60)
    print("# STEP 1: Multi-Cast — 6 Emotions per Character")
    print("#" * 60)

    engine._load_custom_voice_model()

    for char_key in ("marcus_reed", "aurora_vale"):
        speaker = _get_speaker(char_key)
        out_dir = OUTPUT_ROOT / "step1_emotions"
        segments = []
        print(f"\n  Character: {char_key} (preset: {speaker})")

        for text, line_instruct, slug in EMOTION_LINES:
            instruct = _build_instruct(char_key, line_instruct)
            print(f"    [{slug}] {instruct[:60]}...")
            start = time.time()
            wav, sr = engine._generate_custom_voice_chunk(
                text=text, speaker=speaker, instruct=instruct, language=LANGUAGE,
            )
            wav = _postprocess(wav, sr)
            _save(wav, sr, out_dir / f"{char_key}_{slug}.wav")
            segments.append(wav)
            print(f"      -> {len(wav) / sr:.1f}s ({time.time() - start:.1f}s)")

        combined = _concat_with_pause(segments, engine._sample_rate)
        _save(combined, engine._sample_rate, out_dir / f"{char_key}_combined.wav")
        print(f"    Combined: {len(combined) / engine._sample_rate:.1f}s")


# ---------------------------------------------------------------------------
# Step 2: Full scene — different presets per character
# ---------------------------------------------------------------------------

def run_step2(engine: QwenTTSEngine) -> None:
    print("\n" + "#" * 60)
    print("# STEP 2: Full Scene — Multi-Cast with Character Styles")
    print("#" * 60)

    engine._load_custom_voice_model()

    out_dir = OUTPUT_ROOT / "step2_scene"
    all_segments: list[np.ndarray] = []
    per_speaker: dict[str, list[np.ndarray]] = {}
    prev_spk = None

    print(f"\n  Generating {len(SCENE_SCRIPT)} chunks...")
    for spk, cfg in VOICE_MAP.items():
        print(f"    {spk} -> {cfg['speaker']} | style: {cfg['character_style'][:40]}...")

    for idx, (spk, text, line_instruct) in enumerate(SCENE_SCRIPT):
        if prev_spk is not None:
            pause_ms = 600 if spk != prev_spk else 300
            all_segments.append(
                np.zeros(int(engine._sample_rate * pause_ms / 1000), dtype=np.float32)
            )

        speaker = _get_speaker(spk)
        instruct = _build_instruct(spk, line_instruct)
        print(f"    [{idx + 1:02d}/{len(SCENE_SCRIPT)}] {spk} ({speaker}): {text[:35]}...")
        start = time.time()

        try:
            wav, sr = engine._generate_custom_voice_chunk(
                text=text, speaker=speaker, instruct=instruct, language=LANGUAGE,
            )
            wav = _postprocess(wav, sr)
        except Exception as e:
            print(f"      ERROR: {e}")
            wav = np.zeros(int(engine._sample_rate * 0.5), dtype=np.float32)

        all_segments.append(wav)
        per_speaker.setdefault(spk, []).append(wav)
        prev_spk = spk
        print(f"      -> {len(wav) / engine._sample_rate:.1f}s ({time.time() - start:.1f}s)")

    # Save full scene
    full = np.concatenate(all_segments)
    _save(full, engine._sample_rate, out_dir / "scene_full.wav")
    print(f"\n  scene_full.wav: {len(full) / engine._sample_rate:.1f}s")

    # Save per-speaker extracts
    for spk, segs in per_speaker.items():
        combined = _concat_with_pause(segs, engine._sample_rate, pause_ms=400)
        _save(combined, engine._sample_rate, out_dir / f"{spk}_only.wav")
        print(f"  {spk}_only.wav: {len(combined) / engine._sample_rate:.1f}s ({len(segs)} chunks)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="POC 2: Multi-Cast Audiobook (different presets + character_style)")
    parser.add_argument("--step", default="all", choices=["1", "2", "all"])
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    args = parser.parse_args()

    print("=" * 60)
    print("POC 2: Multi-Cast Audiobook (Alexandria Pattern)")
    print("=" * 60)
    print(f"  Device:  {args.device}")
    print(f"  Output:  {OUTPUT_ROOT.resolve()}")
    for spk, cfg in VOICE_MAP.items():
        print(f"  {spk:15s} -> {cfg['speaker']:8s} | {cfg['character_style'][:40]}")

    engine = QwenTTSEngine(device=args.device, precision="bfloat16", model_size="1.7B")
    try:
        if args.step in ("1", "all"):
            run_step1(engine)
        if args.step in ("2", "all"):
            run_step2(engine)

        print("\n" + "=" * 60)
        print("POC 2 COMPLETE")
        print("=" * 60)
        print(f"\nOutput: {OUTPUT_ROOT.resolve()}")
        print("\nKey questions:")
        print("  1. Do the 3 speakers sound distinctly different?")
        print("  2. Does each speaker stay consistent across emotional shifts?")
        print("  3. Compare with POC 1 — does multi-cast sound more natural?")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
