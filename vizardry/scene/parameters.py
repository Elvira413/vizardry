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

__all__ = ['Parameter', 'ParameterContainer', 'Number']

from . import event
import traceback
import wx


class Parameter:
  """
  Base class for parameters.
  """

  def __init__(self, name, label):
    self.name = name
    self.label = label
    self._listeners = event.EventHandler(event.Listener)

  def bind(self, kind, func):
    self._listeners.bind(kind, func)

  def emit(self, kind, data):
    self._listeners.emit(kind, data, self)

  def create_control(self, parent):
    raise NotImplementedError

  def get_value(self):
    raise NotImplementedError

  def set_value(self, value):
    raise NotImplementedError

  def serialize(self):
    return self.get_value()

  def deserialize(self, data):
    self.set_value(data)


class ParameterContainer:
  """
  Represents a container for parameter declarations.
  """

  def __init__(self):
    self._params = []

  def __getitem__(self, name):
    param = self.param(name)
    if param is None:
      raise KeyError(name)
    return param

  def clear(self):
    self._params.clear()

  def param(self, name):
    for param in self._params:
      if param.name == name:
        return param
    return None

  def remove(self, name):
    param = self.param(name)
    if not param:
      raise ValueError('unknown parameter', name)
    self._params.remove(param)

  def add(self, param):
    for other in self._params:
      if other.name == param.name:
        raise ValueError('parameter name already occupied', name)
    self._params.append(param)

  def create_panel(self, parent):
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


class Number(Parameter):

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

  def __init__(self, name, label, multiline=False, syntax=None):
    super().__init__(name, label)
    self.multiline = multiline
    self.syntax = syntax
    self._widget = None
    self._value = ''

  def create_control(self, parent):
    self._value = self.get_value()

    style = 0
    if self.multiline:
      style |= wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_RICH2

    self._widget = wx.TextCtrl(parent, style=style)

    if self.syntax:
      # TODO: Somehow to syntax highlighting (pygments and RTF?)
      self._widget.SetFont(
        wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
          wx.FONTWEIGHT_NORMAL, False, 'DejaVu Sans Mono'))

    self._widget.SetValue(self._value)

    self._widget.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)
    self._widget.Bind(wx.EVT_CHAR_HOOK, self._on_key)
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

  def _on_key(self, event):
    if event.GetKeyCode() == wx.WXK_RETURN:
      if not self.multiline or wx.GetKeyState(wx.WXK_CONTROL):
        self._commit()
        return
    event.Skip()

  def _on_kill_focus(self, event_obj):
    event_obj.Skip()
    new_value = self._widget.GetValue()
    if new_value != self._value:
      self._value = new_value
      self.emit(event.VALUE_CHANGED, None)

  def _commit(self):
    self.emit(event.VALUE_CHANGED, None)
