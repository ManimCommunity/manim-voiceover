from pathlib import Path
from types import SimpleNamespace

import pytest
from manim_voiceover.translate import get_gettext, render, translate


def test_get_gettext_env_and_translation(monkeypatch):
    monkeypatch.delenv("LOCALE", raising=False)
    monkeypatch.delenv("DOMAIN", raising=False)
    assert get_gettext()("hello") == "hello"

    monkeypatch.setenv("LOCALE", "tr")
    monkeypatch.delenv("DOMAIN", raising=False)
    with pytest.raises(ValueError) as exc_info:
        get_gettext()
    assert str(exc_info.value) == "LOCALE is set but DOMAIN is not."

    calls = []

    fake_translation = SimpleNamespace(
        install=lambda: calls.append(("install",)),
        gettext=lambda text: f"tr:{text}",
    )

    def fake_translation_factory(*args, **kwargs):
        calls.append(("translation", args, kwargs))
        return fake_translation

    monkeypatch.setattr("manim_voiceover.translate.gettext.translation", fake_translation_factory)
    assert get_gettext(locale="tr", domain="messages")("hello") == "tr:hello"
    assert calls == [
        (
            "translation",
            ("messages",),
            {"localedir": "locale", "languages": ["tr"]},
        ),
        ("install",),
    ]

    calls.clear()
    monkeypatch.setenv("DOMAIN", "messages")
    assert get_gettext()("hello") == "tr:hello"
    assert calls == [
        (
            "translation",
            ("messages",),
            {"localedir": "locale", "languages": ["tr"]},
        ),
        ("install",),
    ]


def test_render_helpers_and_main(tmp_path, monkeypatch, capsys):
    scene_file = tmp_path / "scene.py"
    scene_file.write_text("class Demo: pass")
    localedir = tmp_path / "locale"
    po_path = localedir / "tr" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True)
    po_path.write_text("")

    render._validate_inputs(str(scene_file), localedir, "l", "Demo")
    assert render._locales_to_render(localedir, "messages", None) == ["tr"]
    assert render._locales_to_render(localedir, "messages", "tr,de") == ["tr", "de"]

    with pytest.raises(FileNotFoundError) as exc_info:
        render._validate_inputs(str(scene_file), tmp_path / "missing", "l", "Demo")
    assert str(exc_info.value) == f"Locale directory {tmp_path / 'missing'} does not exist"
    with pytest.raises(ValueError) as exc_info:
        render._validate_inputs(str(scene_file), localedir, "bad", "Demo")
    assert str(exc_info.value) == "Quality must be one of l,m,h,p,k"
    with pytest.raises(ValueError) as exc_info:
        render._validate_inputs(str(scene_file), localedir, "l", "Missing")
    assert str(exc_info.value) == f"Scene Missing is not in file {scene_file}"

    calls = []
    monkeypatch.setattr(
        "manim_voiceover.translate.render.subprocess.run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or SimpleNamespace(returncode=0),
    )
    monkeypatch.setenv("LOCALE", "old")
    result = render._render_locale(str(scene_file), "messages", localedir, "l", "Demo", "tr")
    assert result == 0
    assert capsys.readouterr().out == "Creating messages.mo for tr\nRendering Demo in tr...\n"
    assert calls == [
        (
            [
                "msgfmt",
                localedir / "tr" / "LC_MESSAGES" / "messages.po",
                "-o",
                localedir / "tr" / "LC_MESSAGES" / "messages.mo",
            ],
            {"check": False},
        ),
        (
            ["manim", "-ql", str(scene_file), "Demo", "-o", "Demo_tr.mp4", "--disable_caching"],
            {"env": {"LOCALE": "tr", "DOMAIN": "messages"}, "check": False},
        ),
    ]
    assert render.os.environ["LOCALE"] == "tr"

    args = SimpleNamespace(
        file=str(scene_file), domain="messages", localedir=localedir, quality="l", scene="Demo", locale="tr"
    )
    monkeypatch.setattr("manim_voiceover.translate.render.parser.parse_args", lambda: args)
    main_calls = []
    monkeypatch.setattr(
        "manim_voiceover.translate.render._validate_inputs",
        lambda file, localedir, quality, scene: main_calls.append(("validate", file, localedir, quality, scene)),
    )
    monkeypatch.setattr(
        "manim_voiceover.translate.render._locales_to_render",
        lambda localedir, domain, locale_arg: main_calls.append(("locales", localedir, domain, locale_arg)) or ["tr"],
    )
    monkeypatch.setattr(
        "manim_voiceover.translate.render._render_locale",
        lambda file, domain, localedir, quality, scene, locale: (
            main_calls.append(("render", file, domain, localedir, quality, scene, locale)) or 0
        ),
    )
    render.main()
    assert main_calls == [
        ("validate", str(scene_file), localedir, "l", "Demo"),
        ("locales", localedir, "messages", "tr"),
        ("render", str(scene_file), "messages", localedir, "l", "Demo", "tr"),
    ]


def test_render_edge_contracts(tmp_path, monkeypatch, capsys):
    scene_file = tmp_path / "scene.py"
    scene_file.write_text("class Demo: pass")
    localedir = tmp_path / "locale"
    tr_messages = localedir / "tr" / "LC_MESSAGES"
    de_messages = localedir / "de" / "LC_MESSAGES"
    tr_messages.mkdir(parents=True)
    de_messages.mkdir(parents=True)
    (tr_messages / "messages.po").write_text("")
    (tr_messages / "messages.mo").write_text("compiled")

    assert render._locales_to_render(localedir, "messages", None) == ["tr"]
    assert capsys.readouterr().out == "Skipping de because messages.po does not exist\n"

    with monkeypatch.context() as scoped_monkeypatch:
        scoped_monkeypatch.setattr("manim_voiceover.translate.render.os.listdir", lambda path: ["fr"])
        scoped_monkeypatch.setattr(
            "manim_voiceover.translate.render.os.path.exists",
            lambda path: Path(path).parts[-3:] == ("fr", "LC_MESSAGES", "messages.po"),
        )
        assert render._locales_to_render(localedir, "messages", None) == ["fr"]

    with monkeypatch.context() as scoped_monkeypatch:
        scoped_monkeypatch.setattr("manim_voiceover.translate.render.os.listdir", lambda path: ["missing", "present"])
        scoped_monkeypatch.setattr(
            "manim_voiceover.translate.render.os.path.exists",
            lambda path: Path(path).parts[-3:] == ("present", "LC_MESSAGES", "messages.po"),
        )
        assert render._locales_to_render(localedir, "messages", None) == ["present"]
        assert capsys.readouterr().out == "Skipping missing because messages.po does not exist\n"

    calls = []
    monkeypatch.setenv("LOCALE", "old")
    monkeypatch.setattr(
        "manim_voiceover.translate.render.subprocess.run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or SimpleNamespace(returncode=3),
    )
    result = render._render_locale(str(scene_file), "messages", localedir, "h", "Demo", "tr")
    assert result == 3
    assert capsys.readouterr().out == "Rendering Demo in tr...\n"
    assert render.os.environ["LOCALE"] == "tr"
    assert calls == [
        (
            ["manim", "-qh", str(scene_file), "Demo", "-o", "Demo_tr.mp4", "--disable_caching"],
            {"env": {"LOCALE": "tr", "DOMAIN": "messages"}, "check": False},
        )
    ]

    args = SimpleNamespace(
        file=str(scene_file), domain="messages", localedir=localedir, quality="h", scene="Demo", locale="tr"
    )
    monkeypatch.setattr("manim_voiceover.translate.render.parser.parse_args", lambda: args)
    with pytest.raises(SystemExit) as exc_info:
        render.main()
    assert exc_info.value.code == 3
    capsys.readouterr()

    monkeypatch.setattr(
        "manim_voiceover.translate.render._render_locale",
        lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    with pytest.raises(SystemExit) as exc_info:
        render.main()
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "KeyboardInterrupt\n"

    with pytest.raises(FileNotFoundError) as exc_info:
        render._validate_inputs(str(tmp_path / "missing.py"), localedir, "l", "Demo")
    assert str(exc_info.value) == f"File {tmp_path / 'missing.py'} does not exist"
    with pytest.raises(ValueError) as exc_info:
        render._validate_inputs(str(scene_file), localedir, "x", "Demo")
    assert str(exc_info.value) == "Quality must be one of l,m,h,p,k"


def test_translate_main_paths(tmp_path, monkeypatch, capsys):
    scene_file = tmp_path / "scene.py"
    scene_file.write_text("")
    localedir = tmp_path / "locale"
    po_path = localedir / "tr" / "LC_MESSAGES" / "messages.po"
    po_path.parent.mkdir(parents=True)
    po_path.write_text('msgid "Hello"\nmsgstr ""\n')

    calls = []
    monkeypatch.setattr("manim_voiceover.translate.translate.dotenv.load_dotenv", lambda path: calls.append(("dotenv", path)))
    monkeypatch.setattr("manim_voiceover.translate.translate.os.getenv", lambda key: calls.append(("getenv", key)) or None)
    with pytest.raises(SystemExit) as exc_info:
        translate.main()
    assert exc_info.value.code == 1
    assert calls == [("dotenv", ".env"), ("getenv", "DEEPL_API_KEY")]
    assert capsys.readouterr().out == (
        "Please set the DEEPL_API_KEY environment variable to your DeepL API Key. "
        "(Available under https://www.deepl.com/account/summary)\n"
    )

    calls.clear()

    class FakePOFile:
        def __init__(self, path, source_lang):
            calls.append(("pofile", path, source_lang))
            self.path = path
            self.source_lang = source_lang

        def translate(self, lang, api_key):
            calls.append(("translate", lang, api_key))
            return True

    monkeypatch.setattr("manim_voiceover.translate.translate.os.getenv", lambda key: calls.append(("getenv", key)) or "key")
    monkeypatch.setattr(
        "manim_voiceover.translate.translate.init_gettext",
        lambda files, domain, localedir: calls.append(("init_gettext", files, domain, localedir)),
    )
    monkeypatch.setattr(
        "manim_voiceover.translate.translate.init_language",
        lambda lang, domain, localedir: calls.append(("init_language", lang, domain, localedir)) or po_path,
    )
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
    assert calls == [
        ("dotenv", ".env"),
        ("getenv", "DEEPL_API_KEY"),
        ("init_gettext", [str(scene_file)], "messages", localedir),
        ("init_language", "tr", "messages", localedir),
        ("pofile", po_path, "en"),
        ("translate", "tr", "key"),
        ("sleep", 2),
    ]

    calls.clear()
    args.target = "not-a-lang"
    with pytest.raises(SystemExit) as exc_info:
        translate.main()
    assert exc_info.value.code == 1
    assert calls == [
        ("dotenv", ".env"),
        ("getenv", "DEEPL_API_KEY"),
        ("init_gettext", [str(scene_file)], "messages", localedir),
    ]
    assert capsys.readouterr().out == (
        "Translating to tr...\n"
        "Target language not-a-lang is not available for DeepL.\n"
        "Available languages are:\n"
        f"{translate.DEEPL_AVAILABLE_TARGET_LANG}\n"
    )


def test_translate_main_all_targets_and_initialize_only(tmp_path, monkeypatch, capsys):
    scene_file = tmp_path / "scene.py"
    scene_file.write_text("")
    localedir = tmp_path / "locale"
    calls = []
    initialized_languages = {}

    monkeypatch.setattr("manim_voiceover.translate.translate.dotenv.load_dotenv", lambda path: calls.append(("dotenv", path)))
    monkeypatch.setattr("manim_voiceover.translate.translate.os.getenv", lambda key: "key")
    monkeypatch.setattr(
        "manim_voiceover.translate.translate.init_gettext",
        lambda files, domain, localedir: calls.append(("init_gettext", files, domain, localedir)),
    )

    def fake_init_language(lang, domain, localedir):
        initialized_languages[lang] = localedir / lang / "LC_MESSAGES" / f"{domain}.po"
        calls.append(("init_language", lang, domain, localedir))
        return initialized_languages[lang]

    monkeypatch.setattr("manim_voiceover.translate.translate.init_language", fake_init_language)

    class FakePOFile:
        def __init__(self, path, source_lang):
            calls.append(("pofile", path, source_lang))

        def translate(self, lang, api_key):
            calls.append(("translate", lang, api_key))
            return lang == "tr"

    monkeypatch.setattr("manim_voiceover.translate.translate.POFile", FakePOFile)
    monkeypatch.setattr("manim_voiceover.translate.translate.sleep", lambda seconds: calls.append(("sleep", seconds)))
    monkeypatch.setattr("manim_voiceover.translate.translate.DEEPL_AVAILABLE_TARGET_LANG", ["tr", "de", "pt-BR"])

    args = SimpleNamespace(
        files=[str(scene_file)],
        source="en",
        target="all",
        domain="messages",
        localedir=localedir,
        only_initialize=False,
    )
    monkeypatch.setattr("manim_voiceover.translate.translate.parser.parse_args", lambda: args)
    translate.main()

    assert ("dotenv", ".env") in calls
    assert ("translate", "tr", "key") in calls
    assert ("translate", "de", "key") in calls
    assert ("translate", "pt-BR", "key") not in calls
    assert ("sleep", 2) in calls
    assert "Translating to tr..." in capsys.readouterr().out

    calls.clear()
    args.target = "tr,de"
    args.only_initialize = True
    translate.main()
    assert ("pofile", initialized_languages["tr"], "en") not in calls
    assert ("translate", "tr", "key") not in calls
    assert ("init_language", "tr", "messages", localedir) in calls
    assert ("init_language", "de", "messages", localedir) in calls


def test_gettext_utils_contracts(tmp_path, monkeypatch, capsys):
    from manim_voiceover.translate.gettext_utils import POEntry, POFile, extract_str, init_gettext, init_language

    runs = []
    monkeypatch.setattr(
        "manim_voiceover.translate.gettext_utils.subprocess.run", lambda args, check: runs.append((args, check))
    )
    source = tmp_path / "scene.py"
    source.write_text('_("Hello")')
    locale_dir = tmp_path / "locale"

    init_gettext([source], "messages", locale_dir)
    (locale_dir / "messages.pot").write_text("")
    init_gettext([source], "messages", locale_dir)
    assert runs == [
        (["xgettext", "-o", locale_dir / "messages.pot", source], False),
        (["xgettext", "-j", "-o", locale_dir / "messages.pot", source], False),
    ]

    runs.clear()
    po_path = init_language("tr", "messages", locale_dir)
    assert po_path == locale_dir / "tr" / "LC_MESSAGES" / "messages.po"
    assert runs == [
        (
            [
                "msginit",
                "--no-translator",
                "-i",
                locale_dir / "messages.pot",
                "-o",
                locale_dir / "tr" / "LC_MESSAGES" / "messages.po",
                "-l",
                "tr",
            ],
            False,
        )
    ]

    runs.clear()
    po_path.write_text('msgid ""\nmsgstr ""\n')
    assert init_language("tr", "messages", locale_dir) == po_path
    assert runs == []

    assert extract_str('# comment\n"Hello"\n" world"') == "Hello world"
    assert extract_str('not quoted"\n"valid"') == "valid"
    entry = POEntry(' "Hello"', ' ""', header="#: scene.py:1\n")
    assert entry.msgid == "Hello"
    assert entry.msgstr == ""
    entry.msgstr = 'Line\t"one"\r\ntwo'
    assert entry.msgstr_repr == ' "Line\\t\\"one\\"\\r\\ntwo"'
    assert entry.to_string() == '#: scene.py:1\nmsgid "Hello"msgstr "Line\\t\\"one\\"\\r\\ntwo"'
    assert repr(entry) == entry.to_string()

    assert POEntry(' "Plain"', ' "Done"').to_string() == 'msgid "Plain"msgstr "Done"'

    empty_po_path = tmp_path / "empty.po"
    empty_po_path.write_text("")
    assert POFile(empty_po_path, source_lang="en").entries == []

    split_po_path = tmp_path / "split.po"
    split_po_path.write_text("ignored")
    with monkeypatch.context() as scoped_monkeypatch:
        scoped_monkeypatch.setattr(
            "manim_voiceover.translate.gettext_utils.re.split",
            lambda pattern, content: ["", 'msgid "Kept"\nmsgstr ""'],
        )
        assert [entry.msgid for entry in POFile(split_po_path, source_lang="en").entries] == ["Kept"]

    po_path.write_text(
        '#: scene.py:1\nmsgid "Hello"\nmsgstr ""\n\n'
        '#: scene.py:2\nmsgid "Already"\nmsgstr "Done"\n\n'
        '#: scene.py:3\nmsgid "Line\\nBreak"\nmsgstr ""\n\n'
        '#: scene.py:4\nmsgid ""\n"Multi"\n" line"\nmsgstr ""\n\n'
        '#: scene.py:5\nmsgid "Tab\\tCarriage\\rReturn"\nmsgstr ""\n'
    )
    po_file = POFile(po_path, source_lang="en")
    assert [item.header for item in po_file.entries] == [
        "#: scene.py:1\n",
        "#: scene.py:2\n",
        "#: scene.py:3\n",
        "#: scene.py:4\n",
        "#: scene.py:5\n",
    ]
    assert [item.msgid for item in po_file.entries] == [
        "Hello",
        "Already",
        "Line\\nBreak",
        "Multi line",
        "Tab\\tCarriage\\rReturn",
    ]
    assert po_file._translation_indices() == [0, 2, 3, 4]
    assert po_file._strings_to_translate([0, 2, 3, 4]) == [
        "Hello",
        "Line Break",
        "Multi line",
        "Tab\tCarriage\rReturn",
    ]

    seen = []

    class FakeTranslator:
        def __init__(self, api_key):
            seen.append(("init", api_key))

        def translate_text(self, text, **kwargs):
            seen.append(("translate_text", text, kwargs))
            return SimpleNamespace(text="Merhaba<msg/>Satir<msg/>Cok satir<msg/>Sekme")

    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.prompt_ask_missing_extras", lambda *args: seen.append(args))
    monkeypatch.setattr("manim_voiceover.translate.gettext_utils.deepl.Translator", FakeTranslator)
    assert po_file.translate("en", api_key="key") is True
    assert ("deepl", "translate", "POFile") in seen
    assert ("init", "key") in seen
    assert (
        "translate_text",
        "Hello<msg/>Line Break<msg/>Multi line<msg/>Tab\tCarriage\rReturn",
        {"source_lang": "en", "target_lang": "en-US", "tag_handling": "xml"},
    ) in seen
    saved = POFile(po_path, source_lang="en")
    assert [item.msgstr for item in saved.entries] == ["Merhaba", "Done", "Satir", "Cok satir", "Sekme"]

    assert POFile(po_path, source_lang="en").translate("tr", api_key="key") is False
    assert f"{po_path} is already translated." in capsys.readouterr().out

    with pytest.raises(AssertionError) as exc_info:
        POFile(po_path, source_lang="en").translate("tr")
    assert str(exc_info.value) == "Please provide a DeepL API key."

    other_path = tmp_path / "other.po"
    po_file.save(other_path)
    assert other_path.read_text() == po_path.read_text()
