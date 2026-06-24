#!/usr/bin/env bash
set -euo pipefail

QUALITY="${1:-ql}"
SCENE_FILE="examples/tts_compare_demo.py"
SCENE_CLASS="TTSCompareDemo"

echo "Running comparison for gtts and kokoro using scene ${SCENE_CLASS} (${QUALITY})"

echo "Rendering with gtts..."
TTS_PROVIDER=gtts manim -p"${QUALITY}" "${SCENE_FILE}" "${SCENE_CLASS}" --disable_caching --output_file compare-gtts.mp4

echo "Rendering with kokoro..."
TTS_PROVIDER=kokoro manim -p"${QUALITY}" "${SCENE_FILE}" "${SCENE_CLASS}" --disable_caching --output_file compare-kokoro.mp4

echo "Done. Compare the outputs in media/videos/tts_compare_demo/."
