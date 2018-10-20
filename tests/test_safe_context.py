import pytest

from auto_init.safe_context import AutoInitContext, _InitState


@pytest.fixture
def ctx() -> AutoInitContext:
    ctx = AutoInitContext()
    assert not ctx._pending_types
    return ctx


@pytest.fixture
def A():
    class A:
        pass
    return A


@pytest.fixture
def P():

    class P:
        x: int
        y: int

        def __repr__(self):
            return f'<{self.__class__.__name__} {self.__dict__}>'

    return P


# These don't work inside fixtures

class C:
    d: 'D'

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.__dict__}>'


class D:
    c: 'C'

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.__dict__}>'


class Node:
    label: str
    parent: 'Node'


class Model:
    pass


class View:
    model: 'Model'
    presenter: 'Presenter'


class Presenter:
    model: 'Model'
    view: 'View'


def test_auto_init_primitive_builtin_types(ctx):
    assert ctx.get_instance(int) == 0
    assert ctx.get_instance(str) == ''
    assert ctx.get_instance(float) == 0.0
    assert ctx.get_instance(bool) is False
    assert not ctx._pending_types


def test_auto_init_composite_builtin_types(ctx):
    assert ctx.get_instance(list) == []
    assert ctx.get_instance(dict) == {}
    assert ctx.get_instance(set) == set()
    assert not ctx._pending_types


def test_auto_init_primitive_user_types(ctx, A):
    a1 = ctx.get_instance(A)
    assert not ctx._pending_types
    assert isinstance(a1, A)

    a2 = ctx.get_instance(A)
    assert not ctx._pending_types
    assert isinstance(a2, A)

    assert a1 is not a2


def test_auto_init_simple_user_type_with_primitive_attributes(ctx, P):
    p1 = ctx.get_instance(P)
    assert not ctx._pending_types
    assert isinstance(p1, P)


@pytest.mark.parametrize('t', [
    int,
    bool,
    float,
    str,
    bytes,
])
def test_create_instance_of_primitive_builtin_type(ctx, t):
    instance, init_state = ctx._create_instance(t)
    assert isinstance(instance, t)
    assert not ctx._pending_types
    assert init_state is None


def test_create_instance_of_simple_user_type(ctx, A):
    a1, init_state = ctx._create_instance(A)
    assert isinstance(a1, A)
    assert init_state is None

    a2, init_state = ctx._create_instance(A)
    assert isinstance(a2, A)
    assert init_state is None

    assert a1 is not a2

    assert not ctx._pending_types


def test_create_instance_of_user_type_with_primitive_attributes(ctx, P):
    p, init_state = ctx._create_instance(P)
    assert isinstance(p, P)
    assert isinstance(init_state, _InitState)

    assert P not in ctx._pending_types

    assert init_state.instance_type is P
    assert init_state.instance is p
    assert init_state.initialised

    assert p.x == 0
    assert p.y == 0


def test_create_instance_with_circular_references(ctx):
    c, init_state = ctx._create_instance(C)

    assert isinstance(c, C)
    assert init_state.instance_type is C
    assert init_state.instance is c

    assert len(init_state.dependencies) == 1
    assert init_state.dependencies[0].instance_type is D

    assert c.d.c is None

    d, init_state = ctx._create_instance(D)
    assert d.c.d is None


def test_create_instance_with_self_reference(ctx):
    n, init_state = ctx._create_instance(Node)
    assert n.label == ''
    assert n.parent is None

    class BiNode:
        first: Node
        second: Node

    b, init_state = ctx._create_instance(BiNode)
    assert isinstance(b.first, Node)
    assert isinstance(b.second, Node)
    assert b.first is not b.second


def test_primitive_singleton(ctx, A):
    a1, _ = ctx._create_instance(A)
    a2, _ = ctx._create_instance(A)
    assert a1 is not a2

    ctx.register_singleton(A)
    a3, _ = ctx._create_instance(A)
    a4, _ = ctx._create_instance(A)
    assert a3 is not a1
    assert a3 is not a2
    assert a3 is a4


def test_singleton_with_primitive_attributes(ctx, P):
    p1, _ = ctx._create_instance(P)
    p2, _ = ctx._create_instance(P)
    assert p1 is not p2

    assert p1.x == 0
    assert p1.y == 0

    ctx.register_singleton(P)
    p3, _ = ctx._create_instance(P)
    p4, _ = ctx._create_instance(P)
    assert p3 is not p1
    assert p3 is not p2
    assert p3 is p4

    assert p3.x == 0
    assert p3.y == 0


def wtest_singletons_with_circular_references(ctx):
    ctx.singleton_types.append(Model)
    ctx.singleton_types.append(Presenter)
    ctx.singleton_types.append(View)

    presenter, init_state = ctx._create_instance(Presenter)
    assert init_state.initialised

    assert presenter.view.model is presenter.model
