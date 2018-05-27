<h1 align="center">VIZARDRY</h1>

Vizardry is a Python application for rapid prototyping of 2D/3D visuals or
algorithms. Its goal is to become a **very limited** clone of Houdini with
direct control of the OpenGL rendering pipeline.

Vizardry's main use case is for real-time visualization of arbitrary processes
and prototyping algorithms on images, geometry or sound.

*Note that Vizardry is currently in a very early work-in-progress state.*

[**Check out the Vizardry Documentation ▸**](docs/README.md)

## Current State of Vizardry

* No node editor yet :-(
* But a list of nodes (rightclick on the root to create a new node)
* Double-click on a node to activate it and jump to the Edit tab
* Ctrl+Return to commit changes in a text field and triggering an update

![](https://i.imgur.com/XetwLb7.png)
![](https://i.imgur.com/WeWmx3m.png)

__Things to Consider for the future__

* NumPy <-> OpenGL exchange (eg. [pygarrayimage](http://code.astraw.com/projects/motmot/pygarrayimage.html))
* Numba (need explicit support, maybe.?)

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
