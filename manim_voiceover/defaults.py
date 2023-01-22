from pathlib import Path

DEFAULT_VOICEOVER_CACHE_DIR = "voiceovers"
DEFAULT_VOICEOVER_CACHE_JSON_FILENAME = "cache.json"

#: Available source languages for DeepL
DEEPL_SOURCE_LANG = {
    "bg": "Bulgarian",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese (all Portuguese varieties mixed)",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sv": "Swedish",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "zh": "Chinese",
}

#: Available target languages for DeepL
DEEPL_TARGET_LANG = {
    "bg": "Bulgarian",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "Alias for en-us",
    "en-gb": "English (British)",
    "en-us": "English (American)",
    "es": "Spanish",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Alias for pt-pt",
    "pt-br": "Portuguese (Brazilian)",
    "pt-pt": "Portuguese (all Portuguese varieties excluding Brazilian Portuguese)",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sv": "Swedish",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "zh": "Chinese (simplified)",
}

DEEPL_AVAILABLE_SOURCE_LANG = list(DEEPL_SOURCE_LANG.keys())
DEEPL_AVAILABLE_TARGET_LANG = list(DEEPL_TARGET_LANG.keys())
