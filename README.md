# manim-voiceover

`manim-voiceover` is a [Manim](https://manim.community) plugin for all things voiceover:

- Add voiceovers to Manim videos *directly in Python*, without using a video editor.
- Develop an animation with an auto-generated AI voice without having to re-record and re-sync the audio.
- Record a voiceover and have it stitched back onto the video instantly. (Note that this is not the same as AI voice cloning)

Currently supported TTS services:

- [Azure Text to Speech](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/) (Recommended)
- [gTTS](https://github.com/pndurette/gTTS/)
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3)

## Install in development mode

`manim-voiceover` is in active development, so we recommend you to install it in development mode:

```sh
# Clone the repository and change directory
git clone git@github.com:ManimCommunity/manim-voiceover.git
cd manim-voiceover/

# Install the package in development mode
pip3 install --editable .

# Render and play an example
manim -pql examples/gtts-example.py --disable_caching
```

If you only hear the first line, you need to run `manim` with the `--disable_caching` flag. This is due to a bug in Manim and will be fixed in the future.

[The example above](examples/gtts-example.py) uses [gTTS](https://github.com/pndurette/gTTS/) which calls the Google Translate API and therefore needs an internet connection to work. If it throws an error, there might be a problem with your internet connection or the Google Translate API.

<!-- Once SoX is installed, proceed with installing `manim-voiceover`:

```sh
cd manim-voiceover
python setup.py install
``` -->

### Installing SoX

`manim-voiceover` can make the output from speech synthesizers faster or slower using [SoX](http://sox.sourceforge.net/). For this to work, version 14.4.2 or higher needs to be installed.

To install SoX on Mac with Homebrew:

```brew install sox```

On Debian based distros:

```sudo apt-get install sox```

or install [from source](https://sourceforge.net/projects/sox/files/sox/).

## Basic Usage

To use `manim-voiceover`, you simply import the `VoiceoverScene` class from the plugin

```py
from manim_voiceover import VoiceoverScene
```

You make sure your Scene classes inherit from `VoiceoverScene`:

```py
class MyAwesomeScene(VoiceoverScene):
    def construct(self):
        ...
```

`manim-voiceover` offers multiple text-to-speech engines, some proprietary and some free. A good one to start with is gTTS, which uses Google Translate's proprietary API. We found out that this is the best for beginners in terms of cross-platform compatibility---however it needs an internet connection.

```py
from manim_voiceover import VoiceoverScene
from manim_voiceover.interfaces import GTTSSpeechSynthesizer

class MyAwesomeScene(VoiceoverScene):
    def construct(self):
        self.set_speech_synthesizer(GTTSSpeechSynthesizer())
```

The logic for adding a voiceover is pretty simple. Wrap the animation inside a `with` block that calls `self.voiceover()`:

```py
with self.voiceover(text="This circle is drawn as I speak.") as tracker:
    ... # animate whatever needs to be animated here
```

Manim will animate whatever is inside that with block. If the voiceover hasn't finished by the end of the animation, Manim will simply wait until it does. You can further use the `tracker` object for getting the total or remaining duration of the voiceover programmatically, which gives you finer control over the video:

```py
with self.voiceover(text="This circle is drawn as I speak.") as tracker:
    self.play(Create(circle), run_time=tracker.duration)
```

Using with-blocks results in clean code, allows you to chain sentences back to back and also serve as a documentation of sorts, as the video is neatly compartmentalized according to whatever lines are spoken during the animations.

See the [examples directory](./examples) for more examples. We recommend starting with the [gTTS example](https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py).

## Configuring Azure

The highest quality text-to-speech services available to the public is currently offered by Microsoft Azure. To use it, you need to create an Azure account.

Then, you need to find out your subscription key and service region. Check out [Azure docs](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/) for more details.

Create a file called `.env` that contains your authentication information in the same directory where you call Manim.

```sh
AZURE_SUBSCRIPTION_KEY="..."
AZURE_SERVICE_REGION="..."
```