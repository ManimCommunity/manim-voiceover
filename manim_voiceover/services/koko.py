"""
Copyright (c) 2025 Xposed73
All rights reserved.
This file is part of the Manim Voiceover project.
"""

import hashlib
import json
from pathlib import Path
from manim_voiceover.services.base import SpeechService
import shutil
from gradio_client import Client
from manim_voiceover.helper import remove_bookmarks, wav2mp3


class KokoroService(SpeechService):
    """Speech service class for kokoro_self (using text_to_speech via Gradio API)."""

    def __init__(self, engine=None, voice: str = 'af_bella', api_url: str = 'http://127.0.0.1:7860/',
                 model: str = "kokoro-v0_19.pth", speed: int = 1, trim: int = 0,
                 pad_between_segments: int = 0, remove_silence: bool = False,
                 minimum_silence: int = 0.05, **kwargs):
        self.voice = voice
        self.api_url = api_url
        self.model = model
        self.speed = speed
        self.trim = trim
        self.pad_between_segments = pad_between_segments
        self.remove_silence = remove_silence
        self.minimum_silence = minimum_silence

        if engine is None:
            engine = self.text_to_speech  # Default to local function

        self.engine = engine
        SpeechService.__init__(self, **kwargs)

    def get_data_hash(self, input_data: dict) -> str:
        """
        Generates a hash based on the input data dictionary.
        The hash is used to create a unique identifier for the input data.

        Parameters:
            input_data (dict): A dictionary of input data (e.g., text, voice, etc.).

        Returns:
            str: The generated hash as a string.
        """
        # Convert the input data dictionary to a JSON string (sorted for consistency)
        data_str = json.dumps(input_data, sort_keys=True)
        
        # Generate a SHA-256 hash of the JSON string
        data_hash = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        return data_hash

    def text_to_speech(self, text, output_file, voice_name, model, speed, trim, pad_between_segments, remove_silence, minimum_silence):
        """
        Generates speech from text using a specified model and saves the audio file.
        This function now interacts with the local Gradio API for text-to-speech.
        """
        # Initialize the Gradio client
        client = Client(self.api_url)

        # Call the API with provided parameters
        result = client.predict(
            text=text,
            model_name=model,
            voice_name=voice_name,
            speed=speed,
            trim=trim,
            pad_between_segments=pad_between_segments,
            remove_silence=remove_silence,
            minimum_silence=minimum_silence,
            api_name="/text_to_speech"
        )

        # Save the audio file in the specified directory
        shutil.move(result, output_file)
        print(f"Saved at {output_file}")

        return output_file

    def generate_from_text(self, text: str, cache_dir: str = None, path: str = None) -> dict:
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_data = {"input_text": text, "service": "kokoro_self"}

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_data_hash(input_data) + ".mp3"  # Correct method call with self
        else:
            audio_path = path

        # Generate .wav file using the modified text_to_speech function
        audio_path_str = str(Path(cache_dir) / audio_path.replace(".mp3", ".wav"))
        self.engine(
            text=text,
            output_file=audio_path_str,
            voice_name=self.voice,
            model=self.model,
            speed=self.speed,
            trim=self.trim,
            pad_between_segments=self.pad_between_segments,
            remove_silence=self.remove_silence,
            minimum_silence=self.minimum_silence
        )
        
        # Convert .wav to .mp3
        mp3_audio_path = str(Path(cache_dir) / audio_path)
        wav2mp3(audio_path_str, mp3_audio_path)

        # Remove original .wav file
        remove_bookmarks(audio_path_str)

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
