==========
Quickstart
==========

.. py:currentmodule:: manim_voiceover

Before proceeding, install Manim Voiceover and make sure it's running properly by following the steps in :doc:`installation`.

Basic Usage
***********

To use Manim Voiceover, you simply import the :py:class:`VoiceoverScene`
class from the plugin

.. code:: py

   from manim_voiceover import VoiceoverScene

Make your scene inherit from :py:class:`VoiceoverScene`:

.. code:: py

   class MyAwesomeScene(VoiceoverScene):
       def construct(self):
           ...

You can also inherit from multiple scene classes:

.. code:: py

   from manim.scene.moving_camera_scene import MovingCameraScene

   class MyAwesomeScene(MovingCameraScene, VoiceoverScene):
       def construct(self):
           ...

This should work as long as the variables or methods of parent classes do not collide.

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
hasn't finished by the end of the animation, Manim will wait
until it finishes. Furthermore, you can use the ``tracker`` object for getting
the total or remaining duration of the voiceover programmatically, which
gives you finer control over the scene:

.. code:: py

   with self.voiceover(text="This circle is drawn as I speak.") as tracker:
       self.play(Create(circle), run_time=tracker.duration)

.. tip::
    Using with-blocks allows you to chain sentences back to back and results in code that is easier to read, since voiceover calls are practically comments.


The ``text`` argument is automatically reused for video subcaptions. Alternatively, you can supply a custom subcaption:

.. code:: py

   with self.voiceover(
       text="This circle is drawn as I speak.",
       subcaption="What a cute circle! :)"
   ) as tracker:
       self.play(Create(circle))

See :doc:`examples` and the `examples directory <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples>`__
for more examples. We recommend starting with the `gTTS
example <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py>`__.

Bookmarks
*********

One of the most important features of Manim Voiceover is bookmarks.
Bookmarks allow you to trigger an animation at a specific word in the voiceover.

.. video:: https://user-images.githubusercontent.com/2453968/201714175-ea5e7e46-9b33-40de-a4c1-ecc7bf55e42b.mp4
   :width: 100%

With bookmarks, you can time your animations much more precisely. See the `bookmark example <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/bookmark-example.py>`__ and `Approximating Tau <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/approximating-tau.py>`__ for more examples.

Record your own voiceover
*************************

Manim Voiceover can record your voiceover directly from the command line. We recommend the following workflow:

1. Develop your animation with one of the text-to-speech engines, e.g. :py:class:`services.gtts.GTTSService`:

.. code:: py

   from manim_voiceover import VoiceoverScene
   from manim_voiceover.services.gtts import GTTSService

   class MyAwesomeScene(VoiceoverScene):
       def construct(self):
           self.set_speech_service(GTTSService())

           with self.voiceover(text="This circle is drawn as I speak.") as tracker:
               self.play(Create(circle))


2. When you're happy with the animation, switch the service with :py:class:`services.recorder.RecorderService` to record your own voiceover:

.. code:: py

   from manim_voiceover import VoiceoverScene
   # from manim_voiceover.services.gtts import GTTSService
   from manim_voiceover.services.recorder import RecorderService

   class MyAwesomeScene(VoiceoverScene):
       def construct(self):
           # self.set_speech_service(GTTSService())
           self.set_speech_service(RecorderService())

           with self.voiceover(text="This circle is drawn as I speak.") as tracker:
               self.play(Create(circle))

3. Render the scene the same way you would normally do:

.. code:: sh

   manim -pql my_awesome_scene.py --disable_caching

This will instruct you in the terminal step by step what to do to record your voiceover.


Generate voiceovers in a different language
*******************************************

Each speech service supports a different set of options, and some of them
support multiple languages. You can learn about these options in the
:ref:`api-speech-services` section in the API reference.

For example, :py:class:`services.gtts.GTTSService`
supports all the languages supported by Google Translate, which you
can find `here <https://cloud.google.com/translate/docs/languages>`__.
The `gTTS example <https://github.com/ManimCommunity/manim-voiceover/blob/main/examples/gtts-example.py>`__
implements the same scene in English and Vietnamese as a demonstration.

If you can't find a good text-to-speech engine for your language, you can directly
record your own voiceover using :py:class:`services.recorder.RecorderService`.