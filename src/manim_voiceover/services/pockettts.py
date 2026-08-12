from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from manim import logger
from scipy.io import wavfile

from manim_voiceover._typing import JsonValue, VoiceoverData
from manim_voiceover.helper import prompt_ask_missing_extras, remove_bookmarks
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string

try:
    from pocket_tts import TTSModel
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[pockettts]"` to use PocketTTSService.')

if TYPE_CHECKING:
    import torch

# Mirrors pocket_tts.utils.utils._ORIGINS_OF_PREDEFINED_VOICES's keys: the
# built-in voice names that can be passed as `voice` without needing an audio
# file, URL, or .safetensors embedding. Kept in sync manually since it isn't
# exported from the package.
POCKETTTS_AVAILABLE_VOICES = (
    "alba",
    "anna",
    "azelma",
    "bill_boerst",
    "caro_davy",
    "charles",
    "cosette",
    "eponine",
    "estelle",
    "eve",
    "fantine",
    "george",
    "giovanni",
    "jane",
    "jean",
    "javert",
    "juergen",
    "lola",
    "marius",
    "mary",
    "michael",
    "paul",
    "peter_yearsley",
    "rafael",
    "stuart_bell",
    "vera",
)

# Mirrors pocket_tts.default_parameters.DEFAULT_VOICE_FOR_LANGUAGE / _FALLBACK,
# which is how the upstream `pocket-tts generate` CLI picks a voice when none
# is given. Kept in sync manually since it isn't exported from the package.
DEFAULT_POCKETTTS_VOICE_FALLBACK = "alba"
DEFAULT_POCKETTTS_VOICE_FOR_LANGUAGE = {
    "italian": "giovanni",
    "spanish": "lola",
    "german": "juergen",
    "portuguese": "rafael",
    "french": "estelle",
}


def _default_voice_for_language(language: str | None) -> str:
    if language is not None:
        for key, voice in DEFAULT_POCKETTTS_VOICE_FOR_LANGUAGE.items():
            if key in language:
                return voice
    return DEFAULT_POCKETTTS_VOICE_FALLBACK


def _write_wave_file(path: Path, audio: torch.Tensor, sample_rate: int) -> None:
    # generate_audio() returns a [channels, samples] tensor; Pocket TTS is
    # single-speaker mono, so squeeze the channel dimension before writing,
    # otherwise scipy would interpret each sample as its own channel.
    samples = audio.detach().cpu().numpy().squeeze()
    wavfile.write(str(path), sample_rate, samples)


class PocketTTSService(SpeechService):
    """Speech service class for `Kyutai's Pocket TTS <https://github.com/kyutai-labs/pocket-tts>`__.

    Pocket TTS is a small (100M parameter) text-to-speech model that runs fully
    locally on CPU, so it needs neither a GPU nor an API key. It returns raw PCM
    audio, which this service writes as a mono WAV file.
    """

    def __init__(
        self,
        voice: str | None = None,
        language: str | None = None,
        quantize: bool = False,
        transcription_model: str | None = None,
        **kwargs: object,
    ) -> None:
        """
        Args:
            voice (str, optional): Which voice to use. Either one of the built-in
                voice names in :data:`POCKETTTS_AVAILABLE_VOICES` (e.g. ``"charles"``),
                or a path, HTTP(S) URL, or ``hf://`` URL to a custom audio prompt (or a
                ``.safetensors`` voice embedding) to clone a voice from. Defaults to
                None, which selects a built-in voice appropriate for `language`
                (``"alba"`` for English).
            language (str, optional): Which pretrained Pocket TTS config to load, e.g.
                ``"french_24l"``. Defaults to None, which loads the default English model.
            quantize (bool, optional): Apply dynamic int8 quantization to the model to
                reduce memory usage and speed up inference. Defaults to False.
        """
        prompt_ask_missing_extras("pocket_tts", "pockettts", "PocketTTSService")

        self.voice = voice
        self.language = language
        self.quantize = quantize
        initialize_speech_service(self, kwargs, transcription_model=transcription_model)
        self.model = TTSModel.load_model(language=language, quantize=quantize)
        self._voice_states: dict[str, dict[str, object]] = {}

    def _get_voice_state(self) -> dict[str, object]:
        voice = self.voice if self.voice is not None else _default_voice_for_language(self.language)
        if voice not in self._voice_states:
            self._voice_states[voice] = self.model.get_state_for_audio_prompt(voice)
        return self._voice_states[voice]

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """"""
        cache_dir = self.cache_dir if cache_dir is None else cache_dir

        input_text = remove_bookmarks(text)
        input_data = self._input_data(input_text)

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".wav"
        else:
            audio_path = path_to_string(path)

        audio = self.model.generate_audio(self._get_voice_state(), input_text)
        _write_wave_file(Path(cache_dir) / audio_path, audio, self.model.sample_rate)

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict

    def _input_data(self, input_text: str) -> dict[str, JsonValue]:
        return {
            "input_text": input_text,
            "service": "pockettts",
            "config": {
                "voice": self.voice,
                "language": self.language,
                "quantize": self.quantize,
            },
        }
