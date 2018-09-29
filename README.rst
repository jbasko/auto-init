=========
auto-init
=========

Class With auto-init
--------------------

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

You Can Still Have Your `__init__`
----------------------------------

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

Also, singletons apply only to the current context.

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
