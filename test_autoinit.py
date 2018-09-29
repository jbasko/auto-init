from autoinit import auto_init_class, AutoInitContext


@auto_init_class(singleton=True)
class DummySingleton:
    pass


@auto_init_class
class Point:
    x: int
    y: int

    def __init__(self, label: str=None):
        self.label = label


@auto_init_class
class Point3d(Point):
    z: int

    # This works too:
    # def __init__(self, label_3d: str=None, **kwargs):
    #     self.label_3d = label_3d
    #     super().__init__(**kwargs)


@auto_init_class
class Line:
    start: Point
    end: Point


def test_basics():
    assert Point() == Point()
    assert Point().label is None
    assert callable(Point._auto_init_base)
    assert Point(auto_init_base=True) != Point()
    assert isinstance(Point(auto_init_base=True), Point._auto_init_base)
    assert repr(Point(x=1, y=2)) == '<Point x=1, y=2>'


def test_access_to_singletons_base_via_auto_init_base():
    assert isinstance(DummySingleton(auto_init_base=True), DummySingleton._auto_init_base)
    assert DummySingleton() is DummySingleton()
    assert DummySingleton() is not DummySingleton(auto_init_base=True)
    assert DummySingleton(auto_init_base=True) is not DummySingleton(auto_init_base=True)


def test_derived_class_inherits_all_attributes():
    p3d = Point3d(x=1, z=3)
    assert p3d._auto_init_attrs == ['x', 'y', 'z']
    assert p3d.x == 1
    assert p3d.y == 0
    assert p3d.z == 3


def test_custom_provider_is_used_for_attributes_and_normal_instances():
    context = AutoInitContext(providers={
        Point: Point3d,
    })

    assert not isinstance(Point(), Point3d)
    assert not isinstance(Line().start, Point3d)

    with context:
        assert isinstance(Point(), Point3d)
        assert Point().z == 0

        assert isinstance(Line().start, Point3d)
        assert isinstance(Line().end, Point3d)

    assert not isinstance(Point(), Point3d)
    assert not isinstance(Line().start, Point3d)


def test_singletons_are_not_shared_across_contexts():
    s00 = DummySingleton()

    context1 = AutoInitContext()
    context2 = AutoInitContext()

    with context1:
        s10 = DummySingleton()
        assert s10 is not s00

        s11 = DummySingleton()
        assert s10 is s11

    with context2:
        s20 = DummySingleton()
        s21 = DummySingleton()
        assert s20 is s21

    assert s20 is not s10
    assert s20 is not s00
