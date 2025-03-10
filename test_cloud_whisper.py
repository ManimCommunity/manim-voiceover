from manim import config
from manim_voiceover.services.base import SpeechService
from manim_voiceover.services.gtts import GTTSService

# Test 1: Check if the use_cloud_whisper attribute exists
print("Test 1: Checking if use_cloud_whisper attribute exists in config")
if hasattr(config, 'use_cloud_whisper'):
    print("✅ Success: config.use_cloud_whisper attribute exists")
    print(f"Current value: {config.use_cloud_whisper}")
else:
    print("❌ Error: config.use_cloud_whisper attribute does not exist")

# Test 2: Create a SpeechService with use_cloud_whisper=True
print("\nTest 2: Creating SpeechService with use_cloud_whisper=True")
try:
    service = SpeechService(use_cloud_whisper=True, transcription_model='base')
    print(f"✅ Success: SpeechService created with use_cloud_whisper={service.use_cloud_whisper}")
except Exception as e:
    print(f"❌ Error: Failed to create SpeechService: {str(e)}")

# Test 3: Create a GTTSService with use_cloud_whisper=True
print("\nTest 3: Creating GTTSService with use_cloud_whisper=True")
try:
    service = GTTSService(use_cloud_whisper=True, transcription_model='base')
    print(f"✅ Success: GTTSService created with use_cloud_whisper={service.use_cloud_whisper}")
except Exception as e:
    print(f"❌ Error: Failed to create GTTSService: {str(e)}")

print("\nAll tests completed!") 