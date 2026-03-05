"""
Qwen3-TTS Engine — Direct local GPU inference for audiobook narration.

Replaces ComfyUI-based TTS with direct Python calls to the qwen-tts library.
Supports three voice modes:
- CustomVoice: 9 preset voices with instruct-based emotion/tone control
- VoiceDesign: Generate unlimited unique voices from text descriptions
- VoiceClone: Clone any voice from a 3-60 second reference audio file

Architecture:
- Models are loaded once and reused across all generations
- Voice clone prompts are cached per character for consistency
- Audio chunks are concatenated with configurable pauses between speakers
"""

import time
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

# Lazy imports for heavy dependencies (torch, qwen_tts)
# These are imported at model load time to avoid slow startup
_Qwen3TTSModel = None
_torch = None


def _lazy_import():
    """Lazy-import torch and qwen_tts to avoid slow startup."""
    global _Qwen3TTSModel, _torch
    if _Qwen3TTSModel is None:
        import torch
        from qwen_tts import Qwen3TTSModel
        _Qwen3TTSModel = Qwen3TTSModel
        _torch = torch


# ---------------------------------------------------------------------------
# Voice configuration types
# ---------------------------------------------------------------------------

class VoiceConfig:
    """Base voice configuration."""
    pass


class CustomVoiceConfig(VoiceConfig):
    """Use a built-in CustomVoice preset with instruct support."""

    def __init__(self, speaker: str = "Ryan"):
        self.type = "custom"
        self.speaker = speaker


class CloneVoiceConfig(VoiceConfig):
    """Clone a voice from a reference audio file."""

    def __init__(self, ref_audio: str, ref_text: str = ""):
        self.type = "clone"
        self.ref_audio = ref_audio
        self.ref_text = ref_text


class DesignVoiceConfig(VoiceConfig):
    """Design a voice from a text description, then freeze as clone prompt."""

    def __init__(self, description: str, sample_text: str = ""):
        self.type = "design"
        self.description = description
        self.sample_text = sample_text or "Hello, welcome to the story."


# ---------------------------------------------------------------------------
# Main TTS Engine
# ---------------------------------------------------------------------------

class QwenTTSEngine:
    """Direct Qwen3-TTS inference engine."""

    def __init__(
        self,
        device: str = "cuda",
        precision: str = "bfloat16",
        model_size: str = "1.7B",
        narrator_voice: Optional[VoiceConfig] = None,
        narration_mode: str = "single_narrator",
        pause_between_speakers_ms: int = 500,
        pause_within_speaker_ms: int = 250,
    ):
        """
        Initialize the TTS engine.

        Args:
            device: "cuda", "cpu", or "auto"
            precision: "bfloat16", "float16", or "float32"
            model_size: "1.7B" or "0.6B"
            narrator_voice: Voice config for the narrator
            narration_mode: "single_narrator" or "multi_cast"
            pause_between_speakers_ms: Silence between different speakers
            pause_within_speaker_ms: Silence between same speaker entries
        """
        self.device = device
        self.precision = precision
        self.model_size = model_size
        self.narrator_voice = narrator_voice or CustomVoiceConfig("Ryan")
        self.narration_mode = narration_mode
        self.pause_between_speakers_ms = pause_between_speakers_ms
        self.pause_within_speaker_ms = pause_within_speaker_ms

        # Models (loaded lazily)
        self._custom_voice_model = None
        self._base_model = None
        self._design_model = None

        # Voice cache: character name -> clone prompt
        self._voice_cache: dict[str, object] = {}

        # Sample rate (set after first generation)
        self._sample_rate: int = 24000  # Qwen3-TTS default

    def _get_dtype(self):
        """Get torch dtype from string."""
        _lazy_import()
        dtypes = {
            "bfloat16": _torch.bfloat16,
            "float16": _torch.float16,
            "float32": _torch.float32,
        }
        return dtypes.get(self.precision, _torch.bfloat16)

    def _get_model_id(self, variant: str) -> str:
        """Get HuggingFace model ID for a variant."""
        return f"Qwen/Qwen3-TTS-12Hz-{self.model_size}-{variant}"

    def _get_attn_impl(self) -> str:
        """Get best attention implementation for the device."""
        if self.device == "cpu":
            return "sdpa"
        try:
            import flash_attn  # noqa: F401
            return "flash_attention_2"
        except ImportError:
            return "sdpa"

    def _load_custom_voice_model(self):
        """Load the CustomVoice model (9 presets with instruct)."""
        if self._custom_voice_model is not None:
            return
        _lazy_import()
        print(f"    Loading CustomVoice model ({self.model_size})...")
        start = time.time()
        self._custom_voice_model = _Qwen3TTSModel.from_pretrained(
            self._get_model_id("CustomVoice"),
            device_map=f"{self.device}:0" if self.device == "cuda" else self.device,
            dtype=self._get_dtype(),
            attn_implementation=self._get_attn_impl(),
        )
        print(f"    CustomVoice model loaded in {time.time() - start:.1f}s")

    def _load_base_model(self):
        """Load the Base model (voice cloning)."""
        if self._base_model is not None:
            return
        _lazy_import()
        print(f"    Loading Base model ({self.model_size})...")
        start = time.time()
        self._base_model = _Qwen3TTSModel.from_pretrained(
            self._get_model_id("Base"),
            device_map=f"{self.device}:0" if self.device == "cuda" else self.device,
            dtype=self._get_dtype(),
            attn_implementation=self._get_attn_impl(),
        )
        print(f"    Base model loaded in {time.time() - start:.1f}s")

    def _load_design_model(self):
        """Load the VoiceDesign model (text description -> voice)."""
        if self._design_model is not None:
            return
        _lazy_import()
        # VoiceDesign only available in 1.7B
        print("    Loading VoiceDesign model (1.7B)...")
        start = time.time()
        self._design_model = _Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            device_map=f"{self.device}:0" if self.device == "cuda" else self.device,
            dtype=self._get_dtype(),
            attn_implementation=self._get_attn_impl(),
        )
        print(f"    VoiceDesign model loaded in {time.time() - start:.1f}s")

    def design_character_voice(
        self,
        description: str,
        sample_text: str = "Hello, welcome to the story.",
        language: str = "English",
    ) -> object:
        """
        Design a unique voice from a text description, then create a
        reusable clone prompt for consistency across all lines.

        Args:
            description: Natural language voice description
                e.g. "Gruff old man, deep gravelly baritone, slow and deliberate"
            sample_text: Sample text to generate the reference audio
            language: Language for generation

        Returns:
            Reusable voice_clone_prompt object
        """
        # Step 1: Generate reference audio with VoiceDesign
        self._load_design_model()
        wavs, sr = self._design_model.generate_voice_design(
            text=sample_text,
            language=language,
            instruct=description,
        )

        # Step 2: Convert to reusable clone prompt via Base model
        self._load_base_model()
        clone_prompt = self._base_model.create_voice_clone_prompt(
            ref_audio=(wavs[0], sr),
            ref_text=sample_text,
        )

        return clone_prompt

    def create_clone_from_file(
        self,
        audio_path: str,
        transcript: str = "",
    ) -> object:
        """
        Create a reusable clone prompt from a reference audio file.

        Args:
            audio_path: Path to reference audio (WAV, MP3, M4A)
            transcript: Transcription of the reference audio

        Returns:
            Reusable voice_clone_prompt object
        """
        self._load_base_model()
        use_xvec_only = not transcript.strip()
        if use_xvec_only:
            print(f"        [clone] No ref_text — using x_vector_only mode (speaker embedding)")
        clone_prompt = self._base_model.create_voice_clone_prompt(
            ref_audio=audio_path,
            ref_text=transcript if not use_xvec_only else None,
            x_vector_only_mode=use_xvec_only,
        )
        return clone_prompt

    def _generate_custom_voice_chunk(
        self,
        text: str,
        speaker: str,
        instruct: str,
        language: str = "English",
    ) -> tuple[np.ndarray, int]:
        """Generate audio using CustomVoice preset with instruct."""
        self._load_custom_voice_model()
        wavs, sr = self._custom_voice_model.generate_custom_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct,
        )
        self._sample_rate = sr
        return wavs[0], sr

    def _generate_clone_chunk(
        self,
        text: str,
        clone_prompt: object,
        language: str = "English",
    ) -> tuple[np.ndarray, int]:
        """Generate audio using a cached clone prompt."""
        self._load_base_model()
        wavs, sr = self._base_model.generate_voice_clone(
            text=text,
            language=language,
            voice_clone_prompt=clone_prompt,
        )
        self._sample_rate = sr
        return wavs[0], sr

    def generate_chunk(
        self,
        text: str,
        speaker: str,
        instruct: str,
        voice_config: VoiceConfig,
        language: str = "English",
    ) -> tuple[np.ndarray, int]:
        """
        Generate audio for a single script chunk.

        Args:
            text: Text to synthesize
            speaker: Speaker name (for logging)
            instruct: Voice direction for TTS
            voice_config: Voice configuration (Custom, Clone, or Design)
            language: Language for generation

        Returns:
            (audio_array, sample_rate)
        """
        if isinstance(voice_config, CustomVoiceConfig):
            return self._generate_custom_voice_chunk(
                text=text,
                speaker=voice_config.speaker,
                instruct=instruct,
                language=language,
            )
        elif isinstance(voice_config, CloneVoiceConfig):
            # Get or create clone prompt
            cache_key = f"clone:{voice_config.ref_audio}"
            if cache_key not in self._voice_cache:
                self._voice_cache[cache_key] = self.create_clone_from_file(
                    audio_path=voice_config.ref_audio,
                    transcript=voice_config.ref_text,
                )
            return self._generate_clone_chunk(
                text=text,
                clone_prompt=self._voice_cache[cache_key],
                language=language,
            )
        else:
            # Fallback to CustomVoice Ryan
            return self._generate_custom_voice_chunk(
                text=text,
                speaker="Ryan",
                instruct=instruct,
                language=language,
            )

    def _create_silence(self, duration_ms: int) -> np.ndarray:
        """Create a silence array of the given duration."""
        num_samples = int(self._sample_rate * duration_ms / 1000)
        return np.zeros(num_samples, dtype=np.float32)

    def _trim_silence(self, audio: np.ndarray, top_db: float = 40.0) -> np.ndarray:
        """Trim leading/trailing silence from a chunk."""
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

    def _apply_edge_fade(self, audio: np.ndarray, fade_ms: float = 5.0) -> np.ndarray:
        """Apply tiny fade-in/out to prevent click artifacts at joins."""
        fade_samples = min(int(self._sample_rate * fade_ms / 1000), len(audio) // 2)
        if fade_samples < 2:
            return audio
        audio = audio.copy()
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples).astype(np.float32)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples).astype(np.float32)
        return audio

    def _normalize_chunk(self, audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
        """Normalize chunk loudness to target dBFS."""
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 1e-10:
            return audio
        target_rms = 10 ** (target_dbfs / 20)
        return (audio * (target_rms / rms)).astype(np.float32)

    def setup_voice_map(
        self,
        characters: list[dict],
        narrator_config: Optional[VoiceConfig] = None,
    ) -> dict[str, VoiceConfig]:
        """
        Build a voice map for all characters based on narration mode.

        Args:
            characters: Character list from codex
            narrator_config: Override narrator voice config

        Returns:
            Dict mapping character_id (or NARRATOR) -> VoiceConfig
        """
        narrator = narrator_config or self.narrator_voice
        voice_map: dict[str, VoiceConfig] = {"NARRATOR": narrator}

        if self.narration_mode == "single_narrator":
            # All speakers use the same narrator voice
            for char in characters:
                char_key = char.get("character_id", char.get("name", "").upper().replace(" ", "_"))
                if char_key:
                    voice_map[char_key] = narrator
        else:
            # multi_cast: design unique voices per character
            # Voice descriptions follow Alexandria formula: [register] + [tonal character]
            # Minimal, acoustically-precise descriptions produce more consistent voices.
            for char in characters:
                char_key = char.get("character_id", char.get("name", "").upper().replace(" ", "_"))
                if not char_key:
                    continue

                # Check for explicit voice description in codex
                phys = char.get("physical_appearance", char.get("physical", {}))
                voice_desc = ""
                if isinstance(phys, dict):
                    voice_desc = phys.get("voice", "")

                if not voice_desc:
                    # Build from character data: [gender register] + [tonal character]
                    gender = char.get("gender", "").lower()
                    role = char.get("role", char.get("role_in_story", "")).lower()

                    # Map gender to vocal register
                    if gender == "male":
                        register = "male baritone"
                    elif gender == "female":
                        register = "female mezzo-soprano"
                    else:
                        register = "androgynous mid-range"

                    # Map role to tonal character
                    if "antagonist" in role or "villain" in role:
                        tone = "dark, commanding edge"
                    elif "protagonist" in role:
                        tone = "grounded, firm presence"
                    else:
                        tone = "clear, balanced delivery"

                    voice_desc = f"{register}, {tone}"

                # Create a design config (will be converted to clone at first use)
                voice_map[char_key] = DesignVoiceConfig(
                    description=voice_desc,
                    sample_text=f"Hello, my name is {char.get('name', 'unknown')}.",
                )

        return voice_map

    def _resolve_voice(
        self,
        speaker: str,
        voice_config: VoiceConfig,
    ) -> VoiceConfig:
        """
        Resolve a DesignVoiceConfig into a cached clone config.
        CustomVoice and Clone configs pass through unchanged.
        """
        if not isinstance(voice_config, DesignVoiceConfig):
            return voice_config

        cache_key = f"design:{speaker}"
        if cache_key not in self._voice_cache:
            print(f"        Designing voice for {speaker}...")
            clone_prompt = self.design_character_voice(
                description=voice_config.description,
                sample_text=voice_config.sample_text,
            )
            self._voice_cache[cache_key] = clone_prompt

        # Return a special config that uses the cached clone prompt
        # We'll handle this in generate_chunk by checking the cache
        return voice_config

    def generate_scene_audio(
        self,
        audio_script: list[dict],
        voice_map: dict[str, VoiceConfig],
        output_path: Path,
        language: str = "English",
    ) -> tuple[bool, float]:
        """
        Generate audio for an entire scene from its audio script.

        Iterates through script chunks, generates audio for each,
        adds appropriate pauses, and concatenates into a single file.

        Args:
            audio_script: List of {speaker, text, instruct} dicts
            voice_map: Speaker name -> VoiceConfig mapping
            output_path: Path to write the output WAV file
            language: Language for generation

        Returns:
            (success, duration_seconds)
        """
        if not audio_script:
            return False, 0.0

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio_segments: list[np.ndarray] = []
        prev_speaker = None
        total_chunks = len(audio_script)

        for idx, chunk in enumerate(audio_script):
            speaker = chunk["speaker"]
            text = chunk["text"]
            instruct = chunk.get("instruct", "Neutral, even narration.")

            # Add pause between chunks
            if prev_speaker is not None:
                if speaker != prev_speaker:
                    audio_segments.append(
                        self._create_silence(self.pause_between_speakers_ms)
                    )
                else:
                    audio_segments.append(
                        self._create_silence(self.pause_within_speaker_ms)
                    )

            # Get voice config for this speaker
            voice_config = voice_map.get(speaker, voice_map.get("NARRATOR", self.narrator_voice))

            # Resolve design voices to clone prompts
            voice_config = self._resolve_voice(speaker, voice_config)

            # Generate audio
            try:
                if isinstance(voice_config, DesignVoiceConfig):
                    # Use cached clone prompt
                    cache_key = f"design:{speaker}"
                    if cache_key in self._voice_cache:
                        wav, sr = self._generate_clone_chunk(
                            text=text,
                            clone_prompt=self._voice_cache[cache_key],
                            language=language,
                        )
                    else:
                        # Fallback to CustomVoice
                        wav, sr = self._generate_custom_voice_chunk(
                            text=text,
                            speaker="Ryan",
                            instruct=instruct,
                            language=language,
                        )
                else:
                    wav, sr = self.generate_chunk(
                        text=text,
                        speaker=speaker,
                        instruct=instruct,
                        voice_config=voice_config,
                        language=language,
                    )

                # Post-process: trim silence, fade edges, normalize volume
                wav = self._trim_silence(wav)
                wav = self._apply_edge_fade(wav)
                wav = self._normalize_chunk(wav)
                audio_segments.append(wav)
                print(f"        [{idx + 1}/{total_chunks}] {speaker}: {len(text)} chars -> {len(wav) / sr:.1f}s")

            except Exception as e:
                print(f"        [{idx + 1}/{total_chunks}] {speaker}: ERROR - {e}")
                # Add a short silence as placeholder
                audio_segments.append(self._create_silence(500))

            prev_speaker = speaker

        if not audio_segments:
            return False, 0.0

        # Check if we got any real audio (not just error silence placeholders)
        real_chunks = sum(1 for seg in audio_segments if np.max(np.abs(seg)) > 1e-6)
        if real_chunks == 0:
            print(f"        All {total_chunks} chunks failed — no audio generated")
            return False, 0.0

        # Concatenate all segments
        combined = np.concatenate(audio_segments)
        duration = len(combined) / self._sample_rate

        # Write WAV file
        sf.write(str(output_path), combined, self._sample_rate)
        print(f"        -> {output_path.name} ({duration:.1f}s)")

        return True, duration

    def close(self):
        """Unload models to free VRAM."""
        self._custom_voice_model = None
        self._base_model = None
        self._design_model = None
        self._voice_cache.clear()
        if _torch is not None:
            _torch.cuda.empty_cache()
