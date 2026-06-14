import json
import os
import typing as t
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic import JsonValue as PydanticJsonValue

from manim_voiceover._typing import JsonValue, VoiceoverData, json_object
from manim_voiceover.helper import append_to_json_file

if t.TYPE_CHECKING:
    PathLike = t.Union[str, os.PathLike[str]]
else:
    PathLike = t.Union[str, os.PathLike]


class VoiceoverInputDataModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    input_text: str
    service: str
    config: t.Optional[t.Dict[str, PydanticJsonValue]] = None


class WordBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    audio_offset: t.Optional[int] = None
    duration_milliseconds: t.Optional[int] = None
    text_offset: t.Optional[int] = None
    word_length: t.Optional[int] = None
    text: t.Optional[str] = None
    boundary_type: t.Optional[str] = None


class VoiceoverCacheEntryModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    input_text: t.Optional[str] = None
    input_data: t.Optional[VoiceoverInputDataModel] = None
    ssml: t.Optional[str] = None
    word_boundaries: t.Optional[t.List[WordBoundaryModel]] = None
    original_audio: t.Optional[str] = None
    final_audio: t.Optional[str] = None
    json_path: t.Optional[str] = None
    transcribed_text: t.Optional[str] = None


def _dump_model_json_object(model: BaseModel) -> t.Dict[str, JsonValue]:
    dumped: t.Mapping[str, object] = model.model_dump(exclude_none=True)
    return json_object(dumped)


def parse_voiceover_cache_entry(raw: object) -> VoiceoverCacheEntryModel:
    try:
        return VoiceoverCacheEntryModel.model_validate(raw)
    except ValidationError as exc:
        raise ValueError("Invalid voiceover cache entry") from exc


def serialize_voiceover_input_data(input_data: VoiceoverInputDataModel) -> t.Dict[str, JsonValue]:
    return _dump_model_json_object(input_data)


def serialize_voiceover_cache_entry(entry: VoiceoverCacheEntryModel) -> VoiceoverData:
    # Keep the dynamic dict conversion isolated at the cache boundary.
    # pragma: no mutate start
    return t.cast(VoiceoverData, _dump_model_json_object(entry))
    # pragma: no mutate end


def load_voiceover_cache(json_file: PathLike) -> t.List[VoiceoverCacheEntryModel]:
    json_path = Path(json_file)
    if not json_path.exists():
        return []

    json_data = json.loads(json_path.read_text())
    if not isinstance(json_data, list):
        raise ValueError("Voiceover cache must be a JSON list")

    return [parse_voiceover_cache_entry(entry) for entry in json_data]


def append_voiceover_cache_entry(
    json_file: PathLike,
    entry: t.Union[VoiceoverCacheEntryModel, VoiceoverData, t.Mapping[str, object]],
) -> None:
    parsed_entry = entry if isinstance(entry, VoiceoverCacheEntryModel) else parse_voiceover_cache_entry(entry)
    append_to_json_file(json_file, serialize_voiceover_cache_entry(parsed_entry))
