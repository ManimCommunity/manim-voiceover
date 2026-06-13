import json
import subprocess
from pathlib import Path
from typing import List, Mapping, Sequence, cast

import numpy as np
from pydub import AudioSegment


def assert_video_has_audio_stream(video_path: Path) -> None:
    stream_info = _ffprobe_audio_stream(video_path)
    assert stream_info["codec_type"] == "audio"


def load_audible_audio(video_path: Path) -> AudioSegment:
    audio = AudioSegment.from_file(video_path)
    assert len(audio) > 0
    assert audio.dBFS > -60
    return audio


def assert_audio_is_speech_like(audio: AudioSegment, minimum_median_bandwidth_hz: float = 250) -> None:
    bandwidth = _median_spectral_bandwidth(audio)
    assert bandwidth > minimum_median_bandwidth_hz, (
        f"Expected speech-like audio bandwidth above {minimum_median_bandwidth_hz} Hz, got {bandwidth:.2f} Hz"
    )


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
