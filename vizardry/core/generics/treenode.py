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

import weakref


class TreeNode:
  """
  Base class for a node datastructure that can accept arbitrary number of
  children but can only be the child of a single other node. Note that the
  parent is stored as a weak reference while child nodes are stored as
  actual references.
  """

  def __init__(self):
    self.__parent = None
    self.__children = []

  @property
  def parent(self):
    if self.__parent:
      return self.__parent()
    return None

  @property
  def children(self):
    return self.__children  # TODO: Return a VIEW of the children

  def detach(self):
    """
    Detach this node from its parent node.
    """

    parent = self.parent
    self.__parent = None
    if parent:
      parent.__children.remove(self)

  def attach_to(self, parent, before=None, after=None, first=False):
    """
    Attach this node to the specified parent node.

    # Parameters
    parent (TreeNode): The parent node to attach the node to.
    before (TreeNode): A child of the parent node to insert this node before.
    after (TreeNode): A child of the parent node to insert this node after.
    first (bool): If #True, the node will be inserted as the first child.
    raise (RuntimeError): If more than one of the parameters *before*, *after*
      and *first* are specified.
    raise (ValueError): If *before* or *after* is specified but they are not
      child nodes of the *parent* node or if *parent* is the same as *self*.
    """

    if not isinstance(parent, TreeNode):
      raise TypeError('parent must be TreeNode instance')

    if sum(1 for x in [before, after, first] if x) > 1:
      raise RuntimeError('incompatible parameters')

    if before and not isinstance(before, TreeNode):
      raise RuntimeError('before must be a TreeNode instance')
    if after and not isinstance(after, TreeNode):
      raise RuntimeError('after must be a TreeNode instance')

    if parent is self:
      raise ValueError('can not attach a node to itself')

    self.detach()

    if before:
      index = parent.__children.index(before)
    elif after:
      index = parent.__children.index(after)
    elif first:
      index = 0
    else:
      index = len(parent.__children)

    self.__parent = weakref.ref(parent)
    parent.__children.insert(index, self)

  def iter_hierarchy(self, filter=None, this=True):
    """
    Returns a generator that iterates over the hierarchy of the node.

    # Parameters
    filter (callable): A function that accepts a node and returns whether
      it should be yielded by this generator or not.
    this (bool): If this is #True, the node that this method is called with
      will be yielded first. If it is set to #False however, the node will
      be skipped and only the children will be yielded recursively.
    return (iterable of TreeNode)
    """

    def generator(node, this):
      if this and (filter is None or filter(node)):
        yield node
      for child in node.__children:
        yield from generator(child, True)

    return generator(self, this)
