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

import nr.types
import os
import posixpath
import re
import traceback
import weakref
from vizardry import gl
from vizardry.core.generics.eventhandler import EventHandler
from vizardry.core.generics.network import *
from vizardry.core.interfaces import NodeBehaviour, GLObjectInterface
from vizardry.core.parameters import Parameters


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


class Scene(Network):
  """
  A scene is a container for a node network and manages certain aspects of the
  execution pipeline.
  """

  EV_VIEWPORT_UPDATE = 'Scene.EV_VIEWPORT_UPDATE'
  EV_FOCUS_PARAMETERS = 'Scene.EV_FOCUS_PARAMETERS'
  EV_ACTIVE_NODE_CHANGED = 'Scene.EV_ACTIVE_NODE_CHANGED'

  class RootBehaviour(nr.interface.Implementation):
    nr.interface.implements(NodeBehaviour)

  def __init__(self):
    super().__init__(lambda s: SceneNode(s, 'root', self.RootBehaviour()))
    self.__active_node = None
    self.__listeners = EventHandler()

  @property
  def active_node(self):
    return self.__active_node() if self.__active_node else None

  @active_node.setter
  def active_node(self, node):
    if not isinstance(node, SceneNode):
      raise TypeError('expected SceneNode')
    if node.network != self:
      raise RuntimeError('active_node must be in the same scene')
    old_node = self.active_node
    if node != old_node:
      self.__active_node = weakref.ref(node)
      data = {'new_node': node, 'old_node': old_node}
      self.emit(self.EV_ACTIVE_NODE_CHANGED, data)

  def bind(self, *args, **kwargs):
    self.__listeners.bind(*args, **kwargs)

  def emit(self, *args, **kwargs):
    self.__listeners.emit(*args, **kwargs)

  def gl_render(self):
    #for node in self.__removed_gl_nodes:
    #  with node.behaviour.gl_resources.as_current(release=False):
    #    try:
    #      node.behaviour.gl_cleanup()
    #    except:
    #      traceback.print_exc()
    #self.__removed_gl_nodes.clear()
    #self.__new_gl_nodes.clear()

    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    for node in self.root.iter_hierarchy():
      if not node.implements(GLObjectInterface):
        continue
      with node.behaviour.gl_resources.as_current(release=False):
        try:
          node.behaviour.gl_render()
        except:
          traceback.print_exc()

  def gl_cleanup(self):
    for node in self.root.iter_hierarchy():
      if not node.implements(GLObjectInterface):
        continue
      with node.behaviour.gl_resources.as_current(release=False):
        try:
          node.behaviour.gl_cleanup()
        except:
          traceback.print_exc()

  # Network

  def on_node_enters_network(self, node):
    if type(node) != SceneNode:
      raise TypeError('only SceneNodes can be added to the Scene network.')


class SceneNode(NetworkNode):
  """
  Represents a node in the scene. The behaviour of the node is defined by
  its *behaviour* object which must be an instance of a class that implements
  the #NodeBehaviour interface.

  Additionally, every node can have

  * input and output slots for computed data which can be connected
  * parameters that can be displayed in the User Interface and read/changed
    from code
  * listeners that are bound to certain events associated with the node (eg.
    name or location change)
  """

  EV_UP = 'up'
  EV_DOWN = 'down'
  EV_LOCAL = 'local'

  EV_NAME_CHANGED = 'ScenNode.EV_NAME_CHANGED'
  EV_PARENT_CHANGED = 'ScenNode.EV_PARENT_CHANGED'

  def __init__(self, network, name, behaviour):
    if not isinstance(network, Scene):
      raise TypeError('network must be a Scene instance')
    if not NodeBehaviour.implemented_by(behaviour):
      raise TypeError('must implement the NodeBehaviour interface')
    self.__listeners = EventHandler()
    self.params = Parameters()
    self.inputs = InputList()
    self.outputs = OutputList()
    self.behaviour = behaviour
    behaviour.node = weakref.ref(self)
    super().__init__(network, name)
    behaviour.node_attached(self)

  def __repr__(self):
    return '<SceneNode path={!r} behaviour={!r}>'.format(
      self.path, self.behaviour)

  scene = NetworkNode.network

  @property
  def scene(self):
    """
    An alias for the #network property.
    """

    return self.network

  def bind(self, kind, func, global_=False):
    """
    Bind a function to the specified event kind. If *global_* is #True, the
    listener will receive any events that are propagated through the
    hierarchy, otherwise it will only be invoked if the event was actually
    emitted by the very node it was bound with.
    """

    if global_:
      filter = None
    else:
      filter = lambda ev: ev.source == self
    self.__listeners.bind(kind, func, filter=filter)

  def emit(self, kind, data, direction=None, source=None):
    """
    Emit an event that propagates through the scene graph in the specified
    direction (either #EV_UP, #EV_DOWN or #EV_LOCAL). If no direction is
    specified, the event will propagate both up and down.
    """

    if direction not in (None, self.EV_UP, self.EV_DOWN, self.EV_LOCAL):
      raise ValueError('invalid event direction: {!r}'.format(direction))
    if source is None:
      source = self

    self.__listeners.emit(kind, data, source)

    if direction is None or direction == self.EV_UP:
      parent = self.parent
      if parent:
        parent.emit(kind, data, self.EV_UP, source)
    if direction is None or direction == self.EV_DOWN:
      for child in self.children:
        child.emit(kind, data, self.EV_DOWN, source)

  def implements(self, interface):
    """
    A shortcut to check if the behaviour of the node implements a certain
    behaviour. Returns #False if the node has no behaviour attached.
    """

    return interface.implemented_by(self.behaviour)

  # NetworkNode

  @NetworkNode.name.setter
  def name(self, value):
    old_name = self.name
    NetworkNode.name.__set__(self, value)
    if old_name != self.name:
      data = {'new_name': self.name, 'old_name': old_name}
      self.emit(self.EV_NAME_CHANGED, data)

  # TreeNode

  def detach(self):
    old_parent = self.parent
    super().detach()
    if old_parent is not None:
      data = {'new_parent': None, 'old_parent': old_parent}
      self.emit(self.EV_PARENT_CHANGED, data)

  def attach_to(self, parent, *args, **kwargs):
    old_parent = self.parent
    super().attach_to(parent, *args, **kwargs)
    if old_parent != parent:
      data = {'new_parent': parent, 'old_parent': old_parent}
      self.emit(self.EV_PARENT_CHANGED, data)


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

  def __call__(self, scene, name=None):
    return SceneNode(scene, name or self.name, self.behaviour_class())


def get_node_factories():
  return node_factory.factories
