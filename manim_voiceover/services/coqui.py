import importlib
import typing as t
from pathlib import Path
from typing import Optional

from manim_voiceover._typing import VoiceoverData
from manim_voiceover.helper import prompt_ask_missing_package, remove_bookmarks, wav2mp3
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string


class CoquiTTS(t.Protocol):
    speakers: Optional[t.Sequence[str]]
    languages: Optional[t.Sequence[str]]

    def tts_to_file(
        self,
        text: str,
        speaker: Optional[str],
        language: Optional[str],
        file_path: Path,
    ) -> None: ...


# DEFAULT_MODEL = TTS.list_models()[0]
DEFAULT_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"


class CoquiService(SpeechService):
    """Speech service for Coqui TTS.
    Default model: ``tts_models/en/ljspeech/tacotron2-DDC``.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        config_path: Optional[str] = None,
        vocoder_path: Optional[str] = None,
        vocoder_config_path: Optional[str] = None,
        progress_bar: bool = True,
        gpu: bool = False,
        speaker_idx: int = 0,
        language_idx: int = 0,
        **kwargs: object,
    ) -> None:
        prompt_ask_missing_package("TTS", "TTS>=0.13.3")
        tts_module = importlib.import_module("TTS.api")
        tts_factory = getattr(tts_module, "TTS")
        # pragma: no mutate start
        self.tts = t.cast(
            CoquiTTS,
            tts_factory(
                model_name=model_name,
                config_path=config_path,
                vocoder_path=vocoder_path,
                vocoder_config_path=vocoder_config_path,
                progress_bar=progress_bar,
                gpu=gpu,
            ),
        )
        # pragma: no mutate end

        # Run TTS
        self.speaker = self.tts.speakers[speaker_idx] if self.tts.speakers is not None else None
        self.language = self.tts.languages[language_idx] if self.tts.languages is not None else None

        self.init_kwargs = kwargs
        initialize_speech_service(self, kwargs)

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[PathLike] = None,
        path: Optional[PathLike] = None,
        **kwargs: object,
    ) -> VoiceoverData:
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {"input_text": text, "service": "coqui"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        output_path = str(Path(cache_dir) / audio_path)
        wav_path = Path(output_path).with_suffix(".wav")

        # Text to speech to a file
        self.tts.tts_to_file(
            text=input_text,
            speaker=self.speaker,
            language=self.language,
            file_path=wav_path,
        )
        wav2mp3(wav_path, output_path)

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            # "word_boundaries": word_boundaries,
        }

        return json_dict
