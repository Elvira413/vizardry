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

__all__ = ['ChannelRef', 'Output', 'Input', 'SceneNode', 'RootNode', 'Scene']

from .base import *
from . import event
from .parameters import ParameterContainer
from .. import gl

import nr.types
import os
import posixpath
import re
import traceback
import weakref


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


class SceneNode:
  """
  Wrapper around a scene node implementation.
  """

  class _Listener(event.Listener):
    __annotations__ = [
      ('func', callable),
      ('from_anywhere', bool, False)
    ]

    def check(self, event, **kwargs):
      if self.from_anywhere or kwargs.get('current') == event.source:
        return True
      return False

  def __init__(self, name, data):
    if data is not None and not isinstance(data, BaseSceneNodeData):
      raise TypeError('data must be BaseSceneNodeData instance', data)
    self._parent = None
    self._children = []
    self._listeners = event.EventHandler(SceneNode._Listener)
    self.supports_children = False
    self.auto_invoke_children = True
    self.data = data
    self.inputs = []
    self.outputs = []
    self.parameters = ParameterContainer()
    self.gl_resources = gl.ResourceManager()
    if data:
      data._node = weakref.ref(self)
      data.init(self)

    self.name = name

  def __repr__(self):
    return '<{} path={!r} name={!r} data={!r}>'.format(
      type(self).__name__, self.path, self.name, self.data)

  @property
  def path(self):
    parent = self.parent
    if parent:
      if isinstance(parent, RootNode):
        return '/' + self.name
      else:
        return parent.path + '/' + self.name
    return self.name

  @property
  def root(self):
    """
    Returns the #RootNode of the tree, or #None if the node is not attached to
    a graph that contains a #RootNode.
    """

    parent = self.parent
    while parent:
      self = parent
      parent = self.parent
    if isinstance(self, RootNode):
      return self
    return None

  @property
  def parent(self):
    return self._parent() if self._parent else None

  @parent.setter
  def parent(self, parent):
    if parent is not None and not isinstance(parent, SceneNode):
      raise TypeError('parent must be SceneNode instance')
    if not parent.supports_children:
      raise RuntimeError('this scene node does not support children', parent)
    old_path = self.path
    old_parent = self.parent
    self.remove()
    if parent is not None:
      self._parent = weakref.ref(parent)
      parent._children.append(self)
    self._update_name(self._name, old_parent)

  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, value):
    self._update_name(value, self.parent)

  @property
  def children(self):
    return self._children

  def remove(self):
    parent = self.parent
    self._parent = None
    if parent:
      parent._children.remove(self)

  def add(self, child):
    if not isinstance(child, SceneNode):
      raise TypeError('child must be SceneNode instance', child)
    child.parent = self

  def _update_name(self, name, old_parent):
    if not isinstance(name, str):
      raise TypeError('name bust be str', name)
    if not name or not re.match('[A-z0-9_]+$', name):
      raise ValueError('invalid name', name)

    is_initial = not hasattr(self, '_name')
    old_path = None if is_initial else self.path

    # Make sure the name doesn't collide with that of any other node
    # in the same parent node.
    parent = self.parent
    if parent:
      # Get the desired name without numeric suffix.
      norm_name = re.match('(.*)\d+$', name)
      norm_name = norm_name.group(1) if norm_name else name
      regex = re.compile(re.escape(norm_name) + '(\d+)?$')
      highest_number = None

      for child in parent.children:
        if child == self: continue
        match = regex.match(child._name)
        if not match: continue
        num = int(match.group(1) or '1')
        if highest_number is None or num > highest_number:
          highest_number = num

      if highest_number is not None:
        name = norm_name + str(highest_number + 1)

      assert all(x._name != name for x in parent.children if x != self)

    self._name = name

    if not is_initial and (old_path != self.path or old_parent != self.parent):
      ev_data = {'node': self, 'old_path': old_path, 'old_parent': old_parent}
      self.emit(event.PATH_CHANGED, ev_data)
      if not self.parent and old_parent:
        old_parent.emit(event.PATH_CHANGED, ev_data)

  def find_node(self, path):
    """
    Finds a node using a path reference relative to this node.
    """

    path = self.abs_path(path)
    if not path:
      return None

    node = self.root
    for part in path.split('/')[1:]:
      if not node:
        break
      if part == '..':
        node = node.parent
      elif part == '.':
        pass
      else:
        for child in node.children:
          if child.name == part:
            node = child
            break
        else:
          node = None
          break

    return node

  def abs_path(self, path):
    """
    Converts the specified path to an absolute path.
    """

    return posixpath.normpath(posixpath.join(self.path, path))

  def emit(self, kind, data, direction=None, source=None):
    """
    Triggers an event that propagates through the scene graph in the specified
    direction (either #event.UP, #event.DOWN or #event.LOCAL). If no direction
    is specified, the event will propagate in both directions.
    """

    if direction not in (None, event.UP, event.DOWN, event.LOCAL):
      raise ValueError('invalid event direction', direction)
    if source is None:
      source = self

    self._listeners.emit(kind, data, source, current=self)

    if direction is None or direction == event.UP:
      parent = self.parent
      if parent:
        parent.emit(kind, data, event.UP, source)
    if direction is None or direction == event.DOWN:
      for child in self._children:
        child.emit(kind, data, event.DOWN, source)

  def bind(self, kind, listener, from_anywhere=False):
    """
    Binds a listener for the specified event kind. The listener must accept
    an #Event object as its only argument. If *from_anywhere* is #True, then
    the listener will be invoked for any event received even if it was not
    triggered from this node.
    """

    self._listeners.bind(kind, listener, from_anywhere)

  # Forwards to the scene node implementation

  def gl_init(self):
    if self.data:
      with self.gl_resources.as_current(release=False):
        self.data.gl_init(self)
    if self.supports_children and self.auto_invoke_children:
      for child in self.children:
        child.gl_init()

  def gl_cleanup(self):
    if self.data:
      with self.gl_resources.as_current(release=False):
        self.data.gl_cleanup(self)
    self.gl_resources.release()
    if self.supports_children and self.auto_invoke_children:
      for child in self.children:
        child.gl_cleanup()

  def gl_render(self):
    if self.data:
      with self.gl_resources.as_current(release=False):
        self.data.gl_render(self)
    if self.supports_children and self.auto_invoke_children:
      for child in self.children:
        child.gl_render()

  def execute(self):
    if self.data:
      self.data.execute(self)
    if self.supports_children and self.auto_invoke_children:
      for child in self.children:
        child.execute()

  def get_icon(self):
    return self.data.get_icon(self)

  def build_context_menu(self, menu):
    if self.data:
      self.data.build_context_menu(self, menu)


class RootNode(SceneNode):
  """
  This is a special class that represents the root scene node.
  """

  def __init__(self, scene):
    super().__init__('', None)
    self.supports_children = True
    self._scene = weakref.ref(scene)

  @property
  def scene(self):
    return self._scene()

  @property
  def name(self):
    return '<root>'

  @name.setter
  def name(self, value):
    if value != '':
      raise ValueError('name of root node can not be set')

  @property
  def path(self):
    return '/'

  @property
  def parent(self):
    return None

  @parent.setter
  def parent(self, parent):
    raise ValueError('RootNode can not be the child of another node.')


class Scene:

  def __init__(self, default=True):
    self.root = RootNode(self)
    self.filename = None
    self.gl_context = None
    self.active_node = None
    self._new_nodes = set()
    self._removed_nodes = set()

    self.root.bind(event.PATH_CHANGED, self.__path_changed, True)

    if default:
      import textwrap
      from .impl.inlinenode import InlineNodeData
      node = SceneNode('inline', InlineNodeData())
      node.parameters['code'].set_value(textwrap.dedent("""
        from vizardry import gl
        from vizardry.gl.native import *

        def gl_init():
          global program
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

        def gl_render():
          glClearColor(0.5, 0.5, 0.5, 0.0)
          glClear(GL_COLOR_BUFFER_BIT)
          glUseProgram(program)
          #glUniform1f(glGetUniformLocation(program, "time"), scene.time)
          glBegin(GL_TRIANGLE_STRIP)
          glVertex2f(-1.0, -1.0)
          glVertex2f(1.0, -1.0)
          glVertex2f(-1.0, 1.0)
          glVertex2f(1.0, 1.0)
          glEnd()
      """))
      self.root.add(node)
      self.active_node = node

  @property
  def name(self):
    if self.filename:
      return os.path.baseame(self.filename)
    else:
      return 'Untitled'

  def __path_changed(self, ev):
    if ev['old_parent'] != ev.source.parent:
      # Parent has changed. Has the root changed, too?
      old_root = ev['old_parent'].root if ev['old_parent'] else None
      if old_root != ev.source.root:
        if old_root == self.root:
          if ev.source in self._new_nodes:
            self._new_nodes.discard(ev.source)
          else:
            self._removed_nodes.add(ev.source)
        elif ev.source.root == self.root:
          if ev.source in self._removed_nodes:
            self._removed_nodes.discard(ev.source)
          else:
            self._new_nodes.add(ev.source)

  def gl_cleanup(self):
    self.root.gl_cleanup()

  def gl_render(self):
    for node in self._removed_nodes:
      node.gl_cleanup()
    for node in self._new_nodes:
      node.gl_init()
    self._removed_nodes.clear()
    self._new_nodes.clear()
    self.root.gl_render()
