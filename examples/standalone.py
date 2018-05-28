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
This example creates a standalone GL window using PyOpenGL and builds a scene
graph that is periodically executed.
"""

import nr.interface
import pygame
import sys
from vizardry.core.interfaces import GLObjectInterface
from vizardry.core.scene import Scene, node_factory
from vizardry.gl import *


class MandelbrotBehaviour(nr.interface.Implementation):
  nr.interface.implements(GLObjectInterface)

  program = None

  def gl_render(self):
    if not self.program:
      self.program = Program.from_fragment('''
        #version 330 core
        uniform float time;
        in vec2 fragCoord;
        out vec4 fragColor;
        const int ncolors = 5;
        const vec3 colors[ncolors] = vec3[](
          vec3(0.1, 0.3, 1.0),
          vec3(0.1, 0.3, 1.0),
          vec3(0.7, 0.9, 0.8),
          vec3(1.0, 1.0, 1.0),
          vec3(0.7, 0.2, 0.2)
        );
        void main() {
          vec2 c = fragCoord.xy;
          c = c * vec2(4,3) - vec2(2.5, 1.5);
          vec2 z = vec2(0, 0); //cos(time / 100), sin(time / 100));
          int limit = 16;
          int i = 0;
          for (i = 0; i < limit; ++i) {
            if (z.x * z.x + z.y * z.y >= 4.0) {
              break;
            }
            z = vec2(z.x*z.x - z.y*z.y, 2.*z.x*z.y) + c;
          }
          float x = (float(i) / float(limit) + time * 0.25) * (ncolors-1);
          int il = int(x) % ncolors;
          float w = x - il;
          fragColor = vec4(colors[il] * (1.0-w) + colors[(il+1)] * w, 1.0);
        }
        ''')

    glUseProgram(self.program)
    glBegin(GL_TRIANGLE_STRIP)
    glVertex2f(-1.0, -1.0)
    glVertex2f(1.0, -1.0)
    glVertex2f(-1.0, 1.0)
    glVertex2f(1.0, 1.0)
    glEnd()


Mandelbrot = node_factory(MandelbrotBehaviour, 'mandel')


def main():
  pygame.init()
  pygame.display.set_mode((800, 600), pygame.DOUBLEBUF|pygame.OPENGL)
  pygame.display.set_caption('Vizardry Standalone')

  scene = Scene()
  node = Mandelbrot(scene)
  node.attach_to(scene.root)

  running = True
  while running:
    scene.gl_render()
    pygame.display.flip()

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        scene.gl_cleanup()
        pygame.quit()
        running = False


if __name__ == '__main__':
  main()
