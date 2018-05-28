<h1 align="center">VIZARDRY</h1>

Vizardry is a Python **framework** and **application** for rapid prototyping
of 2D/3D visuals or algorithms. Its goal is to become a *very limited* clone
of Houdini, allowing you to very quickly prototype and realize real-time
visualizations and process images, geometry and sound.

The Vizardry application is used to interactively build scene graphs, however
you can embed and execute the scene graph in whatever way you want. Check out
the [standalone.py](examples/standalone.py) example.

<table>
  <tr><th>Vizardry</th><th>examples/standalone.py</th></tr>
  <tr><td><img src="https://i.imgur.com/5VDqMyh.png"></td>
      <td><img src="https://i.imgur.com/2oFZawD.png"></td></tr>
</table>

*Note that Vizardry is currently in a very early work-in-progress state.*

[**Check out the Vizardry Documentation ▸**](docs/README.md)

---

## Current State of Vizardry

* No node editor yet :-(
* But a list of nodes (rightclick on the root to create a new node)
* Double-click on a node to activate it and jump to the Edit tab
* Ctrl+Return to commit changes in a text field and triggering an update

__Things to Consider for the future__

* NumPy <-> OpenGL exchange (eg. [pygarrayimage](http://code.astraw.com/projects/motmot/pygarrayimage.html))
* Numba (need explicit support, maybe.?)

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
