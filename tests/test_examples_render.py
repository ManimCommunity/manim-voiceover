import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydub import AudioSegment

EXAMPLE_SCENES = [
    ("examples/local-voiceover-example.py", "LocalVoiceoverExample"),
    ("examples/local-bookmark-example.py", "LocalBookmarkExample"),
]


@pytest.mark.parametrize(("example_path", "scene_name"), EXAMPLE_SCENES)
def test_example_renders_video_with_audio(tmp_path, example_path, scene_name):
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
        example_path,
        scene_name,
    ]

    subprocess.run(command, check=True)

    video_path = media_dir / "videos" / Path(example_path).stem / "480p15" / f"{scene_name}.mp4"
    assert video_path.exists(), f"Manim did not render {video_path}"

    stream_info = _ffprobe_audio_stream(video_path)
    assert stream_info["codec_type"] == "audio"

    rendered_audio = AudioSegment.from_file(video_path)
    assert len(rendered_audio) > 0
    assert rendered_audio.dBFS > -60


def _ffprobe_audio_stream(video_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "json",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(result.stdout)["streams"]
    assert streams, f"{video_path} does not contain an audio stream"
    return streams[0]
