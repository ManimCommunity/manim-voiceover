import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from manim_voiceover.services.openai import OpenAIService
from manim_voiceover.config import config
from manim_voiceover.helper import remove_bookmarks

# Set the cloud whisper flag manually
config.use_cloud_whisper = True

print("=== OpenAI TTS + Cloud-based Whisper Demo ===")
print(f"Cloud Whisper enabled: {config.use_cloud_whisper}")

# Create a temporary directory for audio files
temp_dir = Path("./temp_openai_demo")
temp_dir.mkdir(exist_ok=True)

# Create an OpenAIService with cloud whisper enabled
service = OpenAIService(
    voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
    model="tts-1",  # tts-1 or tts-1-hd
    transcription_model="base",  # Model name is still required
    use_cloud_whisper=True,      # This enables cloud-based Whisper
    cache_dir=str(temp_dir)
)

print(f"\nOpenAIService created with use_cloud_whisper={service.use_cloud_whisper}")

# Check if OpenAI API key is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key or openai_api_key == "your_openai_api_key_here":
    print("\n⚠️ Warning: OPENAI_API_KEY is not set or is using the default value.")
    print("Please edit the .env file with your actual OpenAI API key.")
    sys.exit(1)

# Generate speech from text with bookmarks
print("\nGenerating speech from text with bookmarks...")
text = """This demonstration uses OpenAI's text-to-speech service 
with <bookmark mark='cloud_point'/> cloud-based Whisper for 
word-level <bookmark mark='alignment_point'/> alignment."""

print("\nText to synthesize:")
print(text)

# Generate the speech
result = service._wrap_generate_from_text(text)

print(f"\nSpeech generated successfully!")
print(f"Audio file: {result.get('final_audio')}")
print(f"Audio path: {temp_dir / result.get('final_audio')}")
print(f"Word boundaries available: {'word_boundaries' in result}")
print(f"Word boundaries count: {len(result.get('word_boundaries', []))}")
print(f"Transcribed text: {result.get('transcribed_text', 'Not available')}")

# Print the raw result for debugging
print("\nRaw result keys:", result.keys())
for key, value in result.items():
    if key == 'word_boundaries':
        print(f"Word boundaries type: {type(value)}")
        print(f"Word boundaries length: {len(value)}")
        if value and len(value) > 0:
            print(f"First word boundary: {value[0]}")
    elif key == 'input_data':
        print(f"Input data: {value}")
    else:
        print(f"{key}: {value}")

print(f"\nWord boundaries:")
if 'word_boundaries' in result and result['word_boundaries']:
    for i, boundary in enumerate(result['word_boundaries']):
        print(f"  {i+1}. '{boundary['text']}' at {boundary['audio_offset']/1000:.2f} seconds")
    
    # Find the bookmarks
    print("\nBookmarks:")
    text_without_bookmarks = remove_bookmarks(text).lower()
    text_with_bookmarks = text.lower()
    
    # Find 'cloud_point' bookmark
    cloud_index = text_with_bookmarks.find("<bookmark mark='cloud_point'/>")
    if cloud_index >= 0:
        # Find the closest word boundary after the bookmark
        cloud_word_index = len(remove_bookmarks(text[:cloud_index]).split())
        if cloud_word_index < len(result['word_boundaries']):
            cloud_word = result['word_boundaries'][cloud_word_index]
            print(f"  - 'cloud_point' bookmark would trigger at word '{cloud_word['text']}' at time {cloud_word['audio_offset']/1000:.2f} seconds")
    
    # Find 'alignment_point' bookmark
    alignment_index = text_with_bookmarks.find("<bookmark mark='alignment_point'/>")
    if alignment_index >= 0:
        # Find the closest word boundary after the bookmark
        alignment_word_index = len(remove_bookmarks(text[:alignment_index]).split())
        if alignment_word_index < len(result['word_boundaries']):
            alignment_word = result['word_boundaries'][alignment_word_index]
            print(f"  - 'alignment_point' bookmark would trigger at word '{alignment_word['text']}' at time {alignment_word['audio_offset']/1000:.2f} seconds")
else:
    print("  No word boundaries found in the result.")

print("\nDemo completed!")
print(f"You can listen to the generated audio file at: {temp_dir / result.get('final_audio')}") 