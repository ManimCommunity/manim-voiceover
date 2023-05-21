import argparse
import os
import sys
from pathlib import Path


# Get the current working directory as Path
CWD = Path.cwd()

ALLOWED_Q = ["l", "m", "h", "p", "k"]

parser = argparse.ArgumentParser(description="Translate scenes")
parser.add_argument(
    "file",
    type=str,
    help="Python file to translate",
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
    "--localedir",
    type=Path,
    default=CWD / "locale",
    help="Directory for gettext locale files",
)
# Argument for quality, -qh for high quality, -ql for low quality
parser.add_argument(
    "-q",
    "--quality",
    type=str,
    default="l",
    help="Quality of translation  [l|m|h|p|k]",
)
# Add locale
parser.add_argument(
    "-l",
    "--locale",
    type=str,
    default=None,
    help="Locale for translation. Enter a comma separated list of locales. If not specified, all locales will be rendered.",
)

# Argument for scene
parser.add_argument(
    "-s",
    "--scene",
    type=str,
    # default="",
    required=True,
    help="Scene to translate",
)


def main():
    args = parser.parse_args()
    file = args.file
    domain = args.domain
    localedir = args.localedir
    quality = args.quality
    scene = args.scene

    # If locale directory does not exist, raise error
    if not os.path.exists(localedir):
        raise FileNotFoundError(f"Locale directory {localedir} does not exist")

    # If file does not exist, raise error
    if not os.path.exists(file):
        raise FileNotFoundError(f"File {file} does not exist")

    # If quality is not h or l, raise error
    if quality not in ALLOWED_Q:
        raise ValueError(f"Quality must be one of {','.join(ALLOWED_Q)}")

    # If scene is not in file, raise error
    if scene not in open(file).read():
        raise ValueError(f"Scene {scene} is not in file {file}")

    locales = []

    if args.locale is None:
        # Iterate all locale directories
        for locale in os.listdir(localedir):
            # Check if the .po file exists
            po_path = localedir / locale / "LC_MESSAGES" / f"{domain}.po"
            if not os.path.exists(po_path):
                print(f"Skipping {locale} because {domain}.po does not exist")
                continue
            locales.append(locale)
    else:
        locales = args.locale.split(",")

    # Iterate all locale directories
    for locale in locales:
        # Check if the .po file exists
        po_path = localedir / locale / "LC_MESSAGES" / f"{domain}.po"
        mo_path = localedir / locale / "LC_MESSAGES" / f"{domain}.mo"

        # if not os.path.exists(po_path):
        #     print(f"Skipping {locale} because {domain}.po does not exist")
        #     continue

        # If the .mo file does not exist, create it
        if not os.path.exists(mo_path):
            print(f"Creating {domain}.mo for {locale}")
            os.system(f"msgfmt {po_path} -o {mo_path}")

        print(f"Rendering {scene} in {locale}...")
        # Set LOCALE environment variable to locale
        os.environ["LOCALE"] = locale
        ofile = scene + "_" + locale + ".mp4"
        cmd = [
            f"LOCALE={locale}",
            f"DOMAIN={domain}",
            "manim",
            f"-q{quality}",
            file,
            scene,
            "-o",
            ofile,
            "--disable_caching",
        ]

        # Run manim with the command
        try:
            result = os.system(" ".join(cmd))
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            sys.exit(0)
        except:
            sys.exit(0)

        if result != 0:
            sys.exit(result)


if __name__ == "__main__":
    main()
