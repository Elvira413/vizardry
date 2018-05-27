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

import os
import posixpath
import re
import traceback
import weakref
from vizardry import gl
from vizardry.core import event
from vizardry.core.interfaces import NodeBehaviour, GLObjectInterface


class BaseGLContext:
  """
  Interface for activating/disabling/destroying an OpenGL context.
  """

  def __enter__(self):
    self.enable_gl_context()
    return self

  def __exit__(self, *a):
    self.disable_gl_context()

  def enable_gl_context(self):
    raise NotImplementedError

  def disable_gl_context(self):
    raise NotImplementedError

  def destroy_gl_context(self):
    raise NotImplementedError


class SceneNode:
  """
  Represents a node in a tree of nodes. The behaviour of a node is represented
  by an implementation of the #NodeBehaviour interface.
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

  def __init__(self, name, behaviour):
    if behaviour is not None and not NodeBehaviour.implemented_by(behaviour):
      raise TypeError('must implemented the NodeBehaviour interface')
    self._parent = None
    self._children = []
    self._listeners = event.EventHandler(SceneNode._Listener)
    self.supports_children = False
    self.auto_invoke_children = True
    self.behaviour = behaviour
    self.name = name

    if behaviour:
      behaviour.node = weakref.ref(self)
      behaviour.node_attached()

  def __repr__(self):
    return '<{} path={!r} name={!r} behaviour={!r}>'.format(
      type(self).__name__, self.path, self.name, self.behaviour)

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
  def scene(self):
    root = self.root
    if root:
      return root.scene
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
    if path == '/':
      return node

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

  def implements(self, interface):
    """
    A shortcut to check if the behaviour of the node implements a certain
    behaviour. Returns #False if the node has no behaviour attached.
    """

    if self.behaviour is not None:
      return interface.implemented_by(self.behaviour)
    return False


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

  def __init__(self):
    self.root = RootNode(self)
    self.filename = None
    self.gl_context = None
    self.active_node = None
    self.__listeners = event.EventHandler(event.Listener)
    self.__new_gl_nodes = set()
    self.__removed_gl_nodes = set()

    self.root.bind(event.PATH_CHANGED, self.__path_changed, True)

  @property
  def name(self):
    if self.filename:
      return os.path.baseame(self.filename)
    else:
      return 'Untitled'

  def __path_changed(self, ev):
    if ev.source.implements(GLObjectInterface) and ev['old_parent'] != ev.source.parent:
      # Parent has changed. Has the root changed, too?
      old_root = ev['old_parent'].root if ev['old_parent'] else None
      if old_root != ev.source.root:
        if old_root == self.root:
          if ev.source in self.__new_gl_nodes:
            self.__new_gl_nodes.discard(ev.source)
          else:
            self.__removed_gl_nodes.add(ev.source)
        elif ev.source.root == self.root:
          if ev.source in self.__removed_gl_nodes:
            self.__removed_gl_nodes.discard(ev.source)
          else:
            self.__new_gl_nodes.add(ev.source)

  def bind(self, kind, func):
    self.__listeners.bind(kind, func)

  def emit(self, kind, data):
    self.__listeners.emit(kind, data, self)

  def nodes(self, interface=None):
    """
    Returns a generator that yields all nodes in the scene. If an *interface*
    is specified, only nodes where the behaviour implements the specified
    interface are yielded.
    """

    def generator(node):
      yield node
      for child in node.children:
        yield from generator(child)

    gen = generator(self.root)
    if interface:
      gen = filter(lambda x: x.implements(interface), gen)
    return gen

  def set_active_node(self, node):
    if not isinstance(node, SceneNode):
      raise TypeError('expected SceneNode')
    if node.root != self.root:
      raise RuntimeError('node is not in the same root')
    self.active_node = node
    self.emit(event.SCENE_CHANGED, None)

  def gl_cleanup(self):
    for node in self.nodes(GLObjectInterface):
      with node.behaviour.gl_resources.as_current(release=False):
        try:
          node.behaviour.gl_cleanup()
        except:
          traceback.print_exc()

  def gl_render(self):
    for node in self.__removed_gl_nodes:
      with node.behaviour.gl_resources.as_current(release=False):
        try:
          node.behaviour.gl_cleanup()
        except:
          traceback.print_exc()
    self.__removed_gl_nodes.clear()
    self.__new_gl_nodes.clear()

    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    for node in self.nodes(GLObjectInterface):
      with node.behaviour.gl_resources.as_current(release=False):
        try:
          node.behaviour.gl_render()
        except:
          traceback.print_exc()


class node_factory:
  """
  Create a factory which creates a new #SceneNode with an instance of
  the specified *behaviour_class*.
  """

  factories = []

  def __init__(self, behaviour_class, name):
    self.behaviour_class = behaviour_class
    self.name = name
    node_factory.factories.append(self)

  def __call__(self, name=None):
    return SceneNode(name or self.name, self.behaviour_class())


def get_node_factories():
  return node_factory.factories
