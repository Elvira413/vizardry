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
Object wrappers for GL resources.
"""

__all__ = ['GLError', 'ResourceManager', 'Program', 'Shader']

from .api import *

import contextlib
import warnings
import weakref


def _decode(x):
  if hasattr(x, 'decode'):
    return x.decode()
  return x


class GLError(RuntimeError):
  pass


class ResourceManager:
  """
  A resource manager is supposed to keep track of a set of OpenGL handles.
  Note that when you create a #_GLHandle, it will add itself to the resource
  manager automatically.
  """

  class _ResourceTypeProxy:
    def __init__(self, manager, cls):
      self._manager = manager
      self._cls = cls
    def __call__(self, *args, **kwargs):
      handle = self._cls(*args, **kwargs)
      self._manager.register_handle(handle)
      return handle
    def __getattr__(self, name):
      value = getattr(self._cls, name)
      if callable(value):
        return ResourceManager._ResourceTypeProxy(self._manager, value)
      return value

  def __init__(self):
    self._handles = set()

  def __getattr__(self, name):
    for subclass in _GLHandle.__subclasses__():
      if subclass.__name__ == name:
        return self._ResourceTypeProxy(self, subclass)
    raise AttributeError(name)

  def register_handle(self, handle):
    if not isinstance(handle, _GLHandle):
      raise TypeError('expected _GLHandle')
    handle._resource_manager = weakref.ref(self)
    self._handles.add(handle)

  def release(self):
    for handle in self._handles:
      handle.release()
    self._handles.clear()

  current = None

  @contextlib.contextmanager
  def as_current(self, release=True):
    if ResourceManager.current is not None:
      raise RuntimeError('another ResourceManager is current')
    ResourceManager.current = self
    try:
      yield self
    finally:
      ResourceManager.current = None
      if release:
        self.release()

  @contextlib.contextmanager
  def as_autorelease(self):
    try:
      yield self
    finally:
      self.release()


class _GLHandle:
  """
  Base class for OpenGL handles. Subclasses must implement the #release()
  method that should delete the OpenGL handle.
  """

  _handle = 0

  def __new__(cls, *args, **kwargs):
    if not ResourceManager.current:
      raise RuntimeError('no active ResourceManager')
    self = object.__new__(cls)
    ResourceManager.current.register_handle(self)
    return self

  def __del__(self):
    if self._handle != 0:
      warnings.warn('{!r} has not been released before GC.'.format(self), RuntimeWarning)

  def __bool__(self):
    return self._handle != 0

  def __index__(self):
    return self._handle

  def __repr__(self):
    return '<{}.{} handle={!r}>'.format(type(self).__module__,
      type(self).__name__, self._handle)

  @property
  def handle(self):
    return self._handle

  @property
  def resource_manager(self):
    return self._resource_manager()

  def release(self):
    raise NotImplementedError

  @property
  def _as_parameter_(self):
    return ctypes.c_uint(self._handle)


class Shader(_GLHandle):

  def __init__(self, shader_type, shader_source=None):
    self._log = None
    self._handle = glCreateShader(shader_type)
    if self._handle == 0:
      raise GLError('glCreateShader() failed')
    if shader_source:
      self.compile(shader_source)

  @property
  def log(self):
    return self._log or ''

  def compile(self, shader_source):
    glShaderSource(self, shader_source)
    glCompileShader(self)

    # TODO: Reliably determine if the compilation was successful.
    self._log = _decode(glGetShaderInfoLog(self))
    if self._log and 'error' in self._log:
      raise GLError(self._log)

  def release(self):
    if self._handle != 0:
      glDeleteShader(self)
      self._handle = 0


class Program(_GLHandle):

  def __init__(self, *shaders):
    self._log = None
    self._handle = glCreateProgram()
    if self._handle == 0:
      raise GLError('glCreateProgram() failed')
    if shaders:
      self.link(*shaders)

  @classmethod
  def from_fragment(cls, fragment):
    with ResourceManager().as_autorelease() as temp_manager:
      if isinstance(fragment, str):
        fragment = temp_manager.Shader(GL_FRAGMENT_SHADER, fragment)

      vertex = temp_manager.Shader(GL_VERTEX_SHADER, '''
        #version 330 core
        layout(location = 0) in vec2 position;
        out vec2 fragCoord;
        void main() {
          gl_Position = vec4(position, 0.0, 1.0);
          fragCoord = (position + 1) * 0.5;
        }
      ''')

      return cls(vertex, fragment)

  @property
  def log(self):
    return self._log or ''

  def link(self, *shaders):
    for shader in shaders:
      glAttachShader(self, shader)
    try:
      glLinkProgram(self)
    finally:
      for shader in shaders:
        glDetachShader(self, shader)

    # TODO: Reliably determine if the linking step was successful.
    self._log = _decode(glGetProgramInfoLog(self))
    if self._log and 'error' in self._log:
      raise GLError(self._log)

  def release(self):
    if self._handle != 0:
      glDeleteProgram(self)
      self._handle = 0
