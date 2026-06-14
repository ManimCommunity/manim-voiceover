import hashlib
import itertools
import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from pydub import AudioSegment

# from pydub.silence import split_on_silence
from pydub.silence import detect_nonsilent

from manim_voiceover._typing import JsonValue, VoiceoverData
from manim_voiceover.services.base import PathLike, SpeechService, initialize_speech_service


# Had to modify `split_on_silence` from pydub to allow for
# keeping different durations of silence at chunk beginnings and ends
def split_on_silence_modified(
    audio_segment: AudioSegment,
    min_silence_len: int = 1000,
    silence_thresh: int = -16,
    keep_silence: bool | int | tuple[int, int] = (100, 1000),
    seek_step: int = 10,
    **kwargs: object,
) -> list[AudioSegment]:
    """
    Returns list of audio segments from splitting audio_segment on silent sections

    audio_segment - original pydub.AudioSegment() object

    min_silence_len - (in ms) minimum length of a silence to be used for
        a split. default: 1000ms

    silence_thresh - (in dBFS) anything quieter than this will be
        considered silence. default: -16dBFS

    keep_silence - (in ms or True/False) leave some silence at the beginning
        and end of the chunks. Keeps the sound from sounding like it
        is abruptly cut off.
        When the length of the silence is less than the keep_silence duration
        it is split evenly between the preceding and following non-silent
        segments.
        If True is specified, all the silence is kept, if False none is kept.
        default: 100ms

    seek_step - step size for interating over the segment in ms
    """

    # from the itertools documentation
    def pairwise(iterable: Iterable[list[int]]) -> Iterator[tuple[list[int], list[int]]]:
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    if isinstance(keep_silence, bool):
        keep_silence_begin = len(audio_segment) if keep_silence else 0
        keep_silence_end = keep_silence_begin
    elif isinstance(keep_silence, int):
        keep_silence_begin = keep_silence
        keep_silence_end = keep_silence
    else:
        keep_silence_begin = keep_silence[0]
        keep_silence_end = keep_silence[1]

    output_ranges = [
        [start - keep_silence_begin, end + keep_silence_end]
        for (start, end) in detect_nonsilent(audio_segment, min_silence_len, silence_thresh, seek_step)
    ]

    for range_i, range_ii in pairwise(output_ranges):
        last_end = range_i[1]
        next_start = range_ii[0]
        # pragma: no mutate start
        if next_start < last_end:
            range_i[1] = (last_end + next_start) // 2
            range_ii[0] = range_i[1]
        # pragma: no mutate end

    return [audio_segment[max(start, 0) : min(end, len(audio_segment))] for start, end in output_ranges]


# Disable this for now
class _StitcherService(SpeechService):
    """Speech service for stitching audio recordings back onto a Manim scene"""

    def __init__(
        self,
        source_path: str,
        min_silence_len: int = 2000,
        silence_thresh: int = -45,
        seek_step: int = 10,
        keep_silence: tuple[int, int] = (100, 1000),
        **kwargs: object,
    ) -> None:
        self.source_path = source_path
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.seek_step = seek_step
        self.keep_silence = keep_silence

        initialize_speech_service(self, kwargs)
        self.process_audio()
        self.current_segment_index = 0

    def _params(self) -> dict[str, JsonValue]:
        return {
            "source_path": self.source_path,
            "min_silence_len": self.min_silence_len,
            "silence_thresh": self.silence_thresh,
            "seek_step": self.seek_step,
            "keep_silence": list(self.keep_silence),
        }

    def process_audio(self) -> None:
        segment = AudioSegment.from_file(self.source_path)

        # Check whether the audio file has already been processed
        if os.path.exists(self.get_json_path()):
            config = json.loads(Path(self.get_json_path()).read_text())
            try:
                if self._params() == config["params"]:
                    # Return only if all the segments exist
                    if all(os.path.exists(segment["path"]) for segment in config["segments"]):
                        return
            except KeyError:
                pass

        chunks = split_on_silence_modified(
            segment,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            seek_step=self.seek_step,
            keep_silence=self.keep_silence,
        )

        output_dict: dict[str, object] = {
            "params": self._params(),
        }
        segments: list[dict[str, object]] = []
        for i, chunk in enumerate(chunks):
            # silence_chunk = AudioSegment.silent(duration=800)
            # audio_chunk = chunk + silence_chunk
            audio_chunk = chunk
            # normalized_chunk = match_target_amplitude(audio_chunk, -20.0)
            data_hash = hashlib.sha256(audio_chunk.raw_data).hexdigest()

            # Export the audio chunk with new bitrate.
            output_path = os.path.join(self.cache_dir, data_hash + ".mp3")
            audio_chunk.export(
                output_path,
                bitrate="256k",
                format="mp3",
            )
            segments.append({"index": i, "path": output_path})

        # Save output info
        output_dict["segments"] = segments
        with open(self.get_json_path(), "w") as f:
            f.write(json.dumps(output_dict, indent=4))

    def get_json_path(self) -> str:
        return os.path.splitext(self.source_path)[0] + ".json"

    def generate_from_text(
        self,
        text: str,
        cache_dir: PathLike | None = None,
        path: PathLike | None = None,
        **kwargs: object,
    ) -> VoiceoverData:
        config = json.loads(Path(self.get_json_path()).read_text())
        audio_path = config["segments"][self.current_segment_index]["path"]
        json_path = os.path.splitext(audio_path)[0] + ".json"

        self.current_segment_index += 1

        json_dict: VoiceoverData = {
            # "word_boundaries": word_boundaries,
            "input_text": text,
            # "input_data": input_data,
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict
