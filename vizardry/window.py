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

from .scene import BaseGLContext, Scene

import OpenGL.GL
import traceback
import wx, wx.glcanvas


DEFAULT_CODE = """
from vizardry import gl
from vizardry.gl.native import *
scene.framerate = 50
node = scene.create_node('basic')


program = gl.Program.from_fragment('''

  #version 330 core
  uniform float time;
  in vec2 fragCoord;
  out vec4 fragColor;
  const int ncolors = 4;
  const vec4 colors[ncolors] = vec4[](
    vec4(0.1, 0.3, 1.0, 1.0),
    vec4(0.7, 0.9, 1.0, 1.0),
    vec4(1.0, 1.0, 0.6, 1.0),
    vec4(0.5, 0.0, 0.5, 1.0)
  );
  void main() {
    vec2 c = fragCoord.xy;
    c = c * vec2(4,3) - vec2(2.5, 1.5);
    vec2 z = vec2(0, 0); //cos(time / 100), sin(time / 100));
    int limit = 16;
    int i = 0;
    for (i = 0; i < limit; ++i) {
      if (z.x * z.x + z.y * z.y >= 4.0) {
        break;
      }
      z = vec2(z.x*z.x - z.y*z.y, 2.*z.x*z.y) + c;
    }
    float x = mod(float(i) / float(limit) + time * 0.25, 1.0) * ncolors;
    int il = min(int(x), ncolors-2);
    float w = x - il;
    fragColor = colors[il] * (1.0-w) + colors[(il+1)] * w;
  }

''')


@node.hook
def gl_paint():
  glClearColor(0.5, 0.5, 0.5, 0.0)
  glClear(GL_COLOR_BUFFER_BIT)
  glUseProgram(program)
  glUniform1f(glGetUniformLocation(program, "time"), scene.time)
  glBegin(GL_TRIANGLE_STRIP)
  glVertex2f(-1.0, -1.0)
  glVertex2f(1.0, -1.0)
  glVertex2f(-1.0, 1.0)
  glVertex2f(1.0, 1.0)
  glEnd()
"""


class Viewport(wx.Panel):

  def __init__(self, parent, scene):
    style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
    super().__init__(parent, -1)
    gl_attribs = (
      wx.glcanvas.WX_GL_RGBA,
      wx.glcanvas.WX_GL_DOUBLEBUFFER,
      wx.glcanvas.WX_GL_DEPTH_SIZE, 24)
    self.canvas = wx.glcanvas.GLCanvas(self, attribList=gl_attribs)
    self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self._erase_background)
    self.canvas.Bind(wx.EVT_SIZE, self._size_event)
    self.canvas.Bind(wx.EVT_PAINT, self._paint_event)
    self.context = wx.glcanvas.GLContext(self.canvas)
    self.scene = scene or Scene()

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.canvas, 1, wx.EXPAND)
    self.SetSizer(sizer)

  def _erase_background(self, event):
    pass  # Do nothing, to avoid flashing on Windows

  def _size_event(self, event):
    self.Show()
    with self.scene.gl_context:
      size = self.canvas.GetClientSize()
      OpenGL.GL.glViewport(0, 0, size.width, size.height)
      self.canvas.Refresh(False)
      event.Skip()

  def _paint_event(self, event):
    with self.scene.gl_context:
      self.scene.event('gl_paint')
      self.canvas.SwapBuffers()
      event.Skip()


class ViewportGLContext(BaseGLContext):

  def __init__(self, viewport):
    super().__init__()
    self._viewport = viewport

  def _set_current(self):
    self._viewport.canvas.SetCurrent(self._viewport.context)

  def _disable(self):
    pass

  def _destroy(self):
    pass


class EditorPane(wx.Panel):

  def __init__(self, parent, scene):
    super().__init__(parent, -1)
    self.scene = scene
    self.notebook =  wx.Notebook(self)

    # Edit Page #
    # ========= #

    self.edit_page = wx.Panel(self.notebook)
    self.code = wx.TextCtrl(self.edit_page, style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_RICH2)
    self.code.SetFont(
      wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_NORMAL, False, 'DejaVu Sans Mono'))
    self.code.SetValue(DEFAULT_CODE)
    self.code.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.code, 1, wx.EXPAND)
    sizer.Add(wx.Button(self.edit_page, 1, 'Update'))
    self.edit_page.SetSizer(sizer)
    self.edit_page.Bind(wx.EVT_BUTTON, lambda e:  self._update() if e.GetId() == 1 else 0)

    self.notebook.AddPage(self.edit_page, 'Edit')

    # ==

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.notebook, 1, wx.EXPAND)
    self.SetSizer(sizer)

  def _on_key(self, event):
    if event.GetKeyCode() == wx.WXK_RETURN and wx.GetKeyState(wx.WXK_CONTROL):
      self._update()
    else:
      event.Skip()

  def _update(self):
    self.scene.reset()
    with self.scene.gl_context:
      self.scene.event('gl_flush')
      try:
        code = compile(self.code.GetValue(), 'Vizardry', 'exec')
        scope = {'scene': self.scene}
        exec(code, scope)
        self.GetParent().update()
      except:
        traceback.print_exc()


class MainWindow(wx.Frame):
  """
  The Vizardry main window.
  """

  def __init__(self, title, scene=None):
    super().__init__(None, -1, "Vizardry")
    self.scene = scene or Scene()
    self.timer = wx.Timer(self, 1)
    self.viewport = Viewport(self, self.scene)
    self.settings_pane = EditorPane(self, self.scene)
    self.Bind(wx.EVT_TIMER, self._timer, self.timer)

    self.scene.gl_context = ViewportGLContext(self.viewport)

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.viewport, 4, wx.EXPAND)
    sizer.Add(self.settings_pane, 3, wx.EXPAND)
    self.SetSizer(sizer)

    self.SetClientSize(1024, 512)
    self.Bind(wx.EVT_CLOSE, self._close)

  def _close(self, event):
    self.scene.reset()
    self.scene.gl_context.destroy()
    event.Skip()

  def _timer(self, event):
    self.scene.event('update')
    self.update()

  def _update_timer(self):
    if self.scene.framerate is None:
      self.timer.Stop()
    else:
      ms = int(1.0 / self.scene.framerate * 1000)
      self.timer.Start(ms)

  def update(self):
    self._update_timer()
    self.viewport.canvas.Refresh(False)
