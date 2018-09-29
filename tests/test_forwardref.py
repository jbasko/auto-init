# Keep this test separate from others because this requires "from __future__ ..." which breaks other tests.
from __future__ import annotations

from auto_init import auto_init_class


def test_does_not_explode_on_self_references():
    @auto_init_class
    class Node:
        label: str
        parent: 'Node'  # get_type_hints raises NameError if this is not quoted

    n1 = Node()
    assert n1.label == ''
    assert n1.parent is None
