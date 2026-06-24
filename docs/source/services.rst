Speech Services
---------------

Manim Voiceover can plug into various speech synthesizers to generate voiceover audio.
Below is a comparison of the available services, their pros and cons, and how to set them up.

Choosing a speech service
*************************

.. py:currentmodule:: manim_voiceover.services


Manim Voiceover defines the :py:class:`~~base.SpeechService` class for adding new speech synthesizers. The classes introduced below are all derived from :py:class:`~~base.SpeechService`.

.. list-table:: Comparison of available speech services
   :widths: 20 20 10 10 40
   :align: center
   :header-rows: 1

   * - Speech service
     - Quality
     - Can run offline?
     - Paid / requires an account?
     - Notes
   * - :py:class:`~recorder.RecorderService`
     - N/A
     - N/A
     - N/A
     - This is a utility class to record your own voiceovers with a microphone.
   * - :py:class:`~gemini.GeminiService`
     - Very good, human-like
     - No
     - Yes
     - Recommended for generated AI voices. Requires a Gemini API key or Google Cloud ADC, and Python 3.11 or newer.
   * - :py:class:`~azure.AzureService`
     - Very good, human-like
     - No
     - Yes
     - Azure gives 500min/month free TTS quota. However, registration still needs a credit or debit card. See `Azure free account FAQ <https://azure.microsoft.com/en-us/free/free-account-faq/>`__ for more details.
   * - :py:class:`~elevenlabs.ElevenLabsService`
     - Very good, human-like
     - No
     - Yes
     - Requires ElevenLabs account. Click `here <https://elevenlabs.io/sign-up>`__ to sign up.
   * - :py:class:`~gtts.GTTSService`
     - Good
     - No
     - No
     - It's a free API subsidized by Google, so there is a likelihood it may stop working in the future.
   * - :py:class:`~kokoro.KokoroService`
     - Very good
     - Yes
     - No
     - Local open-weight model. Requires downloading model assets on first run.
   * - :py:class:`~openai.OpenAIService`
     - Very good, human-like
     - No
     - Yes
     - Requires OpenAI developer account. See `platform <https://platform.openai.com/signup>`__ to sign up, and the `pricing page <https://openai.com/pricing#:~:text=%24-,0.030,-/%201K%20characters>`__ for more details.
   * - :py:class:`~pyttsx3.PyTTSX3Service`
     - Bad
     - Yes
     - No
     - Requires `espeak <https://espeak.sourceforge.net/>`__. Does not work reliably on Mac.

It is on our roadmap to provide a high quality TTS engine that runs locally for free. If you have any suggestions, please let us know in the `Discord server <https://manim.community/discord>`__.

:py:class:`~recorder.RecorderService`
*************************************

This is not a speech synthesizer but a utility class to record your own voiceovers with a microphone. It provides a command line interface to record voiceovers during rendering.

Install Manim Voiceover with the ``recorder`` extra in order to use :py:class:`~recorder.RecorderService`:

.. code:: sh

   pip install "manim-voiceover[recorder]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/recorder-example.py>`__ to get started.

:py:class:`~gemini.GeminiService`
*********************************

`Gemini text-to-speech <https://ai.google.dev/gemini-api/docs/speech-generation>`__ is the recommended service for generated AI voices in Manim Voiceover. It provides controllable text-to-speech through the Google Gen AI SDK, and requires an internet connection and Python 3.11 or newer.

Install Manim Voiceover with the ``gemini`` extra in order to use :py:class:`~gemini.GeminiService`:

.. code:: sh

   pip install "manim-voiceover[gemini]"

For Gemini Developer API authentication, create a file called ``.env``
that contains your API key in the same directory where you call Manim.

.. code:: sh

   GEMINI_API_KEY="..." # insert the API key here

Gemini uses API-key authentication by default:

.. code:: python

   self.set_speech_service(GeminiService(voice="Kore"))

For Google Cloud Vertex AI authentication, use Application Default
Credentials and set ``auth_mode="adc"``:

.. code:: python

   self.set_speech_service(
       GeminiService(voice="Kore", auth_mode="adc", project="my-project-id")
   )

:py:class:`~azure.AzureService`
*******************************

`Microsoft Azure Speech Service <https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/overview>`__ is also available for generated voices. To use it, you will need to `create an
Azure account <https://azure.microsoft.com/en-us/free/>`__.

.. tip::
    Azure currently offers free TTS of 500 minutes/month. This is more than enough for most projects.

Install Manim Voiceover with the ``azure`` extra in order to use :py:class:`~azure.AzureService`:

.. code:: sh

   pip install "manim-voiceover[azure]"

Then, you need to find out your subscription key and service region:

- Sign in to `Azure portal <https://portal.azure.com/>`__ and create a new Speech Service resource.
- Go to the `Azure Cognitive Services page <https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/Microsoft.CognitiveServices%2Faccounts>`__.
- Click on the resource you created and go to the ``Keys and Endpoint`` tab. Copy the ``Key 1`` and ``Location`` values.

Create a file called ``.env`` that contains your authentication
information in the same directory where you call Manim.

.. code:: sh

   AZURE_SUBSCRIPTION_KEY="..." # insert Key 1 here
   AZURE_SERVICE_REGION="..."   # insert Location here

Check out `Azure
docs <https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/>`__
for more details.

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/azure-example.py>`__ to get started.

:py:class:`~gtts.GTTSService`
*****************************

`gTTS <https://gtts.readthedocs.io/>`__ is a text-to-speech
library that wraps Google Translate's text-to-speech API. It needs an internet connection to work.

Install Manim Voiceover with the ``gtts`` extra in order to use :py:class:`~gtts.GTTSService`:

.. code:: sh

   pip install "manim-voiceover[gtts]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py>`__ to get started.

:py:class:`~kokoro.KokoroService`
*********************************

`Kokoro <https://github.com/hexgrad/kokoro>`__ is an open-weight local text-to-speech model. It can run offline after model assets are downloaded.

Install Manim Voiceover with the ``kokoro`` extra in order to use :py:class:`~kokoro.KokoroService`:

.. code:: sh

   pip install "manim-voiceover[kokoro]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/kokoro-example.py>`__ to get started.

.. note::
   Some languages require additional grapheme-to-phoneme extras via ``misaki``. See the upstream Kokoro docs for details.

:py:class:`~openai.OpenAIService`
*************************************
`OpenAI <https://platform.openai.com/docs/api-reference/audio/createSpeech/>`__ provides a text-to-speech service. It is through an API, so it requires an internet connection to work. It also requires an API key to use. Register for one `here <https://platform.openai.com/>`__.

Install Manim Voiceover with the ``openai`` extra in order to use :py:class:`~openai.OpenAIService`:

.. code:: sh

   pip install "manim-voiceover[openai]"

Then, you need to find out your api key:

- Sign in to `OpenAI platform <https://platform.openai.com/>`__ and click into Api Keys from the left panel.
- Click create a new secret key and copy it.

Create a file called ``.env`` that contains your authentication
information in the same directory where you call Manim.

.. code:: sh

   OPENAI_API_KEY="..." # insert the secret key here. It should start with "sk-"

Check out `OpenAI docs <https://platform.openai.com/docs/guides/text-to-speech/>`__ for more details.

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/openai-example.py>`__ to get started.

:py:class:`~pyttsx3.PyTTSX3Service`
***********************************

`pyttsx3 <https://pyttsx3.readthedocs.io/>`__ is a text-to-speech
library that wraps `espeak <https://espeak.sourceforge.net/>`__, a formant synthesis speech synthesizer.

Install Manim Voiceover with the ``pyttsx3`` extra in order to use :py:class:`~pyttsx3.PyTTSX3Service`:

.. code:: sh

   pip install "manim-voiceover[pyttsx3]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/pyttsx3-example.py>`__ to get started.


:py:class:`~elevenlabs.ElevenLabsService`
******************************************

`ElevenLabs <https://www.elevenlabs.io/>`__ offers one of the most natural sounding speech service APIs. It has a range of realistic and emotive voices, and also allows you to clone your own voice by uploading a few minutes of your speech. To use it, you will need to create an account at `Eleven Labs <https://elevenlabs.io/sign-up>`__.

.. tip::
    ElevenLabs currently offers free TTS of 10,000 characters/month and up to 3 custom voices.

Install Manim Voiceover with the ``elevenlabs`` extra in order to use :py:class:`~elevenlabs.ElevenLabsService`:

.. code:: sh

   pip install "manim-voiceover[elevenlabs]"

Then, you need to find out your API key.

- Sign in to `ElevenLabs portal <https://www.elevenlabs.io/>`__ and go to your profile to obtain the key
- Set the environment variable ``ELEVEN_API_KEY`` to your key

Create a file called ``.env`` that contains your authentication
information in the same directory where you call Manim.

.. code:: sh

   ELEVEN_API_KEY="..." # insert Key 1 here

Check out `ElevenLabs
docs <https://elevenlabs.io/docs/api-reference/python-text-to-speech-guide#getting-started>`__
for more details.

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/elevenlabs-example.py>`__ to get started.
