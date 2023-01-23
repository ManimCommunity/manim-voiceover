Installation
============

Install Manim Voiceover from PyPI with the extras ``azure`` and ``gtts``:

.. code:: sh

   pip install --upgrade "manim-voiceover[azure,gtts]"

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

Extras
~~~~~~

Manim Voiceover does not install all dependencies by default. It will detect on the fly which packages are missing and will ask for your permission to install them, so you don't have to worry about installing them manually.

If you want to install all of the dependencies, use the ``all`` extra:

.. code:: sh

   pip install --upgrade "manim-voiceover[all]"


You can see other extras in the `pyproject.toml <https://github.com/ManimCommunity/manim-voiceover/blob/main/pyproject.toml>`__ file.

Installing PortAudio
~~~~~~~~~~~~~~~~~~~~

Manim Voiceover lets you record voiceovers during rendering using `PyAudio <https://people.csail.mit.edu/hubert/pyaudio/>`__.
PyAudio depends on `PortAudio <http://www.portaudio.com/>`__ which needs to be installed separately.

On Debian based distros:

.. code:: sh

   sudo apt install portaudio19-dev
   sudo pip install pyaudio
   # Or install from apt globally:
   sudo apt install python3-pyaudio

On macOS, you can install it using `Homebrew <https://brew.sh/>`__:

.. code:: sh

   brew install portaudio
   pip install pyaudio

On Windows, PortAudio should come prepackaged with the binaries, so just install PyAudio with pip:

.. code:: sh

   python -m pip install pyaudio

For more information, see the `PyAudio documentation <https://people.csail.mit.edu/hubert/pyaudio/#downloads>`__.

Installing SoX
~~~~~~~~~~~~~~

Manim Voiceover can make the output from speech synthesizers faster
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

Installing gettext
~~~~~~~~~~~~~~~~~~

Manim Voiceover uses `gettext <https://www.gnu.org/software/gettext/>`__ to
store and fetch translations of voiceover text. If you plan to translate
your videos automatically, you need to install gettext.

On Debian based distros:

.. code:: sh

   sudo apt install gettext

On macOS, you can install it using `Homebrew <https://brew.sh/>`__:

.. code:: sh

   brew install gettext