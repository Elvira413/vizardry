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

import nr.interface
import traceback
from vizardry.core.interfaces import GLObjectInterface
from vizardry.core.parameters import Text
from vizardry.core.scene import node_factory

DEFAULT_CODE ='''
from vizardry import gl
from vizardry.gl.api import *

def gl_render():
  pass
'''.lstrip()


class GLInlineBehaviour(nr.interface.Implementation):
  nr.interface.implements(GLObjectInterface)

  def __init__(self):
    super().__init__()
    self.__scope = None

  def __update(self):
    """
    Executes the Python code in the 'code' parameter.
    """

    node = self.node()
    self.__scope = {}

    try:
      code = compile(node.params['code'], 'vizardry:' + node.path, 'exec')
      scope = {'node': node}
      exec(code, scope)
    except:
      traceback.print_exc()
    else:
      self.__scope = scope
      node.scene.emit(node.scene.EV_VIEWPORT_UPDATE)

  @nr.interface.override
  def node_attached(self, node):
    node.params.add(Text('code', 'Python Code', multiline=True, syntax='python'))
    node.params('code').bind(Text.EV_VALUE_CHANGED, lambda ev: self.__update())
    node.params['code'] = DEFAULT_CODE

  @nr.interface.override
  def gl_render(self):
    if self.__scope is None:
      self.__update()

    if 'gl_render' in self.__scope:
      self.__scope['gl_render']()


GLInline = node_factory(GLInlineBehaviour, 'glinline')
