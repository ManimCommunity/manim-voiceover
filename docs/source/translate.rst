##################
Translating Scenes
##################

Manim Voiceover supports translating scenes into other languages. It uses the `gettext <https://en.wikipedia.org/wiki/Gettext>`__ convention of wrapping translatable strings in ``_()``. gettext is an established internationalization and localization (i18n and l10n) system commonly used for writing multilingual programs.

Check out `the translation example <https://github.com/ManimCommunity/manim-voiceover/tree/main/examples/translation-example/>`__:


.. code:: py

    import os
    from manim import *
    from manim_voiceover import VoiceoverScene
    from manim_voiceover.services.gtts import GTTSService
    from manim_voiceover.translate import get_gettext

    # It is good practice to get the LOCALE and DOMAIN from environment variables
    LOCALE = os.getenv("LOCALE")
    DOMAIN = os.getenv("DOMAIN")

    # The following function uses the LOCALE and DOMAIN environment variables
    # to set the language, and returns a gettext function that can be used to
    # translate strings.
    _ = get_gettext()

    class TranslationExample(VoiceoverScene):
        def construct(self):
            # We use the free TTS service from Google Translate
            # The TTS language is set via the LOCALE environment variable
            self.set_speech_service(GTTSService(lang=LOCALE))

            circle = Circle()
            square = Square().shift(2 * RIGHT)

            # The voiceover strings are wrapped in _()
            # This means that their translations will be looked up in the .po files
            # and used to replace the original strings
            with self.voiceover(text=_("This circle is drawn as I speak.")) as tracker:
                self.play(Create(circle), run_time=tracker.duration)

            with self.voiceover(text=_("Let's shift it to the left 2 units.")) as tracker:
                self.play(circle.animate.shift(2 * LEFT), run_time=tracker.duration)

            with self.voiceover(
                text=_("Now, let's transform it into a square.")
            ) as tracker:
                self.play(Transform(circle, square), run_time=tracker.duration)

            with self.voiceover(text=_("Thank you for watching.")):
                self.play(Uncreate(circle))

            self.wait()


In this example, the German and Vietnamese translations are available in the files `locale/de/LC_MESSAGES/translation-example.po <https://github.com/ManimCommunity/manim-voiceover/tree/main/examples/translation-example/locale/de/LC_MESSAGES/translation-example.po>`__ and `locale/vi/LC_MESSAGES/translation-example.po <https://github.com/ManimCommunity/manim-voiceover/tree/main/examples/translation-example/locale/vi/LC_MESSAGES/translation-example.po>`__ respectively.

We have introduced the command line utility ``manim_render_translation`` to make it easier to render translations. It is similar to calling ``manim render``, but it also lets you choose which locale (i.e. language) to render:

.. code:: sh

   cd examples/translation-example
   manim_render_translation translation-example.py \
       -s TranslationExample                       \
       -d translation-example                      \
       -l de,vi                                    \
       -qh

Here,

- ``-s``: Scene to render.
- ``-d``: gettext domain (the name of the translation file wihout the ``.po`` extension)
- ``-l``: Locale to render. If not specified, all locales will be rendered.
- ``-q``: Render quality, same as in ``manim render``.

For more information, run ``manim_render_translation --help``.

Translating scenes using DeepL
******************************

Using the DeepL API
https://www.deepl.com/pro-api
