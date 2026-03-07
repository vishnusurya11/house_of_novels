"""
Voice Consistency POC — Tests whether Qwen3-TTS can maintain voice identity
across different emotional instructions.

Two steps:
  Step 1: Single voice, 6 emotions x 2 characters — tests emotional range per voice
  Step 2: Full scene with narrator + 2 characters interleaved — realistic use case

Four approaches tested in each step:
  A) CustomVoice preset + varying instruct (baseline, known to work)
  B) VoiceDesign direct — same description, different text (no clone)
  C) VoiceDesign + emotional modifiers appended to description
  D) Multi-Clone — emotion-specific clone prompts from same base voice

Run:
    uv run python -m src.tts.voice_consistency_poc                       # All steps, all tests
    uv run python -m src.tts.voice_consistency_poc --step 1 --tests a    # Quick single test
    uv run python -m src.tts.voice_consistency_poc --step 2 --tests a c  # Scene comparison
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
OUTPUT_ROOT = Path("forge/tts_poc")

# ---------------------------------------------------------------------------
# Character profiles — used across both steps
# ---------------------------------------------------------------------------

CHARACTERS = {
    "marcus_reed": {
        "custom_speaker": "Ryan",
        "voice_desc": "deep male baritone, calm authority, mission commander",
    },
    "aurora_vale": {
        "custom_speaker": "Vivian",
        "voice_desc": "female mezzo-soprano, precise and analytical, confident scientist",
    },
}

# ---------------------------------------------------------------------------
# Step 1 test data: 6 emotion-varied lines per character
# ---------------------------------------------------------------------------

# (text, instruct/emotion, filename slug)
EMOTION_LINES = [
    (
        "I didn't realize anyone was keeping track.",
        "Calm, measured, neutral delivery. Quiet composure.",
        "01_neutral",
    ),
    (
        "Natural interference doesn't repeat the same pattern every forty-three seconds.",
        "Tense, low intensity, controlled worry. Deliberate emphasis.",
        "02_tense",
    ),
    (
        "We didn't come all this way to ignore the most interesting discovery in the system.",
        "Commanding authority, firm conviction, rising energy.",
        "03_commanding",
    ),
    (
        "The crew doesn't have to like it. They just have to be ready.",
        "Cold resolve, quiet steel, finality.",
        "04_resolve",
    ),
    (
        "Those are the only kind worth finding.",
        "Warm amusement, quiet laugh, genuine lightness.",
        "05_amused",
    ),
    (
        "That planet was supposed to be empty.",
        "Hushed disbelief, dawning unease, edge of fear.",
        "06_uneasy",
    ),
]

# ---------------------------------------------------------------------------
# Step 2 test data: full scene with narrator + Marcus + Elena
# ---------------------------------------------------------------------------

# (speaker_key, text, instruct)
# speaker_key maps to CHARACTERS dict; "narrator" is special
SCENE_SCRIPT = [
    (
        "narrator",
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
        "Slow, atmospheric narration. Measured pace, quiet awe.",
    ),
    (
        "aurora_vale",
        "You've been standing here for an hour.",
        "Casual observation, slight concern, matter-of-fact.",
    ),
    (
        "narrator",
        "Marcus didn't turn at first. He watched a lightning storm flash "
        "faintly along the planet's night side.",
        "Brief, neutral narration. Observational.",
    ),
    (
        "marcus_reed",
        "I didn't realize anyone was keeping track.",
        "Calm, dry, distracted. Not dismissive, just absorbed.",
    ),
    (
        "narrator",
        "Aurora stepped onto the deck behind him, the metal floor humming "
        "softly beneath her boots as the ship adjusted its orbit. She paused "
        "beside a console, glancing at the glowing data streaming across its "
        "surface.",
        "Steady narration, gentle movement, ambient sound awareness.",
    ),
    (
        "aurora_vale",
        "Someone has to. You stopped answering messages from the bridge.",
        "Direct, slightly reproachful, professional concern.",
    ),
    (
        "narrator",
        "Marcus finally looked over his shoulder.",
        "Brief transition beat. Neutral.",
    ),
    (
        "marcus_reed",
        "I was thinking.",
        "Simple, quiet, reflective.",
    ),
    (
        "narrator",
        "Aurora crossed the room and joined him at the window. The reflection "
        "of the planet shimmered faintly across the glass, painting both of "
        "them in pale blue light.",
        "Atmospheric narration, visual imagery, calm.",
    ),
    (
        "aurora_vale",
        "That's never a comforting phrase coming from a mission commander.",
        "Light sarcasm, warmth underneath, conversational.",
    ),
    (
        "narrator",
        "Marcus gave a faint smile that didn't quite reach his eyes.",
        "Brief, intimate character beat. Understated.",
    ),
    (
        "marcus_reed",
        "It depends on what I'm thinking about.",
        "Guarded, slight deflection, hint of humor.",
    ),
    (
        "narrator",
        "Aurora followed his gaze down to the planet again.",
        "Transition narration. Simple, flowing.",
    ),
    (
        "aurora_vale",
        "Let me guess. The signal.",
        "Knowing, resigned, cutting to the point.",
    ),
    (
        "narrator",
        "Marcus nodded.",
        "Minimal narration. Beat.",
    ),
    (
        "marcus_reed",
        "It's still repeating.",
        "Low, serious, weighted. Quiet intensity.",
    ),
    (
        "narrator",
        "Somewhere deep within the ship, scanners clicked and hummed as they "
        "continued their quiet work.",
        "Ambient narration, background atmosphere, subtle unease.",
    ),
    (
        "aurora_vale",
        "The science team thinks it's natural interference.",
        "Measured, professional, offering the rational explanation.",
    ),
    (
        "narrator",
        "Marcus rested a hand against the cold glass.",
        "Brief physical action. Quiet tension.",
    ),
    (
        "marcus_reed",
        "Natural interference doesn't repeat the same pattern every "
        "forty-three seconds.",
        "Firm, deliberate, controlled intensity. Making a point.",
    ),
    (
        "narrator",
        "Aurora didn't respond immediately. The two of them watched the "
        "planet spin slowly beneath them.",
        "Weighted pause. Tension building through silence.",
    ),
    (
        "aurora_vale",
        "You think someone is sending it.",
        "Hushed realization, guarded, testing the thought aloud.",
    ),
    (
        "marcus_reed",
        "I think something is.",
        "Quiet, ominous emphasis. Letting the distinction land.",
    ),
    (
        "narrator",
        "Far below them, lightning flared again across the planet's dark "
        "hemisphere.",
        "Visual punctuation. Atmospheric, slightly foreboding.",
    ),
    (
        "aurora_vale",
        "That planet was supposed to be empty.",
        "Disbelief, dawning unease, edge of fear.",
    ),
    (
        "narrator",
        "Marcus nodded slowly.",
        "Minimal beat. Weight in simplicity.",
    ),
    (
        "marcus_reed",
        "That's what the survey drones said.",
        "Dry, skeptical, implied distrust.",
    ),
    (
        "aurora_vale",
        "And you trust drones?",
        "Sharp, challenging, raising an eyebrow.",
    ),
    (
        "narrator",
        "Marcus turned to look at her more fully now.",
        "Physical shift, direct engagement. Pivoting moment.",
    ),
    (
        "marcus_reed",
        "I trust them more than coincidence.",
        "Steady conviction, measured, final.",
    ),
    (
        "narrator",
        "Aurora folded her arms and leaned lightly against the railing.",
        "Settling posture, preparing for a longer exchange.",
    ),
    (
        "aurora_vale",
        "So what's the plan?",
        "Direct, practical, bracing herself.",
    ),
    (
        "narrator",
        "Marcus hesitated.",
        "Brief pause. Weighty.",
    ),
    (
        "marcus_reed",
        "The signal originates somewhere on the surface.",
        "Matter-of-fact, laying groundwork for the hard ask.",
    ),
    (
        "aurora_vale",
        "Of course it does.",
        "Dry resignation, she saw this coming.",
    ),
    (
        "narrator",
        "Marcus met her eyes.",
        "Direct beat. Gravity.",
    ),
    (
        "marcus_reed",
        "Which means we'll have to go down there.",
        "Quiet command, slight reluctance, accepting the inevitable.",
    ),
    (
        "narrator",
        "Aurora stared at him for a long moment.",
        "Weighted silence. Processing.",
    ),
    (
        "aurora_vale",
        "You're serious.",
        "Flat disbelief, searching his face for doubt.",
    ),
    (
        "narrator",
        "Marcus turned back toward the planet.",
        "Physical withdrawal, gazing outward. Resolved.",
    ),
    (
        "marcus_reed",
        "We didn't come all this way to ignore the most interesting discovery "
        "in the system.",
        "Rising conviction, commander's authority, quiet fire.",
    ),
    (
        "narrator",
        "The ship shifted slightly as thrusters fired to stabilize its orbit.",
        "Ambient mechanical detail. Brief grounding moment.",
    ),
    (
        "aurora_vale",
        "Interesting discoveries are usually the dangerous ones.",
        "Warning, concern, pragmatic caution.",
    ),
    (
        "narrator",
        "Marcus allowed himself a quiet laugh.",
        "Brief warmth, breaking tension momentarily.",
    ),
    (
        "marcus_reed",
        "Those are the only kind worth finding.",
        "Warm amusement, genuine lightness, conviction.",
    ),
    (
        "narrator",
        "Aurora pushed herself away from the railing.",
        "Movement beat. Preparing to act.",
    ),
    (
        "aurora_vale",
        "The crew isn't going to like this.",
        "Pragmatic warning, accepting the decision, moving forward.",
    ),
    (
        "narrator",
        "Marcus glanced toward the glowing world below.",
        "Contemplative gaze. Finality approaching.",
    ),
    (
        "marcus_reed",
        "The crew doesn't have to like it.",
        "Cold resolve, quiet steel, command authority.",
    ),
    (
        "narrator",
        "The lightning storms continued to ripple across the planet's "
        "atmosphere, silent from this distance.",
        "Atmospheric close. Vast silence, cosmic scale.",
    ),
    (
        "marcus_reed",
        "They just have to be ready.",
        "Final quiet authority, settling weight, end of discussion.",
    ),
    (
        "narrator",
        "For a long moment neither of them spoke. The planet turned slowly "
        "beneath their ship, carrying its hidden signal around the curve of "
        "its horizon again and again. Somewhere down there, something was "
        "calling into the void—and for the first time since the mission "
        "began, Marcus Reed felt certain the call had been meant for them.",
        "Reflective, closing narration. Slow pace, emotional weight, quiet wonder.",
    ),
]

# Narrator voice config (used across tests B/C/D)
NARRATOR_VOICE_DESC = "male narrator, rich authoritative baritone, dynamic dramatic delivery"
NARRATOR_CUSTOM_SPEAKER = "Ryan"


# ---------------------------------------------------------------------------
# Post-processing (mirrors production pipeline)
# ---------------------------------------------------------------------------

def _trim_silence(audio: np.ndarray, sr: int, top_db: float = 40.0) -> np.ndarray:
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


def _apply_edge_fade(audio: np.ndarray, sr: int, fade_ms: float = 5.0) -> np.ndarray:
    fade_samples = min(int(sr * fade_ms / 1000), len(audio) // 2)
    if fade_samples < 2:
        return audio
    audio = audio.copy()
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples).astype(np.float32)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples).astype(np.float32)
    return audio


def _normalize(audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
    rms = np.sqrt(np.mean(audio ** 2))
    if rms < 1e-10:
        return audio
    target_rms = 10 ** (target_dbfs / 20)
    return (audio * (target_rms / rms)).astype(np.float32)


def _postprocess(audio: np.ndarray, sr: int) -> np.ndarray:
    audio = _trim_silence(audio, sr)
    audio = _apply_edge_fade(audio, sr)
    audio = _normalize(audio)
    return audio


def _save(audio: np.ndarray, sr: int, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sr)


def _concat_with_pause(
    segments: list[np.ndarray], sr: int, pause_ms: int = 600
) -> np.ndarray:
    """Concatenate audio segments with silence between them."""
    pause = np.zeros(int(sr * pause_ms / 1000), dtype=np.float32)
    parts = []
    for i, seg in enumerate(segments):
        if i > 0:
            parts.append(pause)
        parts.append(seg)
    return np.concatenate(parts) if parts else np.array([], dtype=np.float32)


# ===================================================================
#  STEP 1: Single voice, 6 emotions x 3 characters
# ===================================================================

def _step1_test_a(engine: QwenTTSEngine) -> None:
    """Step 1 — Test A: CustomVoice presets with varying instruct."""
    print("\n" + "=" * 60)
    print("STEP 1 / TEST A: CustomVoice preset + instruct")
    print("=" * 60)

    engine._load_custom_voice_model()

    for char_key, char_cfg in CHARACTERS.items():
        speaker = char_cfg["custom_speaker"]
        out_dir = OUTPUT_ROOT / "step1_emotions" / "test_a_custom_voice"
        segments = []
        print(f"\n  Character: {char_key} (preset: {speaker})")

        for text, instruct, slug in EMOTION_LINES:
            print(f"    [{slug}] {instruct[:45]}...")
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


def _step1_test_b(engine: QwenTTSEngine) -> None:
    """Step 1 — Test B: VoiceDesign direct, same description per character."""
    print("\n" + "=" * 60)
    print("STEP 1 / TEST B: VoiceDesign direct — no clone")
    print("=" * 60)

    engine._load_design_model()

    for char_key, char_cfg in CHARACTERS.items():
        desc = char_cfg["voice_desc"]
        out_dir = OUTPUT_ROOT / "step1_emotions" / "test_b_design_direct"
        segments = []
        print(f"\n  Character: {char_key} (desc: {desc})")

        for text, _instruct, slug in EMOTION_LINES:
            print(f"    [{slug}] same desc, different text...")
            start = time.time()
            wavs, sr = engine._design_model.generate_voice_design(
                text=text, language=LANGUAGE, instruct=desc,
            )
            wav = _postprocess(wavs[0], sr)
            _save(wav, sr, out_dir / f"{char_key}_{slug}.wav")
            segments.append(wav)
            print(f"      -> {len(wav) / sr:.1f}s ({time.time() - start:.1f}s)")

        combined = _concat_with_pause(segments, engine._sample_rate)
        _save(combined, engine._sample_rate, out_dir / f"{char_key}_combined.wav")
        print(f"    Combined: {len(combined) / engine._sample_rate:.1f}s")


def _step1_test_c(engine: QwenTTSEngine) -> None:
    """Step 1 — Test C: VoiceDesign with emotion appended to description."""
    print("\n" + "=" * 60)
    print("STEP 1 / TEST C: VoiceDesign + emotional modifiers")
    print("=" * 60)

    engine._load_design_model()

    for char_key, char_cfg in CHARACTERS.items():
        base_desc = char_cfg["voice_desc"]
        out_dir = OUTPUT_ROOT / "step1_emotions" / "test_c_design_emotional"
        segments = []
        print(f"\n  Character: {char_key} (base: {base_desc})")

        for text, emotion, slug in EMOTION_LINES:
            desc = f"{base_desc}, {emotion}"
            print(f"    [{slug}] {desc[:55]}...")
            start = time.time()
            wavs, sr = engine._design_model.generate_voice_design(
                text=text, language=LANGUAGE, instruct=desc,
            )
            wav = _postprocess(wavs[0], sr)
            _save(wav, sr, out_dir / f"{char_key}_{slug}.wav")
            segments.append(wav)
            print(f"      -> {len(wav) / sr:.1f}s ({time.time() - start:.1f}s)")

        combined = _concat_with_pause(segments, engine._sample_rate)
        _save(combined, engine._sample_rate, out_dir / f"{char_key}_combined.wav")
        print(f"    Combined: {len(combined) / engine._sample_rate:.1f}s")


def _step1_test_d(engine: QwenTTSEngine) -> None:
    """Step 1 — Test D: Multi-Clone with emotion-specific clone prompts."""
    print("\n" + "=" * 60)
    print("STEP 1 / TEST D: Multi-Clone — emotion-specific clones")
    print("=" * 60)

    engine._load_design_model()
    engine._load_base_model()

    for char_key, char_cfg in CHARACTERS.items():
        base_desc = char_cfg["voice_desc"]
        out_dir = OUTPUT_ROOT / "step1_emotions" / "test_d_multi_clone"
        segments = []
        print(f"\n  Character: {char_key} (base: {base_desc})")

        for text, emotion, slug in EMOTION_LINES:
            desc = f"{base_desc}, {emotion}"
            print(f"    [{slug}] design+clone: {desc[:50]}...")
            start = time.time()

            clone_prompt = engine.design_character_voice(
                description=desc, sample_text=text, language=LANGUAGE,
            )
            wav, sr = engine._generate_clone_chunk(
                text=text, clone_prompt=clone_prompt, language=LANGUAGE,
            )
            wav = _postprocess(wav, sr)
            _save(wav, sr, out_dir / f"{char_key}_{slug}.wav")
            segments.append(wav)
            print(f"      -> {len(wav) / sr:.1f}s ({time.time() - start:.1f}s)")

        combined = _concat_with_pause(segments, engine._sample_rate)
        _save(combined, engine._sample_rate, out_dir / f"{char_key}_combined.wav")
        print(f"    Combined: {len(combined) / engine._sample_rate:.1f}s")


# ===================================================================
#  STEP 2: Full scene — narrator + Marcus + Elena interleaved
# ===================================================================

def _get_voice_desc(speaker_key: str) -> str:
    """Get voice description for a speaker."""
    if speaker_key == "narrator":
        return NARRATOR_VOICE_DESC
    return CHARACTERS[speaker_key]["voice_desc"]


def _get_custom_speaker(speaker_key: str) -> str:
    """Get CustomVoice preset name for a speaker."""
    if speaker_key == "narrator":
        return NARRATOR_CUSTOM_SPEAKER
    return CHARACTERS[speaker_key]["custom_speaker"]


def _generate_scene(
    engine: QwenTTSEngine,
    test_label: str,
    out_dir: Path,
    generate_fn,
) -> None:
    """
    Generate the full scene using a given generation function.

    Args:
        engine: TTS engine
        test_label: Display label for logging
        out_dir: Output directory
        generate_fn: Callable(engine, speaker_key, text, instruct) -> (wav, sr)
    """
    print(f"\n  Generating {len(SCENE_SCRIPT)} chunks...")

    # Track segments per speaker for per-speaker extraction
    all_segments: list[np.ndarray] = []
    per_speaker: dict[str, list[np.ndarray]] = {}
    prev_speaker = None

    for idx, (speaker_key, text, instruct) in enumerate(SCENE_SCRIPT):
        # Add pause between chunks
        if prev_speaker is not None:
            pause_ms = 600 if speaker_key != prev_speaker else 300
            all_segments.append(
                np.zeros(int(engine._sample_rate * pause_ms / 1000), dtype=np.float32)
            )

        print(f"    [{idx + 1:02d}/{len(SCENE_SCRIPT)}] {speaker_key}: {text[:40]}...")
        start = time.time()

        try:
            wav, sr = generate_fn(engine, speaker_key, text, instruct)
            wav = _postprocess(wav, sr)
        except Exception as e:
            print(f"      ERROR: {e}")
            wav = np.zeros(int(engine._sample_rate * 0.5), dtype=np.float32)

        all_segments.append(wav)
        per_speaker.setdefault(speaker_key, []).append(wav)
        prev_speaker = speaker_key
        print(f"      -> {len(wav) / engine._sample_rate:.1f}s ({time.time() - start:.1f}s)")

    # Save full scene
    full = np.concatenate(all_segments)
    _save(full, engine._sample_rate, out_dir / "scene_full.wav")
    print(f"  scene_full.wav: {len(full) / engine._sample_rate:.1f}s")

    # Save per-speaker extracts
    for spk, segs in per_speaker.items():
        combined = _concat_with_pause(segs, engine._sample_rate, pause_ms=400)
        _save(combined, engine._sample_rate, out_dir / f"{spk}_only.wav")
        print(f"  {spk}_only.wav: {len(combined) / engine._sample_rate:.1f}s ({len(segs)} chunks)")


def _step2_test_a(engine: QwenTTSEngine) -> None:
    """Step 2 — Test A: Full scene with CustomVoice presets."""
    print("\n" + "=" * 60)
    print("STEP 2 / TEST A: Full scene — CustomVoice presets + instruct")
    print("=" * 60)

    engine._load_custom_voice_model()

    def gen_fn(eng, speaker_key, text, instruct):
        speaker = _get_custom_speaker(speaker_key)
        return eng._generate_custom_voice_chunk(
            text=text, speaker=speaker, instruct=instruct, language=LANGUAGE,
        )

    _generate_scene(
        engine, "CustomVoice",
        OUTPUT_ROOT / "step2_scene" / "test_a_custom_voice",
        gen_fn,
    )


def _step2_test_b(engine: QwenTTSEngine) -> None:
    """Step 2 — Test B: Full scene with VoiceDesign direct (no clone)."""
    print("\n" + "=" * 60)
    print("STEP 2 / TEST B: Full scene — VoiceDesign direct, no clone")
    print("=" * 60)

    engine._load_design_model()

    def gen_fn(eng, speaker_key, text, instruct):
        desc = _get_voice_desc(speaker_key)
        wavs, sr = eng._design_model.generate_voice_design(
            text=text, language=LANGUAGE, instruct=desc,
        )
        return wavs[0], sr

    _generate_scene(
        engine, "VoiceDesign direct",
        OUTPUT_ROOT / "step2_scene" / "test_b_design_direct",
        gen_fn,
    )


def _step2_test_c(engine: QwenTTSEngine) -> None:
    """Step 2 — Test C: Full scene with VoiceDesign + emotional modifiers."""
    print("\n" + "=" * 60)
    print("STEP 2 / TEST C: Full scene — VoiceDesign + emotion in desc")
    print("=" * 60)

    engine._load_design_model()

    def gen_fn(eng, speaker_key, text, instruct):
        base_desc = _get_voice_desc(speaker_key)
        desc_with_emotion = f"{base_desc}, {instruct}"
        wavs, sr = eng._design_model.generate_voice_design(
            text=text, language=LANGUAGE, instruct=desc_with_emotion,
        )
        return wavs[0], sr

    _generate_scene(
        engine, "VoiceDesign + emotion",
        OUTPUT_ROOT / "step2_scene" / "test_c_design_emotional",
        gen_fn,
    )


def _step2_test_d(engine: QwenTTSEngine) -> None:
    """Step 2 — Test D: Full scene with multi-clone (emotion-specific clones)."""
    print("\n" + "=" * 60)
    print("STEP 2 / TEST D: Full scene — Multi-Clone per emotion")
    print("=" * 60)

    engine._load_design_model()
    engine._load_base_model()

    # Cache clone prompts per (speaker, emotion_hash) to avoid re-designing
    # identical emotion variants
    clone_cache: dict[str, object] = {}

    def gen_fn(eng, speaker_key, text, instruct):
        base_desc = _get_voice_desc(speaker_key)
        desc_with_emotion = f"{base_desc}, {instruct}"
        cache_key = f"{speaker_key}:{instruct}"

        if cache_key not in clone_cache:
            clone_cache[cache_key] = eng.design_character_voice(
                description=desc_with_emotion,
                sample_text=text,
                language=LANGUAGE,
            )

        return eng._generate_clone_chunk(
            text=text,
            clone_prompt=clone_cache[cache_key],
            language=LANGUAGE,
        )

    _generate_scene(
        engine, "Multi-Clone",
        OUTPUT_ROOT / "step2_scene" / "test_d_multi_clone",
        gen_fn,
    )


# ===================================================================
#  Dispatch tables
# ===================================================================

STEP1_TESTS = {
    "a": ("CustomVoice + instruct", _step1_test_a),
    "b": ("VoiceDesign direct", _step1_test_b),
    "c": ("VoiceDesign + emotional", _step1_test_c),
    "d": ("Multi-Clone", _step1_test_d),
}

STEP2_TESTS = {
    "a": ("CustomVoice + instruct", _step2_test_a),
    "b": ("VoiceDesign direct", _step2_test_b),
    "c": ("VoiceDesign + emotional", _step2_test_c),
    "d": ("Multi-Clone", _step2_test_d),
}


# ===================================================================
#  Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(description="Qwen3-TTS Voice Consistency POC")
    parser.add_argument(
        "--step",
        default="all",
        choices=["1", "2", "all"],
        help="Which step to run: 1 (emotions), 2 (scene), all (default: all)",
    )
    parser.add_argument(
        "--tests",
        nargs="*",
        default=["a", "b", "c", "d"],
        choices=["a", "b", "c", "d"],
        help="Which test approaches to run (default: all). E.g. --tests a c",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device for inference (default: cuda)",
    )
    args = parser.parse_args()

    run_step1 = args.step in ("1", "all")
    run_step2 = args.step in ("2", "all")

    print("=" * 60)
    print("Qwen3-TTS Voice Consistency POC")
    print("=" * 60)
    print(f"  Device:     {args.device}")
    print(f"  Steps:      {'1 ' if run_step1 else ''}{'2' if run_step2 else ''}")
    print(f"  Tests:      {', '.join(args.tests)}")
    print(f"  Characters: {', '.join(CHARACTERS.keys())}")
    print(f"  Output:     {OUTPUT_ROOT.resolve()}")

    if run_step1:
        print(f"\n  Step 1: {len(EMOTION_LINES)} emotions x {len(CHARACTERS)} characters")
    if run_step2:
        print(f"  Step 2: {len(SCENE_SCRIPT)}-chunk scene (narrator + marcus_reed + aurora_vale)")

    engine = QwenTTSEngine(
        device=args.device,
        precision="bfloat16",
        model_size="1.7B",
    )

    try:
        # --- Step 1 ---
        if run_step1:
            print("\n" + "#" * 60)
            print("# STEP 1: Single Voice, 6 Emotions x 3 Characters")
            print("#" * 60)
            for key in args.tests:
                label, fn = STEP1_TESTS[key]
                fn(engine)

        # --- Step 2 ---
        if run_step2:
            print("\n" + "#" * 60)
            print("# STEP 2: Full Scene — Narrator + Marcus Reed + Aurora Vale")
            print("#" * 60)
            for key in args.tests:
                label, fn = STEP2_TESTS[key]
                fn(engine)

        # --- Summary ---
        print("\n" + "=" * 60)
        print("POC COMPLETE")
        print("=" * 60)
        print(f"\nOutput: {OUTPUT_ROOT.resolve()}")

        if run_step1:
            print("\nStep 1 — Listen to *_combined.wav per character:")
            print("  Q: Does each character sound like ONE person across 6 emotions?")
            for key in args.tests:
                d = OUTPUT_ROOT / "step1_emotions" / f"test_{key}_{'_'.join(STEP1_TESTS[key][0].lower().split())}"
                # Use the actual dir names
                actual = {
                    "a": "test_a_custom_voice",
                    "b": "test_b_design_direct",
                    "c": "test_c_design_emotional",
                    "d": "test_d_multi_clone",
                }
                p = OUTPUT_ROOT / "step1_emotions" / actual[key]
                if p.exists():
                    wavs = sorted(p.glob("*.wav"))
                    print(f"  Test {key.upper()}: {len(wavs)} files in {p}")

        if run_step2:
            print("\nStep 2 — Listen to scene_full.wav and *_only.wav:")
            print("  Q1: Can you tell the 3 speakers apart in scene_full.wav?")
            print("  Q2: Does each speaker stay consistent in *_only.wav?")
            print("  Q3: Which test approach sounds most natural?")
            for key in args.tests:
                actual = {
                    "a": "test_a_custom_voice",
                    "b": "test_b_design_direct",
                    "c": "test_c_design_emotional",
                    "d": "test_d_multi_clone",
                }
                p = OUTPUT_ROOT / "step2_scene" / actual[key]
                if p.exists():
                    wavs = sorted(p.glob("*.wav"))
                    print(f"  Test {key.upper()}: {len(wavs)} files in {p}")

    finally:
        engine.close()


if __name__ == "__main__":
    main()
