from abc import ABC, abstractmethod
import os
import json
import hashlib

from manim_voiceover.modify_audio import adjust_speed


class SpeechService(ABC):
    """Abstract base class for a speech service.
    """
    def __init__(self, global_speed: float = 1.00, output_dir: str = "media/tts", **kwargs):
        """
        Args:
            global_speed (float, optional): The speed at which to play the audio. Defaults to 1.00.
            output_dir (str, optional): The directory to save the audio files to. Defaults to "media/tts".
        """
        # TODO: Get output_dir from Manim config
        self.global_speed = global_speed
        self.output_dir = output_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _wrap_generate_from_text(self, text: str, path: str = None, **kwargs) -> dict:
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
        """Implement this method for each speech service. Refer to `AzureService` for an example.

        Args:
            text (str): The text to synthesize speech from.
            output_dir (str, optional): The output directory to save the audio file and data to. Defaults to None.
            path (str, optional): The path to save the audio file to. Defaults to None.

        Returns:
            dict: Output data dictionary. TODO: Define the format.
        """
        raise NotImplementedError
