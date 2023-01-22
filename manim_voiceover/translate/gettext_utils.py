import re
import os
import typing as t

from manim import logger

from manim_voiceover.helper import prompt_ask_missing_extras

try:
    import deepl
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[translate]"` to be able to translate voiceovers.'
    )


def init_gettext(files, domain, localedir):
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
            os.system(f"xgettext -j -o {pot_path} {file}")
        else:
            # If it does not, create it
            os.system(f"xgettext -o {pot_path} {file}")


def init_language(target_lang, domain, localedir):
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
        os.system(
            f"msginit --no-translator -i {localedir / f'{domain}.pot'} -o {po_path} -l {target_lang}"
        )

    return po_path


def extract_str(part):
    """Extract repr'd string from a PO file entry"""
    # If there are lines that are comments, remove them
    tokens = [
        i.strip()[1:-1]
        for i in part.strip().split("\n")
        if i.strip().startswith('"') and i.strip().endswith('"')
    ]
    return "".join(tokens)


class POEntry:
    """An entry in a PO file"""

    def __init__(self, msgid_part, msgstr_part, header=None):
        self.msgid_repr = msgid_part
        self.msgstr_repr = msgstr_part
        self.header = header  # Headers are important, keep them

    def __repr__(self):
        return self.to_string()

    @property
    def msgid(self):
        return extract_str(self.msgid_repr)

    @property
    def msgstr(self):
        return extract_str(self.msgstr_repr)

    # Set the msgstr
    @msgstr.setter
    def msgstr(self, value):
        # Escape double quotes
        value = value.replace('"', '\\"')
        # Escample whitespace
        value = value.replace("\t", "\\t")
        value = value.replace("\r", "\\r")
        value = value.replace("\n", "\\n")

        self.msgstr_repr = " " + '"' + value + '"'

    def to_string(self):
        header = ""
        if self.header is not None:
            header = self.header
        return header + f"""msgid{self.msgid_repr}msgstr{self.msgstr_repr}"""


class POFile:
    """A PO file"""

    def __init__(self, path: str, source_lang: str):
        self.path = path
        self.source_lang = source_lang

        self.entries: t.List[POEntry] = []

        with open(path, "r") as f:
            content = f.read()

        # Regex to split the PO file. Match only the last double quote before each msgid.
        # Arbitrary characters can be between the double quote and the msgid
        regex = r'"((?=[^"]*msgid))'
        # NOTE: This doesn't account for " that are in comments

        # Split the PO file
        parts = re.split(regex, content)
        parts = [i + '"' for i in parts if i != ""]

        # Iterate over all strings
        for part in parts:
            header = part.split("msgid")[0]
            msgid_part = part.split("msgid")[1].split("msgstr")[0]
            msgstr_part = part.split("msgstr")[1]

            entry = POEntry(msgid_part, msgstr_part, header=header)
            self.entries.append(entry)

    def translate(self, target_lang, api_key=None):
        "Translates a .po file using DeepL. Note: This overwrites the .po file."

        assert api_key is not None, "Please provide a DeepL API key."

        prompt_ask_missing_extras("deepl", "translate", "POFile")

        if target_lang == "en":
            target_lang = "en-US"
        elif target_lang == "pt":
            target_lang = "pt-BR"

        translate_idx = []
        for idx, entry in enumerate(self.entries):
            if entry.msgid == "" or entry.msgstr != "":
                continue
            translate_idx.append(idx)

        if len(translate_idx) == 0:
            print(f"{self.path} is already translated.")
            return False

        to_translate = []
        for idx in translate_idx:
            string_to_translate = self.entries[idx].msgid

            # Unescape whitespace
            string_to_translate = string_to_translate.replace("\\t", "\t")
            string_to_translate = string_to_translate.replace("\\n", "\n")
            string_to_translate = string_to_translate.replace("\\r", "\r")

            # Join the lines
            string_to_translate = " ".join(string_to_translate.split("\n"))

            to_translate.append(string_to_translate)

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

        translated = translated.text.split("<msg/>")

        try:
            for idx, translation in zip(translate_idx, translated):
                self.entries[idx].msgstr = translation
                # translated_dict[list(to_translate.keys())[idx]] = translation
        except:
            print("This shouldn't happen. Please report this bug.")
            import ipdb

            ipdb.set_trace()

        self.save(self.path)
        return True

    def save(self, path):
        content = "".join([i.to_string() for i in self.entries])

        with open(path, "w") as f:
            f.write(content)
            f.flush()
