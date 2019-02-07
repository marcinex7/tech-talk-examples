# Writing custom Pants plugins

Based on protobuf and gRPC python code generation

## Pants

<< Few words about pants >>

## Protocol Buffers and gRPC

<< Few words about protobuf+gRPC >>

## Example usecase

In our example, we will have a server, which will stores books, along with it's authors and addresses of authors, and client application, which will use exposed gRPC methods to execute CRUD operations on our model.

### Model

Our model consist of 3 related proto files in `src/proto/example` catalog:

Book depends on Author, while Author depends on Address:

* book/book.proto:
```proto
syntax = "proto3";
package example.book;

import "example/author/author.proto";

message Book {
    int32 id = 1;
    string name = 2;
    string price = 3;
    example.author.Author author = 4;
}
```

* author/author.proto:
```proto
syntax = "proto3";
package example.author;

import "example/author/address.proto";

message Author {
    string first_name = 1;
    string last_name = 2;
    example.address.Address address = 3;
}
```

* author/address.proto:
```proto
syntax = "proto3";
package example.address;

message Address {
    string city = 1;
    string street = 2;
    string number = 3;
    string zip_code = 4;
}
```

Note, that proto files lives in separate catalogs, so we need to create a **pants dependency** between them.

it's done in `book/BUILD`:
```build
  dependencies=[
#   [...]
    'src/proto/example/author',
  ]
```

`python_grpcio_library` here is a custom target, which will be described later.

### Service

Service description is places in `book-service.proto` file, which imports `book.proto` for demo purpouses. 

* book-service.proto:
```proto
syntax = "proto3";
package example.book_service;

import "example/book/book.proto";

service BookRpc {
    rpc get(BookGetRequest) returns (BookGetReply) {}
    rpc list(BookListRequest) returns (BookListReply) {}
    rpc add(BookAddRequest) returns (BookAddReply) {}
    rpc delete(BookDeleteRequest) returns (BookDeleteReply) {}
}

// [...]
```

in this file we can see a simple CRUD actions for our `Book` model.

## Example usage without plugin

When we have our proto files ready, we need to generate a python classes from then. Let's consider a 'normal' approach, without pants:

According to [grpcio documentation](https://grpc.io/docs/quickstart/python.html#generate-grpc-code), you need to execute `grpcio_tools` library:

```bash
python -m grpc_tools.protoc -I src/proto --python_out=src/python/generated --grpc_python_out=src/python/generated src/proto/example/**/*.proto
```

Now, under `src/python/generated` path we have generated python libraries, ready to use in our example.

## Custom Pants Plugin

Before writing first pants plugin, you should check [Developing a Pants Plugin](https://www.pantsbuild.org/howto_plugin.html) from pantsbuild documentation. There are basic info, about how to add a plugin into you repository, so pantsbuild can understand it.

According to documentation, in `pants.ini` there are additional lines:

```ini
pythonpath: ["%(buildroot)s/plugins/src/python"]
backend_packages: +["grpcio"]
``` 

First line adds path `plugins/src/python` to pythonpath
Second line ensures, that pants will treat `plugins/src/python/grpcio` catalog as it's own backend package.

Let's look into `plugins/src/python/grpcio` catalog and it's files:
```
plugins/src/python/grpcio
  ├- targets/
  │  ├- BUILD
  │  └- python_grpcio_library.py
  ├- tasks/
  │  ├- BUILD
  │  ├- grpcio_prep.py
  │  └- grpcio_run.py
  ├- BUILD
  ├- grpcio.py
  └- register.py
```

Within `register.py` file you can register your custom goals, tasks and targets in pants lifecycle.

Let's have a closer look into 2 methods inside `register.py`:
```python
def build_file_aliases():
  return BuildFileAliases(
    targets={
      PythonGrpcioLibrary.alias(): PythonGrpcioLibrary,
    }
  )


def register_goals():
  task(name='grpcio-prep', action=GrpcioPrep).install('gen')
  task(name='grpcio-run', action=GrpcioRun).install('gen')
```

Method `build_file_aliases` registers a new target alias `python_grpcio_library`, while `register_goals` method installs our custom tasks into pantsbuild lifecycle. In our example, we are adding `GrpcioPrep` and `GrpcioRun` tasks at the end of `gen` goal.

`gen` goal is used by few code generators available in pants, so it's great choice for our example, as our plugin will also generate some code.

List of all pants goals is available in [documentation](https://www.pantsbuild.org/options_reference.html#available_goals)

### Targets

According to pants documentation: *"A target represents a set of source files, dependencies or other 'nouns' that build commands can act on"*. 

In our example we are introducing a new target, named `python_grpcio_library`, which is simple extension of `python_target`:

```python
class PythonGrpcioLibrary(PythonTarget):

  def __init__(self, sources=None, **kwargs):
    super(PythonGrpcioLibrary, self).__init__(sources=sources, **kwargs)

  @classmethod
  def alias(cls):
    return 'python_grpcio_library'
```

When a custom target is registered in pants, you can use it to describe our proto files:

`src/proto/example/book/BUILD`:
```build
python_grpcio_library(
  sources=globs('*.proto'),
  dependencies=[
    '3rdparty/python:protobuf',
    'src/proto/example/author',
  ]
)
```

### Task GrpcioPrep

GrpcioPrep task is responsible for creating a python pex file with `grpcio` and `grpcio-tools` libraries installed. To achive that, you should extend pants built class: `PythonToolPrepBase` and provide a **subsystem** and **instance** classes.

`tasks/grpcio_prep.py`:
```python
class GrpcioPrep(PythonToolPrepBase):
  tool_subsystem_cls = Grpcio
  tool_instance_cls = GrpcioInstance
```

#### Subsystem

As described in documentation: *"A subsystem is some configurable part of Pants that can be used across multiple tasks and other parts of the system, including other subsystems"*  

Here, we are extending pants base class `PythonToolBase`, which is built in subsystem to create pex libraries with some dependencies. All we need to do, is provide a default **entry point** and default **requirements** as well as **scope** - a name to retieve this subsystem from pants context.

`grpcio.py`:
```python
class Grpcio(PythonToolBase):
  grpcio_version = '1.17.1'

  options_scope = 'grpcio'
  default_requirements = [
    'grpcio-tools=={}'.format(grpcio_version),
    'grpcio=={}'.format(grpcio_version),
  ]
  default_entry_point = 'grpc_tools.protoc'
```

#### Instance

`GrpcioInstance` is simply extended `PythonToolInstance` just to hold created subsystem instance.

```python
class GrpcioInstance(PythonToolInstance):
  pass
```

After `grpcio_prep` task is executed, an executable pex file should be available in output directory, with name `grpcio.pex`. You can find it in `.pants.d/gen/grpcio-prep/current/.pants.d.gen.grpcio-prep.grpcio/current` catalog.

Now we are ready to use it in order to generate python classes from our proto files. 

### Task SimpleCodegenTask

Pants SDK provides a base task class for code generation: `SimpleCodegenTask` which handles few problems: 
 * resolves your target dependencies and gathers sources,
 * provide output directory caching capabilities,
 * ensures, that output directory is 'reachible' from other pants targets
 
Last point is espacially usefull, as we don't need to create or maintain output directory for our generated python code. Thos classes will be just visible for any other `python_target`'s, which will have a dependency to our `python_grpcio_library`. 

Let's look into an example BUILD file to see how it works:
`src/python/example/server/BUILD`:
```build
python_binary(
# [...]
  dependencies=[
#     [...]
      'src/proto/example/book',
  ]
)
```

So our `python_binary` depends directly on our **proto** catalog, and pants ensures, that generated python classes will be visible there.

### Task GrpcioRun


