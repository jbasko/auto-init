import collections
from typing import Callable, Dict, List, Tuple


class Item:
    pass


class ItemConsumer:
    item_list: List[Item]
    item_list_simple: List
    item_list_primitive: list

    item_dict: Dict[str, Item]
    item_dict_simple: Dict
    item_dict_primitive: dict

    item_triple: Tuple[Item, Item, Item]

    item_hook: Callable


def test_list_of_anything_initialised_as_list(ctx):
    ic: ItemConsumer = ctx.get_instance(ItemConsumer)
    assert ic.item_list == []
    assert ic.item_list_simple == []
    assert ic.item_list_primitive == []


def test_dict_of_anything_initialised_as_dict(ctx):
    ic: ItemConsumer = ctx.get_instance(ItemConsumer)
    assert ic.item_dict == {}
    assert ic.item_dict_simple == {}
    assert ic.item_dict_primitive == {}


def test_tuple_initialised_as_none(ctx):
    ic: ItemConsumer = ctx.get_instance(ItemConsumer)
    assert ic.item_triple is None


def test_callable_initialised_as_none(ctx):
    ic: ItemConsumer = ctx.get_instance(ItemConsumer)
    assert ic.item_hook is None


def test_registered_factory_of_specific_container_type(ctx):
    ctx.register_factory(Dict[str, Item], collections.OrderedDict)

    ic: ItemConsumer = ctx.get_instance(ItemConsumer)
    assert isinstance(ic.item_dict, collections.OrderedDict)
    assert not isinstance(ic.item_dict_simple, collections.OrderedDict)
