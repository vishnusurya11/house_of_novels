"""
POC 1: Single Narrator Audiobook — One CustomVoice preset narrates everything.

Like a real audiobook: one narrator "performs" all characters through instruct
alone. Tests whether instruct can convincingly differentiate characters when
using the same voice preset.

Run:
    uv run python -m src.tts.single_narrator_poc
    uv run python -m src.tts.single_narrator_poc --step 2     # Scene only
    uv run python -m src.tts.single_narrator_poc --speaker Aiden  # Different preset
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
OUTPUT_ROOT = Path("forge/tts_poc/poc1_single_narrator")

# Single preset for EVERYTHING — narrator performs all characters
DEFAULT_SPEAKER = "Ryan"

# Character styles — the narrator "acts" as each character via instruct
CHARACTER_STYLES = {
    "narrator": "Measured storytelling, warm baritone, even pace.",
    "marcus_reed": "Performing as a gruff military commander, deep authoritative voice, deliberate.",
    "aurora_vale": "Performing as a precise female scientist, crisp clear diction, analytical.",
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
# Scene script (Step 2)
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
     "Slow, atmospheric narration. Measured pace, quiet awe."),
    ("aurora_vale", "You've been standing here for an hour.",
     "Casual observation, slight concern, matter-of-fact."),
    ("narrator",
     "Marcus didn't turn at first. He watched a lightning storm flash "
     "faintly along the planet's night side.",
     "Brief, neutral narration. Observational."),
    ("marcus_reed", "I didn't realize anyone was keeping track.",
     "Calm, dry, distracted. Not dismissive, just absorbed."),
    ("narrator",
     "Aurora stepped onto the deck behind him, the metal floor humming "
     "softly beneath her boots as the ship adjusted its orbit. She paused "
     "beside a console, glancing at the glowing data streaming across its "
     "surface.",
     "Steady narration, gentle movement, ambient sound awareness."),
    ("aurora_vale", "Someone has to. You stopped answering messages from the bridge.",
     "Direct, slightly reproachful, professional concern."),
    ("narrator", "Marcus finally looked over his shoulder.",
     "Brief transition beat. Neutral."),
    ("marcus_reed", "I was thinking.",
     "Simple, quiet, reflective."),
    ("narrator",
     "Aurora crossed the room and joined him at the window. The reflection "
     "of the planet shimmered faintly across the glass, painting both of "
     "them in pale blue light.",
     "Atmospheric narration, visual imagery, calm."),
    ("aurora_vale", "That's never a comforting phrase coming from a mission commander.",
     "Light sarcasm, warmth underneath, conversational."),
    ("narrator", "Marcus gave a faint smile that didn't quite reach his eyes.",
     "Brief, intimate character beat. Understated."),
    ("marcus_reed", "It depends on what I'm thinking about.",
     "Guarded, slight deflection, hint of humor."),
    ("narrator", "Aurora followed his gaze down to the planet again.",
     "Transition narration. Simple, flowing."),
    ("aurora_vale", "Let me guess. The signal.",
     "Knowing, resigned, cutting to the point."),
    ("narrator", "Marcus nodded.", "Minimal narration. Beat."),
    ("marcus_reed", "It's still repeating.",
     "Low, serious, weighted. Quiet intensity."),
    ("narrator",
     "Somewhere deep within the ship, scanners clicked and hummed as they "
     "continued their quiet work.",
     "Ambient narration, background atmosphere, subtle unease."),
    ("aurora_vale", "The science team thinks it's natural interference.",
     "Measured, professional, offering the rational explanation."),
    ("narrator", "Marcus rested a hand against the cold glass.",
     "Brief physical action. Quiet tension."),
    ("marcus_reed",
     "Natural interference doesn't repeat the same pattern every forty-three seconds.",
     "Firm, deliberate, controlled intensity. Making a point."),
    ("narrator",
     "Aurora didn't respond immediately. The two of them watched the "
     "planet spin slowly beneath them.",
     "Weighted pause. Tension building through silence."),
    ("aurora_vale", "You think someone is sending it.",
     "Hushed realization, guarded, testing the thought aloud."),
    ("marcus_reed", "I think something is.",
     "Quiet, ominous emphasis. Letting the distinction land."),
    ("narrator",
     "Far below them, lightning flared again across the planet's dark hemisphere.",
     "Visual punctuation. Atmospheric, slightly foreboding."),
    ("aurora_vale", "That planet was supposed to be empty.",
     "Disbelief, dawning unease, edge of fear."),
    ("narrator", "Marcus nodded slowly.", "Minimal beat. Weight in simplicity."),
    ("marcus_reed", "That's what the survey drones said.",
     "Dry, skeptical, implied distrust."),
    ("aurora_vale", "And you trust drones?",
     "Sharp, challenging, raising an eyebrow."),
    ("narrator", "Marcus turned to look at her more fully now.",
     "Physical shift, direct engagement. Pivoting moment."),
    ("marcus_reed", "I trust them more than coincidence.",
     "Steady conviction, measured, final."),
    ("narrator", "Aurora folded her arms and leaned lightly against the railing.",
     "Settling posture, preparing for a longer exchange."),
    ("aurora_vale", "So what's the plan?",
     "Direct, practical, bracing herself."),
    ("narrator", "Marcus hesitated.", "Brief pause. Weighty."),
    ("marcus_reed", "The signal originates somewhere on the surface.",
     "Matter-of-fact, laying groundwork for the hard ask."),
    ("aurora_vale", "Of course it does.",
     "Dry resignation, she saw this coming."),
    ("narrator", "Marcus met her eyes.", "Direct beat. Gravity."),
    ("marcus_reed", "Which means we'll have to go down there.",
     "Quiet command, slight reluctance, accepting the inevitable."),
    ("narrator", "Aurora stared at him for a long moment.",
     "Weighted silence. Processing."),
    ("aurora_vale", "You're serious.",
     "Flat disbelief, searching his face for doubt."),
    ("narrator", "Marcus turned back toward the planet.",
     "Physical withdrawal, gazing outward. Resolved."),
    ("marcus_reed",
     "We didn't come all this way to ignore the most interesting discovery in the system.",
     "Rising conviction, commander's authority, quiet fire."),
    ("narrator",
     "The ship shifted slightly as thrusters fired to stabilize its orbit.",
     "Ambient mechanical detail. Brief grounding moment."),
    ("aurora_vale", "Interesting discoveries are usually the dangerous ones.",
     "Warning, concern, pragmatic caution."),
    ("narrator", "Marcus allowed himself a quiet laugh.",
     "Brief warmth, breaking tension momentarily."),
    ("marcus_reed", "Those are the only kind worth finding.",
     "Warm amusement, genuine lightness, conviction."),
    ("narrator", "Aurora pushed herself away from the railing.",
     "Movement beat. Preparing to act."),
    ("aurora_vale", "The crew isn't going to like this.",
     "Pragmatic warning, accepting the decision, moving forward."),
    ("narrator", "Marcus glanced toward the glowing world below.",
     "Contemplative gaze. Finality approaching."),
    ("marcus_reed", "The crew doesn't have to like it.",
     "Cold resolve, quiet steel, command authority."),
    ("narrator",
     "The lightning storms continued to ripple across the planet's "
     "atmosphere, silent from this distance.",
     "Atmospheric close. Vast silence, cosmic scale."),
    ("marcus_reed", "They just have to be ready.",
     "Final quiet authority, settling weight, end of discussion."),
    ("narrator",
     "For a long moment neither of them spoke. The planet turned slowly "
     "beneath their ship, carrying its hidden signal around the curve of "
     "its horizon again and again. Somewhere down there, something was "
     "calling into the void—and for the first time since the mission "
     "began, Marcus Reed felt certain the call had been meant for them.",
     "Reflective, closing narration. Slow pace, emotional weight, quiet wonder."),
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
    """Combine line-level instruct with persistent character style."""
    style = CHARACTER_STYLES.get(speaker_key, "")
    if style:
        return f"{line_instruct} {style}"
    return line_instruct


# ---------------------------------------------------------------------------
# Step 1: Emotion range per character (single narrator voice)
# ---------------------------------------------------------------------------

def run_step1(engine: QwenTTSEngine, speaker: str) -> None:
    print("\n" + "#" * 60)
    print("# STEP 1: Single Narrator — 6 Emotions per Character")
    print("#" * 60)

    engine._load_custom_voice_model()

    for char_key in ("marcus_reed", "aurora_vale"):
        out_dir = OUTPUT_ROOT / "step1_emotions"
        segments = []
        print(f"\n  Character: {char_key} (all using preset: {speaker})")

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
# Step 2: Full scene — one narrator does everything
# ---------------------------------------------------------------------------

def run_step2(engine: QwenTTSEngine, speaker: str) -> None:
    print("\n" + "#" * 60)
    print("# STEP 2: Full Scene — Single Narrator Performs All Characters")
    print("#" * 60)

    engine._load_custom_voice_model()

    out_dir = OUTPUT_ROOT / "step2_scene"
    all_segments: list[np.ndarray] = []
    per_speaker: dict[str, list[np.ndarray]] = {}
    prev_spk = None

    print(f"\n  Generating {len(SCENE_SCRIPT)} chunks (all preset: {speaker})...")

    for idx, (spk, text, line_instruct) in enumerate(SCENE_SCRIPT):
        if prev_spk is not None:
            pause_ms = 600 if spk != prev_spk else 300
            all_segments.append(
                np.zeros(int(engine._sample_rate * pause_ms / 1000), dtype=np.float32)
            )

        instruct = _build_instruct(spk, line_instruct)
        print(f"    [{idx + 1:02d}/{len(SCENE_SCRIPT)}] {spk}: {text[:40]}...")
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
        description="POC 1: Single Narrator Audiobook (one preset, all characters via instruct)")
    parser.add_argument("--step", default="all", choices=["1", "2", "all"])
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--speaker", default="Ryan",
                        help="CustomVoice preset (default: Ryan)")
    args = parser.parse_args()

    print("=" * 60)
    print("POC 1: Single Narrator Audiobook")
    print("=" * 60)
    print(f"  Preset:  {args.speaker} (one voice for everything)")
    print(f"  Device:  {args.device}")
    print(f"  Output:  {OUTPUT_ROOT.resolve()}")

    engine = QwenTTSEngine(device=args.device, precision="bfloat16", model_size="1.7B")
    try:
        if args.step in ("1", "all"):
            run_step1(engine, args.speaker)
        if args.step in ("2", "all"):
            run_step2(engine, args.speaker)

        print("\n" + "=" * 60)
        print("POC 1 COMPLETE")
        print("=" * 60)
        print(f"\nOutput: {OUTPUT_ROOT.resolve()}")
        print("\nKey question: Can one narrator convincingly 'act' as")
        print("different characters through instruct alone?")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
