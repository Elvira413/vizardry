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

from .parameters import ParameterPaneManager

import time
import traceback


class BaseSceneNode:
  """
  Represents a node in the Vizardry scene which is capable of interacting
  with the GL canvas.
  """

  def __init__(self, name):
    self.name = name
    self.icon = None

  def gl_flush(self):
    pass

  def gl_paint(self):
    """
    Called to paint the GL scene. You should use PyOpenGL.
    """

    pass

  def gl_resize(self, size):
    pass

  def update(self):
    pass

  def parameter_pane(self):
    """
    Return the wxPython parameter pane for this node.
    """

    return None


class CompositableSceneNode(BaseSceneNode):

  def __init__(self, name):
    super().__init__(name)
    self.parameters = ParameterPaneManager()

  def hook(self, arg):
    """
    Hook a function that is usually implemented as a class method.

    # Parameters
    arg (str, function):
      Either the name of a hook or a function that has the same name as the
      hook you want to place. If a name is specified, a decorator is returned.
    """

    def decorator(func, name):
      if not hasattr(BaseSceneNode, name):
        raise RuntimeError('unsupported hook: {}'.format(name))
      setattr(self, name, func)
      return func

    if isinstance(arg, str):
      return lambda f: decorator(f, arg)
    else:
      return decorator(arg, arg.__name__)

  def parameter_pane(self):
    return self.parameters.pane


class Scene:
  """
  Represents a Vizardry scene which is composed of nodes that can interact
  with the GL canvas.
  """

  def __init__(self):
    self.gl_handles = []
    self.old_gl_handles = []
    self.nodes = []
    self.reset()

  @property
  def time(self):
    return time.clock() - self.start_time

  def reset(self):
    self.old_gl_handles += self.gl_handles
    self.gl_handles.clear()
    self.nodes.clear()
    self.framerate = None
    self.start_time = time.clock()

  def event(self, __name, *args, **kwargs):
    if __name == 'gl_flush':
      for handle, deleter in self.old_gl_handles:
        deleter(handle)
      self.old_gl_handles.clear()
    for node in self.nodes:
      try:
        getattr(node, __name)(*args, **kwargs)
      except:
        traceback.print_exc()

  def create_node(self, name, node_type=CompositableSceneNode):
    """
    Create a new scene node (#CompositableSceneNode by default), add it to the
    scene and return it.
    """

    node = node_type(name)
    self.nodes.append(node)
    return node

  def gl_handle(self, handle, deleter):
    assert callable(deleter)
    self.gl_handles.append((handle, deleter))
    return handle
