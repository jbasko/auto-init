=========
auto-init
=========

**auto-init** is a dependency injection tool that works in Python 3.6+ thanks to type hints.
If you write nice object oriented code and separate interfaces from implementations
then you could benefit from this.

Introduction
++++++++++++

Did you know that if you provide a type hint for an attribute in a class body and do not set a value then
the attribute isn't actually initialised (neither in class, nor in instances)?

.. code-block:: python

    class Point:
        x: int
        y: int
        z: int = None

For ``p``, an instance of ``Point``, only ``p.z`` is set. This is great because we can build a dependency
injection mechanism on top of this!

Simple Example
--------------

.. code-block:: python

    from auto_init import AutoInitContext

    ctx = AutoInitContext()
    p: Point = ctx.get_instance(Point)
    assert p.x == 0
    assert p.y == 0
    assert p.z is None


Note that the ``Point`` class could also be a dataclass and it would work too.


Not so Simple Example
---------------------

.. code-block:: python

    import logging

    from auto_init import AutoInitContext


    class Worker:
        enterprise: "Enterprise"
        log: logging.Logger


    class Reporter:
        enterprise: "Enterprise"
        log: logging.Logger


    class Enterprise:
        worker: Worker
        reporter: Reporter


    ctx = AutoInitContext()
    ctx.register_instance(logging.getLogger(__name__))
    ctx.register_singleton(Enterprise)

    enterprise: Enterprise = ctx.get_instance(Enterprise)
    assert enterprise.worker.log is enterprise.reporter.log
    assert enterprise.worker.enterprise is enterprise
    assert enterprise.reporter.enterprise is enterprise

Installation
++++++++++++

.. code-block:: shell

    pip install auto-init


API
+++

``AutoInitContext()``
    Create a new auto-initialisation context.

    ``register_singleton(instance_type: Type, factory: Callable=None)``
        Register a singleton type. This is different from ``register_instance`` in that here **auto-init**
        is responsible for the creation as well as initialisation of the singleton instance. This should
        be used when the singleton itself has dependencies that need to be injected. See the *enterprise.py*
        example under ``auto_init/examples/`` .
        If ``factory`` is not supplied, the ``instance_type`` is used to create the instance.

    ``register_factory(instance_type: Type, factory: Callable)``
        Register a callable which is called to create a new instance of the specified type when on is requested.

    ``register_instance(instance, instance_type: Type=None)``
        Register an instance that should always be returned when an instance of the specified type is requested.

    ``get_instance(instance_type: Type) -> Any``
        Get an instance of the specified type.

    ``init_instance(instance)``
        Initialise any unitialised attributes of the instance.


Changelog
+++++++++

v0.0.4
------

* Complete rewrite to deal with circular references. Intrusive approach is no good.
* Forward references in type hints don't really work in Python 3.7 even with futures. Let's use Python 3.6.

v0.0.3
------

* Added ``AutoInitContext.explicit_only`` -- allows marking the context as only initialising the types with specified
  providers and leaving all others *untouched*.
* If a type hint includes a default value (declares a class attribute) then the corresponding instance attribute will
  be a copy by reference of the class attribute unless there is an explicit provider specified in the context.
  This means that ``x: int = None`` will be initialised as ``None``, not as ``0``.

v0.0.2
------

* Non-intrusive auto-init: function ``auto_init`` and method ``AutoInitContext.auto_init`` that initialises instances
  without making any changes to user's classes.
* Added ``AutoInitContext.singleton_types`` -- allows to specify singleton types non-intrusively.
