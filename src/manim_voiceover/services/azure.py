import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover._typing import JsonValue, VoiceoverData, WordBoundary, json_value
from manim_voiceover.helper import (
    create_dotenv_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service, path_to_string

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[azure]"` to use AzureService.')


load_dotenv(find_dotenv(usecwd=True))


class CancellationDetailsProtocol(Protocol):
    reason: object
    error_details: str | None


class SpeechSynthesisResultProtocol(Protocol):
    reason: object
    cancellation_details: CancellationDetailsProtocol


def _required_int(mapping: Mapping[str, object], key: str) -> int:
    value = mapping[key]
    if isinstance(value, int):
        return value
    raise TypeError(f"{key} must be an int")


def _required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping[key]
    if isinstance(value, str):
        return value
    raise TypeError(f"{key} must be a string")


def _json_value(value: object) -> JsonValue:
    return json_value(value)


def _normalize_prosody(value: object) -> dict[str, JsonValue] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(
            "The prosody argument must be a dict that contains at least one of the following keys: "
            "'pitch', 'contour', 'range', 'rate', 'volume'."
        )
    prosody: dict[str, JsonValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("prosody must map string keys to JSON-compatible values")
        prosody[key] = json_value(item)
    return prosody


def serialize_word_boundary(wb: Mapping[str, object]) -> WordBoundary:
    duration = wb["duration_milliseconds"]
    if not hasattr(duration, "microseconds"):
        raise TypeError("duration_milliseconds must expose microseconds")
    microseconds = getattr(duration, "microseconds")
    if not isinstance(microseconds, int):
        raise TypeError("duration_milliseconds.microseconds must be an int")
    return {
        "audio_offset": _required_int(wb, "audio_offset"),
        "duration_milliseconds": int(microseconds / 1000),
        "text_offset": _required_int(wb, "text_offset"),
        "word_length": _required_int(wb, "word_length"),
        "text": _required_str(wb, "text"),
        "boundary_type": _required_str(wb, "boundary_type"),
    }


def create_dotenv_azure() -> None:
    logger.info(
        "Check out https://voiceover.manim.community/en/stable/services.html#azureservice "
        "to learn how to create an account and get your subscription key."
    )
    if not create_dotenv_file(["AZURE_SUBSCRIPTION_KEY", "AZURE_SERVICE_REGION"]):
        raise Exception(
            "The environment variables AZURE_SUBSCRIPTION_KEY and AZURE_SERVICE_REGION are not set. "
            "Please set them or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()


def _get_azure_credentials() -> tuple[str, str]:
    try:
        return os.environ["AZURE_SUBSCRIPTION_KEY"], os.environ["AZURE_SERVICE_REGION"]
    except KeyError:
        logger.error(
            "Could not find the environment variables AZURE_SUBSCRIPTION_KEY and AZURE_SERVICE_REGION. "
            "Microsoft Azure's text-to-speech API needs account credentials to connect. "
            "You can create an account for free and get a free quota of TTS minutes."
        )
        create_dotenv_azure()
        raise RuntimeError("Azure credentials are unavailable.")


class AzureService(SpeechService):
    """Speech service for Azure TTS API."""

    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        # style="newscast-casual",
        style: str | None = None,
        output_format: str = "Audio48Khz192KBitRateMonoMp3",
        prosody: dict[str, JsonValue] | None = None,
        **kwargs: object,
    ) -> None:
        """
        Args:
            voice (str, optional): The voice to use. Defaults to ``en-US-AriaNeural``.
            style (str, optional): The style to use. Defaults to None.
            output_format (str, optional): The output format to use.
                Defaults to ``Audio48Khz192KBitRateMonoMp3``.
            prosody (dict, optional): Global prosody settings to use. Defaults to None.
        """
        prompt_ask_missing_extras("azure.cognitiveservices.speech", "azure", "AzureService")

        self.voice = voice
        self.style = style
        self.output_format = output_format
        self.prosody = prosody
        initialize_speech_service(self, kwargs)

    def _build_ssml(self, text: str, prosody: dict[str, JsonValue] | None) -> tuple[str, int]:
        ssml_beginning = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">'
            f'<voice name="{self.voice}">'
        )
        ssml_end = "</voice></speak>"

        if prosody is not None:
            prosody_opening_tag = "<prosody " + " ".join([f'{key}="{val}"' for key, val in prosody.items()]) + ">"
            ssml_beginning += prosody_opening_tag
            ssml_end = "</prosody>" + ssml_end

        if self.style is not None:
            ssml_beginning += f'<mstts:express-as style="{self.style}">'
            ssml_end = "</mstts:express-as>" + ssml_end

        return ssml_beginning + text + ssml_end, len(ssml_beginning)

    def _raise_for_canceled_synthesis(self, speech_synthesis_result: SpeechSynthesisResultProtocol) -> None:
        if speech_synthesis_result.reason != speechsdk.ResultReason.Canceled:
            return

        cancellation_details = speech_synthesis_result.cancellation_details
        logger.error("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error and cancellation_details.error_details:
            logger.error("Error details: {}".format(cancellation_details.error_details))
            if "authentication" in cancellation_details.error_details.lower():
                logger.error(
                    "The authentication credentials are invalid. Please check the environment variables "
                    "AZURE_SUBSCRIPTION_KEY and AZURE_SERVICE_REGION."
                )
                logger.info("Would you like to enter new values for the variables in the .env file? [Y/n]")
                if input().lower() in ["y", "yes", ""]:
                    create_dotenv_azure()

        raise Exception("Speech synthesis failed")

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        """"""
        inner = text
        # Remove bookmarks
        inner = remove_bookmarks(inner)
        if cache_dir is None:
            cache_dir = self.cache_dir

        # Apply prosody
        prosody = _normalize_prosody(kwargs.get("prosody", self.prosody))
        ssml, initial_offset = self._build_ssml(inner, prosody)

        input_data: dict[str, JsonValue] = {
            "input_text": text,
            "ssml": ssml,
            "service": "azure",
            "config": {
                "voice": self.voice,
                "style": self.style,
                "output_format": self.output_format,
                "prosody": self.prosody,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path_to_string(path)

        azure_subscription_key, azure_service_region = _get_azure_credentials()

        speech_config = speechsdk.SpeechConfig(
            subscription=azure_subscription_key,
            region=azure_service_region,
        )
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat[self.output_format])
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(Path(cache_dir) / audio_path))

        speech_service = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        word_boundaries: list[Mapping[str, object]] = []
        # speech_synthesizer.bookmark_reached.connect(lambda evt: print(
        #     "Bookmark reached: {}, audio offset: {}ms, bookmark text: {}.".format(evt, evt.audio_offset, evt.text)))

        def process_event(evt: object) -> Mapping[str, object]:
            # print(f'{type(evt)=}')
            result = {label[1:]: val for label, val in evt.__dict__.items()}
            result["boundary_type"] = result["boundary_type"].name
            result["text_offset"] = result["text_offset"] - initial_offset
            return result

        speech_service.synthesis_word_boundary.connect(lambda evt: word_boundaries.append(process_event(evt)))
        speech_synthesis_result = speech_service.speak_ssml_async(ssml).get()

        json_dict: VoiceoverData = {
            "input_text": text,
            "input_data": input_data,
            "ssml": ssml,
            "word_boundaries": [serialize_word_boundary(wb) for wb in word_boundaries],
            "original_audio": audio_path,
        }

        self._raise_for_canceled_synthesis(speech_synthesis_result)

        return json_dict
