# -*- coding: utf8 -*-
# Copyright (c) 2018 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import nr.types
import traceback

EVENT_UP = 'up'
EVENT_DOWN = 'down'
EVENT_LOCAL = 'local'
EVENT_VALUE_CHANGED = 'event.value.changed'
EVENT_PATH_CHANGED = 'event.path.changed'
EVENT_VIEWPORT_UPDATE = 'event.viewport.update'


class Event(nr.types.Named):

  __annotations__ = [
    ('kind', str),
    ('data', dict),
    ('source', 'SceneNode')
  ]

  def __getitem__(self, name):
    return self.data[name]


class Listener(nr.types.Named):

  __annotations__ = [
    ('func', callable)
  ]

  def check(self, event, **kwargs):
    return True


class EventHandler:

  def __init__(self, listener_class):
    self._listener_class = listener_class
    self._listeners = {}

  def bind(self, kind, *args, **kwargs):
    listener = self._listener_class(*args, **kwargs)
    self._listeners.setdefault(kind, []).append(listener)

  def unbind(self, kind, func=None):
    if func is None:
      self._listeners.pop(kind, None)
      return True
    else:
      items = self._listeners.get(kind, [])
      listener = next((x for x in items if x.func == func), None)
      if listener:
        items.remove(listener)
        return True
      return False

  def emit(self, kind, data, source, **listener_check_kwargs):
    if data is None:
      data = {}
    event = Event(kind, data, source)
    for listener in self._listeners.get(kind, []):
      if listener.check(event, **listener_check_kwargs):
        try:
          listener.func(event)
        except:
          traceback.print_exc()


__all__ = ['Event']
for _k, _v in list(globals().items()):
  if _k.startswith('EVENT_'):
    globals()[_k[6:]] = _v
    __all__.append(_k)
del _k, _v
