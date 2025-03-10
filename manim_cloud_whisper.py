#!/usr/bin/env python3
"""
Custom entry point for running Manim with cloud-based Whisper.
"""

import sys
import os
import subprocess

def main():
    """Run Manim with cloud-based Whisper enabled."""
    # Set the environment variable to enable cloud-based Whisper
    os.environ["MANIM_VOICEOVER_USE_CLOUD_WHISPER"] = "1"
    
    # Get the Manim command arguments
    args = sys.argv[1:]
    
    # Run the Manim command
    cmd = ["manim"] + args
    print(f"Running: {' '.join(cmd)}")
    print("Cloud-based Whisper enabled via environment variable.")
    
    # Execute the command
    result = subprocess.run(cmd)
    
    # Return the exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 