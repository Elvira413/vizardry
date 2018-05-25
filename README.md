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

![](https://i.imgur.com/eVzQgRK.png)

## Planned Features

* 1️⃣ Node-based composition of components
* 1️⃣ Support for node parameters (display, easy generation, serializable)
* 1️⃣ Scene graph (serializable, 2️⃣ GUI to view and edit nodes)
* 2️⃣ Full control of processing pipeline &ndash; You may choose an automatic
  per-frame execution or a background processing pipeline that gets regular
  updates for rendering into the viewport
* 3️⃣ Simple APIs for common areas such as 2D and 3D visualization (and
  navigation), Audio playback, image and video export, etc.
* 4️⃣ Better code editor
