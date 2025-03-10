import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import OpenAI directly
import openai

print("=== OpenAI API Debug ===")

# Check if OpenAI API key is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key or openai_api_key == "your_openai_api_key_here":
    print("\n⚠️ Warning: OPENAI_API_KEY is not set or is using the default value.")
    print("Please edit the .env file with your actual OpenAI API key.")
    sys.exit(1)

# Create a temporary directory for audio files
temp_dir = Path("./temp_debug")
temp_dir.mkdir(exist_ok=True)

# First, generate speech using OpenAI TTS
print("\nGenerating speech from text...")
text = "This is a test of the cloud-based Whisper feature."

# Generate speech using OpenAI TTS
response = openai.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=text
)

audio_path = temp_dir / "test_speech.mp3"
response.stream_to_file(str(audio_path))

print(f"Speech generated and saved to {audio_path}")

# Now, transcribe the audio using OpenAI Whisper API
print("\nTranscribing audio with word-level timestamps...")
with open(audio_path, "rb") as audio_file:
    transcription = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word"]
    )

# Print the raw response
print("\nRaw API Response:")
print(json.dumps(transcription.model_dump(), indent=2))

# Check if word-level timestamps are available
print("\nChecking for word-level timestamps:")
if hasattr(transcription, "words"):
    print(f"Found {len(transcription.words)} words with timestamps:")
    for i, word in enumerate(transcription.words):
        print(f"  {i+1}. '{word.word}' from {word.start:.2f}s to {word.end:.2f}s")
else:
    print("No word-level timestamps found in the response.")

print("\nDebug completed!") 