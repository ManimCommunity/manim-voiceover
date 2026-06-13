import json
import subprocess
import sys
from pathlib import Path
from typing import List, Mapping, Sequence, Tuple, cast

import numpy as np
import pytest
from pydub import AudioSegment

EXAMPLE_SCENES: Sequence[Tuple[str, str]] = [
    ("examples/gtts-example.py", "GTTSExample"),
]


@pytest.mark.parametrize(("example_path", "scene_name"), EXAMPLE_SCENES)
def test_actual_example_renders_video_with_audible_speech(tmp_path: Path, example_path: str, scene_name: str) -> None:
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
    assert _median_spectral_bandwidth(rendered_audio) > 250


def _ffprobe_audio_stream(video_path: Path) -> Mapping[str, object]:
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
    ffprobe_output = cast(Mapping[str, object], json.loads(result.stdout))
    streams = cast(Sequence[Mapping[str, object]], ffprobe_output["streams"])
    assert streams, f"{video_path} does not contain an audio stream"
    return streams[0]


def _median_spectral_bandwidth(audio: AudioSegment) -> float:
    samples_per_second = 16_000
    frame_size = 2048
    step = 1024
    normalized = audio.set_channels(1).set_frame_rate(samples_per_second)
    samples = np.array(normalized.get_array_of_samples(), dtype=np.float64)
    if samples.size < frame_size:
        return 0.0

    max_amplitude = float(1 << (8 * normalized.sample_width - 1))
    samples = samples / max_amplitude
    frequencies = np.fft.rfftfreq(frame_size, d=1 / samples_per_second)
    bandwidths: List[float] = []
    for start in range(0, samples.size - frame_size + 1, step):
        frame = samples[start : start + frame_size]
        if float(np.sqrt(np.mean(frame**2))) < 0.005:
            continue
        spectrum = np.abs(np.fft.rfft(frame * np.hanning(frame_size)))
        magnitude_sum = float(np.sum(spectrum))
        if magnitude_sum <= 0:
            continue
        centroid = float(np.sum(frequencies * spectrum) / magnitude_sum)
        bandwidth = float(np.sqrt(np.sum(((frequencies - centroid) ** 2) * spectrum) / magnitude_sum))
        bandwidths.append(bandwidth)

    if not bandwidths:
        return 0.0
    return float(np.median(bandwidths))
