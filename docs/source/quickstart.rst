==========
Quickstart
==========

.. note::
 Before proceeding, install Manim Voiceover and make sure it's running properly by
 following the steps in :doc:`../installation`.

Choosing a speech service
*************************

.. list-table:: Comparison of available speech services
   :widths: 25 25 50
   :header-rows: 1

   * - Speech service
     - Quality
     - Heading row 1, column 3
   * - :code:`AzureService`
     - Very good, human-like
     - Row 1, column 3
   * - :code:`GTTSService`
     - Good
     - Row 2, column 3
   * - :code:`PyTTSX3Service`
     - Bad
     - Row 2, column 3

.. This quickstart guide will lead you through creating a sample project using Manim: an animation
.. engine for precise programmatic animations.

.. First, you will use a command line
.. interface to create a ``Scene``, the class through which Manim generates videos.
.. In the ``Scene`` you will animate a circle. Then you will add another ``Scene`` showing
.. a square transforming into a circle. This will be your introduction to Manim's animation ability.
.. Afterwards, you will position multiple mathematical objects (``Mobject``\s). Finally, you
.. will learn the ``.animate`` syntax, a powerful feature that animates the methods you
.. use to modify ``Mobject``\s.


Starting a new project
**********************

