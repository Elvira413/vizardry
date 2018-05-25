<h1 align="center">VIZARDRY</h1>

Vizardry is a Python application for rapid prototyping of 2D/3D visuals or
algorithms. Its goal is to become a **very limited** clone of Houdini with
direct control of the OpenGL rendering pipeline.

Vizardry's main use case is for real-time visualization of arbitrary processes
and prototyping algorithms on images, geometry or sound.

*Note that Vizardry is currently in a very early work-in-progress state.*

## Current State

* OpenGL Canvas on the left
* A single code panel on the right allowing you to set the framerate and
  render into the GL Canvas

![](https://i.imgur.com/lAfJFVR.png)

## Planned Features

* 1️⃣ Node-based composition of components
* 1️⃣ Support for node parameters (display, easy generation, serializable)
* 1️⃣ Scene graph (serializable, 2️⃣ GUI to view and edit nodes)
* 2️⃣ Full control of processing pipeline &ndash; You may choose an automatic
  per-frame execution or a background processing pipeline that gets regular
  updates for rendering into the viewport
* 3️⃣ Simple APIs for common areas such as 2D and 3D visualization (and
  navigation), Audio playback, Graph plotting, image and video export, etc.
* 4️⃣ Better code editor

__Things to Consider__

* NumPy <-> OpenGL exchange (eg. [pygarrayimage](http://code.astraw.com/projects/motmot/pygarrayimage.html))
* Numba (need explicit support, maybe.?)

# Vizardry Documentation

__Table of Contents__

* [GUI](#gui)
  * [Editor](#editor)
* [The Scene Graph](#the-scene-graph)
* [GL Object API](#gl-object-api)

## GUI

### Editor

The code editor in Vizardry is pretty basic at the moment. It is a
`wx.TextCtrl` with rich-text capabilities and a CTRL+Return hotkey
to commit the changes.

## The Scene Graph

## GL Object Api

Using the standard GL API will require the user to explicitly free resources
like programs, shaders, textures and framebuffers. Vizardry manages GL resources
using a "GL Flush" event, deleting all existing resources.

> **Important**: [[FUTURE]] For the node-based scene graph, nodes should be
> responsible for releasing all allocated GL resources that they do not
> require any more.

Multiple `vizardry.gl.ResourceManager` may exist at any given time, but only
one may be the "current" one. Every GL object that you create will be added
automatically to the current resource manager.

```python
from vizardry import gl

with gl.ResourceManager():
  assert gl.ResourceManager.current is not None
  shader = gl.Shader(gl.GL_VERTEX_SHADER)
  shader.compile(''' my shader code ...''')
  assert shader.handle != 0

assert gl.ResourceManager.current is None
assert shader.handle == 0

gl.Shader(gl.GL_VERTEX_SHADER)  # raises RuntimeError
```
