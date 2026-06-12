from types import SimpleNamespace

import pytest
from manim_voiceover.translate import get_gettext, render, translate


def test_get_gettext_env_and_translation(monkeypatch):
    monkeypatch.delenv("LOCALE", raising=False)
    monkeypatch.delenv("DOMAIN", raising=False)
    assert get_gettext()("hello") == "hello"

    monkeypatch.setenv("LOCALE", "tr")
    monkeypatch.delenv("DOMAIN", raising=False)
    with pytest.raises(ValueError):
        get_gettext()

    fake_translation = SimpleNamespace(install=lambda: None, gettext=lambda text: f"tr:{text}")
    monkeypatch.setattr("manim_voiceover.translate.gettext.translation", lambda *args, **kwargs: fake_translation)
    assert get_gettext(locale="tr", domain="messages")("hello") == "tr:hello"


def test_render_helpers_and_main(tmp_path, monkeypatch):
    scene_file = tmp_path / "scene.py"
    scene_file.write_text("class Demo: pass")
    localedir = tmp_path / "locale"
    po_path = localedir / "tr" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True)
    po_path.write_text("")

    render._validate_inputs(str(scene_file), localedir, "l", "Demo")
    assert render._locales_to_render(localedir, "messages", None) == ["tr"]
    assert render._locales_to_render(localedir, "messages", "tr,de") == ["tr", "de"]

    calls = []
    monkeypatch.setattr(
        "manim_voiceover.translate.render.subprocess.run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or SimpleNamespace(returncode=0),
    )
    result = render._render_locale(str(scene_file), "messages", localedir, "l", "Demo", "tr")
    assert result == 0
    assert calls[-1][0][0] == "manim"

    args = SimpleNamespace(
        file=str(scene_file), domain="messages", localedir=localedir, quality="l", scene="Demo", locale="tr"
    )
    monkeypatch.setattr("manim_voiceover.translate.render.parser.parse_args", lambda: args)
    render.main()

    with pytest.raises(FileNotFoundError):
        render._validate_inputs(str(scene_file), tmp_path / "missing", "l", "Demo")
    with pytest.raises(ValueError):
        render._validate_inputs(str(scene_file), localedir, "bad", "Demo")
    with pytest.raises(ValueError):
        render._validate_inputs(str(scene_file), localedir, "l", "Missing")


def test_translate_main_paths(tmp_path, monkeypatch):
    scene_file = tmp_path / "scene.py"
    scene_file.write_text("")
    localedir = tmp_path / "locale"
    po_path = localedir / "tr" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True)
    po_path.write_text('msgid "Hello"\nmsgstr ""\n')

    monkeypatch.setattr("manim_voiceover.translate.translate.dotenv.load_dotenv", lambda path: None)
    monkeypatch.setattr("manim_voiceover.translate.translate.os.getenv", lambda key: None)
    with pytest.raises(SystemExit):
        translate.main()

    calls = []

    class FakePOFile:
        def __init__(self, path, source_lang):
            self.path = path
            self.source_lang = source_lang

        def translate(self, lang, api_key):
            calls.append((lang, api_key))
            return True

    monkeypatch.setattr("manim_voiceover.translate.translate.os.getenv", lambda key: "key")
    monkeypatch.setattr(
        "manim_voiceover.translate.translate.init_gettext", lambda files, domain, localedir: calls.append("init")
    )
    monkeypatch.setattr("manim_voiceover.translate.translate.init_language", lambda lang, domain, localedir: po_path)
    monkeypatch.setattr("manim_voiceover.translate.translate.POFile", FakePOFile)
    monkeypatch.setattr("manim_voiceover.translate.translate.sleep", lambda seconds: calls.append(("sleep", seconds)))

    args = SimpleNamespace(
        files=[str(scene_file)],
        source="en",
        target="tr",
        domain="messages",
        localedir=localedir,
        only_initialize=False,
    )
    monkeypatch.setattr("manim_voiceover.translate.translate.parser.parse_args", lambda: args)
    translate.main()
    assert ("tr", "key") in calls
    assert ("sleep", 2) in calls

    args.target = "not-a-lang"
    with pytest.raises(SystemExit):
        translate.main()
