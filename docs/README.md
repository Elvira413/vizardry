# Vizardry Documentation

__Table of Contents__

* [The Scene Graph](#the-scene-graph)
* [GL Resource Management](#gl-resource-management)

> Note: Some parts of this documentation may describe Vizardry in the state
> that it is supposed to be and not its actual state.

---

## The Scene Graph

The scene graph consists of a `RootNode` which in turn can contain any number
of `SceneNode`s. Except for the root node, every scene node is attached to an
object that we call a "Behaviour" which implements at least the `NodeBehaviour`
interface.

Vizardry uses the [`nr.interface`][nr.interface] module.

The following node behaviour interfaces are available and recognized by
Vizardry:

* `ParameterInterface` &ndash; Allows the node to define parameters that can
  be displayed and edited in the Vizardry parameter panel.

* `ComputeInterface` &ndash; Allows to the node declare input and output slots
  for data that can be directed into other nodes. The node will be invoked at
  every frame (as determined by a node implementing the `TimerInterface`).
  Many `GLObjectInterface` implementations will also want to implement this
  interface in order to be able to read the output from other nodes (per the
  connections set between the inputs and outputs).

* `GLObjectInterface` &ndash; Allows the node to render into the GL canvas.
  The default `GLInlineNode` implementation allows you to write Python code
  directly in Vizardry that will be executed during the GL rendering pipeline.

---

## GL Resource Management

The `GLObjectInterface` provides a `gl_resources` member that manages OpenGL
resources. All objects created with the object oriented GL API provided by
Vizardry are managed by a resource manager. The caller is responsible for
making the GL resource manager current before invoking the `gl_render()` or
`gl_cleanup()` methods.

---

  [nr.interface]: https://github.com/NiklasRosenstein-Python/nr.interface

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
