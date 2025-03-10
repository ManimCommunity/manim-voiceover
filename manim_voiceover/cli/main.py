"""
CLI entrypoint for manim-voiceover
"""

import inspect
import os
import sys
from pathlib import Path

from manim.cli.render.commands import main_command as original_main_command
from manim.cli.render.commands import render

from manim_voiceover.cli.config import add_voiceover_args

# Store the original command function
original_render_command = render.command

def patched_render_command(function):
    """Patch the render command to add our custom arguments."""
    # Call the original decorated function
    cmd = original_render_command(function)
    
    # Add our parameter to the command
    from click import option
    cmd = option('--use-cloud-whisper', 
                 is_flag=True, 
                 help='Use OpenAI cloud API for Whisper instead of local model')(cmd)
    
    return cmd

def patched_main():
    """Entry point for renderer with cloud whisper support."""
    # Find the render subcommand in the argument parser
    import argparse
    
    # Create a dummy parser just to intercept the args
    dummy_parser = argparse.ArgumentParser(add_help=False)
    dummy_parser.add_argument("--use-cloud-whisper", action="store_true")
    
    # Parse known args to get our flags
    args, unknown = dummy_parser.parse_known_args()
    
    # Set the global config value
    from manim.config import config
    if hasattr(args, 'use_cloud_whisper') and args.use_cloud_whisper:
        config.use_cloud_whisper = True
    
    # Call the original main command
    return original_main_command()

# Apply our monkey patch
render.command = patched_render_command

# No need for this line since we're directly importing and patching in __init__.py
# main_command = patched_main 