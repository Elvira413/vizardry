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

from ..scene import Scene, event
from .viewport import Viewport
import traceback
import wx, wx.glcanvas


class EditorPane(wx.Panel):

  def __init__(self, parent, scene):
    super().__init__(parent, -1)
    self.scene = scene
    self.notebook =  wx.Notebook(self)

    self.scene_page = wx.Panel(self.notebook)
    self.notebook.AddPage(self.scene_page, 'Scene')
    self.edit_page = wx.Panel(self.notebook)
    self.notebook.AddPage(self.edit_page, 'Edit')
    self.notebook.SetSelection(1)

    self.parameter_pane = None

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.notebook, 1, wx.EXPAND)
    self.SetSizer(sizer)

    self.update()

  def update(self):
    if self.parameter_pane:
      self.parameter_pane.Destroy()
      self.parameter_pane = None
    if self.scene.active_node:
      self.parameter_pane = self.scene.active_node.parameters.create_panel(self.edit_page)
      sizer = wx.BoxSizer(wx.VERTICAL)
      sizer.Add(self.parameter_pane, 1, wx.EXPAND)
      self.edit_page.SetSizer(sizer)


class MainWindow(wx.Frame):
  """
  The Vizardry main window.
  """

  def __init__(self, title, scene=None):
    super().__init__(None, -1, "Vizardry")
    if scene is None:
      scene = Scene()

    self.viewport = Viewport(self, scene)
    self.settings_pane = EditorPane(self, scene)

    self.scene = scene or Scene()
    self.scene.gl_context = self.viewport.create_context()
    self.scene.root.bind(event.VIEWPORT_UPDATE, self.__viewport_update, True)

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.viewport, 4, wx.EXPAND)
    sizer.Add(self.settings_pane, 3, wx.EXPAND)
    self.SetSizer(sizer)

    self.SetClientSize(1024, 512)
    self.Bind(wx.EVT_CLOSE, self.__close)

    #self.timer = wx.Timer(self, 1)
    #self.Bind(wx.EVT_TIMER, self._timer, self.timer)

  def __viewport_update(self, ev):
    self.viewport.canvas.Refresh(False)

  def __close(self, ev):
    self.scene.gl_cleanup()
    self.scene.gl_context.destroy_gl_context()
    ev.Skip()

  """
  def _timer(self, event):
    self.scene.event('update')
    self.update()

  def _update_timer(self):
    if self.scene.framerate is None:
      self.timer.Stop()
    else:
      ms = int(1.0 / self.scene.framerate * 1000)
      self.timer.Start(ms)
  """

  def update(self):
    self._update_timer()
    self.viewport.canvas.Refresh(False)
