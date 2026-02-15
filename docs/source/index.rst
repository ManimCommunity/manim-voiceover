.. manim documentation master file, created by
   sphinx-quickstart on Tue Aug  4 13:58:07 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Manim Voiceover
===============

`Manim Voiceover <https://voiceover.manim.community>`__ is a `Manim <https://manim.community>`__ plugin for all things voiceover:

- Add voiceovers to Manim videos *directly in Python* without having to use a video editor.
- Record voiceovers with your microphone during rendering with a simple command line interface (see :py:class:`~manim_voiceover.services.recorder.RecorderService`).
- Develop animations with auto-generated AI voices from various free and proprietary services.
- Per-word timing of animations, i.e. trigger animations at specific words in the voiceover, even for the recordings. This works thanks to `faster-whisper <https://github.com/SYSTRAN/faster-whisper>`__.

A demo:

.. video:: https://user-images.githubusercontent.com/2453968/198145393-6a1bd709-4441-4821-8541-45d5f5e25be7.mp4
   :width: 100%

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   services
   examples
   translate
   api
