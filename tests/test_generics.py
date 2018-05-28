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

from nose.tools import *
from vizardry.core.generics.eventhandler import EventHandler
from vizardry.core.generics.treenode import TreeNode
from vizardry.core.generics.network import Network, NetworkNode, \
  NodeNameConflictError, NodeNameInvalidError


def test_EventHandler():
  class Box:
    def __init__(self, value):
      self.value = value
    def set(self, value):
      self.value = value
  class Invoked(Exception):
    pass
  def raise_invoked(event):
    raise Invoked

  def handle_exception(*a):
    raise

  box = Box(False)

  handler = EventHandler()
  handler.handle_exception = handle_exception
  handler.bind('event1', raise_invoked)
  handler.bind('event2', lambda ev: box.set(True))

  assert_false(box.value)
  handler.emit('event2')
  assert_true(box.value)

  with assert_raises(Invoked):
    handler.emit('event1')


def test_TreeNode():
  node1 = TreeNode()
  node2 = TreeNode()
  node3 = TreeNode()
  node4 = TreeNode()

  node2.attach_to(node1)
  node3.attach_to(node2)
  node4.attach_to(node1, before=node2)

  assert_equals(node1.children, [node4, node2])
  assert_equals(node2.children, [node3])

  with assert_raises(ValueError):
    node4.attach_to(node4)  # Can not attach a node to itself
  with assert_raises(ValueError):
    node4.attach_to(node1, after=node3)  # node3 is not a child of node1


def test_Network():
  network = Network(lambda n: NetworkNode(n, 'root'))
  assert_equals(network.root.path, '/')

  node1 = NetworkNode(network, 'node1')
  node2 = NetworkNode(network, 'node2')
  node3 = NetworkNode(network, 'node3')
  node4 = NetworkNode(network, 'node4')

  node1.attach_to(network.root)
  node2.attach_to(node1)
  node3.attach_to(node2)
  node4.attach_to(node1)

  assert_equals(node1.path, '/node1')
  assert_equals(node2.path, '/node1/node2')
  assert_equals(node3.path, '/node1/node2/node3')
  assert_equals(node4.path, '/node1/node4')

  with assert_raises(NodeNameInvalidError):
    NetworkNode(network, 'invalid name')  # invalid node name
  with assert_raises(NodeNameConflictError):
    # node with that name already in the same network
    NetworkNode(network, 'node4').attach_to(node1)

  network2 = Network(lambda n: NetworkNode(n, 'root'))
  with assert_raises(RuntimeError):
    node1.attach_to(network2.root)  # must be part of the same network
  assert_equals(node1.parent, network.root)  # not detached after failed attach_to()
