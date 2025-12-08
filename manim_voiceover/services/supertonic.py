"""
Supertonic TTS Speech Service for Manim Voiceover

A fast, high-quality offline text-to-speech service using ONNX models.
Models are automatically downloaded from Hugging Face on first use.
"""

import os
from pathlib import Path
from typing import Literal, Optional

import numpy as np
import soundfile as sf

from manim import logger
from manim_voiceover.helper import remove_bookmarks, wav2mp3
from manim_voiceover.services.base import SpeechService

try:
    import onnxruntime as ort
except ImportError:
    logger.error(
        "Missing onnxruntime. Run `pip install onnxruntime` to use SupertonicService."
    )


# Hugging Face model repository
HF_REPO_ID = "Supertone/supertonic"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "supertonic"

# Required model files
ONNX_FILES = [
    "onnx/duration_predictor.onnx",
    "onnx/text_encoder.onnx",
    "onnx/vector_estimator.onnx",
    "onnx/vocoder.onnx",
    "onnx/tts.json",
    "onnx/unicode_indexer.json",
]

VOICE_STYLE_FILES = [
    "voice_styles/M1.json",
    "voice_styles/M2.json",
    "voice_styles/F1.json",
    "voice_styles/F2.json",
]

DEFAULT_VOICE_STYLE = "M1"
VoiceStyle = Literal["M1", "M2", "F1", "F2"]


def _download_models(cache_dir: Path) -> None:
    """Download Supertonic models from Hugging Face Hub."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ImportError(
            "huggingface_hub is required to download models. "
            "Install with: pip install huggingface_hub"
        )

    logger.info(f"Downloading Supertonic models to {cache_dir}...")
    cache_dir.mkdir(parents=True, exist_ok=True)

    all_files = ONNX_FILES + VOICE_STYLE_FILES

    for file_path in all_files:
        local_path = cache_dir / file_path
        if not local_path.exists():
            logger.info(f"  Downloading {file_path}...")
            downloaded = hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=file_path,
                local_dir=cache_dir,
                local_dir_use_symlinks=False,
            )
            logger.info(f"  -> {downloaded}")

    logger.info("Supertonic models downloaded successfully!")


def _ensure_models(cache_dir: Path) -> tuple[Path, Path]:
    """Ensure models are downloaded and return paths to onnx and voice_styles dirs."""
    onnx_dir = cache_dir / "onnx"
    voice_styles_dir = cache_dir / "voice_styles"

    # Check if all required files exist
    all_present = all(
        (cache_dir / f).exists() for f in ONNX_FILES + VOICE_STYLE_FILES
    )

    if not all_present:
        _download_models(cache_dir)

    return onnx_dir, voice_styles_dir


class SupertonicService(SpeechService):
    """Speech service using Supertonic TTS (ONNX-based).

    A fast, high-quality offline text-to-speech service with multiple voice styles.
    Models are automatically downloaded from Hugging Face on first use (~250MB).

    Args:
        voice_style (str): Voice style to use. Options: "M1", "M2", "F1", "F2"
            (M = male, F = female, 1/2 are style variants). Default: "M1".
        total_step (int): Number of denoising steps (higher = better quality, slower).
            Default: 5. Recommended range: 3-10.
        speed (float): Speech speed multiplier. Default: 1.05.
            Values < 1.0 slow down, > 1.0 speed up.
        silence_duration (float): Duration of silence between text chunks (seconds).
            Default: 0.3
        use_gpu (bool): Whether to use GPU for inference. Default: False (CPU).
        model_cache_dir (str, optional): Directory to cache downloaded models.
            Defaults to ~/.cache/supertonic
        **kwargs: Additional arguments passed to SpeechService.

    Example:
        >>> from manim_voiceover.services.supertonic import SupertonicService
        >>> # Basic usage - models auto-download on first use
        >>> service = SupertonicService()
        >>>
        >>> # With custom voice and settings
        >>> service = SupertonicService(
        ...     voice_style="F1",  # Female voice
        ...     total_step=5,
        ...     speed=1.0,
        ... )
    """

    def __init__(
        self,
        voice_style: VoiceStyle = DEFAULT_VOICE_STYLE,
        total_step: int = 5,
        speed: float = 1.05,
        silence_duration: float = 0.3,
        use_gpu: bool = False,
        model_cache_dir: Optional[str] = None,
        **kwargs,
    ):
        self.voice_style_name = voice_style
        self.total_step = total_step
        self.speed = speed
        self.silence_duration = silence_duration
        self.use_gpu = use_gpu

        # Set up model cache directory
        if model_cache_dir is not None:
            self.model_cache_dir = Path(model_cache_dir)
        else:
            self.model_cache_dir = DEFAULT_CACHE_DIR

        # Ensure models are downloaded and get paths
        self.onnx_dir, self.voice_styles_dir = _ensure_models(self.model_cache_dir)

        # Load TTS components
        self._load_tts()
        self._load_voice_style(voice_style)

        self.init_kwargs = kwargs
        SpeechService.__init__(self, **kwargs)

    def _load_tts(self):
        """Load all ONNX models and configuration."""
        import json

        # Load configuration
        cfg_path = self.onnx_dir / "tts.json"
        with open(cfg_path, "r") as f:
            self.cfgs = json.load(f)

        # Load unicode indexer
        unicode_indexer_path = self.onnx_dir / "unicode_indexer.json"
        with open(unicode_indexer_path, "r") as f:
            self.unicode_indexer = json.load(f)

        # Set up ONNX runtime
        opts = ort.SessionOptions()
        if self.use_gpu:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            logger.info("SupertonicService: Using GPU for inference")
        else:
            providers = ["CPUExecutionProvider"]
            logger.info("SupertonicService: Using CPU for inference")

        # Load all ONNX models
        self.dp_ort = ort.InferenceSession(
            str(self.onnx_dir / "duration_predictor.onnx"),
            sess_options=opts,
            providers=providers,
        )
        self.text_enc_ort = ort.InferenceSession(
            str(self.onnx_dir / "text_encoder.onnx"),
            sess_options=opts,
            providers=providers,
        )
        self.vector_est_ort = ort.InferenceSession(
            str(self.onnx_dir / "vector_estimator.onnx"),
            sess_options=opts,
            providers=providers,
        )
        self.vocoder_ort = ort.InferenceSession(
            str(self.onnx_dir / "vocoder.onnx"),
            sess_options=opts,
            providers=providers,
        )

        # Extract config values
        self.sample_rate = self.cfgs["ae"]["sample_rate"]
        self.base_chunk_size = self.cfgs["ae"]["base_chunk_size"]
        self.chunk_compress_factor = self.cfgs["ttl"]["chunk_compress_factor"]
        self.ldim = self.cfgs["ttl"]["latent_dim"]

        logger.info(f"SupertonicService: Loaded TTS model (sample_rate={self.sample_rate})")

    def _load_voice_style(self, voice_style: VoiceStyle):
        """Load a voice style from JSON file."""
        import json

        voice_style_path = self.voice_styles_dir / f"{voice_style}.json"
        if not voice_style_path.exists():
            raise FileNotFoundError(
                f"Voice style '{voice_style}' not found at {voice_style_path}. "
                f"Available styles: M1, M2, F1, F2"
            )

        with open(voice_style_path, "r") as f:
            voice_data = json.load(f)

        # Extract style vectors
        ttl_dims = voice_data["style_ttl"]["dims"]
        dp_dims = voice_data["style_dp"]["dims"]

        ttl_data = np.array(voice_data["style_ttl"]["data"], dtype=np.float32).flatten()
        self.style_ttl = ttl_data.reshape(1, ttl_dims[1], ttl_dims[2])

        dp_data = np.array(voice_data["style_dp"]["data"], dtype=np.float32).flatten()
        self.style_dp = dp_data.reshape(1, dp_dims[1], dp_dims[2])

        logger.info(f"SupertonicService: Loaded voice style '{voice_style}'")

    def _preprocess_text(self, text: str) -> str:
        """Normalize unicode text."""
        from unicodedata import normalize
        return normalize("NFKD", text)

    def _text_to_ids(self, text_list: list[str]) -> tuple[np.ndarray, np.ndarray]:
        """Convert text to unicode IDs with mask."""
        text_list = [self._preprocess_text(t) for t in text_list]
        text_ids_lengths = np.array([len(text) for text in text_list], dtype=np.int64)
        text_ids = np.zeros((len(text_list), text_ids_lengths.max()), dtype=np.int64)

        for i, text in enumerate(text_list):
            unicode_vals = [ord(char) for char in text]
            # unicode_indexer is a list where index = unicode codepoint, value = token id
            text_ids[i, : len(unicode_vals)] = np.array(
                [self.unicode_indexer[val] for val in unicode_vals], dtype=np.int64
            )

        # Create mask
        max_len = text_ids_lengths.max()
        ids = np.arange(0, max_len)
        mask = (ids < np.expand_dims(text_ids_lengths, axis=1)).astype(np.float32)
        text_mask = mask.reshape(-1, 1, max_len)

        return text_ids, text_mask

    def _sample_noisy_latent(self, duration: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Sample noisy latent vectors for diffusion."""
        bsz = len(duration)
        wav_len_max = duration.max() * self.sample_rate
        wav_lengths = (duration * self.sample_rate).astype(np.int64)
        chunk_size = self.base_chunk_size * self.chunk_compress_factor
        latent_len = ((wav_len_max + chunk_size - 1) / chunk_size).astype(np.int32)
        latent_dim = self.ldim * self.chunk_compress_factor
        noisy_latent = np.random.randn(bsz, latent_dim, latent_len).astype(np.float32)

        # Create latent mask
        latent_size = self.base_chunk_size * self.chunk_compress_factor
        latent_lengths = (wav_lengths + latent_size - 1) // latent_size
        max_latent_len = latent_lengths.max()
        ids = np.arange(0, max_latent_len)
        latent_mask = (ids < np.expand_dims(latent_lengths, axis=1)).astype(np.float32)
        latent_mask = latent_mask.reshape(-1, 1, max_latent_len)

        noisy_latent = noisy_latent * latent_mask
        return noisy_latent, latent_mask

    def _infer_single(self, text: str) -> tuple[np.ndarray, float]:
        """Run inference for a single text chunk."""
        text_ids, text_mask = self._text_to_ids([text])

        # Duration prediction
        dur_onnx, *_ = self.dp_ort.run(
            None, {"text_ids": text_ids, "style_dp": self.style_dp, "text_mask": text_mask}
        )
        dur_onnx = dur_onnx / self.speed

        # Text encoding
        text_emb_onnx, *_ = self.text_enc_ort.run(
            None,
            {"text_ids": text_ids, "style_ttl": self.style_ttl, "text_mask": text_mask},
        )

        # Sample noisy latent
        xt, latent_mask = self._sample_noisy_latent(dur_onnx)

        # Diffusion denoising steps
        total_step_np = np.array([self.total_step], dtype=np.float32)
        for step in range(self.total_step):
            current_step = np.array([step], dtype=np.float32)
            xt, *_ = self.vector_est_ort.run(
                None,
                {
                    "noisy_latent": xt,
                    "text_emb": text_emb_onnx,
                    "style_ttl": self.style_ttl,
                    "text_mask": text_mask,
                    "latent_mask": latent_mask,
                    "current_step": current_step,
                    "total_step": total_step_np,
                },
            )

        # Vocoder
        wav, *_ = self.vocoder_ort.run(None, {"latent": xt})
        return wav[0], float(dur_onnx[0])

    def _chunk_text(self, text: str, max_len: int = 300) -> list[str]:
        """Split text into chunks by sentences."""
        import re

        # Split by paragraph
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text.strip()) if p.strip()]

        chunks = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Split by sentence boundaries
            pattern = r"(?<!Mr\.)(?<!Mrs\.)(?<!Ms\.)(?<!Dr\.)(?<!Prof\.)(?<!Sr\.)(?<!Jr\.)(?<!Ph\.D\.)(?<!etc\.)(?<!e\.g\.)(?<!i\.e\.)(?<!vs\.)(?<!Inc\.)(?<!Ltd\.)(?<!Co\.)(?<!Corp\.)(?<!St\.)(?<!Ave\.)(?<!Blvd\.)(?<!\b[A-Z]\.)(?<=[.!?])\s+"
            sentences = re.split(pattern, paragraph)

            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= max_len:
                    current_chunk += (" " if current_chunk else "") + sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence

            if current_chunk:
                chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def _synthesize(self, text: str) -> np.ndarray:
        """Synthesize speech from text, handling long texts by chunking."""
        text_chunks = self._chunk_text(text)

        all_audio = []
        silence_samples = int(self.silence_duration * self.sample_rate)

        for i, chunk in enumerate(text_chunks):
            wav, _ = self._infer_single(chunk)

            if i > 0 and silence_samples > 0:
                silence = np.zeros(silence_samples, dtype=np.float32)
                all_audio.append(silence)

            all_audio.append(wav)

        return np.concatenate(all_audio) if len(all_audio) > 1 else all_audio[0]

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """Generate speech from text.

        Args:
            text: The text to synthesize.
            cache_dir: Directory to cache audio files.
            path: Optional specific path for the audio file.
            **kwargs: Additional arguments (unused).

        Returns:
            Dictionary containing input data and audio path.
        """
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": text,
            "service": "supertonic",
            "voice_style": self.voice_style_name,
            "total_step": self.total_step,
            "speed": self.speed,
        }

        # Check cache
        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        # Generate audio path
        if path is None:
            audio_path = self.get_data_hash(input_data) + ".mp3"
        else:
            audio_path = path

        output_path = Path(cache_dir) / audio_path
        wav_path = output_path.with_suffix(".wav")

        # Synthesize
        logger.info(f"SupertonicService: Synthesizing '{input_text[:50]}...'")
        audio = self._synthesize(input_text)

        # Save as WAV then convert to MP3
        sf.write(str(wav_path), audio, self.sample_rate)
        wav2mp3(wav_path, str(output_path))

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict

    def set_voice_style(self, voice_style: VoiceStyle):
        """Change the voice style.

        Args:
            voice_style: New voice style ("M1", "M2", "F1", or "F2").
        """
        self._load_voice_style(voice_style)
        self.voice_style_name = voice_style
