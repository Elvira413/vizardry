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

"""
This module covers the core interfaces understood by Vizardry.
"""

import nr.interface
import pkg_resources
import weakref
import wx
from vizardry.core.parameters import Parameters
from vizardry.core.network import InputList, OutputList
from vizardry.gl import ResourceManager as GLResourceManager

ICON = None


class NodeBehaviour(nr.interface.Interface):
  """
  This is the parent of all interfaces that operate with nodes.
  """

  node = nr.interface.attr(weakref.ref)

  def __init__(self):
    self.node = lambda: None

  @nr.interface.default
  def node_attached(self, node):
    pass

  @nr.interface.default
  def node_icon(self):
    global ICON
    if ICON is None:
      ICON = wx.Image(pkg_resources.resource_stream('vizardry', 'res/python_file.png'))
    return ICON


class ParameterInterface(NodeBehaviour):
  """
  This interface allows a node to define parameters that can be displayed and
  edited in the Vizardry parameter panel.

  For more information on parameters, check the #vizardry.core.parameters
  package documentation.
  """

  params = nr.interface.attr(Parameters)

  def __init__(self):
    self.params = Parameters()


class ComputeInterface(NodeBehaviour):
  """
  This interface allows the node to declare input and output slots for data
  that can be computed in the #execute() callback, and connect these slots
  with other nodes in the same network (by path references).
  """

  inputs = nr.interface.attr(InputList)
  outputs = nr.interface.attr(OutputList)

  def __init__(self):
    self.inputs = InputList()
    self.outputs = OutputList()

  def compute(self):
    """
    This method is called to compute the values for the output slots of the
    node. The outputs that are linked into the inputs of the node are
    garuanteed to have been calculated.
    """

    pass


class GLObjectInterface(NodeBehaviour):
  """
  This interface allows the node to render into the GL canvas when it is
  active. Note that there may be multiple active nodes in a network.
  """

  gl_resources = nr.interface.attr(GLResourceManager)

  def __init__(self):
    self.gl_resources = GLResourceManager()

  def gl_render(self):
    """
    This method is called to render the node into the GL canvas. The caller
    of this method is responsible for entering the #gl_resources context
    manager in order to assign GL objects allocated in this method to the
    correct resource manager.
    """

    pass

  @nr.interface.default
  def gl_cleanup(self):
    """
    This method is called before the node will never again be rendered into
    the GL canvas. This should perform any cleanup steps. The default
    implementation simply calls #~GLResourceManager.release() on the
    #gl_resources object.

    The caller of this metod is responsible for entering the #gl_resources
    context manager.
    """

    self.gl_resources.release()


# TODO: GLCameraInterface
