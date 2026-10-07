import io
from pathlib import Path

import pytest

from manim_voiceover import tts


class FakeService:
    instances = []
    wrap_calls = []
    error = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.cache_dir = Path("/fake-cache")
        FakeService.instances.append(self)

    def _wrap_generate_from_text(self, text, **kwargs):
        if FakeService.error is not None:
            raise FakeService.error
        FakeService.wrap_calls.append((text, kwargs))
        return {"final_audio": "final.mp3"}


duration_calls = []


@pytest.fixture(autouse=True)
def fake_boundaries(monkeypatch, tmp_path):
    FakeService.instances = []
    FakeService.wrap_calls = []
    FakeService.error = None
    duration_calls.clear()
    monkeypatch.setattr(tts, "EdgeTTSService", FakeService)
    monkeypatch.setattr(tts, "get_duration", lambda path: duration_calls.append(path) or 1.5)


def test_positional_text_and_defaults(tmp_path, capsys):
    output = tmp_path / "out.mp3"
    assert tts.main(["hello   world", "-o", str(output)]) == 0
    assert FakeService.instances[0].kwargs == {
        "voice": tts.DEFAULT_EDGE_VOICE,
        "rate": tts.DEFAULT_EDGE_RATE,
        "pitch": tts.DEFAULT_EDGE_PITCH,
        "volume": tts.DEFAULT_EDGE_VOLUME,
    }
    assert FakeService.wrap_calls == [("hello world", {"path": output, "overwrite": False})]
    assert duration_calls == [Path("/fake-cache/final.mp3")]
    stdout = capsys.readouterr().out.splitlines()
    assert stdout == [
        f"Output: {Path('/fake-cache/final.mp3')}",
        "Duration: 1.50 seconds",
    ]


def test_parser_metadata_and_help():
    parser = tts._build_parser()
    assert parser.prog == "manim_voiceover_tts"
    assert parser.description == "Synthesize narration audio with Edge TTS."
    actions = {action.dest: action for action in parser._actions}
    assert actions["text"].nargs == "?"
    assert actions["text"].help == "Narration text. Read from stdin when omitted."
    assert actions["output"].option_strings == ["-o", "--output"]
    assert actions["output"].default == "voiceover.mp3"
    assert actions["output"].help == "Output MP3 path."
    assert actions["voice"].default == tts.DEFAULT_EDGE_VOICE
    assert actions["voice"].help == "Edge TTS voice name."
    assert actions["rate"].default == tts.DEFAULT_EDGE_RATE
    assert actions["rate"].help == "Speech rate, e.g. +0%%."
    assert actions["pitch"].default == tts.DEFAULT_EDGE_PITCH
    assert actions["pitch"].help == "Speech pitch, e.g. +0Hz."
    assert actions["volume"].default == tts.DEFAULT_EDGE_VOLUME
    assert actions["volume"].help == "Speech volume, e.g. +0%%."
    assert actions["overwrite"].default is False
    assert actions["overwrite"].help == "Overwrite an existing output file."


def test_all_options_forwarded(tmp_path):
    output = tmp_path / "out.mp3"
    assert (
        tts.main(
            [
                "hello",
                "-o",
                str(output),
                "--voice",
                "en-US-AvaNeural",
                "--rate",
                "+10%",
                "--pitch",
                "+2Hz",
                "--volume=-5%",
                "--overwrite",
            ]
        )
        == 0
    )
    assert FakeService.instances[0].kwargs == {
        "voice": "en-US-AvaNeural",
        "rate": "+10%",
        "pitch": "+2Hz",
        "volume": "-5%",
    }
    assert FakeService.wrap_calls == [("hello", {"path": output, "overwrite": True})]


def test_stdin_fallback(tmp_path, monkeypatch):
    stdin = io.StringIO("hello from stdin\n")
    monkeypatch.setattr(tts.sys, "stdin", stdin)
    output = tmp_path / "out.mp3"
    assert tts.main(["-o", str(output)]) == 0
    assert FakeService.wrap_calls[0][0] == "hello from stdin"


def test_default_output_path(monkeypatch):
    monkeypatch.setattr(tts.sys, "stdin", io.StringIO("hello"))
    assert tts.main([]) == 0
    assert FakeService.wrap_calls[0][1]["path"] == Path("voiceover.mp3").resolve()


@pytest.mark.parametrize("argv", [["   "], []])
def test_empty_or_missing_input_is_parser_error(argv, monkeypatch, capsys):
    class TtyStdin(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr(tts.sys, "stdin", TtyStdin("ignored"))
    with pytest.raises(SystemExit):
        tts.main(argv)
    assert capsys.readouterr().err.endswith("error: narration text must not be empty\n")
    assert FakeService.instances == []


def test_absolute_final_audio_used_as_is(tmp_path, monkeypatch, capsys):
    absolute = tmp_path / "final.mp3"

    class AbsoluteService(FakeService):
        def _wrap_generate_from_text(self, text, **kwargs):
            return {"final_audio": str(absolute)}

    monkeypatch.setattr(tts, "EdgeTTSService", AbsoluteService)
    assert tts.main(["hello"]) == 0
    assert capsys.readouterr().out.splitlines() == [f"Output: {absolute}", "Duration: 1.50 seconds"]


def test_synthesis_failure_returns_one(tmp_path, capsys):
    FakeService.error = RuntimeError("backend exploded")
    assert tts.main(["secret narration"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "Error: backend exploded"
    assert "secret narration" not in captured.err


def test_duration_probe_failure_returns_one(monkeypatch, capsys):
    def failing_duration(path):
        raise ValueError("not audio")

    monkeypatch.setattr(tts, "get_duration", failing_duration)
    assert tts.main(["hello"]) == 1
    assert "Error: not audio" in capsys.readouterr().err
