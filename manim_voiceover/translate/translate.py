import argparse
import os
import sys
from time import sleep
from pathlib import Path
import dotenv

from manim_voiceover.defaults import DEEPL_AVAILABLE_TARGET_LANG
from manim_voiceover.translate.gettext_utils import POFile, init_gettext, init_language


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
parser.add_argument(
    "--only-initialize",
    action="store_true",
    help="Only initialize the language directories",
)


def main():
    dotenv.load_dotenv(".env")
    DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

    if DEEPL_API_KEY is None:
        print(
            "Please set the DEEPL_API_KEY environment variable to your DeepL API Key. (Available under https://www.deepl.com/account/summary)"
        )
        sys.exit(1)

    args = parser.parse_args()

    # Initialize gettext
    init_gettext(args.files, args.domain, args.localedir)

    if args.target == "all":
        langs = [i for i in DEEPL_AVAILABLE_TARGET_LANG if "-" not in i]
    else:
        langs = args.target.split(",")

    for lang in langs:
        if lang not in DEEPL_AVAILABLE_TARGET_LANG:
            print(f"Target language {args.target} is not available for DeepL.")
            print("Available languages are:")
            print(DEEPL_AVAILABLE_TARGET_LANG)
            sys.exit(1)

        print(f"Translating to {lang}...")
        # Initialize language directory
        po_path = init_language(lang, args.domain, args.localedir)

        if not args.only_initialize:
            po_file = POFile(po_path, source_lang=args.source)
            # Translate po file
            wait = po_file.translate(lang, api_key=DEEPL_API_KEY)
            if wait:
                sleep(2)


if __name__ == "__main__":
    main()
