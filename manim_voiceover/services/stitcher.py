import os
import json
import itertools
from pydub import AudioSegment
from typing import Tuple, Iterable

# from pydub.silence import split_on_silence

from pydub.silence import detect_nonsilent
import hashlib

from manim_voiceover.services.base import SpeechService


# Had to modify `split_on_silence` from pydub to allow for
# keeping different durations of silence at chunk beginnings and ends
def split_on_silence_modified(
    audio_segment: str,
    min_silence_len: int = 1000,
    silence_thresh: int = -16,
    keep_silence: Tuple[int, int] = (100, 1000),
    seek_step: int = 10,
    **kwargs,
):
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
    def pairwise(iterable: Iterable) -> zip:
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    if isinstance(keep_silence, bool):
        keep_silence_begin = len(audio_segment) if keep_silence else 0
        keep_silence_end = keep_silence_begin
    elif isinstance(keep_silence, float) or isinstance(keep_silence, int):
        keep_silence_begin = keep_silence
        keep_silence_end = keep_silence
    elif isinstance(keep_silence, list) or isinstance(keep_silence, tuple):
        assert len(keep_silence) == 2
        keep_silence_begin = keep_silence[0]
        keep_silence_end = keep_silence[1]

    output_ranges = [
        [start - keep_silence_begin, end + keep_silence_end]
        for (start, end) in detect_nonsilent(
            audio_segment, min_silence_len, silence_thresh, seek_step
        )
    ]

    for range_i, range_ii in pairwise(output_ranges):
        last_end = range_i[1]
        next_start = range_ii[0]
        if next_start < last_end:
            range_i[1] = (last_end + next_start) // 2
            range_ii[0] = range_i[1]

    return [
        audio_segment[max(start, 0) : min(end, len(audio_segment))]
        for start, end in output_ranges
    ]


# Disable this for now
class _StitcherService(SpeechService):
    """Speech service for stitching audio recordings back onto a Manim scene"""

    def __init__(
        self,
        source_path: str,
        min_silence_len: int = 2000,
        silence_thresh: int = -45,
        seek_step: int = 10,
        keep_silence: Tuple[int, int] = (100, 1000),
        **kwargs,
    ):
        self.params = {
            "source_path": source_path,
            "min_silence_len": min_silence_len,
            "silence_thresh": silence_thresh,
            "seek_step": seek_step,
            "keep_silence": keep_silence,
        }

        SpeechService.__init__(self, **kwargs)
        self.process_audio()
        self.current_segment_index = 0

    def process_audio(self) -> None:
        segment = AudioSegment.from_file(self.params["source_path"])

        # Check whether the audio file has already been processed
        if os.path.exists(self.get_json_path()):
            config = json.load(open(self.get_json_path(), "r"))
            try:
                if self.params == config["params"]:
                    all_files_exist = True
                    for segment in config["segments"]:
                        if not os.path.exists(segment["path"]):
                            all_files_exist = False
                            break
                    # Return only if all the segments exist
                    if all_files_exist:
                        return
            except KeyError:
                pass

        chunks = split_on_silence_modified(segment, **self.params)

        output_dict = {
            "params": self.params,
            "segments": [],
        }
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
            output_dict["segments"].append({"index": i, "path": output_path})

        # Save output info
        with open(self.get_json_path(), "w") as f:
            f.write(json.dumps(output_dict, indent=4))

    def get_json_path(self) -> str:
        return os.path.splitext(self.params["source_path"])[0] + ".json"

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None
    ) -> dict:
        config = json.load(open(self.get_json_path(), "r"))
        audio_path = config["segments"][self.current_segment_index]["path"]
        json_path = os.path.splitext(audio_path)[0] + ".json"

        self.current_segment_index += 1

        json_dict = {
            # "word_boundaries": word_boundaries,
            "input_text": text,
            # "input_data": input_data,
            "original_audio": audio_path,
            "json_path": json_path,
        }

        return json_dict
