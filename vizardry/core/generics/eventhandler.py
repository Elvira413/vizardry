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

import itertools
import nr.interface
import traceback
import sys


class Event(nr.interface.Interface):
  kind = nr.interface.attr(str)

  @nr.interface.default
  def __repr__(self):
    return '<{} kind={!r}>'.format(type(self).__name__)


class Listener(nr.interface.Interface):

  def invoke(self, event):
    pass


class StandardEvent(nr.interface.Implementation):
  nr.interface.implements(Event)

  def __init__(self, kind, data=None, source=None):
    self.kind = kind
    self.data = data
    self.source = source

  def __repr__(self):
    return '<StandardEvent kind={!r} data={!r} source={!r}>'.format(
      self.kind, self.data, self.source)


class StandardListener(nr.interface.Implementation):
  nr.interface.implements(Listener)

  def __init__(self, func, filter=None):
    self.func = func
    self.filter = filter

  def invoke(self, event):
    if not self.filter or self.filter(event):
      self.func(event)


class EventHandler:
  """
  The event handler allows you to register listeners and emit events for
  these listeners. A listener may be registered globally or for a specific
  event.

  # Parameters
  event_class (Event): An implementation of the #Event interface. Defaults
    to the #StandardEvent class which accepts an explicit *kind* and *data*
    argument and an optional *source* parameter.
  listener_class (Listener): An implementation of the #Listener interface.
    Defaults to the #StandardListener class which just the function to call
    on the event and an optional *filter* function.
  """

  def __init__(self, event_class=StandardEvent, listener_class=StandardListener):
    self.event_class = event_class
    self.listener_class = listener_class
    self.listeners = {}

  def bind(self, __kind, *args, **kwargs):
    """
    Creates a new listener that is registered for the specified event kind.
    The additional arguments are forwarded to the #listener_class that was
    passed when the #EventHandler was created.

    # Parameter
    __kind (any): The event kind to bind the listener to. If this is #None,
      the listener will bind to any event.
    *args, **kwargs: Arguments to the #listener_class.
    return (listener_class): The listener added to the event handler.
    """

    listener = self.listener_class(*args, **kwargs)
    self.listeners.setdefault(__kind, []).append(listener)
    return listener

  def unbind(self, kind, listener):
    """
    Unbind a listener from the specified event kind.

    # Parameter
    kind (any): The event kind.
    listener (listener_class): The listener returned from #bind().
    raise (ValueError): If *listener* is not a listener for the event.
    """

    self.listeners.get(kind, []).remove(listener)

  def emit(self, *args, **kwargs):
    """
    Emit an event, invoking all listeners that are bound to it. Any
    exceptions that occur inside the listeners will be caught and
    forwarded to the #handle_exception() method.

    # Parameters
    *args, **kwargs: Arguments for the #event_class constructor.
    """

    event = self.event_class(*args, **kwargs)
    listeners = itertools.chain(
      self.listeners.get(None, []), self.listeners.get(event.kind, []))

    for listener in listeners:
      try:
        listener.invoke(event)
      except:
        self.handle_exception(event, listener, sys.exc_info())

  def handle_exception(self, event, listener, exc_info):
    """
    Handle an exception that occurred when a listener was invoked for the
    specified event. The default implementation will print the traceback.
    """

    traceback.print_exc()
