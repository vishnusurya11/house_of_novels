"""
LoRA Voice Trainer — Fine-tune Qwen3-TTS voice adapters for characters.

Extracted from lora_voice_poc.py for production pipeline use.
Generates training samples via VoiceDesign, then trains LoRA adapters
using the official Qwen3-TTS dual-channel approach (sft_12hz.py).

Usage:
    # Train adapters from codex character data:
    uv run python -m src.tts.lora_trainer --codex forge/xxx/codex.json

    # Train specific characters only:
    uv run python -m src.tts.lora_trainer --codex forge/xxx/codex.json --characters MARCUS_REED AURORA_VALE

    # Generate training samples only (no training):
    uv run python -m src.tts.lora_trainer --codex forge/xxx/codex.json --stage generate

    # Train from existing samples only:
    uv run python -m src.tts.lora_trainer --codex forge/xxx/codex.json --stage train
"""

import json
import shutil
import time
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from src.config import (
    TTS_DEVICE,
    TTS_LORA_TRAINING_CONFIG,
    TTS_MODEL_SIZE,
)

# Default training texts — generic sentences with varied emotional contexts.
# Voice identity comes from the VoiceDesign description, not text content.
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


# ---------------------------------------------------------------------------
# LoRA Voice Trainer
# ---------------------------------------------------------------------------

class LoRAVoiceTrainer:
    """Train LoRA voice adapters for characters.

    Two-stage pipeline:
    1. generate_training_samples(): VoiceDesign model → training WAV files
    2. train_adapter(): LoRA fine-tuning on base model talker
    """

    def __init__(
        self,
        adapter_dir: str | Path,
        training_data_dir: Optional[str | Path] = None,
        training_config: Optional[dict] = None,
        device: str = "cuda",
        model_size: str = "1.7B",
    ):
        """
        Args:
            adapter_dir: Output directory for trained adapters
            training_data_dir: Directory for training WAV samples (default: adapter_dir/../lora_training)
            training_config: Training hyperparameters (from config.yaml tts.lora.training)
            device: "cuda" or "cpu"
            model_size: "1.7B" or "0.6B"
        """
        self.adapter_dir = Path(adapter_dir)
        self.training_data_dir = Path(training_data_dir) if training_data_dir else self.adapter_dir.parent / "lora_training"
        self.device = device
        self.model_size = model_size

        # Merge default config with overrides
        defaults = {
            "samples_per_character": 12,
            "epochs": 12,
            "learning_rate": 5e-6,
            "lora_rank": 32,
            "lora_alpha": 128,
            "lora_dropout": 0.05,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
            "batch_size": 1,
            "gradient_accumulation_steps": 8,
            "max_audio_duration_sec": 30,
            "target_loss": [4.1, 4.2],
        }
        cfg = training_config or {}
        self.config = {**defaults, **cfg}

    def generate_training_samples(
        self,
        character_id: str,
        voice_description: str,
        character_style: str = "",
        sample_texts: Optional[list[tuple[str, str]]] = None,
    ) -> Path:
        """Stage 1: Generate training WAVs via VoiceDesign model.

        Args:
            character_id: Character identifier (e.g. "MARCUS_REED")
            voice_description: Acoustic voice description for VoiceDesign
            character_style: Persistent acting note (saved as metadata)
            sample_texts: Override training texts as [(text, emotion_hint), ...]

        Returns:
            Path to training data directory for this character
        """
        from src.tts.qwen_tts_engine import QwenTTSEngine

        texts = sample_texts or TRAINING_TEXTS[:self.config["samples_per_character"]]
        char_key = character_id.lower()
        char_dir = self.training_data_dir / char_key
        char_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  Generating {len(texts)} training samples for {character_id}...")
        print(f"  Voice: {voice_description}")

        engine = QwenTTSEngine(device=self.device, precision="bfloat16", model_size=self.model_size)
        engine._load_design_model()

        metadata = []
        try:
            for idx, (text, emotion_hint) in enumerate(texts):
                filename = f"sample_{idx:03d}.wav"
                desc = f"{voice_description}, {emotion_hint}"

                print(f"    [{idx + 1:02d}/{len(texts)}] {text[:40]}...")
                start = time.time()

                wavs, sr = engine._design_model.generate_voice_design(
                    text=text, language="English", instruct=desc,
                )
                wav = _postprocess(wavs[0], sr)
                char_dir.joinpath(filename).parent.mkdir(parents=True, exist_ok=True)
                sf.write(str(char_dir / filename), wav, sr)

                metadata.append({"text": text, "audio_filepath": filename})

                duration = len(wav) / sr
                print(f"      -> {duration:.1f}s ({time.time() - start:.1f}s)")

                # Save first sample as reference
                if idx == 0:
                    sf.write(str(char_dir / "ref.wav"), wav, sr)
                    (char_dir / "ref_text.txt").write_text(text, encoding="utf-8")

            # Write metadata
            with open(char_dir / "metadata.jsonl", "w", encoding="utf-8") as f:
                for entry in metadata:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # Save voice map entry for this character
            voice_info = {
                "character_id": character_id,
                "voice_description": voice_description,
                "character_style": character_style,
            }
            with open(char_dir / "voice_info.json", "w", encoding="utf-8") as f:
                json.dump(voice_info, f, indent=2, ensure_ascii=False)

            print(f"  Saved {len(metadata)} samples to {char_dir}")

        finally:
            engine.close()

        return char_dir

    def train_adapter(
        self,
        character_id: str,
        training_data_dir: Optional[Path] = None,
    ) -> Path:
        """Stage 2: Train LoRA adapter on training samples.

        Uses the official Qwen3-TTS dual-channel approach (sft_12hz.py):
        - text_embedding + codec_embedding (additive)
        - Speaker embedding injected at position 6
        - All 16 codec group embeddings summed at audio positions
        - Sub-talker loss at codec positions only

        Args:
            character_id: Character identifier
            training_data_dir: Override data directory (default: self.training_data_dir/char_key)

        Returns:
            Path to trained adapter directory
        """
        import torch
        import librosa
        from peft import LoraConfig, get_peft_model
        from qwen_tts import Qwen3TTSModel
        from transformers import AutoTokenizer

        char_key = character_id.lower()
        char_dir = Path(training_data_dir) if training_data_dir else self.training_data_dir / char_key
        adapter_out = self.adapter_dir / char_key
        adapter_out.mkdir(parents=True, exist_ok=True)

        metadata_path = char_dir / "metadata.jsonl"
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"No training data at {char_dir}. Run generate_training_samples() first."
            )

        print(f"\n  Training adapter for: {character_id}")
        print(f"  Data: {char_dir}")
        print(f"  Output: {adapter_out}")

        # Load metadata
        with open(metadata_path, encoding="utf-8") as f:
            samples = [json.loads(line) for line in f if line.strip()]
        print(f"  Samples: {len(samples)}")

        # Load voice info for character_style metadata
        voice_info_path = char_dir / "voice_info.json"
        voice_info = {}
        if voice_info_path.exists():
            with open(voice_info_path, encoding="utf-8") as f:
                voice_info = json.load(f)

        # Load base model + tokenizer
        model_id = f"Qwen/Qwen3-TTS-12Hz-{self.model_size}-Base"
        print(f"  Loading Base model ({self.model_size})...")
        model = Qwen3TTSModel.from_pretrained(
            model_id,
            device_map=f"{self.device}:0" if self.device == "cuda" else self.device,
            dtype=torch.bfloat16,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        # Config token IDs
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

        talker = model.model.talker
        text_emb_layer = talker.model.text_embedding
        codec_emb_layer = talker.model.codec_embedding

        # Speaker embedding from reference audio
        ref_audio_path = char_dir / "ref.wav"
        ref_text_path = char_dir / "ref_text.txt"
        ref_text = ref_text_path.read_text(encoding="utf-8").strip() if ref_text_path.exists() else ""

        ref_audio, _ = librosa.load(str(ref_audio_path), sr=24000, mono=True)
        with torch.no_grad():
            speaker_emb = model.model.extract_speaker_embedding(ref_audio, 24000)
        print(f"  Speaker embedding: {speaker_emb.shape}")

        # Apply LoRA
        talker.enable_input_require_grads()
        talker.gradient_checkpointing_enable()

        lora_config = LoraConfig(
            r=self.config["lora_rank"],
            lora_alpha=self.config["lora_alpha"],
            lora_dropout=self.config.get("lora_dropout", 0.05),
            target_modules=self.config["target_modules"],
            task_type="CAUSAL_LM",
        )
        peft_talker = get_peft_model(talker, lora_config)
        trainable = sum(p.numel() for p in peft_talker.parameters() if p.requires_grad)
        total = sum(p.numel() for p in peft_talker.parameters())
        print(f"  LoRA params: {trainable:,} / {total:,} ({trainable / total:.2%})")

        # Encode training samples
        print(f"  Encoding {len(samples)} audio samples...")
        encoded_samples = []
        max_dur = self.config["max_audio_duration_sec"]

        for sample in samples:
            audio_path = str(char_dir / sample["audio_filepath"])
            try:
                audio, _ = librosa.load(audio_path, sr=24000, mono=True)
                duration = len(audio) / 24000
                if duration > max_dur:
                    print(f"    SKIP {sample['audio_filepath']}: {duration:.1f}s > {max_dur}s")
                    continue

                with torch.no_grad():
                    enc = model.model.speech_tokenizer.encode(audio, sr=24000, return_dict=True)
                    audio_codes = enc.audio_codes[0]  # (T, 16)

                assistant_text = (
                    f"<|im_start|>assistant\n{sample['text']}"
                    f"<|im_end|>\n<|im_start|>assistant\n"
                )
                text_ids = tokenizer(assistant_text, return_tensors="pt").input_ids

                encoded_samples.append({
                    "text_ids": text_ids.cpu(),
                    "audio_codes": audio_codes.cpu(),
                })
            except Exception as e:
                print(f"    ERROR encoding {sample['audio_filepath']}: {e}")

        if not encoded_samples:
            raise RuntimeError(f"No samples encoded for {character_id}")

        print(f"  Encoded: {len(encoded_samples)} samples")

        # Training loop
        epochs = self.config["epochs"]
        grad_accum = self.config["gradient_accumulation_steps"]
        lr = self.config["learning_rate"]

        optimizer = torch.optim.AdamW(peft_talker.parameters(), lr=lr)
        target_loss = self.config.get("target_loss", [4.1, 4.2])

        print(f"\n  Training: {epochs} epochs, lr={lr}")
        print(f"  Grad accumulation: {grad_accum}")

        peft_talker.train()
        final_loss = 0.0

        for epoch in range(epochs):
            epoch_loss = 0.0
            n_steps = 0
            optimizer.zero_grad()

            for step, sample in enumerate(encoded_samples):
                try:
                    text_ids = sample["text_ids"].to(self.device)
                    audio_codes = sample["audio_codes"].to(self.device)

                    tl = text_ids.shape[1]
                    T = audio_codes.shape[0]
                    audio_codec_0 = audio_codes[:, 0]
                    total_len = tl + T + 8

                    # Build dual-channel input_ids
                    input_ids = torch.zeros((1, total_len, 2), dtype=torch.long, device=self.device)
                    codec_all = torch.zeros((1, total_len, 16), dtype=torch.long, device=self.device)

                    # Text channel
                    input_ids[0, :3, 0] = text_ids[0, :3]
                    input_ids[0, 3:7, 0] = tts_pad
                    input_ids[0, 7, 0] = tts_bos
                    input_ids[0, 8:8 + tl - 3, 0] = text_ids[0, 3:]
                    input_ids[0, 8 + tl - 3, 0] = tts_eos
                    input_ids[0, 8 + tl - 2:, 0] = tts_pad

                    # Codec channel
                    input_ids[0, 3:8, 1] = torch.tensor(
                        [codec_nothink, codec_think_bos, codec_think_eos, 0, codec_pad],
                        device=self.device,
                    )
                    input_ids[0, 8:8 + tl - 3, 1] = codec_pad
                    input_ids[0, 8 + tl - 3, 1] = codec_pad
                    input_ids[0, 8 + tl - 2, 1] = codec_bos
                    input_ids[0, 8 + tl - 1:8 + tl - 1 + T, 1] = audio_codec_0
                    input_ids[0, 8 + tl - 1 + T, 1] = codec_eos

                    codec_all[0, 8 + tl - 1:8 + tl - 1 + T, :] = audio_codes

                    # Labels
                    c0_labels = torch.full((1, total_len), -100, dtype=torch.long, device=self.device)
                    c0_labels[0, 8 + tl - 1:8 + tl - 1 + T] = audio_codec_0
                    c0_labels[0, 8 + tl - 1 + T] = codec_eos

                    # Masks
                    text_mask = torch.ones((1, total_len, 1), dtype=torch.bool, device=self.device)
                    codec_emb_mask = torch.zeros((1, total_len, 1), dtype=torch.bool, device=self.device)
                    codec_emb_mask[0, 3:, 0] = True
                    codec_emb_mask[0, 6, 0] = False

                    codec_mask = torch.zeros((1, total_len), dtype=torch.bool, device=self.device)
                    codec_mask[0, 8 + tl - 1:8 + tl - 1 + T] = True

                    attn_mask = torch.ones((1, total_len), dtype=torch.long, device=self.device)

                    # Build embeddings
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

                    # Forward pass
                    outputs = peft_talker(
                        inputs_embeds=embeds[:, :-1, :],
                        attention_mask=attn_mask[:, :-1],
                        labels=c0_labels[:, 1:],
                        output_hidden_states=True,
                    )

                    # Sub-talker loss
                    hidden = outputs.hidden_states[0][-1]
                    st_hidden = hidden[codec_mask[:, 1:]]
                    st_codec = codec_all[codec_mask]
                    _, st_loss = peft_talker.forward_sub_talker_finetune(st_codec, st_hidden)

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

            if len(encoded_samples) % grad_accum != 0:
                optimizer.step()
                optimizer.zero_grad()

            avg_loss = epoch_loss / max(n_steps, 1)
            final_loss = avg_loss
            target_lo, target_hi = target_loss
            status = "OK" if target_lo <= avg_loss <= target_hi else "  "
            print(f"    Epoch {epoch + 1:02d}/{epochs}: loss={avg_loss:.3f} {status}")

            if self.device == "cuda":
                torch.cuda.empty_cache()

        # Save adapter
        peft_talker.save_pretrained(str(adapter_out))

        # Copy reference files alongside adapter
        ref_wav = char_dir / "ref.wav"
        if ref_wav.exists():
            shutil.copy2(ref_wav, adapter_out / "ref_sample.wav")
        if ref_text_path.exists():
            shutil.copy2(ref_text_path, adapter_out / "ref_text.txt")

        # Save training metadata
        meta = {
            "character": character_id,
            "voice_description": voice_info.get("voice_description", ""),
            "character_style": voice_info.get("character_style", ""),
            "num_samples": len(encoded_samples),
            "epochs": epochs,
            "final_loss": final_loss,
            "lora_rank": self.config["lora_rank"],
            "lora_alpha": self.config["lora_alpha"],
            "learning_rate": lr,
        }
        with open(adapter_out / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print(f"  Adapter saved to {adapter_out}")

        # Cleanup
        del peft_talker, talker, model, optimizer
        if self.device == "cuda":
            torch.cuda.empty_cache()

        return adapter_out

    def train_all(
        self,
        characters: list[dict],
        skip_existing: bool = True,
    ) -> dict[str, Path]:
        """Train adapters for all characters.

        Args:
            characters: List of character dicts with character_id, voice_design, etc.
            skip_existing: Skip characters that already have trained adapters

        Returns:
            Dict of character_id -> adapter_path
        """
        results: dict[str, Path] = {}

        for char in characters:
            char_id = char.get("character_id", "")
            if not char_id:
                continue

            voice_desc = char.get("voice_design", "")
            if not voice_desc:
                print(f"  SKIP {char_id}: No voice_design in character data")
                continue

            adapter_path = self.adapter_dir / char_id.lower()
            if skip_existing and (adapter_path / "adapter_config.json").exists():
                print(f"  SKIP {char_id}: Adapter already exists at {adapter_path}")
                results[char_id] = adapter_path
                continue

            # Stage 1: Generate training samples
            char_dir = self.generate_training_samples(
                character_id=char_id,
                voice_description=voice_desc,
                character_style=char.get("character_style", ""),
            )

            # Stage 2: Train adapter
            adapter_out = self.train_adapter(
                character_id=char_id,
                training_data_dir=char_dir,
            )
            results[char_id] = adapter_out

        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="LoRA Voice Trainer — fine-tune Qwen3-TTS voice adapters",
    )
    parser.add_argument(
        "--codex", type=str, required=True,
        help="Path to codex JSON file with character data",
    )
    parser.add_argument(
        "--adapter-dir", type=str, default="",
        help="Output directory for adapters (default: forge/{ts}/lora_adapters/)",
    )
    parser.add_argument(
        "--characters", nargs="*", default=None,
        help="Specific character IDs to train (default: all)",
    )
    parser.add_argument(
        "--stage", choices=["generate", "train", "all"], default="all",
        help="Pipeline stage to run (default: all)",
    )
    parser.add_argument(
        "--device", default=TTS_DEVICE, choices=["cuda", "cpu"],
    )
    args = parser.parse_args()

    # Load codex
    codex_path = Path(args.codex)
    if not codex_path.exists():
        print(f"ERROR: Codex not found: {codex_path}")
        return

    with open(codex_path, encoding="utf-8") as f:
        codex = json.load(f)

    characters = codex.get("story", {}).get("characters", [])
    if not characters:
        print("ERROR: No characters in codex")
        return

    # Filter characters if specified
    if args.characters:
        char_ids = set(c.upper() for c in args.characters)
        characters = [c for c in characters if c.get("character_id", "").upper() in char_ids]
        if not characters:
            print(f"ERROR: None of {args.characters} found in codex")
            return

    # Determine adapter directory
    adapter_dir = args.adapter_dir or str(codex_path.parent / "lora_adapters")

    print("=" * 60)
    print("LoRA Voice Trainer")
    print("=" * 60)
    print(f"  Codex: {codex_path}")
    print(f"  Characters: {len(characters)}")
    print(f"  Adapter dir: {adapter_dir}")
    print(f"  Stage: {args.stage}")
    print(f"  Device: {args.device}")

    trainer = LoRAVoiceTrainer(
        adapter_dir=adapter_dir,
        training_config=TTS_LORA_TRAINING_CONFIG,
        device=args.device,
        model_size=TTS_MODEL_SIZE,
    )

    if args.stage == "all":
        results = trainer.train_all(characters)
        print(f"\n  Trained {len(results)} adapters")
        for char_id, path in results.items():
            print(f"    {char_id}: {path}")
    elif args.stage == "generate":
        for char in characters:
            char_id = char.get("character_id", "")
            voice_desc = char.get("voice_design", "")
            if char_id and voice_desc:
                trainer.generate_training_samples(
                    character_id=char_id,
                    voice_description=voice_desc,
                    character_style=char.get("character_style", ""),
                )
    elif args.stage == "train":
        for char in characters:
            char_id = char.get("character_id", "")
            if char_id:
                try:
                    trainer.train_adapter(character_id=char_id)
                except FileNotFoundError as e:
                    print(f"  SKIP {char_id}: {e}")

    print("\n" + "=" * 60)
    print("Training complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
