<h1 align="center">VIZARDRY</h1>

Vizardry is a Python application for rapid prototyping of 2D/3D visuals or
algorithms. Its goal is to become a **very limited** clone of Houdini with
direct control of the OpenGL rendering pipeline.

Vizardry's main use case is for real-time visualization of arbitrary processes
and prototyping algorithms on images, geometry or sound.

*Note that Vizardry is currently in a very early work-in-progress state.*

[**Check out the Vizardry Documentation ▸**](docs/README.md)

## Current State of Vizardry

* OpenGL Canvas on the left
* The single "GLInline" in the scene is editable in the "Edit" tab and
  currently has only one parameter: The Python code text field
* Editing the node name works now, too!

![](https://i.imgur.com/AXz9J2j.png)


__Things to Consider__

* NumPy <-> OpenGL exchange (eg. [pygarrayimage](http://code.astraw.com/projects/motmot/pygarrayimage.html))
* Numba (need explicit support, maybe.?)

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
