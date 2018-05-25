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

__all__ = ['BaseGLContext', 'BaseSceneNodeData']

from .. import gl


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


class BaseSceneNodeData:
  """
  Base class for the implementation of a scene node. Subclasses are
  instantiated and attached to actual scene nodes. The data class implements
  the behaviour of the node.
  """

  _node = None  # The actual scene node attached to this data, as a weakref.

  @property
  def node(self):
    return self._node() if self._node else None

  def init(self, node):
    """
    Called when the data object is attached to a scene node. This method
    should declare the inputs, outputs and parameters of the node.
    """

    pass

  def gl_init(self, node):
    """
    Called when the node first encounters the OpenGL context. The node's
    GL resource manager is current in this method.
    """

    pass

  def gl_cleanup(self, node):
    """
    Called before the node will never gain the chance to interact with
    the OpenGL context again. The node's GL resource manager is current in
    this method.
    """

    pass

  def gl_render(self, node):
    """
    Called in the rendering pipeline of the GL canvas. The node's GL resource
    manager is current in this method. This method will usually be called
    after #execute() but can be called multiple times without #execute()
    being called in between.
    """

    pass

  def execute(self, node):
    """
    Called to execute the node to calculate the data for its outputs. All
    connected inputs are garuanteed to have been calculate and been made
    available.
    """

    pass

  def get_icon(self, node):
    """
    Return a #wx.Bitmap for the node, or #None if the node has no icon.
    """

    return None
