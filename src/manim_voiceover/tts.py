import argparse
import sys
from pathlib import Path

from manim_voiceover.modify_audio import get_duration
from manim_voiceover.services.edge import (
    DEFAULT_EDGE_PITCH,
    DEFAULT_EDGE_RATE,
    DEFAULT_EDGE_VOICE,
    DEFAULT_EDGE_VOLUME,
    EdgeTTSService,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manim_voiceover_tts",
        description="Synthesize narration audio with Edge TTS.",
    )
    parser.add_argument("text", nargs="?", help="Narration text. Read from stdin when omitted.")
    parser.add_argument("-o", "--output", default="voiceover.mp3", help="Output MP3 path.")
    parser.add_argument("--voice", default=DEFAULT_EDGE_VOICE, help="Edge TTS voice name.")
    parser.add_argument("--rate", default=DEFAULT_EDGE_RATE, help="Speech rate, e.g. +0%%.")
    parser.add_argument("--pitch", default=DEFAULT_EDGE_PITCH, help="Speech pitch, e.g. +0Hz.")
    parser.add_argument("--volume", default=DEFAULT_EDGE_VOLUME, help="Speech volume, e.g. +0%%.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing output file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    text = args.text
    if text is None:
        text = "" if sys.stdin.isatty() else sys.stdin.read()
    text = " ".join(text.split())
    if not text:
        parser.error("narration text must not be empty")

    output_path = Path(args.output).expanduser().resolve()

    try:
        service = EdgeTTSService(
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch,
            volume=args.volume,
        )
        data = service._wrap_generate_from_text(text, path=output_path, overwrite=args.overwrite)
        final_audio = Path(data["final_audio"])
        if not final_audio.is_absolute():
            final_audio = Path(service.cache_dir) / final_audio
        duration = get_duration(final_audio)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Output: {final_audio}")
    print(f"Duration: {duration:.2f} seconds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
