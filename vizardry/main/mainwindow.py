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

import textwrap
import traceback
import wx
from vizardry.core.interfaces import NodeBehaviour
from vizardry.core.scene import Scene, get_node_factories
from vizardry.main.viewport import Viewport


class ParameterPanel(wx.Panel):

  def __init__(self, parent, node):
    super().__init__(parent, -1)
    self.node = node

    icon = node.behaviour.node_icon()
    if isinstance(icon, wx.Image):
      icon = icon.Scale(24, 24).ConvertToBitmap()

    self.path_panel = wx.Panel(self)
    self.node_icon = wx.StaticBitmap(self.path_panel)
    if icon:
      self.node_icon.SetBitmap(icon)
    self.node_name = wx.TextCtrl(self.path_panel, style=wx.TE_PROCESS_ENTER)
    self.node_name.SetValue(node.name)
    self.node_name.Bind(wx.EVT_TEXT_ENTER, self.__on_name_changed)
    self.node_name.Bind(wx.EVT_KILL_FOCUS, self.__on_name_kill_focus)
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.node_icon)
    sizer.Add(wx.StaticText(self.path_panel, label=(node.parent.path if node.parent else '/')))
    sizer.Add(self.node_name)
    self.path_panel.SetSizer(sizer)

    self.node_params = node.params.create_panel(self)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.path_panel)
    if self.node_params:
      sizer.Add(self.node_params, 1, wx.EXPAND)
    self.SetSizer(sizer)

  def __on_name_changed(self, ev):
    try:
      self.node.name = self.node_name.GetValue()
    except ValueError as exc:
      print(exc)
    else:
      # The actual name may not be exactly what was entered if there
      # was a name collision.
      self.node_name.SetValue(self.node.name)

  def __on_name_kill_focus(self, ev):
    ev.Skip()
    self.node_name.SetValue(self.node.name)


class NodelistPanel(wx.Panel):

  def __init__(self, parent, scene):
    super().__init__(parent, -1)
    self.scene = scene
    self.listbox = wx.ListBox(self, style=wx.LB_SINGLE|wx.LB_SORT)
    self.listbox.Bind(wx.EVT_LISTBOX, lambda ev: self.__listbox_event(ev, False))
    self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, lambda ev: self.__listbox_event(ev, True))
    self.listbox.Bind(wx.EVT_RIGHT_DOWN, self.__rightclick)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.listbox, 1, wx.EXPAND)
    self.SetSizer(sizer)

    self.refresh()

    func = lambda ev: self.refresh()
    self.scene.root.bind(self.scene.root.EV_NAME_CHANGED, func, global_=True)
    self.scene.root.bind(self.scene.root.EV_PARENT_CHANGED, func, global_=True)

  def __rightclick(self, ev):
    index = self.listbox.HitTest(ev.GetPosition())
    if index != wx.NOT_FOUND:
      node = self.scene.root.find_node(self.listbox.GetString(index))
      if not node: return

      self.listbox.SetSelection(index)
      menu = wx.Menu()

      if node.supports_children:
        create_node_map = {}
        create_node_menu = wx.Menu()
        i = 0
        for factory in get_node_factories():
          create_node_map[i] = factory
          create_node_menu.Append(i, factory.name)
          i += 1
        menu.Append(wx.ID_ANY, "Create ...", create_node_menu)

      i = self.GetPopupMenuSelectionFromUser(menu)

      if node.supports_children and i in create_node_map:
        new_node = create_node_map[i]()
        node.add(new_node)
        self.scene.active_node = new_node
        self.refresh()

  def __listbox_event(self, ev, double_click):
    index = self.listbox.GetSelection()
    if index != wx.NOT_FOUND:
      node = self.scene.root.find_node(self.listbox.GetString(index))
    self.scene.active_node = node
    if double_click:
      self.scene.emit(self.scene.EV_FOCUS_PARAMETERS)

  def refresh(self):
    self.listbox.Clear()
    for index, node in enumerate(self.scene.root.iter_hierarchy()):
      self.listbox.Append(node.path)
      if node == self.scene.active_node:
        self.listbox.SetSelection(index)


class EditorPane(wx.Panel):

  def __init__(self, parent, scene):
    super().__init__(parent, -1)
    self.scene = scene
    self.notebook =  wx.Notebook(self)

    self.nodelist_page = NodelistPanel(self.notebook, scene)
    self.notebook.AddPage(self.nodelist_page, 'Nodes')
    self.edit_page = wx.Panel(self.notebook)
    self.notebook.AddPage(self.edit_page, 'Edit')
    self.notebook.SetSelection(1 if self.scene.active_node else 0)
    self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__page_changed)

    self.parameter_panel = None

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.notebook, 1, wx.EXPAND)
    self.SetSizer(sizer)

    self.update()

    self.scene.bind(self.scene.EV_FOCUS_PARAMETERS, lambda ev: self.notebook.SetSelection(1))

  def __page_changed(self, ev):
    if self.notebook.GetSelection() == 1:
      self.update()

  def update(self):
    if self.parameter_panel:
      self.parameter_panel.Destroy()
      self.parameter_panel = None
    if self.scene.active_node:
      self.parameter_panel = ParameterPanel(self.edit_page, self.scene.active_node)
      sizer = wx.BoxSizer(wx.VERTICAL)
      sizer.Add(self.parameter_panel, 1, wx.EXPAND)
      self.edit_page.SetSizer(sizer)
      self.edit_page.SendSizeEvent()


class MainWindow(wx.Frame):
  """
  The Vizardry main window.
  """

  def __init__(self, title, scene=None):
    super().__init__(None, -1, "Vizardry")
    if scene is None:
      scene = Scene()
      add_default_nodes(scene)

    self.viewport = Viewport(self, scene)
    self.settings_pane = EditorPane(self, scene)

    self.scene = scene or Scene()
    self.scene.bind(self.scene.EV_VIEWPORT_UPDATE, self.__viewport_update)

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


def add_default_nodes(scene):
  from vizardry.behaviours.glinline import GLInline
  from vizardry.behaviours.resource import Resource

  glinline = GLInline(scene)
  glinline.params['code'] = textwrap.dedent('''
    from vizardry import gl
    from vizardry.gl.api import *

    program = None

    def gl_render():
      global program
      if not program:
        code = node.find_node('../fragment').params['text']
        program = gl.Program.from_fragment(code)
      glUseProgram(program)
      glBegin(GL_TRIANGLE_STRIP)
      glVertex2f(-1.0, -1.0)
      glVertex2f(1.0, -1.0)
      glVertex2f(-1.0, 1.0)
      glVertex2f(1.0, 1.0)
      glEnd()
    ''').lstrip()
  glinline.attach_to(scene.root)

  fragment = Resource(scene, 'fragment')
  fragment.params['text'] = textwrap.dedent('''
    #version 330 core
    uniform float time;
    in vec2 fragCoord;
    out vec4 fragColor;
    const int ncolors = 5;
    const vec3 colors[ncolors] = vec3[](
      vec3(0.1, 0.3, 1.0),
      vec3(0.1, 0.3, 1.0),
      vec3(0.7, 0.9, 0.8),
      vec3(1.0, 1.0, 1.0),
      vec3(0.7, 0.2, 0.2)
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
      float x = (float(i) / float(limit) + time * 0.25) * (ncolors-1);
      int il = int(x) % ncolors;
      float w = x - il;
      fragColor = vec4(colors[il] * (1.0-w) + colors[(il+1)] * w, 1.0);
    }
    ''').lstrip()
  fragment.attach_to(scene.root)
