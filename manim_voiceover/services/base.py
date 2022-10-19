from abc import ABC, abstractmethod
import os
import json
import hashlib

from manim_voiceover.modify_audio import adjust_speed


class SpeechService(ABC):
    def __init__(self, global_speed: float = None, output_dir: str = None):
        # self.tts_config = tts_config
        if output_dir is None:
            output_dir = "media/tts"
        if global_speed is None:
            global_speed = 1.00

        self.global_speed = global_speed
        self.output_dir = output_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def synthesize_from_text(self, text: str, path: str = None, **kwargs) -> dict:
        # Replace newlines with lines, reduce multiple consecutive spaces to single
        text = " ".join(text.split())

        dict_ = self.generate_from_text(text, output_dir=None, path=path, **kwargs)
        # path = dict_["original_audio"]
        # import ipdb; ipdb.set_trace()

        if self.global_speed != 1:
            split_path = os.path.splitext(dict_["original_audio"])
            adjusted_path = split_path[0] + "_adjusted" + split_path[1]
            adjust_speed(dict_["original_audio"], adjusted_path, self.global_speed)
            dict_["final_audio"] = adjusted_path
            if "word_boundaries" in dict_:
                for word_boundary in dict_["word_boundaries"]:
                    word_boundary["audio_offset"] = int(
                        word_boundary["audio_offset"] / self.global_speed
                    )
        else:
            dict_["final_audio"] = dict_["original_audio"]

        open(dict_["json_path"], "w").write(json.dumps(dict_))
        return dict_

    def get_data_hash(self, data: dict) -> str:
        dumped_data = json.dumps(data)
        data_hash = hashlib.sha256(dumped_data.encode("utf-8")).hexdigest()
        return data_hash

    @abstractmethod
    def generate_from_text(self, text: str, output_dir: str = None, path: str = None) -> dict:
        raise NotImplementedError
