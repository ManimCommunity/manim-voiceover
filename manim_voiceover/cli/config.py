"""
Configuration support for manim-voiceover CLI
"""

import os
from manim.utils.file_ops import guarantee_existence
from manim._config import config_file, library_wide_cfg_file, ManimConfig
import manim.config as manim_config

# The Manim config system doesn't provide an easy way to extend the CLI from plugins
# So instead, we'll monkey patch the ManimConfig class to add our custom flag
original_digest_args = manim_config.ManimConfig.digest_args

def patched_digest_args(self, args, namespace=''):
    # Call original method
    original_digest_args(self, args, namespace)
    
    # Handle our custom CLI flags
    if hasattr(args, 'use_cloud_whisper'):
        self.use_cloud_whisper = args.use_cloud_whisper
        
# Apply the monkey patch
manim_config.ManimConfig.digest_args = patched_digest_args

# Make sure the config object has our flag
if not hasattr(manim_config.config, 'use_cloud_whisper'):
    manim_config.config.use_cloud_whisper = False

def add_voiceover_args(parser):
    """Add manim-voiceover specific arguments to the parser."""
    whisper_group = parser.add_argument_group("Manim Voiceover")
    whisper_group.add_argument(
        "--use-cloud-whisper",
        action="store_true",
        help="Use OpenAI's cloud Whisper API instead of local model for transcription",
    ) 