#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Control an alsaplayer instance. This is really a wrapper for the apcontrol
module.

apcontrol API:

add_and_play(str) -> None
add_path(str) -> None
add_playlist(str) -> None
clear_playlist() -> None
get_album() -> str
get_artist() -> str
get_comment() -> str
get_file_path() -> str
get_file_path_for_track(int) -> str
get_frame() -> int
get_frames() -> int
get_genre() -> str
get_length() -> int
get_pan() -> float
get_playlist_length() -> int
get_playlist_position() -> int
get_position() -> int
get_session_name() -> str
get_speed() -> float
get_status() -> str
get_stream_type() -> str
get_title() -> str
get_track_number() -> str
get_tracks() -> int
get_volume() -> float
get_year() -> str
insert(str, int) -> None
is_looping() -> int
is_playing() -> int
is_playlist_looping() -> int
is_running() -> int
jump_to(int) -> None
next() -> None
pause() -> None
ping() -> None
play() -> None
prev() -> None
quit() -> None
remove(int) -> None
save_playlist() -> None
set_current(int) -> None
set_frame(int) -> None
set_looping(int) -> None
set_pan(float) -> None
set_playlist_looping(int) -> None
set_position(int) -> None
set_position_relative(int) -> None
set_speed(float) -> None
set_volume(float) -> None
shuffle_playlist() -> None
sort(str) -> None
stop() -> None
unpause() -> None

"""

import sys, os
import apcontrol

class AlsaPlayerWrapper(object):
    def __init__(self, sess):
        self._s = sess
        self._save_speed = 0.0

    def __str__(self):
        if self._s.is_running():
            s = []
            s.append('Session      : %s' % self._s.get_session_name())
            s.append('File path    : %s' % self._s.get_file_path())
            s.append('Stream type  : %s' % self._s.get_stream_type ())
            s.append('Position %s of %s seconds, frame %s out of %s frames.' % (self._s.get_position(), self._s.get_length(), self._s.get_frame(), self._s.get_frames()))
            s.append('Status       : %s %s %s' % (self._s.get_status(), 
                            self._s.is_playing() and "(playing)" or "(not playing)", 
                            self._s.is_looping() and "(looping)" or "(not looping)"))
            s.append('Volume       : %s' % self._s.get_volume())
            s.append('Pan          : %s' % self._s.get_pan())
            s.append('Speed        : %s' % self._s.get_speed())
            s.append('Track %3.3s:' % (self._s.get_track_number(),))
            s.append(' genre       : %s' % self._s.get_genre())
            s.append(' artist      : %s' % self._s.get_artist())
            s.append(' album       : %s' % self._s.get_album())
            s.append(' title       : %s (%s)' % (self._s.get_title(), self._s.get_year()))
            s.append(' comment     : %s' % self._s.get_comment())
            return "\n".join(s)
        else:
            return "Alsaplayer session is not running."
 
    # auto-delegate...
    def __getattr__(self, name):
        return getattr(self._s, name)

    def play(self): # avoid a segfault in current player
        if not self._s.is_playing():
            self._s.play()

    def append(self, path):
        self._s.add_playlist(path)

    def __len__(self):
        if self._s.is_running():
            return self._s.get_playlist_length()
        else:
            return 0

    def clear(self):
        self._s.clear_playlist()

    def current_position(self):
        return self._s.get_playlist_position()

    def save(self):
        self._s.save_playlist()

    def shuffle(self):
        self._s.shuffle_playlist()

    def pause(self):
        s = self._s.get_speed()
        if s:
            self._save_speed = s
        self._s.set_speed(0.0)

    def unpause(self):
        if self._save_speed:
            self._s.set_speed(self._save_speed)

    def speedup(self, val=10.0):
        current = self._s.get_speed()
        new = min(2.0, current + (val/100.0))
        self._s.set_speed(new)

    def speeddown(self, val=10.0):
        current = self._s.get_speed()
        new = max(-2.0, current - (val/100.0))
        self._s.set_speed(new)

    def reverse(self):
        new = self._s.get_speed() * -1.0
        self._s.set_speed(new)

    def backup(self, secs=5):
        self._s.set_position_relative(-secs)

    def get_uri(self):
        # XXX define URI
        return '%s#%d' % (self._s.get_file_path(), self._s.get_position())
    
    def add_uri(self, uri):
        uri = uri.strip(" \n\r\t[]<>")
        if uri.find("#") >= 0:
            [path, pos] = uri.split("#",1)
            pos = int(pos)
        else:
            path, pos = uri, 0
        if path != self._s.get_file_path():
            if os.path.isfile(path):
                self._s.add_path(path)
            else:
                raise ValueError, "AlsaPlayer: set_uri: file not found."
        self._s.set_position(pos)
        return path, pos


def get_session(session=0):
    s = apcontrol.Session(session)
    if s.is_running():
        _alsaplayer = AlsaPlayerWrapper(s)
        return _alsaplayer
    else:
        raise ValueError, 'Session %d is not running' % (session,)


