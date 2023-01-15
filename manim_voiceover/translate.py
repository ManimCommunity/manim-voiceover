import argparse
import os
import sys
import deep_translator
from pathlib import Path
import gettext

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


def translate_po_file(po_path, target_lang):
    "Translates a .po file using DeepL. Note: This overwrites the .po file."
    with open(po_path, "r") as f:
        content = f.read()

    # Get all strings to translate
    strings = content.split("msgid")[1:]

    # Iterate over all strings
    for string in strings:

        # Get the string to translate
        string_to_translate = string.split("msgstr")[0].strip()

        # If there are lines that are comments, remove them
        tokens = [
            i.strip()[1:-1]
            for i in string_to_translate.split("\n")
            if i.strip().startswith('"') and i.strip().endswith('"')
        ]

        string_to_translate = "".join(tokens)

        if string_to_translate == "":
            continue

        # Unescape whitespace
        string_to_translate = string_to_translate.replace("\\t", "\t")
        string_to_translate = string_to_translate.replace("\\n", "\n")


        import ipdb

        ipdb.set_trace()

        # # Translate the string
        # translated_string = deep_translator.DeepL(
        #     source="en", target=target_lang
        # ).translate(string_to_translate)

        # # Replace the string in the content


def main():
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
    translate_po_file(po_path, args.target)


if __name__ == "__main__":
    main()
