from typing import Dict, List, Mapping, TypedDict, Union

JsonScalar = Union[str, int, float, bool, None]
JsonValue = Union[JsonScalar, Dict[str, "JsonValue"], List["JsonValue"]]


class WordTimestamp(TypedDict):
    word: str
    start: float


class TranscriptionSegment(TypedDict):
    words: List[WordTimestamp]


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
    word_boundaries: List[WordBoundary]
    original_audio: str
    final_audio: str
    json_path: str
    transcribed_text: str
