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

from .. import gl, scene

import wx, wx.glcanvas


class Viewport(wx.Panel):

  def __init__(self, parent, scene):
    style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
    super().__init__(parent, -1)
    gl_attribs = (
      wx.glcanvas.WX_GL_RGBA,
      wx.glcanvas.WX_GL_DOUBLEBUFFER,
      wx.glcanvas.WX_GL_DEPTH_SIZE, 24)
    self.canvas = wx.glcanvas.GLCanvas(self, attribList=gl_attribs)
    self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.__erase_background)
    self.canvas.Bind(wx.EVT_SIZE, self.__size_event)
    self.canvas.Bind(wx.EVT_PAINT, self.__paint_event)
    self.canvas.Bind(wx.EVT_RIGHT_DOWN, self.__right_click)
    self.context = wx.glcanvas.GLContext(self.canvas)
    self.scene = scene

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.canvas, 1, wx.EXPAND)
    self.SetSizer(sizer)


  def create_context(self):
    return ViewportGLContext(self.canvas, self.context)

  def __erase_background(self, ev):
    pass  # Do nothing, to avoid flashing on Windows

  def __size_event(self, ev):
    self.Show()
    with self.scene.gl_context:
      size = self.canvas.GetClientSize()
      gl.glViewport(0, 0, size.width, size.height)
      self.canvas.Refresh(False)
      ev.Skip()

  def __paint_event(self, ev):
    with self.scene.gl_context:
      self.scene.gl_render()
      self.canvas.SwapBuffers()
      ev.Skip()

  def __right_click(self, ev):
    menu = wx.Menu()
    if self.scene.active_node:
      self.scene.active_node.build_context_menu(menu)
    if menu.GetMenuItemCount() > 0:
      menu.AppendSeparator()
    menu.Append(1, '&Save as Image ...')
    sel = self.GetPopupMenuSelectionFromUser(menu)
    # TODO: Implement Save as Image ...


class ViewportGLContext(scene.BaseGLContext):

  def __init__(self, canvas, context):
    super().__init__()
    self._canvas = canvas
    self._context = context

  def enable_gl_context(self):
    self._canvas.SetCurrent(self._context)

  def disable_gl_context(self):
    pass

  def destroy_gl_context(self):
    pass
