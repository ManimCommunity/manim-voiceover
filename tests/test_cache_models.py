import json

import pytest

from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
from manim_voiceover.services.cache import (
    VoiceoverCacheEntryModel,
    append_voiceover_cache_entry,
    load_voiceover_cache,
    parse_voiceover_cache_entry,
    serialize_voiceover_cache_entry,
    serialize_voiceover_input_data,
)


def test_cache_entry_serializes_to_current_minimal_shape():
    raw_entry = {
        "input_text": "Hello world",
        "input_data": {
            "input_text": "Hello world",
            "service": "gtts",
        },
        "original_audio": "hello-world-abc12345.mp3",
        "final_audio": "hello-world-abc12345.mp3",
    }

    entry = parse_voiceover_cache_entry(raw_entry)

    assert serialize_voiceover_cache_entry(entry) == raw_entry


def test_cache_entry_serialization_does_not_add_wrapper_version_or_default_config():
    raw_entry = {
        "input_text": "Hello world",
        "input_data": {
            "input_text": "Hello world",
            "service": "gtts",
        },
        "original_audio": "hello-world-abc12345.mp3",
        "final_audio": "hello-world-abc12345.mp3",
    }

    serialized = serialize_voiceover_cache_entry(VoiceoverCacheEntryModel.model_validate(raw_entry))

    assert serialized == raw_entry
    assert "schema_version" not in serialized
    assert "config" not in serialized["input_data"]


def test_cache_entry_preserves_provider_specific_input_data():
    raw_entry = {
        "input_text": "Hello world",
        "input_data": {
            "input_text": "Hello world",
            "service": "azure",
            "ssml": "<speak>Hello world</speak>",
            "config": {
                "voice": "en-US-AriaNeural",
                "style": "friendly",
            },
        },
        "ssml": "<speak>Hello world</speak>",
        "word_boundaries": [
            {
                "audio_offset": 0,
                "duration_milliseconds": 100,
                "text_offset": 0,
                "word_length": 5,
                "text": "Hello",
                "boundary_type": "Word",
            }
        ],
        "original_audio": "hello-world-abc12345.mp3",
        "final_audio": "hello-world-abc12345.mp3",
    }

    entry = parse_voiceover_cache_entry(raw_entry)

    assert serialize_voiceover_cache_entry(entry) == raw_entry
    assert entry.input_data is not None
    assert serialize_voiceover_input_data(entry.input_data) == raw_entry["input_data"]


def test_cache_entry_accepts_custom_input_data_without_service():
    raw_entry = {
        "input_text": "Hello world",
        "input_data": {
            "input_text": "Hello world",
            "custom_option": "custom-value",
        },
        "original_audio": "hello-world-abc12345.mp3",
    }

    entry = parse_voiceover_cache_entry(raw_entry)

    assert serialize_voiceover_cache_entry(entry) == raw_entry
    assert entry.input_data is not None
    assert serialize_voiceover_input_data(entry.input_data) == raw_entry["input_data"]


def test_append_voiceover_cache_entry_writes_top_level_list(tmp_path):
    cache_path = tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
    entry = {
        "input_text": "Hello world",
        "input_data": {
            "input_text": "Hello world",
            "service": "gtts",
        },
        "original_audio": "hello-world-abc12345.mp3",
        "final_audio": "hello-world-abc12345.mp3",
    }

    append_voiceover_cache_entry(cache_path, entry)

    assert json.loads(cache_path.read_text()) == [entry]
    assert cache_path.read_text().startswith("[\n  {")


def test_append_voiceover_cache_entry_preserves_existing_list(tmp_path):
    cache_path = tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
    existing_entry = {
        "input_text": "first",
        "input_data": {
            "input_text": "first",
            "service": "gtts",
        },
    }
    next_entry = {
        "input_text": "second",
        "input_data": {
            "input_text": "second",
            "service": "gtts",
        },
    }
    cache_path.write_text(json.dumps([existing_entry]))

    append_voiceover_cache_entry(cache_path, next_entry)

    assert json.loads(cache_path.read_text()) == [existing_entry, next_entry]


def test_parse_voiceover_cache_entry_rejects_non_object():
    with pytest.raises(ValueError) as exc_info:
        parse_voiceover_cache_entry("not an object")

    assert str(exc_info.value) == "Invalid voiceover cache entry"
    assert exc_info.value.__cause__ is not None


def test_parse_voiceover_cache_entry_rejects_invalid_field_types():
    with pytest.raises(ValueError) as exc_info:
        parse_voiceover_cache_entry(
            {
                "input_text": 10,
                "input_data": {
                    "input_text": "Hello world",
                    "service": "gtts",
                },
            }
        )

    assert str(exc_info.value) == "Invalid voiceover cache entry"
    assert exc_info.value.__cause__ is not None


def test_load_voiceover_cache_accepts_current_cache_list(tmp_path):
    cache_path = tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
    entry = {
        "input_text": "cached",
        "input_data": {
            "input_text": "cached",
            "service": "openai",
        },
        "original_audio": "cached.mp3",
    }
    cache_path.write_text(json.dumps([entry]))

    loaded = load_voiceover_cache(cache_path)

    assert [serialize_voiceover_cache_entry(item) for item in loaded] == [entry]


def test_load_voiceover_cache_rejects_non_list_cache(tmp_path):
    cache_path = tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
    cache_path.write_text(json.dumps({"input_text": "not a list"}))

    with pytest.raises(ValueError) as exc_info:
        load_voiceover_cache(cache_path)

    assert str(exc_info.value) == "Voiceover cache must be a JSON list"
