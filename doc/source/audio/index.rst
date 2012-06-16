.. Copyright 2011, Keith Dart
..
.. vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
..
.. This document is in RST format <http://docutils.sourceforge.net/rst.html>.



Pycopia audio package
=====================

Modules for working with audio, voice, and audio players.

.. toctree::
   :maxdepth: 2

Voice Modems
------------

Interface with voice modems using the vgetty program. Can be used to implement
answering machines, interactive voice response systems. and auto dialers.

.. automodule:: pycopia.audio.Vgetty
   :members:


Control alsaplayer
------------------

Control alsaplayer. This is an ancient audio player that is not really
maintained any more. But may be still available in source form.

The available modules:

    vimplayer
        play audio files controlled from vim editor.

    alsacontrol
        Control an alsaplayer server

    alsaplayer
        Start an alsaplayer server.

