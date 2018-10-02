"""
Is there really any need for the intrusiveness i.e. @auto_init_class decorator?
Because we can just let user decide at runtime whether they want to use the auto initialisation or not!
"""
from typing import Dict, Generator, List

from auto_init import AutoInitContext, auto_init, auto_init_class


class T0:
    pass


class T1:
    x: int


class T2:
    t0: T0
    t1: T1
    y: int


class T3(T1):
    t0: T0
    t2: T2


def test_auto_init_builtin_types():
    context = AutoInitContext()
    assert context.auto_init(int) == 0
    assert context.auto_init(str) == ''
    assert context.auto_init(list) == []


def test_auto_init_typing_types():
    context = AutoInitContext()
    assert context.auto_init(List) == []
    assert context.auto_init(List[str]) == []
    assert context.auto_init(Dict) == {}
    assert context.auto_init(Dict[str, List[str]]) == {}
    assert context.auto_init(Generator) is None


def test_nonintrusive_auto_init():
    context = AutoInitContext()

    t2 = context.auto_init(T2)
    assert isinstance(t2.t0, T0)
    assert isinstance(t2.t1, T1)
    assert t2.y == 0

    t3 = context.auto_init(T3)
    assert isinstance(t3.t0, T0)
    assert t3.t0 is not t2.t0
    assert isinstance(t3.t2, T2)
    assert t3.t2 is not t2


def test_singletons():
    context = AutoInitContext(singleton_types={
        T0, T2,
    })

    assert context.auto_init(T0) is context.auto_init(T0)
    assert context.auto_init(T1) is not context.auto_init(T1)
    assert context.auto_init(T2) is context.auto_init(T2)


def test_implicit_context():
    with AutoInitContext(singleton_types={T1}):
        assert auto_init(T0) is not auto_init(T0)
        assert auto_init(T1) is auto_init(T1)

        t2 = auto_init(T2)
        assert t2.t1 is auto_init(T1)


def test_with_args_and_kwargs():
    with AutoInitContext():
        assert auto_init(list, args=((1, 2, 3),)) == [1, 2, 3]
        assert auto_init(dict, kwargs={'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
        t1 = auto_init(T1, attrs={'x': 5})
        assert t1.x == 5


def test_nested_attrs_are_initialised():

    # This also tests @auto_init_class mixing with normal classes.
    @auto_init_class
    class Label:
        text: str

    class Point:
        x: int
        y: int

    class Line:
        label: Label
        start: Point
        end: Point

    label = auto_init(Label)
    assert label.text == ''

    point = auto_init(Point, attrs={'y': 5})
    assert point.__dict__ == {'x': 0, 'y': 5}

    line = auto_init(Line)
    assert line.start.__dict__ == {'x': 0, 'y': 0}
    assert line.end.__dict__ == {'x': 0, 'y': 0}

    direct_label = Label()
    assert direct_label.__class__ is label.__class__


def test_app_model_example():
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
