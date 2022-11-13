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

