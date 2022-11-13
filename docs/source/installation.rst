Installation
============

Install Manim Voiceover from PyPI with the extras ``azure`` and ``gtts``:

.. code:: sh

   pip install "manim-voiceover[azure,gtts]"

Check whether your installation works correctly:

.. code:: sh

   wget https://github.com/ManimCommunity/manim-voiceover/raw/main/examples/gtts-example.py
   manim -pql gtts-example.py --disable_caching

.. important::
   Manim needs to be called with the ``--disable_caching`` flag due to a `bug <https://github.com/ManimCommunity/manim/pull/907>`__.
   Don't forget to include it every time you render.

`The example above <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py>`__ uses
`gTTS <https://github.com/pndurette/gTTS/>`__ which calls the Google
Translate API and therefore needs an internet connection to work. If it
throws an error, there might be a problem with your internet connection
or the Google Translate API.

Installing SoX
~~~~~~~~~~~~~~

``manim-voiceover`` can make the output from speech synthesizers faster
or slower using `SoX <http://sox.sourceforge.net/>`__ (version 14.4.2 or
higher is required).

Install SoX on Mac with Homebrew:

.. code:: sh

   brew install sox

Install SoX (and a necessary mp3 handler) on Debian based distros:

.. code:: sh

   sudo apt-get install sox libsox-fmt-all

Or install `from
source <https://sourceforge.net/projects/sox/files/sox/>`__.