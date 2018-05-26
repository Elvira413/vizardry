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

"""
This module provides classes for managing node connections in the network.
"""

import nr.types


class ChannelRef(nr.types.Named):
  """
  Represents a reference to a node and one of its input or output channels
  (depending on the context). Can be parsed from a string formatted as
  `path/to/node:channel`.
  """

  __annotations__ = [
    ('path', str),
    ('channel', str)
  ]

  @classmethod
  def parse(cls, s):
    path, channel = s.partition(':')[::2]
    if not path or not channel or channel.count(':') != 0:
      raise ValueError('invalid ChannelRef string', s)
    return cls(path, channel)


class Output(nr.types.Named):
  """
  Represents an output channel of a node and the assigned value.
  """

  __annotations__ = [
    ('name', str),
    ('type', object),
    ('calculated', bool, False),
    ('value', object, None)
  ]


class Input(nr.types.Named):
  """
  Represents an input channel of a node and a reference to the output channel
  that is linked to it. That reference may be #None if the input is not
  connected.
  """

  __annotations__ = [
    ('name', str),
    ('type', object),
    ('ref', (ChannelRef, None))
  ]


class _BaseList:

  def __init__(self):
    self._items = []

  def __iter__(self):
    return iter(self._items)

  def __len__(self):
    return len(self._items)

  def __getitem__(self, index):
    return self._items[index]

  def __repr__(self):
    return '{}({})'.format(type(self).__name__, self._outputs)

  def clear(self):
    self._items.clear()


class OutputList(_BaseList):

  def add(self, *a, **kw):
    output = Output(*a, **kw)
    for other in self._outputs:
      if other.name == output.name:
        raise ValueError('output already exists: {!r}'.format(output.name))
    self._outputs.append(output)


class InputList(_BaseList):

  def add(self, *a, **kw):
    input = Input(*a, **kw)
    for input in self._items:
      if other.name == input.name:
        raise ValueError('input already exists: {!r}'.format(input.name))
    self._items.append(input)
