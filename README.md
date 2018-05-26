<h1 align="center">VIZARDRY</h1>

Vizardry is a Python application for rapid prototyping of 2D/3D visuals or
algorithms. Its goal is to become a **very limited** clone of Houdini with
direct control of the OpenGL rendering pipeline.

Vizardry's main use case is for real-time visualization of arbitrary processes
and prototyping algorithms on images, geometry or sound.

*Note that Vizardry is currently in a very early work-in-progress state.*

## Current State

* OpenGL Canvas on the left
* The single "InlineNode" in the scene is editable in the "Edit" tab and
  currently has only one parameter: The Python code text field

![](https://i.imgur.com/bDHvWNd.png)

## Planned Features

* 1️⃣ Node-based composition of components *(In progress...)*
* 1️⃣ Support for node parameters (display, easy generation, serializable) *(In progress...)*
* 2️⃣ Node-Editor to arrange and connect nodes
* 2️⃣ Serializable scene graph
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

* [The Scene Graph](#the-scene-graph)
* [GL Resource Management](#gl-resource-management)

> Note: Some parts of this documentation may describe Vizardry in the state
> that it is supposed to be and not its actual state.

## The Scene Graph

The scene graph consists of a `RootNode` which in turn can contain any number
of `SceneNode`s. Except for the root node, every scene node is attached to an
object that we call a "Node Descriptor" which implements several interfaces
that describe the nodes behaviour.

### Interfaces

Every interface acts as a singleton that has access to a scene, allowing it to
take on a managing role for all nodes of that interface. Interfaces can be
declared by subclassing the `vizardry.Interface` class. To extend an existing
interface, use the `vizardry.extends()` function inside the class-body.

Interfaces can then be implemented with the `vizardry.Implementation` class
and declaring the interfaces it implements with `vizardry.implements()`.

<details><summary><b>Expand: Example of a potential <code>TimerInterface</code></b></summary>

```python
import vizardry
from vizardry.params import NodeLink
class TimerInterface(vizardry.Interface):
  " Describe the interface with method stubs here. "
  vizardry.extends(vizardry.NodeBehaviour)
  def get_refresh_rate(self): 
    pass
  def on_refresh(self):
    pass

  class SceneDescriptor(vizardry.Implementation):
    " Describe the global behaviour of the interface. "
    vizardry.implements(vizardry.SceneDescriptor)
    def declare_parameters(self):
      self.parameters.add(NodeLink('timer', 'Timer Node', implements=TimerInterface))
```

Here the `TimerInterface` extends the `vizardry.NodeBehavour` interface
because it is supposed to be implemented by nodes. The `NodeBehaviour`
interface requires a declaration of a `SceneDescriptor` implementation.

</details>

---

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

* `GLCameraInterface` &ndash; Allows the node to define the GL viewport and
  receive mouse events while the CTRL key is pressed. Usually this interface
  need not be implemented by the user as the default implementation
  `GLCameraNode` covers most use cases (2D/3D Viewport).


### Node Descriptors

Node descriptors are simply a combination of one or more implementations of
`NodeBehaviour` interfaces. They can be created by creating a
`vizardry.Implementation` subclasses and the respective `vizardry.implements()`
declarations.

<details><summary><b>Expand: Potential implementation of a node descriptor</b></summary>

```python
class InlineNodeDescriptor(vizardry.Implementation):
  vizardry.implements(vizardry.ComputeInterface, vizardry.GLObjectInterface,
    vizardry.ParameterInterface)
  def declare_inputs_outputs(self):
    self.inputs.add(vizardry.Input('input1', object))
    self.outputs.add(vizardry.Output('output', object))
  def declare_parameters(self):
    self.params.add(vizardry.Text('code', 'Python Code', multiline=True
      syntax='python'))
    self.params.param('code').bind(vizardry.EVENT_VALUE_CHANGED, self.__update)
  def gl_render(self):
    if self.__gl_render:
      self.__gl_render()
  def __update(self):
    code = self.params['code']
    scope = {'node': self.node}
    exec(code, scope)
    self.__gl_render = scope['gl_render']
    self.emit(vizardry.EVENT_VIEWPORT_UPDATE)
```

</details>

---

## GL Resource Management

The `GLObjectInterface` and `GLCameraInterface` both provide a `gl_resources`
member that manages OpenGL resources. All objects created with the object
oriented GL API provided by Vizardry are managed by a resource manager. When
implementing these interface, you should use the `gl_resources.as_current()`
context manager to have the GL handles be managed by the correct resource
manager.
