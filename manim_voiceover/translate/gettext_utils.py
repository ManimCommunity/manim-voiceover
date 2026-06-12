import os
import re
import subprocess
import typing as t
from pathlib import Path

from manim import logger

from manim_voiceover.helper import prompt_ask_missing_extras

try:
    import deepl
except ImportError:
    logger.error('Missing packages. Run `pip install "manim-voiceover[translate]"` to be able to translate voiceovers.')


if t.TYPE_CHECKING:
    PathLike = t.Union[str, os.PathLike[str]]
else:
    PathLike = t.Union[str, os.PathLike]


def init_gettext(files: t.Sequence[PathLike], domain: str, localedir: Path) -> None:
    """Initialize gettext for a list of files"""
    # If locale directory does not exist, create it
    if not os.path.exists(localedir):
        os.makedirs(localedir)

    pot_path = localedir / f"{domain}.pot"

    # Iterate over all files
    for file in files:
        # Check if pot_path exists
        if os.path.exists(pot_path):
            # If it does, update it
            subprocess.run(["xgettext", "-j", "-o", pot_path, file], check=False)
        else:
            # If it does not, create it
            subprocess.run(["xgettext", "-o", pot_path, file], check=False)


def init_language(target_lang: str, domain: str, localedir: Path) -> Path:
    """Initialize a language for a domain"""
    # Init language directory
    lang_dir = localedir / target_lang / "LC_MESSAGES"

    # If language directory does not exist, create it
    if not os.path.exists(lang_dir):
        os.makedirs(lang_dir)

    # Init po file
    po_path = lang_dir / f"{domain}.po"

    # Check if po_path exists
    if os.path.exists(po_path):
        # If it does, update it
        # os.system(f"msgmerge -U {po_path} {localedir / f'{domain}.pot'}")
        pass
    else:
        # If it does not, create it
        subprocess.run(
            ["msginit", "--no-translator", "-i", localedir / f"{domain}.pot", "-o", po_path, "-l", target_lang],
            check=False,
        )

    return po_path


def extract_str(part: str) -> str:
    """Extract repr'd string from a PO file entry"""
    # If there are lines that are comments, remove them
    tokens = [i.strip()[1:-1] for i in part.strip().split("\n") if i.strip().startswith('"') and i.strip().endswith('"')]
    return "".join(tokens)


class POEntry:
    """An entry in a PO file"""

    def __init__(self, msgid_part: str, msgstr_part: str, header: t.Optional[str] = None) -> None:
        self.msgid_repr = msgid_part
        self.msgstr_repr = msgstr_part
        self.header = header  # Headers are important, keep them

    def __repr__(self) -> str:
        return self.to_string()

    @property
    def msgid(self) -> str:
        return extract_str(self.msgid_repr)

    @property
    def msgstr(self) -> str:
        return extract_str(self.msgstr_repr)

    # Set the msgstr
    @msgstr.setter
    def msgstr(self, value: str) -> None:
        # Escape double quotes
        value = value.replace('"', '\\"')
        # Escample whitespace
        value = value.replace("\t", "\\t")
        value = value.replace("\r", "\\r")
        value = value.replace("\n", "\\n")

        self.msgstr_repr = " " + '"' + value + '"'

    def to_string(self) -> str:
        header = ""
        if self.header is not None:
            header = self.header
        return header + f"""msgid{self.msgid_repr}msgstr{self.msgstr_repr}"""


class POFile:
    """A PO file"""

    def __init__(self, path: PathLike, source_lang: str) -> None:
        self.path = path
        self.source_lang = source_lang

        self.entries: t.List[POEntry] = []

        # pragma: no mutate start
        with open(path, "r") as f:
            # pragma: no mutate end
            content = f.read()

        parts = re.split(r"\n\s*\n(?=(?:#.*\n)*msgid)", content.strip())

        for part in parts:
            if part == "":
                continue
            header = part.split("msgid")[0]
            msgid_part = part.split("msgid")[1].split("msgstr")[0]
            msgstr_part = part.split("msgstr")[1]

            entry = POEntry(msgid_part, msgstr_part, header=header)
            self.entries.append(entry)

    @staticmethod
    def _normalize_target_lang(target_lang: str) -> str:
        if target_lang == "en":
            return "en-US"
        if target_lang == "pt":
            return "pt-BR"
        return target_lang

    def _translation_indices(self) -> t.List[int]:
        return [idx for idx, entry in enumerate(self.entries) if entry.msgid != "" and entry.msgstr == ""]

    def _strings_to_translate(self, translate_idx: t.Sequence[int]) -> t.List[str]:
        to_translate = []
        for idx in translate_idx:
            string_to_translate = self.entries[idx].msgid

            # Unescape whitespace
            string_to_translate = string_to_translate.replace("\\t", "\t")
            string_to_translate = string_to_translate.replace("\\n", "\n")
            string_to_translate = string_to_translate.replace("\\r", "\r")

            # Join the lines
            to_translate.append(" ".join(string_to_translate.split("\n")))
        return to_translate

    def translate(self, target_lang: str, api_key: t.Optional[str] = None) -> bool:
        # pragma: no mutate start
        "Translates a .po file using DeepL. Note: This overwrites the .po file."
        # pragma: no mutate end

        assert api_key is not None, "Please provide a DeepL API key."

        prompt_ask_missing_extras("deepl", "translate", "POFile")

        target_lang = self._normalize_target_lang(target_lang)
        translate_idx = self._translation_indices()

        if len(translate_idx) == 0:
            print(f"{self.path} is already translated.")
            return False

        to_translate = self._strings_to_translate(translate_idx)
        translate_text = "<msg/>".join(to_translate)

        translator = deepl.Translator(api_key)
        translated = translator.translate_text(
            translate_text,
            source_lang=self.source_lang,
            target_lang=target_lang,
            tag_handling="xml",
        )

        # DeepTranslator doesn't allow passing tag_handling="xml"
        # translated = DeeplTranslator(
        #     api_key=api_key, source=source_lang, target=target_lang, use_free_api=True
        # ).translate(translate_text)

        if isinstance(translated, list):
            raise RuntimeError("DeepL returned multiple results for a single translation request.")
        translated_strings = translated.text.split("<msg/>")
        if len(translated_strings) != len(translate_idx):
            raise RuntimeError("DeepL returned a different number of translations than requested.")

        for idx, translation in zip(translate_idx, translated_strings):
            self.entries[idx].msgstr = translation

        self.save(self.path)
        return True

    def save(self, path: PathLike) -> None:
        content = "\n\n".join([i.to_string() for i in self.entries])

        with open(path, "w") as f:
            f.write(content)
            f.flush()
