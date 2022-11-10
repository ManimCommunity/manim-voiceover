==========
Quickstart
==========

.. py:currentmodule:: manim_voiceover

Before proceeding, install Manim Voiceover and make sure it's running properly by following the steps in :doc:`../installation`.

Basic Usage
***********

To use Manim Voiceover, you simply import the :py:class:`VoiceoverScene`
class from the plugin

.. code:: py

   from manim_voiceover import VoiceoverScene

You make sure your Scene classes inherit from :py:class:`VoiceoverScene`:

.. code:: py

   class MyAwesomeScene(VoiceoverScene):
       def construct(self):
           ...

Manim Voiceover can use various text-to-speech engines, some
proprietary and some free. A good one to start with is gTTS, which uses
the Google Translate API. We found out that this is the best
for beginning to use the library owing to its cross-platform compatibility—however it still needs
an internet connection.

.. code:: py

   from manim_voiceover import VoiceoverScene
   from manim_voiceover.services.gtts import GTTSService

   class MyAwesomeScene(VoiceoverScene):
       def construct(self):
           self.set_speech_service(GTTSService())

The logic for adding a voiceover is pretty simple. Wrap the animation
inside a ``with`` block that calls ``self.voiceover()``:

.. code:: py

   with self.voiceover(text="This circle is drawn as I speak.") as tracker:
       ... # animate whatever needs to be animated here

Manim will animate whatever is inside that with block. If the voiceover
hasn't finished by the end of the animation, Manim will simply wait
until it finishes. Furthermore, you can use the ``tracker`` object for getting
the total or remaining duration of the voiceover programmatically, which
gives you finer control over the scene:

.. code:: py

   with self.voiceover(text="This circle is drawn as I speak.") as tracker:
       self.play(Create(circle), run_time=tracker.duration)

Using with-blocks allows you to chain sentences back to back and
results in code that is easier to read, since voiceover calls are practically comments.

See the `examples directory <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples>`__
for more examples. We recommend starting with the `gTTS
example <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py>`__.

Choosing a speech service
*************************

Manim Voiceover defines the :py:class:`services.base.SpeechService` class for extending its functionality to include various text-to-speech engines.

.. list-table:: Comparison of available speech services
   :widths: 20 20 10 10 40
   :header-rows: 1

   * - Speech service
     - Quality
     - Can run offline?
     - Paid / requires an account?
     - Notes
   * - :py:class:`services.azure.AzureService`
     - Very good, human-like
     - No
     - Yes
     - Azure gives 500min/month free TTS quota. However, registration still needs a credit or debit card. See `Azure free account FAQ <https://azure.microsoft.com/en-us/free/free-account-faq/>`__ for more details.
   * - :py:class:`services.gtts.GTTSService`
     - Good
     - No
     - No
     - It's a free API subsidized by Google, so there is a likelihood it may stop working in the future.
   * - :py:class:`services.pyttsx3.PyTTSX3Service`
     - Bad
     - Yes
     - No
     - Depends on espeak, does not work reliably on Mac.

It is on our roadmap to provide a high quality TTS engine that runs locally for free. If you have any suggestions, please let us know in the `Discord server <https://manim.community/discord>`__.

Configuring Azure
~~~~~~~~~~~~~~~~~

As of now, the highest quality text-to-speech service available in Manim Voiceover is `Microsoft Azure Speech Service <https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/overview>`__. To use it, you will need to `create an
Azure account <https://azure.microsoft.com/en-us/free/>`__.

.. tip::
    Azure currently offers free TTS of 500 minutes/month. This is more than enough for most projects.

Install Manim Voiceover with the ``azure`` extras in order to be
able to use :py:class:`services.azure.AzureService`:

.. code:: sh

   pip install manim-voiceover "manim-voiceover[azure]"

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
