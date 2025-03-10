import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from manim_voiceover.services.gtts import GTTSService
from manim_voiceover.config import config

# Set the cloud whisper flag manually
config.use_cloud_whisper = True

print("=== Testing Cloud-based Whisper Implementation ===")
print(f"Cloud Whisper enabled: {config.use_cloud_whisper}")

# Create a temporary directory for audio files
temp_dir = Path("./temp_test")
temp_dir.mkdir(exist_ok=True)

# Create a GTTSService with cloud whisper enabled
service = GTTSService(
    transcription_model="base",  # Model name is still required
    use_cloud_whisper=True,      # This enables cloud-based Whisper
    cache_dir=str(temp_dir)
)

print(f"\nGTTSService created with use_cloud_whisper={service.use_cloud_whisper}")

# Check if OpenAI API key is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key or openai_api_key == "your_openai_api_key_here":
    print("\n⚠️ Warning: OPENAI_API_KEY is not set or is using the default value.")
    print("Please edit the .env file with your actual OpenAI API key.")
    print("Skipping the actual API call test.")
else:
    # Generate speech from text
    print("\nGenerating speech from text...")
    text = "This is a test of the cloud-based Whisper feature."
    result = service._wrap_generate_from_text(text)
    
    print(f"\nSpeech generated successfully!")
    print(f"Audio file: {result.get('final_audio')}")
    print(f"Word boundaries available: {'word_boundaries' in result}")
    
    if 'word_boundaries' in result:
        print(f"\nWord boundaries:")
        for boundary in result['word_boundaries'][:5]:  # Show first 5 boundaries
            print(f"  - {boundary['text']} at {boundary['audio_offset']}")

print("\nTest completed!") 