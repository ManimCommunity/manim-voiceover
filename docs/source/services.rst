Speech Services
---------------

Manim Voiceover can plug into various speech synthesizers to generate voiceover audio.
Below is a comparison of the available services, their pros and cons, and how to set them up.

Choosing a speech service
*************************

.. py:currentmodule:: manim_voiceover.services


Manim Voiceover defines the :py:class:`~~base.SpeechService` class for extending its functionality to include various text-to-speech engines.

.. list-table:: Comparison of available speech services
   :widths: 20 20 10 10 40
   :align: center
   :header-rows: 1

   * - Speech service
     - Quality
     - Can run offline?
     - Paid / requires an account?
     - Notes
   * - :py:class:`~azure.AzureService`
     - Very good, human-like
     - No
     - Yes
     - Azure gives 500min/month free TTS quota. However, registration still needs a credit or debit card. See `Azure free account FAQ <https://azure.microsoft.com/en-us/free/free-account-faq/>`__ for more details.
   * - :py:class:`~coqui.CoquiService`
     - Good, human-like
     - Yes
     - No
     - Requires `PyTorch <https://pytorch.org/>`__ to run. May be difficult to set up on certain platforms.
   * - :py:class:`~gtts.GTTSService`
     - Good
     - No
     - No
     - It's a free API subsidized by Google, so there is a likelihood it may stop working in the future.
   * - :py:class:`~pyttsx3.PyTTSX3Service`
     - Bad
     - Yes
     - No
     - Requires `espeak <https://espeak.sourceforge.net/>`__. Does not work reliably on Mac.

It is on our roadmap to provide a high quality TTS engine that runs locally for free. If you have any suggestions, please let us know in the `Discord server <https://manim.community/discord>`__.

:py:class:`~azure.AzureService`
*******************************

As of now, the highest quality text-to-speech service available in Manim Voiceover is `Microsoft Azure Speech Service <https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/overview>`__. To use it, you will need to `create an
Azure account <https://azure.microsoft.com/en-us/free/>`__.

.. tip::
    Azure currently offers free TTS of 500 minutes/month. This is more than enough for most projects.

Install Manim Voiceover with the ``azure`` extra in order to use :py:class:`~azure.AzureService`:

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

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/azure-example.py>`__ to get started.

:py:class:`~coqui.CoquiService`
*******************************

Install Manim Voiceover with the ``coqui`` extra in order to use :py:class:`~coqui.CoquiService`:

.. code:: sh

   pip install manim-voiceover "manim-voiceover[coqui]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/coqui-example.py>`__ to get started.

:py:class:`~gtts.GTTSService`
*****************************

Install Manim Voiceover with the ``gtts`` extra in order to use :py:class:`~gtts.GTTSService`:

.. code:: sh

   pip install manim-voiceover "manim-voiceover[gtts]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py>`__ to get started.

:py:class:`~pyttsx3.PyTTSX3Service`
***********************************

Install Manim Voiceover with the ``pyttsx3`` extra in order to use :py:class:`~pyttsx3.PyTTSX3Service`:

.. code:: sh

   pip install manim-voiceover "manim-voiceover[pyttsx3]"

Refer to the `example usage <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/pyttsx3-example.py>`__ to get started.