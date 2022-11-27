import os
from pathlib import Path
from pydub import AudioSegment

from manim_voiceover.helper import wav2mp3
from manim import logger

try:
    import TTS
    from TTS.utils.manage import ModelManager
    from .utils_synthesizer import Synthesizer
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[coqui]"` to use CoquiService.'
    )

DEFAULT_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"


def synthesize_coqui(
    text,
    output_path,
    model_name=DEFAULT_MODEL,
    vocoder_name=None,
    model_path=None,
    config_path=None,
    vocoder_path=None,
    vocoder_config_path=None,
    encoder_path=None,
    encoder_config_path=None,
    speakers_file_path=None,
    language_ids_file_path=None,
    speaker_idx=None,
    language_idx=None,
    speaker_wav=None,
    capacitron_style_wav=None,
    capacitron_style_text=None,
    reference_wav=None,
    reference_speaker_idx=None,
    use_cuda=False,
    # gst_style=None,
    # model_info_by_name=None,
    # model_info_by_idx=None,
    # list_speaker_idxs=False,
    # list_language_idxs=False,
    # save_spectogram=False,
    # progress_bar=True,
):

    # load model manager
    path = Path(TTS.__file__).parent / ".models.json"
    # manager = ModelManager(path, progress_bar=progress_bar)
    manager = ModelManager(path)

    # CASE3: load pre-trained model paths
    if model_name is not None and not model_path:
        model_path, config_path, model_item = manager.download_model(model_name)
        vocoder_name = (
            model_item["default_vocoder"] if vocoder_name is None else vocoder_name
        )

    if vocoder_name is not None and not vocoder_path:
        vocoder_path, vocoder_config_path, _ = manager.download_model(vocoder_name)

    # load models
    synthesizer = Synthesizer(
        model_path,
        config_path,
        speakers_file_path,
        language_ids_file_path,
        vocoder_path,
        vocoder_config_path,
        encoder_path,
        encoder_config_path,
        use_cuda,
    )

    # RUN THE SYNTHESIS
    print(" > Text: {}".format(text))
    wav, word_boundaries = synthesizer.tts(
        text,
        speaker_idx,
        language_idx,
        speaker_wav,
        reference_wav=reference_wav,
        style_wav=capacitron_style_wav,
        style_text=capacitron_style_text,
        reference_speaker_name=reference_speaker_idx,
    )
    # save the results
    print(" > Saving output to {}".format(output_path))

    # Replace file extension with .wav
    wav_path = Path(output_path).with_suffix(".wav")
    synthesizer.save_wav(wav, wav_path)
    wav2mp3(wav_path, output_path)

    return wav_path, word_boundaries
