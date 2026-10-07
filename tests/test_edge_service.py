import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
from manim_voiceover.services import edge
from manim_voiceover.services.edge import EdgeTTSService


class FakeCommunicate:
    calls = []
    save_paths = []
    save_path_existed = []
    payload = b"mp3-bytes"
    error = None

    def __init__(self, text, voice, rate=None, volume=None, pitch=None):
        self.text = text
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        FakeCommunicate.calls.append((text, voice, rate, volume, pitch))

    def save_sync(self, path):
        FakeCommunicate.save_path_existed.append(Path(path).is_file())
        if FakeCommunicate.error is not None:
            raise FakeCommunicate.error
        Path(path).write_bytes(FakeCommunicate.payload)
        FakeCommunicate.save_paths.append(path)


@pytest.fixture(autouse=True)
def fake_edge_tts(monkeypatch):
    FakeCommunicate.calls = []
    FakeCommunicate.save_paths = []
    FakeCommunicate.save_path_existed = []
    FakeCommunicate.payload = b"mp3-bytes"
    FakeCommunicate.error = None

    def fake_import(name):
        assert name == "edge_tts"
        return SimpleNamespace(Communicate=FakeCommunicate)

    monkeypatch.setattr(edge.importlib, "import_module", fake_import)
    yield


def make_service(tmp_path, **kwargs):
    return EdgeTTSService(cache_dir=tmp_path, **kwargs)


def test_module_import_without_extra():
    assert edge.DEFAULT_EDGE_VOICE == "en-US-EmmaMultilingualNeural"


def test_missing_dependency_raises_actionable_import_error(tmp_path, monkeypatch):
    def missing(name):
        raise ImportError(name)

    monkeypatch.setattr(edge.importlib, "import_module", missing)
    with pytest.raises(ImportError) as exc_info:
        EdgeTTSService(cache_dir=tmp_path)
    assert (
        str(exc_info.value)
        == 'EdgeTTSService requires the edge-tts package. Install it with `pip install "manim-voiceover[edge]"`.'
    )


def test_normalization_and_bookmark_removal(tmp_path):
    service = make_service(tmp_path)
    result = service.generate_from_text("  hello\n <bookmark mark='a'/>  world  ")
    assert result["input_text"] == "hello <bookmark mark='a'/> world"
    assert result["input_data"]["input_text"] == "hello world"
    assert FakeCommunicate.calls[0][0] == "hello world"


@pytest.mark.parametrize("text", ["   ", "<bookmark mark='a'/>", " \n<bookmark mark='a'/>\t "])
def test_rejects_empty_or_bookmark_only_text(tmp_path, text):
    service = make_service(tmp_path)
    with pytest.raises(ValueError) as exc_info:
        service.generate_from_text(text)
    assert str(exc_info.value) == "input text is empty after removing bookmarks"
    assert FakeCommunicate.calls == []


def test_input_data_shape_and_deterministic_filename(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    temp_kwargs = {}
    original_ntf = edge.tempfile.NamedTemporaryFile

    def spy(*args, **kwargs):
        temp_kwargs.update(kwargs)
        return original_ntf(*args, **kwargs)

    monkeypatch.setattr(edge.tempfile, "NamedTemporaryFile", spy)
    result = service.generate_from_text("hello world")
    assert result["input_data"] == {
        "input_text": "hello world",
        "service": "edge",
        "config": {"voice": service.voice, "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
    }
    assert result["original_audio"] == service.get_audio_basename(result["input_data"]) + ".mp3"
    assert (tmp_path / result["original_audio"]).read_bytes() == b"mp3-bytes"
    save_path = Path(FakeCommunicate.save_paths[0])
    assert save_path.parent == tmp_path
    assert save_path.name != result["original_audio"]
    assert save_path.name.startswith(Path(result["original_audio"]).stem + "-")
    assert save_path.name.endswith(".mp3")
    assert FakeCommunicate.save_path_existed == [True]
    assert temp_kwargs == {
        "prefix": Path(result["original_audio"]).stem + "-",
        "suffix": ".mp3",
        "dir": tmp_path,
        "delete": False,
    }
    assert FakeCommunicate.calls[0] == (
        "hello world",
        service.voice,
        service.rate,
        service.volume,
        service.pitch,
    )


def test_each_config_option_changes_cache_key(tmp_path):
    service = make_service(tmp_path)
    variants = [
        service,
        make_service(tmp_path, voice="en-US-AvaNeural"),
        make_service(tmp_path, rate="+10%"),
        make_service(tmp_path, pitch="+2Hz"),
        make_service(tmp_path, volume="-10%"),
    ]
    names = {variant.get_audio_basename(variant._input_data("hello")) for variant in variants}
    assert len(names) == 5
    assert service.get_audio_basename(service._input_data("different text")) not in names


def test_cached_result_reused_for_existing_mp3(tmp_path):
    service = make_service(tmp_path)
    result = service._wrap_generate_from_text("hello world")
    assert len(FakeCommunicate.calls) == 1
    again = service.generate_from_text("hello world")
    assert again["original_audio"] == result["original_audio"]
    assert len(FakeCommunicate.calls) == 1


def test_cache_hit_preserves_current_bookmarks(tmp_path):
    service = make_service(tmp_path)
    service._wrap_generate_from_text("hello <bookmark mark='first'/> world")

    result = service.generate_from_text("hello <bookmark mark='second'/> world")

    assert result["input_text"] == "hello <bookmark mark='second'/> world"
    assert len(FakeCommunicate.calls) == 1


def _seed_cache_entry(tmp_path, service, original_audio):
    input_data = service._input_data("hello world")
    entry = {"input_text": "hello world", "input_data": input_data, "original_audio": original_audio}
    (tmp_path / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME).write_text(json.dumps([entry]))
    return entry


def test_stale_cache_entries_regenerate(tmp_path):
    service = make_service(tmp_path)
    entry = _seed_cache_entry(tmp_path, service, "missing.mp3")
    result = service.generate_from_text("hello world")
    assert len(FakeCommunicate.calls) == 1
    assert result["original_audio"] != entry["original_audio"]
    assert (tmp_path / result["original_audio"]).is_file()

    FakeCommunicate.calls = []
    (tmp_path / "empty.mp3").write_bytes(b"")
    _seed_cache_entry(tmp_path, service, "empty.mp3")
    result = service.generate_from_text("hello world")
    assert len(FakeCommunicate.calls) == 1
    assert result["original_audio"] != "empty.mp3"

    FakeCommunicate.calls = []
    (tmp_path / "voice.wav").write_bytes(b"wav")
    _seed_cache_entry(tmp_path, service, "voice.wav")
    result = service.generate_from_text("hello world")
    assert len(FakeCommunicate.calls) == 1
    assert result["original_audio"] != "voice.wav"

    FakeCommunicate.calls = []
    (tmp_path / "good.mp3").write_bytes(b"old-bytes")
    _seed_cache_entry(tmp_path, service, "good.mp3")
    result = service.generate_from_text("hello world")
    assert result["original_audio"] == "good.mp3"
    assert len(FakeCommunicate.calls) == 0


def test_one_byte_cached_mp3_is_reused(tmp_path):
    service = make_service(tmp_path)
    (tmp_path / "tiny.mp3").write_bytes(b"x")
    _seed_cache_entry(tmp_path, service, "tiny.mp3")
    result = service.generate_from_text("hello world")
    assert result["original_audio"] == "tiny.mp3"
    assert len(FakeCommunicate.calls) == 0


def test_explicit_relative_output(tmp_path):
    service = make_service(tmp_path)
    result = service.generate_from_text("hello", path="sub/dir/out.mp3")
    assert result["original_audio"] == "sub/dir/out.mp3"
    assert (tmp_path / "sub/dir/out.mp3").read_bytes() == b"mp3-bytes"


def test_explicit_absolute_output(tmp_path):
    service = make_service(tmp_path)
    destination = tmp_path / "abs" / "out.mp3"
    result = service.generate_from_text("hello", path=destination)
    assert result["original_audio"] == str(destination)
    assert destination.read_bytes() == b"mp3-bytes"


@pytest.mark.parametrize("bad_path", ["out.wav", "out.MP4", "out"])
def test_explicit_non_mp3_output_rejected(tmp_path, bad_path):
    service = make_service(tmp_path)
    with pytest.raises(ValueError) as exc_info:
        service.generate_from_text("hello", path=bad_path)
    assert str(exc_info.value) == "Edge TTS output path must have a .mp3 extension"
    assert FakeCommunicate.calls == []


def test_explicit_output_overwrite_contract(tmp_path):
    service = make_service(tmp_path)
    destination = tmp_path / "out.mp3"
    destination.write_bytes(b"previous")
    with pytest.raises(FileExistsError) as exc_info:
        service.generate_from_text("hello", path="out.mp3")
    assert str(exc_info.value) == f"Output file already exists: {destination}"
    assert destination.read_bytes() == b"previous"
    assert FakeCommunicate.calls == []

    result = service.generate_from_text("hello", path="out.mp3", overwrite=True)
    assert result["original_audio"] == "out.mp3"
    assert destination.read_bytes() == b"mp3-bytes"


def test_non_bool_overwrite_rejected_before_synthesis(tmp_path):
    service = make_service(tmp_path)
    with pytest.raises(TypeError) as exc_info:
        service.generate_from_text("hello", path="out.mp3", overwrite="yes")
    assert str(exc_info.value) == "overwrite must be a bool"
    assert FakeCommunicate.calls == []


def test_explicit_output_bypasses_cache(tmp_path):
    service = make_service(tmp_path)
    _seed_cache_entry(tmp_path, service, "cached.mp3")
    (tmp_path / "cached.mp3").write_bytes(b"cached")
    result = service.generate_from_text("hello world", path="other.mp3")
    assert result["original_audio"] == "other.mp3"
    assert len(FakeCommunicate.calls) == 1


def test_sdk_failure_cleans_up_temp_file(tmp_path):
    service = make_service(tmp_path)
    FakeCommunicate.error = RuntimeError("sdk exploded")
    with pytest.raises(RuntimeError, match="sdk exploded"):
        service.generate_from_text("hello")
    assert [p.name for p in tmp_path.iterdir()] == []


def test_empty_output_raises_and_cleans_up(tmp_path):
    service = make_service(tmp_path)
    FakeCommunicate.payload = b""
    with pytest.raises(RuntimeError) as exc_info:
        service.generate_from_text("hello")
    assert str(exc_info.value) == "Edge TTS produced an empty audio file."
    assert [p.name for p in tmp_path.iterdir()] == []


def test_replace_failure_cleans_up(tmp_path, monkeypatch):
    service = make_service(tmp_path)

    def failing_replace(src, dst):
        raise OSError("cannot replace")

    monkeypatch.setattr(edge.os, "replace", failing_replace)
    with pytest.raises(OSError, match="cannot replace"):
        service.generate_from_text("hello")
    assert [p.name for p in tmp_path.iterdir()] == []
