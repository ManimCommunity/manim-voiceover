import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic import JsonValue as PydanticJsonValue

from manim_voiceover._typing import JsonValue, VoiceoverData, json_object
from manim_voiceover.helper import append_to_json_file

PathLike = str | os.PathLike[str]


class VoiceoverInputDataModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    input_text: str
    service: str | None = None
    config: dict[str, PydanticJsonValue] | None = None


class WordBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    audio_offset: int | None = None
    duration_milliseconds: int | None = None
    text_offset: int | None = None
    word_length: int | None = None
    text: str | None = None
    boundary_type: str | None = None


class VoiceoverCacheEntryModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    input_text: str | None = None
    input_data: VoiceoverInputDataModel | None = None
    ssml: str | None = None
    word_boundaries: list[WordBoundaryModel] | None = None
    original_audio: str | None = None
    final_audio: str | None = None
    json_path: str | None = None
    transcribed_text: str | None = None


def _dump_model_json_object(model: BaseModel) -> dict[str, JsonValue]:
    dumped: Mapping[str, object] = model.model_dump(exclude_none=True)
    return json_object(dumped)


def parse_voiceover_cache_entry(raw: object) -> VoiceoverCacheEntryModel:
    try:
        return VoiceoverCacheEntryModel.model_validate(raw)
    except ValidationError as exc:
        raise ValueError("Invalid voiceover cache entry") from exc


def serialize_voiceover_input_data(input_data: VoiceoverInputDataModel) -> dict[str, JsonValue]:
    return _dump_model_json_object(input_data)


def serialize_voiceover_cache_entry(entry: VoiceoverCacheEntryModel) -> VoiceoverData:
    # Keep the dynamic dict conversion isolated at the cache boundary.
    # pragma: no mutate start
    return cast(VoiceoverData, _dump_model_json_object(entry))
    # pragma: no mutate end


def load_voiceover_cache(json_file: PathLike) -> list[VoiceoverCacheEntryModel]:
    json_path = Path(json_file)
    if not json_path.exists():
        return []

    json_data = json.loads(json_path.read_text())
    if not isinstance(json_data, list):
        raise ValueError("Voiceover cache must be a JSON list")

    return [parse_voiceover_cache_entry(entry) for entry in json_data]


def append_voiceover_cache_entry(
    json_file: PathLike,
    entry: VoiceoverCacheEntryModel | VoiceoverData | Mapping[str, object],
) -> None:
    parsed_entry = entry if isinstance(entry, VoiceoverCacheEntryModel) else parse_voiceover_cache_entry(entry)
    append_to_json_file(json_file, serialize_voiceover_cache_entry(parsed_entry))
