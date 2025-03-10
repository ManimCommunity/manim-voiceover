import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our modules
from manim_voiceover.services.openai import OpenAIService
from manim_voiceover.config import config

# Set the cloud whisper flag manually
config.use_cloud_whisper = True

print("=== Testing SpeechService with Cloud Whisper ===")

# Create a temporary directory for audio files
temp_dir = Path("./temp_service_test")
temp_dir.mkdir(exist_ok=True)

# Create an OpenAIService with cloud whisper enabled
service = OpenAIService(
    voice="alloy",
    model="tts-1",
    transcription_model="base",
    use_cloud_whisper=True,
    cache_dir=str(temp_dir)
)

print(f"\nOpenAIService created with use_cloud_whisper={service.use_cloud_whisper}")

# Generate speech from text
print("\nGenerating speech from text...")
text = "This is a direct test of the cloud-based Whisper feature."

# Call the _wrap_generate_from_text method directly
result = service._wrap_generate_from_text(text)

print(f"\nSpeech generated successfully!")
print(f"Audio file: {result.get('final_audio')}")
print(f"Word boundaries available: {'word_boundaries' in result}")
print(f"Word boundaries count: {len(result.get('word_boundaries', []))}")
print(f"Transcribed text: {result.get('transcribed_text', 'Not available')}")

# Print the word boundaries
if 'word_boundaries' in result and result['word_boundaries']:
    print("\nWord boundaries:")
    for i, boundary in enumerate(result['word_boundaries']):
        # Convert from milliseconds to seconds
        time_in_seconds = boundary['audio_offset'] / 1000
        print(f"  {i+1}. '{boundary['text']}' at {time_in_seconds:.2f} seconds")
else:
    print("\nNo word boundaries found in the result.")

print("\nTest completed!") 