from abc import ABC, abstractmethod
import typing as t
import os
import json
import sys
import hashlib
from pathlib import Path
from manim import config, logger
from slugify import slugify
from manim_voiceover.defaults import (
    DEFAULT_VOICEOVER_CACHE_DIR,
    DEFAULT_VOICEOVER_CACHE_JSON_FILENAME,
)
from manim_voiceover.helper import (
    append_to_json_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.modify_audio import adjust_speed
from manim_voiceover.tracker import AUDIO_OFFSET_RESOLUTION


def timestamps_to_word_boundaries(segments):
    word_boundaries = []
    current_text_offset = 0
    
    # Check if we have direct word-level timestamps (from OpenAI API)
    if isinstance(segments, list) and len(segments) > 0 and "words" in segments[0]:
        # Process segment-level timestamps
        for segment in segments:
            for dict_ in segment["words"]:
                word = dict_["word"]
                word_boundaries.append(
                    {
                        "audio_offset": int(dict_["start"] * AUDIO_OFFSET_RESOLUTION),
                        "text_offset": current_text_offset,
                        "word_length": len(word),
                        "text": word,
                        "boundary_type": "Word",
                    }
                )
                current_text_offset += len(word)
    # Check if we have direct word-level timestamps in a flat structure (from OpenAI API)
    elif isinstance(segments, list) and len(segments) > 0 and isinstance(segments[0], dict) and "word" in segments[0]:
        # Process word-level timestamps directly
        for dict_ in segments:
            word = dict_["word"]
            word_boundaries.append(
                {
                    "audio_offset": int(dict_["start"] * AUDIO_OFFSET_RESOLUTION),
                    "text_offset": current_text_offset,
                    "word_length": len(word),
                    "text": word,
                    "boundary_type": "Word",
                }
            )
            current_text_offset += len(word)
    else:
        # Original implementation for local Whisper
        for segment in segments:
            for dict_ in segment["words"]:
                word = dict_["word"]
                word_boundaries.append(
                    {
                        "audio_offset": int(dict_["start"] * AUDIO_OFFSET_RESOLUTION),
                        "text_offset": current_text_offset,
                        "word_length": len(word),
                        "text": word,
                        "boundary_type": "Word",
                    }
                )
                current_text_offset += len(word)

    return word_boundaries


class SpeechService(ABC):
    """Abstract base class for a speech service."""

    def __init__(
        self,
        global_speed: float = 1.00,
        cache_dir: t.Optional[str] = None,
        transcription_model: t.Optional[str] = "whisper-1",
        transcription_kwargs: dict = {},
        use_cloud_whisper: bool = True,
        **kwargs,
    ):
        """Initialize the speech service.

        Args:
            global_speed (float, optional): The global speed factor for the
                generated audio. Defaults to 1.00.
            cache_dir (t.Optional[str], optional): The directory where the
                generated audio will be cached. Defaults to None.
            transcription_model (t.Optional[str], optional): The Whisper model
                to use for transcription. Defaults to "whisper-1".
            transcription_kwargs (dict, optional): Keyword arguments to pass
                to the transcribe() function. Defaults to {}.
            use_cloud_whisper (bool, optional): Whether to use OpenAI's cloud-based
                Whisper API for transcription instead of the local model. Defaults to True.
        """
        self.global_speed = global_speed

        if cache_dir is not None:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = Path(config.media_dir) / DEFAULT_VOICEOVER_CACHE_DIR

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.transcription_model = None
        self._whisper_model = None
        self.use_cloud_whisper = use_cloud_whisper
        self.set_transcription(model=transcription_model, kwargs=transcription_kwargs)

        self.additional_kwargs = kwargs

    def _wrap_generate_from_text(self, text: str, path: str = None, **kwargs) -> dict:
        # Replace newlines with spaces, reduce multiple consecutive spaces to single
        text = " ".join(text.split())

        dict_ = self.generate_from_text(text, cache_dir=None, path=path, **kwargs)
        original_audio = dict_["original_audio"]

        # Check whether word boundaries exist and if not run stt
        if "word_boundaries" not in dict_ and (self._whisper_model is not None or self.use_cloud_whisper):
            if self.use_cloud_whisper:
                # Use OpenAI's cloud-based Whisper API
                try:
                    import openai
                    from dotenv import find_dotenv, load_dotenv
                    load_dotenv(find_dotenv(usecwd=True))
                    
                    if os.getenv("OPENAI_API_KEY") is None:
                        from manim_voiceover.services.openai import create_dotenv_openai
                        create_dotenv_openai()
                    
                    audio_file_path = str(Path(self.cache_dir) / original_audio)
                    with open(audio_file_path, "rb") as audio_file:
                        transcription_result = openai.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="verbose_json",
                            timestamp_granularities=["word"],
                            **self.transcription_kwargs
                        )
                    
                    # Convert the word timestamps to word boundaries directly
                    logger.info("Cloud Transcription: " + transcription_result.text)
                    logger.info(f"Word count: {len(transcription_result.words) if hasattr(transcription_result, 'words') else 0}")
                    
                    word_boundaries = []
                    current_text_offset = 0
                    
                    if hasattr(transcription_result, 'words') and transcription_result.words:
                        logger.info(f"Processing {len(transcription_result.words)} words")
                        for word_obj in transcription_result.words:
                            try:
                                word = word_obj.word.strip()  # Remove any leading/trailing whitespace
                                start_time = word_obj.start
                                
                                # Skip words that are just punctuation or empty
                                if not word or word.isspace() or (len(word) == 1 and not word.isalnum()):
                                    continue
                                
                                word_boundary = {
                                    "audio_offset": int(start_time * AUDIO_OFFSET_RESOLUTION),
                                    "text_offset": current_text_offset,
                                    "word_length": len(word),
                                    "text": word,
                                    "boundary_type": "Word",
                                }
                                
                                word_boundaries.append(word_boundary)
                                current_text_offset += len(word) + 1  # +1 for space
                                
                                logger.info(f"Added word boundary: {word} at {start_time}s")
                            except Exception as e:
                                logger.error(f"Error processing word: {e}")
                    else:
                        logger.warning("No words found in transcription result")
                    
                    logger.info(f"Created {len(word_boundaries)} word boundaries")
                    dict_["word_boundaries"] = word_boundaries
                    dict_["transcribed_text"] = transcription_result.text
                    
                except ImportError:
                    logger.error(
                        'Missing packages. Run `pip install "manim-voiceover[openai]"` to use cloud-based Whisper.'
                    )
                    return dict_
                except Exception as e:
                    logger.error(f"Error using cloud-based Whisper: {str(e)}")
                    return dict_
            else:
                # Use local Whisper model only if it's properly loaded
                if self._whisper_model is not None and not isinstance(self._whisper_model, bool):
                    try:
                        transcription_result = self._whisper_model.transcribe(
                            str(Path(self.cache_dir) / original_audio), **self.transcription_kwargs
                        )
                        
                        logger.info("Transcription: " + transcription_result.text)
                        
                        # For local Whisper model, use segments_to_dicts
                        if hasattr(transcription_result, 'segments_to_dicts'):
                            word_boundaries = timestamps_to_word_boundaries(
                                transcription_result.segments_to_dicts()
                            )
                            dict_["word_boundaries"] = word_boundaries
                            dict_["transcribed_text"] = transcription_result.text
                        else:
                            logger.error("Local Whisper model returned unexpected result format.")
                            return dict_
                    except Exception as e:
                        logger.error(f"Error using local Whisper model: {str(e)}")
                        return dict_
                else:
                    logger.error(
                        "Local Whisper model is not available. Please set use_cloud_whisper=True or install the local model with `pip install \"manim-voiceover[transcribe]\"`."
                    )
                    return dict_

        # Audio callback
        self.audio_callback(original_audio, dict_, **kwargs)

        if self.global_speed != 1:
            split_path = os.path.splitext(original_audio)
            adjusted_path = split_path[0] + "_adjusted" + split_path[1]

            adjust_speed(
                str(Path(self.cache_dir) / dict_["original_audio"]),
                str(Path(self.cache_dir) / adjusted_path),
                self.global_speed,
            )
            dict_["final_audio"] = adjusted_path
            if "word_boundaries" in dict_:
                for word_boundary in dict_["word_boundaries"]:
                    word_boundary["audio_offset"] = int(
                        word_boundary["audio_offset"] / self.global_speed
                    )
        else:
            dict_["final_audio"] = dict_["original_audio"]

        append_to_json_file(
            Path(self.cache_dir) / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME, dict_
        )
        return dict_
    
    def set_transcription(self, model: str = None, kwargs: dict = {}):
        """Set the transcription model and keyword arguments to be passed
        to the transcribe() function.

        Args:
            model (str, optional): The Whisper model to use for transcription. Defaults to None.
            kwargs (dict, optional): Keyword arguments to pass to the transcribe() function. Defaults to {}.
        """
        self.transcription_model = model
        self.transcription_kwargs = kwargs
        
        if model != self.transcription_model or self._whisper_model is None:
            if model is not None:
                if self.use_cloud_whisper:
                    # For cloud-based Whisper, we don't need to load a local model
                    # but we still need the OpenAI package
                    try:
                        import openai
                        self._whisper_model = True  # Just a placeholder to indicate we can use cloud whisper
                    except ImportError:
                        logger.error(
                            'Missing packages. Run `pip install "manim-voiceover[openai]"` to use cloud-based Whisper.'
                        )
                        self._whisper_model = None
                else:
                    # Load local Whisper model
                    try:
                        import whisper as __tmp
                        import stable_whisper as whisper
                    except ImportError:
                        logger.error(
                            'Missing packages. Run `pip install "manim-voiceover[transcribe]"` to be able to transcribe voiceovers.'
                        )

                    prompt_ask_missing_extras(
                        ["whisper", "stable_whisper"],
                        "transcribe",
                        "SpeechService.set_transcription()",
                    )
                    self._whisper_model = whisper.load_model(model)
            else:
                self._whisper_model = None

    def get_audio_basename(self, data: dict) -> str:
        dumped_data = json.dumps(data)
        data_hash = hashlib.sha256(dumped_data.encode("utf-8")).hexdigest()
        suffix = data_hash[:8]
        input_text = data["input_text"]
        input_text = remove_bookmarks(input_text)
        slug = slugify(input_text, max_length=50, word_boundary=True, save_order=True)
        ret = f"{slug}-{suffix}"
        return ret

    @abstractmethod
    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None
    ) -> dict:
        """Implement this method for each speech service. Refer to `AzureService` for an example.

        Args:
            text (str): The text to synthesize speech from.
            cache_dir (str, optional): The output directory to save the audio file and data to. Defaults to None.
            path (str, optional): The path to save the audio file to. Defaults to None.

        Returns:
            dict: Output data dictionary. TODO: Define the format.
        """
        raise NotImplementedError

    def get_cached_result(self, input_data, cache_dir):
        json_path = os.path.join(cache_dir, DEFAULT_VOICEOVER_CACHE_JSON_FILENAME)
        if os.path.exists(json_path):
            json_data = json.load(open(json_path, "r"))
            for entry in json_data:
                if entry["input_data"] == input_data:
                    return entry
        return None

    def audio_callback(self, audio_path: str, data: dict, **kwargs):
        """Callback function for when the audio file is ready.
        Override this method to do something with the audio file, e.g. noise reduction.

        Args:
            audio_path (str): The path to the audio file.
            data (dict): The data dictionary.
        """
        pass
