"""
Initialising all annotated attributes could be a bit destructive for someone's code base.
User may want to just initialise the types specified in the providers map.
"""
from typing import List

from auto_init import AutoInitContext, auto_init


class Point:
    x: int


def test_explicit_only_context():
    with AutoInitContext(explicit_only=True) as context:
        assert context.auto_init(int) is None
        assert context.auto_init(List) is None
        assert context.auto_init(Point) is None

    with AutoInitContext(explicit_only=True, providers={Point: Point}) as context:
        assert context.auto_init(int) is None
        p = context.auto_init(Point)
        assert isinstance(p, Point)
        assert p.__dict__ == {}

    with AutoInitContext(explicit_only=True, providers={Point: Point, int: int}) as context:
        assert context.auto_init(int) == 0
        p = context.auto_init(Point)
        assert isinstance(p, Point)
        assert p.__dict__ == {'x': 0}


def test_db_example():
    class Connection:
        pass

    class Db:
        connection: Connection

    with AutoInitContext(providers={Db: Db}, explicit_only=True):
        assert AutoInitContext.current.explicit_only
        assert isinstance(auto_init(Db), Db)
        assert not hasattr(auto_init(Db), 'connection')

    with AutoInitContext(providers={Db: Db}):
        assert not AutoInitContext.current.explicit_only
        assert isinstance(auto_init(Db).connection, Connection)
