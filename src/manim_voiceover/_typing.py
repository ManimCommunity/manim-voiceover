from collections.abc import Mapping
from typing import TypedDict

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | dict[str, "JsonValue"] | list["JsonValue"]


def json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        output: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            output[key] = json_value(item)
        return output
    raise TypeError("value must be JSON-compatible")


def json_object(value: Mapping[str, object]) -> dict[str, JsonValue]:
    output: dict[str, JsonValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("JSON object keys must be strings")
        output[key] = json_value(item)
    return output


class WordTimestamp(TypedDict):
    word: str
    start: float


class TranscriptionSegment(TypedDict):
    words: list[WordTimestamp]


class WordBoundary(TypedDict, total=False):
    audio_offset: int
    duration_milliseconds: int
    text_offset: int
    word_length: int
    text: str
    boundary_type: str


class VoiceoverData(TypedDict, total=False):
    input_text: str
    input_data: Mapping[str, JsonValue]
    ssml: str
    word_boundaries: list[WordBoundary]
    original_audio: str
    final_audio: str
    json_path: str
    transcribed_text: str
