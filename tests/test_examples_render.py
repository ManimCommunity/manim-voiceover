import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pytest

from _render_assertions import assert_audio_is_speech_like, assert_video_has_audio_stream, load_audible_audio


@dataclass(frozen=True)
class RenderableExample:
    path: Path
    scene_name: str


EXAMPLE_SCENES: Sequence[RenderableExample] = [
    RenderableExample(path=Path("examples/gtts-example.py"), scene_name="GTTSExample"),
]


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.parametrize("example", EXAMPLE_SCENES, ids=lambda example: example.scene_name)
def test_gtts_example_renders_speech_like_audio(tmp_path: Path, example: RenderableExample) -> None:
    if Path.cwd().name == "mutants":
        pytest.skip("mutmut does not copy example files into its generated worktree")

    media_dir = tmp_path / "media"
    command = [
        sys.executable,
        "-m",
        "manim",
        "-ql",
        "--disable_caching",
        "--media_dir",
        str(media_dir),
        str(example.path),
        example.scene_name,
    ]

    subprocess.run(command, check=True)

    video_path = media_dir / "videos" / example.path.stem / "480p15" / f"{example.scene_name}.mp4"
    assert video_path.exists(), f"Manim did not render {video_path}"

    assert_video_has_audio_stream(video_path)
    assert_audio_is_speech_like(load_audible_audio(video_path))
