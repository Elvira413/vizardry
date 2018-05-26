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
This module provides the API for node parameters.
"""

import wx
from vizardry.core import event


class Parameters:
  """
  Manages a collection of parameters.
  """

  def __init__(self):
    self._params = []

  def __getitem__(self, name):
    """
    Return the value of a parameter with the specified *name*.
    """

    param = self.param(name)
    if param is None:
      raise KeyError(name)
    return param.get_value()

  def __setitem__(self, name, value):
    """
    Set the value of a parmaeter with the specified *name*.
    """

    param = self.param(name)
    if param is None:
      raise KeyError(name)
    param.set_value(value)

  def __call__(self, name):
    param = self.param(name)
    if param is None:
      raise KeyError(name)
    return param

  def param(self, name):
    """
    Return the #Parameter with the specified *name*. Returns #None if there
    is no such parameter in the collection.
    """

    for param in self._params:
      if param.name == name:
        return param
    return None

  def remove(self, name):
    """
    Remove a #Parameter with the specified *name*. Raises #ValueError if
    there is no such parameter in the collection.
    """

    param = self.param(name)
    if param is None:
      raise ValueError('unknown parameter', name)
    self._params.remove(param)

  def add(self, param):
    """
    Add a #Parameter to the collection. Raises #ValueError if the name of
    the parameter is already occupied.
    """

    for other in self._params:
      if other.name == param.name:
        raise ValueError('parameter name already occupied: {!r}'.format(name))
    self._params.append(param)

  def create_panel(self, parent):
    """
    Creates a #wx.Panel filled with all controls of the parameters declared
    in the collection.
    """

    panel = wx.Panel(parent)
    sizer = wx.BoxSizer(wx.VERTICAL)
    for param in self._params:
      label = wx.StaticText(panel, label=param.label)
      control = param.create_control(panel)
      sizer.Add(label, 0)
      sizer.Add(control, 1, wx.EXPAND)
    panel.SetSizer(sizer)
    panel.SetAutoLayout(True)
    return panel


class Parameter:
  """
  Base class for parameters.
  """

  def __init__(self, name, label):
    self.name = name
    self.label = label
    self._listeners = event.EventHandler(event.Listener)

  def __repr__(self):
    return '<{} name={!r} label={!r}>'.format(
      type(self).__name__, self.name, self.label)

  def bind(self, kind, func):
    """
    Bind a listener to events that can be emitted by this parameter.
    """

    self._listeners.bind(kind, func)

  def emit(self, kind, data):
    """
    Emit an event from this parameter.
    """

    self._listeners.emit(kind, data, self)

  def create_control(self, parent):
    """
    Return a #wx.Window that controls the parameter value. Implementors
    usually keep a reference to the created control in order to be able
    to get/set the value from the widget.
    """

    raise NotImplementedError

  def get_value(self):
    """
    Return the value of the parameter. This must succeed even if
    #create_control() has not been called yet.
    """

    raise NotImplementedError

  def set_value(self, value):
    """
    Set the value of the parameter. This must succeed even if
    #create_control() has not been called yet.
    """

    raise NotImplementedError

  # TODO: Serialize/deserialize


class Number(Parameter):
  """
  Represents numeric parameter (integral or decimal) with support for
  min/max values, a slider and units.
  """

  # TODO

  def __init__(self, name, label, min=None, max=None, minslider=None,
               maxslider=None, slider=True, degree=False, integer=False):
    super().__init__(name, label)
    self.min = min
    self.max = max
    self.minslider = minslider
    self.maxslider = maxslider
    self.slider = slider
    self.degree = degree
    self.integer = integer

  def create_control(self, parent):
    raise NotImplementedError

  def get_value(self):
    raise NotImplementedError

  def set_value(self, value):
    raise NotImplementedError


class Text(Parameter):
  """
  Represents a text parameter. If a syntax is specified, a rich-text field
  will be created.
  """

  # TODO: Syntax highlighting with Pygments

  def __init__(self, name, label, multiline=False, syntax=None):
    super().__init__(name, label)
    self.multiline = multiline
    self.syntax = syntax
    self._widget = None
    self._value = ''

  def __on_key(self, event):
    if event.GetKeyCode() == wx.WXK_RETURN:
      if not self.multiline or wx.GetKeyState(wx.WXK_CONTROL):
        self.__commit()
        return
    event.Skip()

  def __on_kill_focus(self, event_obj):
    event_obj.Skip()
    new_value = self._widget.GetValue()
    if new_value != self._value:
      self._value = new_value
      self.emit(event.VALUE_CHANGED, None)

  def __commit(self):
    self.emit(event.VALUE_CHANGED, None)

  # Parameter

  def create_control(self, parent):
    self._value = self.get_value()

    style = 0
    if self.multiline:
      style |= wx.TE_MULTILINE|wx.TE_DONTWRAP
    if self.syntax:
      style |= wx.TE_RICH2

    self._widget = wx.TextCtrl(parent, style=style)

    if self.syntax:
      # TODO: Somehow to syntax highlighting (pygments and RTF?)
      self._widget.SetFont(
        wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
          wx.FONTWEIGHT_NORMAL, False, 'DejaVu Sans Mono'))

    self._widget.SetValue(self._value)

    self._widget.Bind(wx.EVT_KILL_FOCUS, self.__on_kill_focus)
    self._widget.Bind(wx.EVT_CHAR_HOOK, self.__on_key)
    return self._widget

  def get_value(self):
    if self._widget:
      return self._widget.GetValue()
    return self._value

  def set_value(self, value):
    value = str(value)
    if self._widget:
      self._widget.SetValue(value)
    self._value = value
