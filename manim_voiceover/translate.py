import argparse
from collections import OrderedDict
import os
import sys
from deep_translator import DeeplTranslator
from pathlib import Path
import gettext
import dotenv

from manim_voiceover.defaults import DEEPL_AVAILABLE_TARGET_LANG


# Get the current working directory as Path
CWD = Path.cwd()


parser = argparse.ArgumentParser(description="Translate scenes")
# Multiple Python files can be passed as arguments
parser.add_argument(
    "files",
    metavar="file",
    type=str,
    nargs="+",
    help="Python files to translate",
)
parser.add_argument(
    "-s",
    "--source",
    type=str,
    default="en",
    help="Source language",
)
parser.add_argument(
    "-t",
    "--target",
    type=str,
    required=True,
    help="Target language",
)
parser.add_argument(
    "-d",
    "--domain",
    type=str,
    required=True,
    help="Domain for gettext",
)
# CWD / locale is the default value, string is converted to Path
parser.add_argument(
    "-l",
    "--localedir",
    type=Path,
    default=CWD / "locale",
    help="Directory for gettext locale files",
)


def init_gettext(files, domain, localedir):
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
        os.system(f"msgmerge -U {po_path} {localedir / f'{domain}.pot'}")
    else:
        # If it does not, create it
        os.system(
            f"msginit --no-translator -i {localedir / f'{domain}.pot'} -o {po_path} -l {target_lang}"
        )

    return po_path


def translate_po_file(po_path, source_lang, target_lang, api_key=None):
    "Translates a .po file using DeepL. Note: This overwrites the .po file."

    assert api_key is not None, "Please provide a DeepL API key."

    with open(po_path, "r") as f:
        content = f.read()

    split = content.split("msgid")
    # Get all strings to translate
    strings = split[1:]

    skipped = {}
    to_translate = OrderedDict()
    msgid = OrderedDict()
    # Iterate over all strings
    for idx, string in enumerate(strings):

        msgid[idx] = string.split("msgstr")[0]

        # Get the string to translate
        string_to_translate = msgid[idx].strip()

        # If there are lines that are comments, remove them
        tokens = [
            i.strip()[1:-1]
            for i in string_to_translate.split("\n")
            if i.strip().startswith('"') and i.strip().endswith('"')
        ]

        string_to_translate = "".join(tokens)

        if string_to_translate == "":
            skipped[idx] = string
            continue

        # Unescape whitespace
        string_to_translate = string_to_translate.replace("\\t", "\t")
        string_to_translate = string_to_translate.replace("\\n", "\n")

        # Join the lines
        string_to_translate = " ".join(string_to_translate.split("\n"))

        to_translate[idx] = string_to_translate

    translate_text = "<msg>".join(to_translate.values())

    translated = DeeplTranslator(
        api_key=api_key, source=source_lang, target=target_lang, use_free_api=True
    ).translate(translate_text)

    translated = translated.split("<msg>")

    translated_dict = OrderedDict()

    for idx, translation in enumerate(translated):
        translated_dict[list(to_translate.keys())[idx]] = translation

    for idx, string in enumerate(skipped):
        translated_dict[idx] = skipped[idx]

    new_content = split[0]
    for idx in sorted(translated_dict.keys()):
        new_content += (
            "msgid" + msgid[idx] + 'msgstr "' + translated_dict[idx] + '"\n\n'
        )

    with open(po_path, "w") as f:
        f.write(new_content)


def main():

    # dotenv.load_dotenv(".env")
    DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

    if DEEPL_API_KEY is None:
        print(
            "Please set the DEEPL_API_KEY environment variable to your DeepL API Key. (Available under https://www.deepl.com/account/summary)"
        )
        sys.exit(1)

    args = parser.parse_args()

    # Initialize gettext
    init_gettext(args.files, args.domain, args.localedir)

    if args.target not in DEEPL_AVAILABLE_TARGET_LANG:
        print(f"Target language {args.target} is not available for DeepL.")
        print("Available languages are:")
        print(DEEPL_AVAILABLE_TARGET_LANG)
        sys.exit(1)

    # Initialize language directory
    po_path = init_language(args.target, args.domain, args.localedir)

    # Translate po file
    translate_po_file(po_path, args.source, args.target, api_key=DEEPL_API_KEY)


if __name__ == "__main__":
    main()
