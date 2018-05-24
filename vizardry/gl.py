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

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


def vzSimpleProgram(fragment, vertex=None):
  if not vertex:
    vertex = '''
      #version 330 core
      layout(location = 0) in vec2 position;
      out vec2 fragCoord;
      void main() {
        gl_Position = vec4(position, 0.0, 1.0);
        fragCoord = (position + 1) * 0.5;
      }
    '''

    shvert = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(shvert, vertex)
    glCompileShader(shvert)

    shfrag = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(shfrag, fragment)
    glCompileShader(shfrag)

    prog = glCreateProgram()
    glAttachShader(prog, shvert)
    glAttachShader(prog, shfrag)
    glLinkProgram(prog)

    glDetachShader(prog, shvert)
    glDetachShader(prog, shfrag)

    glDeleteShader(shvert)
    glDeleteShader(shfrag)

    # TODO: Reliably determine if the shader was linked successfully?
    log = glGetProgramInfoLog(prog)
    if log:
      if hasattr(log, 'decode'): log = log.decode()
      if 'error' in log:
        raise RuntimeError(log)
      print(log)

    return prog
