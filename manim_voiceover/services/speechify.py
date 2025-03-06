import os
import base64
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Union

from dotenv import find_dotenv, load_dotenv
from manim import logger

from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService

load_dotenv(find_dotenv(usecwd=True))


class SpeechifyService(SpeechService):

    def __init__(
        self,
        voice_id: str,  # for custom cloned voices, use the voice_id of the cloned voice
        model: str = "simba-english",
        audio_format: str = "mp3",
        api_key: str = os.getenv("SPEECHIFY_API_KEY"),
        transcription_model: Optional[str] = None,
        global_speed: float = 1.0,
        **kwargs,
    ):
        if not voice_id:
            raise ValueError("Voice ID is required. Please provide a valid voice ID.")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.audio_format = audio_format
        self.global_speed = global_speed
        
        self.access_token = None
        self.token_expiry = 0
        
        # If transcription_model is None, skip setting up transcription to avoid
        # requiring the additional dependencies
        if transcription_model is None:
            self.cache_dir = kwargs.get("cache_dir", os.path.join(os.getcwd(), ".manim-voiceover", "cache"))
            os.makedirs(self.cache_dir, exist_ok=True)
            self.transcription_model = None
            self._whisper_model = None
            self.is_whisper_loaded = False
            self.additional_kwargs = kwargs
        else:
            # Normal initialization with transcription
            SpeechService.__init__(self, transcription_model=transcription_model, global_speed=global_speed, **kwargs)
    
    def _refresh_token(self, force: bool = False) -> None:
        current_time = time.time()
        if not force and self.access_token and current_time < self.token_expiry - 60:
            return
            
        try:
            headers = {
                "accept": "*/*",
                "content-type": "application/json",
                "Authorization": self.api_key
            }
            
            data = {
                "grant_type": "client_credentials"
            }
            
            response = requests.post(
                "https://api.sws.speechify.com/v1/auth/token",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            # Calculate expiry time (current time + expires_in - 30 minute buffer)
            self.token_expiry = current_time + token_data["expires_in"] - 30*60
            
            logger.info("Successfully generated new Speechify access token.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate Speechify token: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to generate Speechify access token: {e}")
    
    def _make_api_request(self, text: str, retry_auth: bool = True) -> Dict[str, Any]:
        self._refresh_token()
        
        if not text.startswith("<speak>"):
            text = f"<speak>{text}</speak>"
        
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        data = {
            "input": text,
            "voice_id": self.voice_id,
            "audio_format": self.audio_format,
            "model": self.model
        }
        
        try:
            response = requests.post(
                "https://api.sws.speechify.com/v1/audio/speech",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 and retry_auth:
                logger.warning("Token expired or invalid. Refreshing token and retrying...")
                self._refresh_token(force=True)
                return self._make_api_request(text, retry_auth=False)  # Prevent infinite retry loop
            
            logger.error(f"Speechify API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to communicate with Speechify API: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Speechify API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to communicate with Speechify API: {e}")

    def generate_from_text(
        self,
        text: str,
        cache_dir: Optional[Union[str, Path]] = None,
        path: Optional[str] = None,
        **kwargs,
    ) -> dict:
        if cache_dir is None:
            cache_dir = self.cache_dir  # type: ignore

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "speechify",
            "config": {
                "model": self.model,
                "voice_id": self.voice_id,
                "audio_format": self.audio_format,
                "global_speed": self.global_speed,
            },
        }

        try:
            if isinstance(cache_dir, str):
                cache_dir_path = Path(cache_dir)
            else:
                cache_dir_path = cache_dir
                
            cached_result = self.get_cached_result(input_data, cache_dir_path)
            if cached_result is not None:
                return cached_result
        except Exception as e:
            logger.warning(f"Error checking cache: {e}")

        if path is None:
            audio_path = self.get_audio_basename(input_data) + f".{self.audio_format}"
        else:
            audio_path = path

        try:
            response = self._make_api_request(input_text)
            
            audio_data = base64.b64decode(response["audio_data"])
            
            if isinstance(cache_dir, str):
                cache_path = Path(cache_dir)
            else:
                cache_path = cache_dir
                
            full_audio_path = cache_path / audio_path
            
            os.makedirs(os.path.dirname(str(full_audio_path)), exist_ok=True)
            
            with open(full_audio_path, "wb") as f:
                f.write(audio_data)
                
        except Exception as e:
            logger.error(e)
            raise Exception(f"Failed to generate speech using Speechify: {e}")

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "final_audio": audio_path,
            "speech_marks": response.get("speech_marks", {}),
            "billable_characters_count": response.get("billable_characters_count", 0)
        }

        return json_dict