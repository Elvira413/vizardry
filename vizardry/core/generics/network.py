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

__all__ = ['NetworkNodeError', 'NodeNameError', 'NodeNameConflictError',
           'NodeNameInvalidError', 'Network', 'NetworkNode']

import posixpath
import re
import weakref
from vizardry.core.generics.treenode import TreeNode


class NetworkNodeError(Exception):
  pass


class NodeNameError(NetworkNodeError):
  pass


class NodeNameConflictError(NodeNameError):
  pass


class NodeNameInvalidError(NodeNameError):
  pass


class Network:
  """
  Represents a node network constructed of #NetworkNode objects. Its main
  purpose is to contain the root node. When a network is constructed, you
  may specifiy a factory function that returns a new #NetworkNode, our you
  may bind a root node after the network is constructed.

  A network may place constraints on node naming and insertion. The
  #NetworkNode will invoke the respective callbacks on the network to
  ask for permission of an operation that changes the node's name or
  location in the tree.
  """

  def __init__(self, root_factory=None):
    self.root = root_factory(self) if root_factory else None

  @property
  def root(self):
    return self.__root

  @root.setter
  def root(self, value):
    if value is not None and not isinstance(value, NetworkNode):
      raise TypeError('root must be NetworkNode')
    if value is not None and value.network != self:
      raise ValueError('root network must match with self')
    self.__root = value

  def on_choose_name(self, node, name):
    """
    This is called before the name of a node is changed. The default
    implementation will ensure that there is no other node in the network
    with the same name. If there is, a #NodeNameConflictError is raised.
    Additionally, it will only permit names that contain no special characters
    besides underscores. If that rule is violated, a #NodeNameInvalidError is
    raised.

    The method must return the *name* either as-is or in a changed way.
    """

    if not re.match('[A-z0-9_]+$', name):
      raise NodeNameInvalidError('invalid node name {!r}'.format(name))
    if node.parent:
      for child in node.parent.children:
        if child != node and child.name == name:
          raise NodeNameConflictError(
            'can not rename to {!r}, another node in the same hierarchy '
            'level occupies that name ({})'.format(name, child.path))
    return name

  def on_attach_to(self, node, parent):
    """
    This method is called when a node is attached to another parent node
    in the network. The default implementation raises a #NodeNameConflictError
    if the node can not be attached to the parent because another node has the
    same name.
    """

    for child in parent.children:
      if child != node and child.name == node.name:
        raise NodeNameConflictError(
          'can not attach to this parent node as another child node has '
          'the same name {!r}'.format(node.name))

  def on_node_enters_network(self, node):
    """
    Called when a node is created for the network. The default implementation
    does nothing. Subclasses may raise an exception if a node type is not
    accepted.
    """

    pass


class NetworkNode(TreeNode):
  """
  Represents a node in a network that is also a tree where every node has a
  name and a unique path. This class implements the node naming, path
  computation and finding other nodes in the same tree.

  Every #NetworkNode must be attached to some #Network, however that does
  not garuantee the node is part of the networks tree hierarchy.
  """

  def __init__(self, network, name):
    super().__init__()
    self.__network = None
    self.__name = '<uninitialized>'
    self.network = network
    self.name = name
    network.on_node_enters_network(self)

  @property
  def network(self):
    return self.__network()

  @network.setter
  def network(self, value):
    if not isinstance(value, Network):
      raise TypeError('network must be Network instance')
    if self.__network is not None:
      raise RuntimeError('can not change node network')
    self.__network = weakref.ref(value)

  @property
  def name(self):
    return self.__name

  @name.setter
  def name(self, value):
    if not isinstance(value, str):
      raise TypeError('name must be str')
    if not value:
      raise ValueError('name can not be empty')
    name = self.network.on_choose_name(self, value)
    self.__name = value

  @property
  def path(self):
    if self == self.network.root:
      return '/'
    if self.parent:
      if self.parent == self.network.root:
        return '/' + self.name
      else:
        return self.parent.path + '/' + self.name
    return self.name

  def abspath(self, path):
    """
    Converts a node path string into an absolute path if it is not already
    absolute, treating the current node as the anchor for the path operation.

    Note that if the #self.path does not return an absolute path (which can
    be the case if the node is not inside the networks tree hierarchy), the
    returned path will not actually be absolute (starting with /).
    """

    return posixpath.normpath(posixpath.join(self.path, path))

  def find_node(self, path):
    """
    Finds a node by a node path string relative to the current node. Note that
    specifying an absolute path will always starting searching for the node
    relative to the node's network's root.
    """

    path = self.abspath(path)
    if path.startswith('/'):
      if path == '/':
        return self.network.root
      node = self.network.root
      parts = path.split('/')[1:]
    else:
      node = self
      parts = path.split('/')

    for part in parts:
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

  # TreeNode

  def attach_to(self, parent, *args, **kwargs):
    if not isinstance(parent, NetworkNode):
      raise RuntimeError('must attach to a NetworkNode')
    if parent.network != self.network:
      raise RuntimeError('parent must be part of the same Network')
    self.network.on_attach_to(self, parent)
    super().attach_to(parent, *args, **kwargs)
