=========
auto-init
=========

Installation
------------

.. code-block:: shell

    pip install auto-init


Changelog
---------

v0.0.3
^^^^^^

* Added ``AutoInitContext.explicit_only`` -- allows marking the context as only initialising the types with specified
  providers and leaving *untouched* all others.
* If a type hint includes a default value (declares a class attribute) then the corresponding instance attribute will
  be a copy by reference of the class attribute unless there is an explicit provider specified in the context.
  This means that ``x: int = None`` will not be initialised as ``None``, not as ``0``.

v0.0.2
^^^^^^

* Non-intrusive auto-init: function ``auto_init`` and method ``AutoInitContext.auto_init`` that initialises instances
  without making any changes to user's classes.
* Added ``AutoInitContext.singleton_types`` -- allows to specify singleton types non-intrusively.


Non-Intrusive Auto-Init
-----------------------

*Non-intrusive* auto-init creates an instance of the specified type and initialises its attributes based on type
annotations.

.. code-block:: python

    from auto_init import auto_init

    class Point:
        x: int
        y: int


    class Line:
        start: Point
        end: Point


    p = auto_init(Point, attrs={'y': 5})
    assert p.x == 0
    assert p.y == 5

    line = auto_init(Line)
    assert line.start.x == 0
    assert line.end.y == 0


If you have an instance of ``AutoInitContext`` available, you can call ``auto_init`` on it:

.. code-block:: python

    with AutoInitContext() as auto_init_context:
        auto_init_context.auto_init(Line)


Intrusive Auto-Init Class
-------------------------

The original, intrusive auto-init create a sub-class of your class with the same name and in the sub-class
adds an initialiser that accepts keyword arguments matching the type-annotated instance attribute names.

It's a bit like dataclasses, but a friendly generated initialiser is not really the goal. The goal
is to make sure that all attributes are initialised in a centrally managed fashion.

.. code-block:: python

    from auto_init import auto_init_class

    @auto_init_class
    class Point:
        x: int
        y: int

    p = Point(y=-5)
    assert p.x == 0
    assert p.y == -5
    assert str(p) == '<Point x=0, y=-5>'


You Can Still Have Your ``__init__``
------------------------------------

Unlike with dataclasses, you can have your own ``__init__`` method.
Your ``__init__`` method will be called after the generated initialiser so all the attributes will
be already initialised.

.. code-block:: python

    @auto_init_class
    class Point:
        x: int
        y: int

        def __init__(self, *args):
            if args:
                self.x, self.y = args


Singletons
----------

A singleton class is a class of which only a single instance should exist. With auto-init, this limitation only
applies to the current context. If you have not created and entered a specific context, it applies to the global
context.

The intrusive way:

.. code-block:: python

    @auto_init_class(singleton=True)
    class AppModel:
        pass

    @auto_init_class
    class AppPresenter:
        model: AppModel

    @auto_init_class
    class AppView:
        model: AppModel

    @auto_init_class
    class App:
        model: AppModel
        view: AppView
        presenter: AppPresenter

    app = App()
    assert isinstance(app.view.model, AppModel)
    assert app.view.model is app.presenter.model


Same idea as above, but non-intrusively:

.. code-block:: python

    class AppModel:
    pass

    class AppPresenter:
        model: AppModel

    class AppView:
        model: AppModel

    class App:
        model: AppModel
        view: AppView
        presenter: AppPresenter

    with AutoInitContext(singleton_types={AppModel}):
        app = auto_init(App)
        assert isinstance(app.view.model, AppModel)
        assert app.view.model is app.presenter.model


Access to the Base Class
------------------------

.. code-block:: python

    @auto_init_class
    class Point:
        x: int
        y: int


    primitive_point = Point(auto_init_base=True)
    initialised_point = Point(x=10)

    assert isinstance(primitive_point, Point._auto_init_base)
    assert not hasattr(primitive_point, 'x')

    assert isinstance(initialised_point, Point)
    assert initialised_point.x == 10


Context
-------

Context allows setting custom providers.

.. code-block:: python

    from auto_init import AutoInitContext, auto_init_class

    @auto_init_class
    class Line:
        start: Point
        end: Point

    context = AutoInitContext(providers={Point: Point3d})

    with context:
        assert isinstance(Point(), Point3d)
        assert isinstance(Line().start, Point3d)


A provider is either a callable in which case it will be called to create a new instance of the type, or a non-callable
in which case the non-callable will be returned every time a new instance of the type will be requested. This means
that you can also specify singletons through providers. Also, through providers you can specify types instances of
which shouldn't be initialised by passing ``None`` as the provider:

.. code-block:: python

    @auto_init_class
    class Db:
        connection: Connection = None


    with AutoInitContext(providers={Connection: None}):
        assert Db().connection is None


If initialising attributes of all types seems a bit too much, you can use a context with ``explicit_only`` set to
``True``:

.. code-block:: python

    class Db:
        connection: Connection

    with AutoInitContext(providers={Db: Db}, explicit_only=True):
        db = auto_init(Db)
        assert not hasattr(db, 'connection)


Default Values
--------------

If in your class you annotate types and provide default values (effectively create class attributes) then they will
be copied as instance attributes unless you specify an explicit provider in which case all default values will
be replaced.

.. code-block:: python

    class Db:
        connection: Connection = None

    assert auto_init(Db).connection is None

    with AutoInitContext(providers={Connection: -1}) as context:
        assert context.auto_init(Db).connection == -1)

In other words, ``connection: Connection`` is very different from ``connection: Connection = None``
because in the latter case ``None`` will not be replaced unless a provider for ``Connection`` class
is explicitly listed.


Inheritance Works
-----------------

.. code-block:: python

    @auto_init_class
    class Point:
        x: int
        y: int

    @auto_init_class
    class Point3d(Point):
        z: int

    assert isinstance(Point3d(), Point)
