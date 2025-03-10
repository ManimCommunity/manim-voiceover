import os
import json
from pathlib import Path
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Create a temporary directory for audio files
temp_dir = Path("./temp_direct_test")
temp_dir.mkdir(exist_ok=True)

# Constants for audio offset resolution (same as in manim-voiceover)
AUDIO_OFFSET_RESOLUTION = 1000  # 1000 = milliseconds

print("=== Direct OpenAI API Test ===")

# First, generate speech using OpenAI TTS
print("\nGenerating speech from text...")
text = "This is a test of the cloud-based Whisper feature."

# Generate speech using OpenAI TTS
response = openai.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=text
)

audio_path = temp_dir / "direct_test.mp3"
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

# Print the raw response structure
print("\nRaw API Response Structure:")
print(f"Response type: {type(transcription)}")
print(f"Response attributes: {dir(transcription)}")
print(f"Has 'words' attribute: {hasattr(transcription, 'words')}")

if hasattr(transcription, 'words'):
    print(f"Words type: {type(transcription.words)}")
    print(f"Words count: {len(transcription.words)}")
    
    # Try to access the first word
    if len(transcription.words) > 0:
        first_word = transcription.words[0]
        print(f"First word type: {type(first_word)}")
        print(f"First word attributes: {dir(first_word)}")
        print(f"First word: {first_word.word if hasattr(first_word, 'word') else 'No word attribute'}")
        print(f"First word start: {first_word.start if hasattr(first_word, 'start') else 'No start attribute'}")

# Convert to word boundaries format used by manim-voiceover
print("\nConverting to word boundaries format...")
word_boundaries = []
current_text_offset = 0

if hasattr(transcription, 'words'):
    for word_obj in transcription.words:
        try:
            word = word_obj.word
            start_time = word_obj.start
            
            # Create a word boundary entry
            word_boundary = {
                "audio_offset": int(start_time * AUDIO_OFFSET_RESOLUTION),
                "text_offset": current_text_offset,
                "word_length": len(word),
                "text": word,
                "boundary_type": "Word",
            }
            
            word_boundaries.append(word_boundary)
            current_text_offset += len(word) + 1  # +1 for space
            
            print(f"Added word boundary: {word} at {start_time}s")
        except Exception as e:
            print(f"Error processing word: {e}")

print(f"\nCreated {len(word_boundaries)} word boundaries")

# Create a cache file that manim-voiceover can use
cache_data = {
    "input_text": text,
    "input_data": {"input_text": text, "service": "openai"},
    "original_audio": audio_path.name,
    "word_boundaries": word_boundaries,
    "transcribed_text": transcription.text,
    "final_audio": audio_path.name
}

cache_file = temp_dir / "cache.json"
with open(cache_file, "w") as f:
    json.dump([cache_data], f, indent=2)

print(f"\nCreated cache file at {cache_file}")
print("\nTest completed!") 