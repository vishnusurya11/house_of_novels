"""
POC 3: LoRA Voice Training Pipeline — Complete scene pipeline.

Three stages:
  1. Generate: Parse scene → LLM voice descriptions → VoiceDesign training samples
  2. Train: LoRA adapters on training samples (official Qwen3-TTS approach)
  3. Render: LLM delivery instructions → LoRA-adapted voices → complete scene WAV

Run:
    uv run python -m src.tts.lora_voice_poc --stage generate   # Stage 1 only
    uv run python -m src.tts.lora_voice_poc --stage train      # Stage 2 only
    uv run python -m src.tts.lora_voice_poc --stage render     # Stage 3 only
    uv run python -m src.tts.lora_voice_poc --stage all        # Full pipeline
"""

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import soundfile as sf


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANGUAGE = "English"
OUTPUT_ROOT = Path("forge/tts_poc/poc3_lora")
TRAINING_DIR = OUTPUT_ROOT / "lora_training"
ADAPTER_DIR = OUTPUT_ROOT / "lora_adapters"
SCENE_OUTPUT_DIR = OUTPUT_ROOT / "scene_output"

# The scene to render (hospital drama — 5 speakers)
SCENE_TEXT = """\
Narrator: The hospital never truly slept. Even at three in the morning the corridors hummed with fluorescent light and distant footsteps, machines whispering softly behind closed doors. Rain pressed against the tall windows of St. Vincent Medical Center, turning the city outside into a blur of smeared lights. In the intensive care unit, a small group had gathered around a glass-walled conference room overlooking the ward. Through the window, a single patient lay surrounded by monitors that blinked in steady green rhythms.

Dr. Maya Lang: The scans came back ten minutes ago.

Narrator: Dr. Maya Lang placed a tablet on the table. The screen showed a rotating image of a human brain marked with faint glowing lines.

Dr. Ethan Rowe: And?

Narrator: Ethan Rowe leaned forward, his lab coat wrinkled from a long night shift.

Dr. Maya Lang: The tumor is growing faster than we expected.

Narrator: Silence settled across the room. Beyond the glass wall, a ventilator exhaled slowly beside the patient's bed.

Nurse Olivia Chen: That wasn't supposed to happen.

Narrator: Olivia Chen crossed her arms, her expression tight with concern.

Dr. Victor Hale: Experimental treatments rarely follow schedules.

Narrator: Dr. Victor Hale spoke quietly from the far end of the table. He had not looked away from the screen.

Dr. Ethan Rowe: Victor, the entire point of the trial was controlled growth suppression.

Narrator: Hale finally lifted his eyes.

Dr. Victor Hale: And we may still achieve that.

Nurse Olivia Chen: The patient's heart rate has been unstable for the last hour.

Narrator: Olivia gestured toward the ICU window.

Nurse Olivia Chen: If the tumor keeps expanding, the pressure on the brainstem could—

Narrator: She stopped herself before finishing the sentence.

Dr. Maya Lang: We know the risks.

Narrator: Maya rubbed her temples.

Dr. Ethan Rowe: The real question is whether we continue the treatment.

Narrator: Outside the conference room, a monitor beeped steadily as a nurse adjusted the IV line beside the patient.

Dr. Victor Hale: Stopping now guarantees failure.

Dr. Ethan Rowe: Continuing might kill him.

Narrator: Rain hammered harder against the hospital windows.

Nurse Olivia Chen: The patient trusted us.

Narrator: Olivia's voice was quiet but firm.

Nurse Olivia Chen: That has to mean something.

Narrator: Maya looked again at the glowing brain scan rotating slowly on the screen.

Dr. Maya Lang: If the treatment works, it could change how we treat cancer forever.

Dr. Ethan Rowe: And if it doesn't?

Narrator: Maya hesitated.

Dr. Maya Lang: Then tonight becomes the case study everyone warns their students about.

Narrator: The four of them stood in silence for a moment while the machines in the ICU continued their steady rhythm.

Dr. Victor Hale: We need a decision.

Narrator: Maya looked through the glass at the unconscious patient lying beneath the pale hospital lights.

Dr. Maya Lang: Then let's make the right one.\
"""

# Generic training texts — varied content for voice training samples.
# Voice identity comes from the voice description, not text content.
TRAINING_TEXTS = [
    ("Hello, welcome aboard the Helios. I trust the journey was uneventful.",
     "neutral, even delivery"),
    ("The readings are consistent with what we expected. Nothing unusual so far.",
     "calm, professional, matter-of-fact"),
    ("I need everyone at their stations within the hour. No exceptions.",
     "firm authority, commanding"),
    ("That's not what the data shows. Look at the third column again.",
     "patient correction, measured"),
    ("We lost contact with the survey team at fourteen hundred hours.",
     "serious, controlled concern"),
    ("I've seen this pattern before. It never ends well.",
     "quiet warning, subtle worry"),
    ("Outstanding work. The calibration is perfect.",
     "warm approval, genuine praise"),
    ("Do you hear that? Something in the lower decks.",
     "hushed, alert, edge of unease"),
    ("Tell me everything you know. Leave nothing out.",
     "intense, focused, demanding"),
    ("Sometimes the simplest answer is the right one.",
     "reflective, philosophical, calm"),
    ("We have approximately six hours before the window closes.",
     "urgent but controlled, time pressure"),
    ("I remember the first time I saw a planet from orbit.",
     "nostalgic, warm, slightly distant"),
]

# LoRA training hyperparameters
LORA_CONFIG = {
    "r": 32,
    "alpha": 128,
    "dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "epochs": 12,
    "learning_rate": 5e-6,
    "batch_size": 1,
    "gradient_accumulation_steps": 8,
    "max_audio_duration_sec": 30,
    "target_loss": (4.1, 4.2),  # Sweet spot per Alexandria docs
}


# ---------------------------------------------------------------------------
# Audio utilities
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


# ---------------------------------------------------------------------------
# Scene parser
# ---------------------------------------------------------------------------

def _to_snake_case(name: str) -> str:
    """Convert 'Dr. Maya Lang' → 'dr_maya_lang'."""
    name = name.strip()
    name = re.sub(r"[.\-']", "", name)       # Remove dots, hyphens, apostrophes
    name = re.sub(r"\s+", "_", name)          # Spaces → underscores
    return name.lower()


def _parse_scene(text: str) -> list[tuple[str, str, str]]:
    """Parse scene text into [(speaker_key, display_name, dialogue), ...].

    Each paragraph starts with 'Speaker Name: dialogue text'.
    """
    blocks = re.split(r"\n\n+", text.strip())
    lines = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        match = re.match(r"^([^:]+?):\s+(.+)", block, re.DOTALL)
        if match:
            display_name = match.group(1).strip()
            dialogue = match.group(2).strip()
            key = _to_snake_case(display_name)
            lines.append((key, display_name, dialogue))
    return lines


def _get_unique_characters(scene_lines: list[tuple[str, str, str]]) -> dict[str, str]:
    """Return {speaker_key: display_name} preserving first-seen order."""
    chars: dict[str, str] = {}
    for key, display_name, _ in scene_lines:
        if key not in chars:
            chars[key] = display_name
    return chars


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM via OpenRouter (annotation_llm config)."""
    from openai import OpenAI
    from src.config import (
        ANNOTATION_LLM_API_KEY,
        ANNOTATION_LLM_BASE_URL,
        ANNOTATION_LLM_MAX_TOKENS,
        ANNOTATION_LLM_MODEL,
        ANNOTATION_LLM_TEMPERATURE,
    )

    client = OpenAI(base_url=ANNOTATION_LLM_BASE_URL, api_key=ANNOTATION_LLM_API_KEY)
    response = client.chat.completions.create(
        model=ANNOTATION_LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=ANNOTATION_LLM_TEMPERATURE,
        max_tokens=ANNOTATION_LLM_MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


VOICE_DIRECTOR_SYSTEM = """\
You are a professional voice director for audiobook narration.
You create distinct, realistic voice descriptions for TTS (text-to-speech) synthesis.
Always respond with valid JSON."""


def _generate_voice_map(
    scene_text: str, characters: dict[str, str],
) -> dict[str, dict[str, str]]:
    """LLM generates voice_description + character_style per character.

    Returns {char_key: {"display_name": ..., "voice_description": ..., "character_style": ...}}
    """
    char_list = "\n".join(
        f"- {key}: {display_name}" for key, display_name in characters.items()
    )
    prompt = f"""Given this scene, generate distinct voice descriptions for each character.

Characters:
{char_list}

Scene:
{scene_text}

For each character, provide:
1. "voice_description": Acoustic voice traits ONLY (register, timbre, resonance, texture).
   Example: "deep male baritone, rich chest resonance, warm smooth timbre"
   Keep it to 8-12 words. These traits are fed to a TTS voice designer.
2. "character_style": A persistent acting note appended to ALL delivery instructions.
   Example: "Gruff military commander, deep deliberate authority."
   Keep it to 6-10 words. Describes HOW they always speak.

IMPORTANT: Make each voice acoustically distinct from the others.
The narrator should have a warm, authoritative storytelling voice.

Respond with JSON:
{{
  "characters": {{
    "<character_key>": {{
      "display_name": "<Display Name>",
      "voice_description": "<acoustic traits>",
      "character_style": "<acting note>"
    }},
    ...
  }}
}}"""

    raw = _call_llm(VOICE_DIRECTOR_SYSTEM, prompt)
    data = json.loads(raw)
    return data["characters"]


def _generate_delivery_instructions(
    scene_text: str, scene_lines: list[tuple[str, str, str]],
) -> list[str]:
    """LLM generates a delivery instruction for each scene line.

    Returns list of instruction strings, one per line.
    """
    numbered = "\n".join(
        f"[{i}] {display_name}: {text}"
        for i, (_, display_name, text) in enumerate(scene_lines)
    )
    prompt = f"""You are directing an audiobook recording. Generate a delivery instruction
for each numbered line below. Consider emotional arc, subtext, and context.

Each instruction should describe: emotion, pacing, intensity, vocal quality.
Keep each instruction to 8-15 words.

Example: "Calm, measured delivery. Quiet composure, even tone."
Example: "Tense whisper, controlled urgency. Slight tremor underneath."

Scene lines:
{numbered}

Respond with JSON:
{{
  "directions": [
    {{"line_index": 0, "instruction": "..."}},
    {{"line_index": 1, "instruction": "..."}},
    ...
  ]
}}"""

    raw = _call_llm(VOICE_DIRECTOR_SYSTEM, prompt)
    data = json.loads(raw)

    # Build ordered list matching scene_lines
    dir_map = {d["line_index"]: d["instruction"] for d in data["directions"]}
    return [dir_map.get(i, "Natural delivery.") for i in range(len(scene_lines))]


# ===================================================================
#  STAGE 1: Generate training samples via VoiceDesign
# ===================================================================

def stage_generate(device: str = "cuda") -> None:
    """Parse scene → LLM voice descriptions → VoiceDesign training samples."""
    from src.tts.qwen_tts_engine import QwenTTSEngine

    print("\n" + "#" * 60)
    print("# STAGE 1: Generate Training Samples via VoiceDesign")
    print("#" * 60)

    # Parse scene
    scene_lines = _parse_scene(SCENE_TEXT)
    characters = _get_unique_characters(scene_lines)
    print(f"\n  Parsed {len(scene_lines)} lines, {len(characters)} characters:")
    for key, name in characters.items():
        print(f"    {key}: {name}")

    # LLM voice descriptions
    print("\n  Generating voice descriptions via LLM...")
    voice_map = _generate_voice_map(SCENE_TEXT, characters)

    # Save voice_map for Stage 2/3
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    voice_map_path = TRAINING_DIR / "voice_map.json"
    with open(voice_map_path, "w", encoding="utf-8") as f:
        json.dump(voice_map, f, indent=2, ensure_ascii=False)
    print(f"  Voice map saved to {voice_map_path}")

    for key, info in voice_map.items():
        print(f"    {key}:")
        print(f"      voice: {info['voice_description']}")
        print(f"      style: {info['character_style']}")

    # Generate training samples
    engine = QwenTTSEngine(device=device, precision="bfloat16", model_size="1.7B")
    engine._load_design_model()

    try:
        for char_key, char_info in voice_map.items():
            char_dir = TRAINING_DIR / char_key
            char_dir.mkdir(parents=True, exist_ok=True)

            voice_desc = char_info["voice_description"]
            metadata = []

            print(f"\n  Character: {char_key}")
            print(f"  Voice desc: {voice_desc}")
            print(f"  Generating {len(TRAINING_TEXTS)} samples...")

            for idx, (text, emotion_hint) in enumerate(TRAINING_TEXTS):
                filename = f"sample_{idx:03d}.wav"
                desc = f"{voice_desc}, {emotion_hint}"

                print(f"    [{idx + 1:02d}/{len(TRAINING_TEXTS)}] {text[:40]}...")
                start = time.time()

                wavs, sr = engine._design_model.generate_voice_design(
                    text=text, language=LANGUAGE, instruct=desc,
                )
                wav = _postprocess(wavs[0], sr)
                _save(wav, sr, char_dir / filename)

                metadata.append({
                    "text": text,
                    "audio_filepath": filename,
                })

                duration = len(wav) / sr
                print(f"      -> {duration:.1f}s ({time.time() - start:.1f}s)")

                # Save first neutral sample as reference
                if idx == 0:
                    _save(wav, sr, char_dir / "ref.wav")
                    (char_dir / "ref_text.txt").write_text(text, encoding="utf-8")

            # Write metadata
            metadata_path = char_dir / "metadata.jsonl"
            with open(metadata_path, "w", encoding="utf-8") as f:
                for entry in metadata:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            print(f"  Saved {len(metadata)} samples + metadata to {char_dir}")

    finally:
        engine.close()

    print("\n  Stage 1 complete. Training data ready.")


# ===================================================================
#  STAGE 2: Train LoRA adapter
# ===================================================================

def stage_train(device: str = "cuda") -> None:
    """Train LoRA adapters following official Qwen3-TTS fine-tuning approach.

    Uses the dual-channel embedding construction from QwenLM/Qwen3-TTS sft_12hz.py:
      - text_embedding + codec_embedding (additive, not concatenated)
      - Speaker embedding injected at position 6
      - All 16 codec group embeddings summed at audio positions
      - Sub-talker loss at codec positions only
    """
    print("\n" + "#" * 60)
    print("# STAGE 2: Train LoRA Adapters")
    print("#" * 60)

    # Lazy imports — these are heavy
    try:
        import torch
        import librosa
        from peft import LoraConfig, get_peft_model
        from qwen_tts import Qwen3TTSModel
        from transformers import AutoTokenizer
    except ImportError as e:
        print(f"\n  ERROR: Missing dependency: {e}")
        print("  Run: uv add peft librosa")
        return

    # Read character list from voice_map.json
    voice_map_path = TRAINING_DIR / "voice_map.json"
    if not voice_map_path.exists():
        print("\n  ERROR: No voice_map.json. Run --stage generate first.")
        return

    with open(voice_map_path, encoding="utf-8") as f:
        voice_map = json.load(f)

    for char_key, char_info in voice_map.items():
        char_dir = TRAINING_DIR / char_key
        adapter_out = ADAPTER_DIR / char_key
        adapter_out.mkdir(parents=True, exist_ok=True)

        metadata_path = char_dir / "metadata.jsonl"
        if not metadata_path.exists():
            print(f"\n  SKIP {char_key}: No training data. Run --stage generate first.")
            continue

        print(f"\n  Training adapter for: {char_key}")
        print(f"  Data: {char_dir}")
        print(f"  Output: {adapter_out}")

        # Load metadata
        with open(metadata_path, encoding="utf-8") as f:
            samples = [json.loads(line) for line in f if line.strip()]
        print(f"  Samples: {len(samples)}")

        # Load base model + text tokenizer
        print("  Loading Base model...")
        model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map=f"{device}:0" if device == "cuda" else device,
            dtype=torch.bfloat16,
        )
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base")

        # Config token IDs (from model config, matching official collate_fn)
        cfg = model.model.config
        tcfg = cfg.talker_config
        tts_pad = cfg.tts_pad_token_id
        tts_bos = cfg.tts_bos_token_id
        tts_eos = cfg.tts_eos_token_id
        codec_nothink = tcfg.codec_nothink_id
        codec_think_bos = tcfg.codec_think_bos_id
        codec_think_eos = tcfg.codec_think_eos_id
        codec_pad = tcfg.codec_pad_id
        codec_bos = tcfg.codec_bos_id
        codec_eos = tcfg.codec_eos_token_id

        # Get talker and save embedding layer references (not modified by LoRA)
        talker = model.model.talker
        text_emb_layer = talker.model.text_embedding
        codec_emb_layer = talker.model.codec_embedding

        # Extract speaker embedding from reference audio
        ref_audio_path = char_dir / "ref.wav"
        ref_text_path = char_dir / "ref_text.txt"
        ref_text = ref_text_path.read_text(encoding="utf-8").strip() if ref_text_path.exists() else ""
        print(f"  Reference: {ref_audio_path}")
        print(f"  Ref text: {ref_text[:50]}...")

        ref_audio, _ = librosa.load(str(ref_audio_path), sr=24000, mono=True)
        with torch.no_grad():
            speaker_emb = model.model.extract_speaker_embedding(ref_audio, 24000)
        print(f"  Speaker embedding: {speaker_emb.shape}")

        # Apply LoRA to talker
        talker.enable_input_require_grads()
        talker.gradient_checkpointing_enable()

        lora_config = LoraConfig(
            r=LORA_CONFIG["r"],
            lora_alpha=LORA_CONFIG["alpha"],
            lora_dropout=LORA_CONFIG["dropout"],
            target_modules=LORA_CONFIG["target_modules"],
            task_type="CAUSAL_LM",
        )
        peft_talker = get_peft_model(talker, lora_config)
        trainable = sum(p.numel() for p in peft_talker.parameters() if p.requires_grad)
        total = sum(p.numel() for p in peft_talker.parameters())
        print(f"  LoRA params: {trainable:,} / {total:,} ({trainable / total:.2%})")

        # Encode training samples: tokenize text + extract audio codecs
        print(f"  Encoding {len(samples)} audio samples...")
        encoded_samples = []

        for sample in samples:
            audio_path = str(char_dir / sample["audio_filepath"])
            try:
                audio, _ = librosa.load(audio_path, sr=24000, mono=True)
                duration = len(audio) / 24000
                if duration > LORA_CONFIG["max_audio_duration_sec"]:
                    print(f"    SKIP {sample['audio_filepath']}: {duration:.1f}s > {LORA_CONFIG['max_audio_duration_sec']}s")
                    continue

                # Encode audio → codec tokens (all 16 groups)
                with torch.no_grad():
                    enc = model.model.speech_tokenizer.encode(
                        audio, sr=24000, return_dict=True,
                    )
                    audio_codes = enc.audio_codes[0]  # (T, 16)

                # Tokenize text in chat format (matching official _build_assistant_text)
                assistant_text = (
                    f"<|im_start|>assistant\n{sample['text']}"
                    f"<|im_end|>\n<|im_start|>assistant\n"
                )
                text_ids = tokenizer(assistant_text, return_tensors="pt").input_ids

                encoded_samples.append({
                    "text_ids": text_ids.cpu(),       # (1, tl)
                    "audio_codes": audio_codes.cpu(),  # (T, 16)
                })
            except Exception as e:
                print(f"    ERROR encoding {sample['audio_filepath']}: {e}")
                continue

        if not encoded_samples:
            print(f"  ERROR: No samples encoded for {char_key}. Skipping.")
            continue

        print(f"  Encoded: {len(encoded_samples)} samples")

        # Training loop
        optimizer = torch.optim.AdamW(
            peft_talker.parameters(),
            lr=LORA_CONFIG["learning_rate"],
        )

        epochs = LORA_CONFIG["epochs"]
        grad_accum = LORA_CONFIG["gradient_accumulation_steps"]

        print(f"\n  Training: {epochs} epochs, lr={LORA_CONFIG['learning_rate']}")
        print(f"  Grad accumulation: {grad_accum} steps")
        print(f"  Target loss: {LORA_CONFIG['target_loss']}")

        peft_talker.train()
        for epoch in range(epochs):
            epoch_loss = 0.0
            n_steps = 0
            optimizer.zero_grad()

            for step, sample in enumerate(encoded_samples):
                try:
                    text_ids = sample["text_ids"].to(device)       # (1, tl)
                    audio_codes = sample["audio_codes"].to(device)  # (T, 16)

                    tl = text_ids.shape[1]  # text token length
                    T = audio_codes.shape[0]  # audio codec length
                    audio_codec_0 = audio_codes[:, 0]  # (T,) first codec group
                    total_len = tl + T + 8  # from official collate_fn

                    # -------------------------------------------------------
                    # Build dual-channel input_ids (official collate_fn layout)
                    # Channel 0 = text, Channel 1 = codec_0
                    # -------------------------------------------------------
                    input_ids = torch.zeros(
                        (1, total_len, 2), dtype=torch.long, device=device,
                    )
                    codec_all = torch.zeros(
                        (1, total_len, 16), dtype=torch.long, device=device,
                    )

                    # -- Text channel (channel 0) --
                    input_ids[0, :3, 0] = text_ids[0, :3]
                    input_ids[0, 3:7, 0] = tts_pad
                    input_ids[0, 7, 0] = tts_bos
                    input_ids[0, 8:8 + tl - 3, 0] = text_ids[0, 3:]
                    input_ids[0, 8 + tl - 3, 0] = tts_eos
                    input_ids[0, 8 + tl - 2:, 0] = tts_pad

                    # -- Codec channel (channel 1) --
                    input_ids[0, 3:8, 1] = torch.tensor(
                        [codec_nothink, codec_think_bos, codec_think_eos, 0, codec_pad],
                        device=device,
                    )
                    input_ids[0, 8:8 + tl - 3, 1] = codec_pad
                    input_ids[0, 8 + tl - 3, 1] = codec_pad
                    input_ids[0, 8 + tl - 2, 1] = codec_bos
                    input_ids[0, 8 + tl - 1:8 + tl - 1 + T, 1] = audio_codec_0
                    input_ids[0, 8 + tl - 1 + T, 1] = codec_eos

                    # -- Codec all groups (16) at audio positions --
                    codec_all[0, 8 + tl - 1:8 + tl - 1 + T, :] = audio_codes

                    # -- Labels: codec_0 at audio positions + eos --
                    c0_labels = torch.full(
                        (1, total_len), -100, dtype=torch.long, device=device,
                    )
                    c0_labels[0, 8 + tl - 1:8 + tl - 1 + T] = audio_codec_0
                    c0_labels[0, 8 + tl - 1 + T] = codec_eos

                    # -- Masks --
                    text_mask = torch.ones(
                        (1, total_len, 1), dtype=torch.bool, device=device,
                    )
                    codec_emb_mask = torch.zeros(
                        (1, total_len, 1), dtype=torch.bool, device=device,
                    )
                    codec_emb_mask[0, 3:, 0] = True
                    codec_emb_mask[0, 6, 0] = False

                    codec_mask = torch.zeros(
                        (1, total_len), dtype=torch.bool, device=device,
                    )
                    codec_mask[0, 8 + tl - 1:8 + tl - 1 + T] = True

                    attn_mask = torch.ones(
                        (1, total_len), dtype=torch.long, device=device,
                    )

                    # -------------------------------------------------------
                    # Build embeddings (following sft_12hz.py exactly)
                    # -------------------------------------------------------
                    text_channel = input_ids[:, :, 0]
                    codec_channel = input_ids[:, :, 1]

                    text_embed = text_emb_layer(text_channel) * text_mask
                    codec_embed = codec_emb_layer(codec_channel) * codec_emb_mask
                    codec_embed[:, 6, :] = speaker_emb

                    embeds = text_embed + codec_embed

                    for gi in range(1, 16):
                        ci_embed = peft_talker.code_predictor.get_input_embeddings()[gi - 1](
                            codec_all[:, :, gi]
                        )
                        embeds = embeds + ci_embed * codec_mask.unsqueeze(-1)

                    # -------------------------------------------------------
                    # Forward pass (shifted)
                    # -------------------------------------------------------
                    outputs = peft_talker(
                        inputs_embeds=embeds[:, :-1, :],
                        attention_mask=attn_mask[:, :-1],
                        labels=c0_labels[:, 1:],
                        output_hidden_states=True,
                    )

                    # -------------------------------------------------------
                    # Sub-talker loss (only at codec positions)
                    # -------------------------------------------------------
                    hidden = outputs.hidden_states[0][-1]
                    st_hidden = hidden[codec_mask[:, 1:]]
                    st_codec = codec_all[codec_mask]
                    _, st_loss = peft_talker.forward_sub_talker_finetune(
                        st_codec, st_hidden,
                    )

                    loss = outputs.loss + 0.3 * st_loss
                    loss = loss / grad_accum
                    loss.backward()
                    epoch_loss += loss.item() * grad_accum
                    n_steps += 1

                    if (step + 1) % grad_accum == 0:
                        optimizer.step()
                        optimizer.zero_grad()

                except Exception as e:
                    print(f"    Step {step} error: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            # Final grad step if needed
            if len(encoded_samples) % grad_accum != 0:
                optimizer.step()
                optimizer.zero_grad()

            avg_loss = epoch_loss / max(n_steps, 1)
            target_lo, target_hi = LORA_CONFIG["target_loss"]
            status = "OK" if target_lo <= avg_loss <= target_hi else "  "
            print(f"    Epoch {epoch + 1:02d}/{epochs}: loss={avg_loss:.3f} {status}")

            if device == "cuda":
                torch.cuda.empty_cache()

        # Save adapter
        peft_talker.save_pretrained(str(adapter_out))

        # Save reference audio alongside adapter
        import shutil
        ref_wav = char_dir / "ref.wav"
        if ref_wav.exists():
            shutil.copy2(ref_wav, adapter_out / "ref_sample.wav")
        if ref_text_path.exists():
            shutil.copy2(ref_text_path, adapter_out / "ref_text.txt")

        # Save training metadata
        meta = {
            "character": char_key,
            "voice_desc": char_info.get("voice_description", ""),
            "character_style": char_info.get("character_style", ""),
            "num_samples": len(encoded_samples),
            "epochs": epochs,
            "final_loss": avg_loss,
            "lora_config": {k: v for k, v in LORA_CONFIG.items() if k != "target_loss"},
        }
        with open(adapter_out / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print(f"  Adapter saved to {adapter_out}")

        # Cleanup
        del peft_talker, talker, model, optimizer
        if device == "cuda":
            torch.cuda.empty_cache()

    print("\n  Stage 2 complete. Adapters trained.")


# ===================================================================
#  STAGE 3: Render full scene with LoRA-adapted voices
# ===================================================================

def stage_render(device: str = "cuda") -> None:
    """LLM delivery instructions → LoRA voices → complete scene WAV."""
    print("\n" + "#" * 60)
    print("# STAGE 3: Render Scene with LoRA Voices")
    print("#" * 60)

    try:
        import torch
        from peft import PeftModel
        from qwen_tts import Qwen3TTSModel
    except ImportError as e:
        print(f"\n  ERROR: Missing dependency: {e}")
        print("  Run: uv add peft librosa")
        return

    # Load voice_map
    voice_map_path = TRAINING_DIR / "voice_map.json"
    if not voice_map_path.exists():
        print("\n  ERROR: No voice_map.json. Run --stage generate first.")
        return
    with open(voice_map_path, encoding="utf-8") as f:
        voice_map = json.load(f)

    # Parse scene
    scene_lines = _parse_scene(SCENE_TEXT)
    characters = _get_unique_characters(scene_lines)
    print(f"\n  Scene: {len(scene_lines)} lines, {len(characters)} characters")

    # Check all adapters exist
    missing = []
    for key in characters:
        adapter_path = ADAPTER_DIR / key
        if not (adapter_path / "adapter_config.json").exists():
            missing.append(key)
    if missing:
        print(f"\n  ERROR: Missing adapters for: {', '.join(missing)}")
        print("  Run --stage train first.")
        return

    # LLM delivery instructions
    print("\n  Generating delivery instructions via LLM...")
    instructions = _generate_delivery_instructions(SCENE_TEXT, scene_lines)

    # Save instructions for reference
    SCENE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inst_path = SCENE_OUTPUT_DIR / "delivery_instructions.json"
    with open(inst_path, "w", encoding="utf-8") as f:
        json.dump(
            [{"line": i, "speaker": scene_lines[i][1], "text": scene_lines[i][2],
              "instruction": instructions[i]} for i in range(len(scene_lines))],
            f, indent=2, ensure_ascii=False,
        )
    print(f"  Saved {len(instructions)} instructions to {inst_path}")

    # Render lines per character (load model+adapter once per character)
    for char_key in characters:
        adapter_path = ADAPTER_DIR / char_key
        char_info = voice_map.get(char_key, {})
        character_style = char_info.get("character_style", "")

        # Find which lines belong to this character
        char_line_indices = [
            i for i, (key, _, _) in enumerate(scene_lines) if key == char_key
        ]
        if not char_line_indices:
            continue

        print(f"\n  Rendering {len(char_line_indices)} lines for: {char_key}")
        print(f"  Adapter: {adapter_path}")
        print(f"  Style: {character_style}")

        # Load base model
        print("  Loading Base model + LoRA adapter...")
        model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map=f"{device}:0" if device == "cuda" else device,
            dtype=torch.bfloat16,
        )

        # Apply LoRA adapter
        model.model.talker = PeftModel.from_pretrained(
            model.model.talker, str(adapter_path),
        )
        model.model.talker.eval()

        # Create voice clone prompt from ref audio
        ref_audio_path = adapter_path / "ref_sample.wav"
        ref_text_path = adapter_path / "ref_text.txt"
        ref_text = ref_text_path.read_text(encoding="utf-8").strip() if ref_text_path.exists() else ""

        clone_prompt = model.create_voice_clone_prompt(
            ref_audio=str(ref_audio_path),
            ref_text=ref_text if ref_text else None,
            x_vector_only_mode=not bool(ref_text),
        )

        # Build instruct_ids for this character's delivery instructions
        # The Base model's generate() supports instruct_ids via kwargs
        for idx in char_line_indices:
            _, display_name, text = scene_lines[idx]
            instruction = instructions[idx]
            full_instruct = f"{instruction} {character_style}".strip()

            print(f"    [{idx:02d}] {display_name}: {text[:40]}...")
            print(f"         instruct: {full_instruct[:60]}...")
            start = time.time()

            try:
                # Tokenize instruct for the Base model
                instruct_text = f"<|im_start|>user\n{full_instruct}<|im_end|>\n"
                instruct_input = model.processor(
                    text=instruct_text, return_tensors="pt", padding=True,
                )
                instruct_tensor = instruct_input["input_ids"].to(model.device)
                if instruct_tensor.dim() == 1:
                    instruct_tensor = instruct_tensor.unsqueeze(0)

                # Generate with LoRA + voice clone + instruct
                wavs, sr = model.generate_voice_clone(
                    text=text,
                    language=LANGUAGE,
                    voice_clone_prompt=clone_prompt,
                    instruct_ids=[instruct_tensor],
                )
                wav = _postprocess(wavs[0], sr)

                line_path = SCENE_OUTPUT_DIR / f"line_{idx:03d}_{char_key}.wav"
                _save(wav, sr, line_path)
                print(f"         -> {len(wav) / sr:.1f}s ({time.time() - start:.1f}s)")

            except Exception as e:
                print(f"         ERROR: {e}")
                import traceback
                traceback.print_exc()
                # Save silence as fallback so assembly doesn't break
                silence = np.zeros(int(24000 * 0.5), dtype=np.float32)
                _save(silence, 24000, SCENE_OUTPUT_DIR / f"line_{idx:03d}_{char_key}.wav")

        # Cleanup this character's model
        del model, clone_prompt
        if device == "cuda":
            torch.cuda.empty_cache()

    # ---------------------------------------------------------------
    # Assemble full scene in order
    # ---------------------------------------------------------------
    print("\n  Assembling full scene...")
    all_segments: list[np.ndarray] = []
    per_speaker: dict[str, list[np.ndarray]] = {}
    prev_speaker = None
    sr = 24000

    for idx, (key, display_name, text) in enumerate(scene_lines):
        # Find the rendered WAV
        line_path = SCENE_OUTPUT_DIR / f"line_{idx:03d}_{key}.wav"
        if not line_path.exists():
            print(f"    WARNING: Missing {line_path}, inserting silence")
            wav = np.zeros(int(sr * 0.5), dtype=np.float32)
        else:
            wav, _ = sf.read(str(line_path), dtype="float32")

        # Insert pause
        if prev_speaker is not None:
            pause_ms = 600 if key != prev_speaker else 300
            pause = np.zeros(int(sr * pause_ms / 1000), dtype=np.float32)
            all_segments.append(pause)

        all_segments.append(wav)
        per_speaker.setdefault(key, []).append(wav)
        prev_speaker = key

    # Save combined scene
    if all_segments:
        full_scene = np.concatenate(all_segments)
        _save(full_scene, sr, SCENE_OUTPUT_DIR / "scene_full.wav")
        print(f"  Full scene: {len(full_scene) / sr:.1f}s -> {SCENE_OUTPUT_DIR / 'scene_full.wav'}")

    # Save per-speaker extracts
    for key, segs in per_speaker.items():
        combined = _concat_with_pause(segs, sr, pause_ms=400)
        _save(combined, sr, SCENE_OUTPUT_DIR / f"{key}_only.wav")
        print(f"  {key}: {len(combined) / sr:.1f}s")

    print("\n  Stage 3 complete. Scene rendered.")


# ===================================================================
#  Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="POC 3: LoRA Voice Pipeline — Scene text → complete audio")
    parser.add_argument(
        "--stage",
        required=True,
        choices=["generate", "train", "render", "all"],
        help="Which stage to run",
    )
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    args = parser.parse_args()

    # Parse scene for summary
    scene_lines = _parse_scene(SCENE_TEXT)
    characters = _get_unique_characters(scene_lines)

    print("=" * 60)
    print("POC 3: LoRA Voice Pipeline")
    print("=" * 60)
    print(f"  Device:     {args.device}")
    print(f"  Stage:      {args.stage}")
    print(f"  Output:     {OUTPUT_ROOT.resolve()}")
    print(f"  Characters: {len(characters)}")
    for key, name in characters.items():
        print(f"    {key}: {name}")
    print(f"  Scene lines: {len(scene_lines)}")

    stages = {
        "generate": [stage_generate],
        "train": [stage_train],
        "render": [stage_render],
        "all": [stage_generate, stage_train, stage_render],
    }

    for fn in stages[args.stage]:
        fn(device=args.device)

    print("\n" + "=" * 60)
    print("POC 3 COMPLETE")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT_ROOT.resolve()}")

    if args.stage in ("render", "all"):
        scene_wav = SCENE_OUTPUT_DIR / "scene_full.wav"
        if scene_wav.exists():
            print(f"\nFull scene: {scene_wav}")
        print("\nCompare with:")
        print("  POC 1: forge/tts_poc/poc1_single_narrator/")
        print("  POC 2: forge/tts_poc/poc2_multi_cast/")


if __name__ == "__main__":
    main()
