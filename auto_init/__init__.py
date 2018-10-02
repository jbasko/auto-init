"""
Dataclasses reinvented + dependency injection. Python 3.7+
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set, Tuple, Type, get_type_hints

__version__ = '0.0.2'


def none_factory(*args, **kwargs):
    return None


class InstanceType(str):
    """
    Type annotations helper. Represents a type hint as a string.
    """

    def __new__(cls, instance_type):
        s = super().__new__(cls, instance_type)
        s._instance_type = instance_type
        return s

    @property
    def is_typing(self):
        return self.startswith('typing.')

    @property
    def is_forward_ref(self):
        return self.startswith('ForwardRef(')

    @property
    def is_list(self):
        return self.startswith('typing.List[') or self == 'typing.List'

    @property
    def is_dict(self):
        return self.startswith('typing.Dict[') or self == 'typing.Dict'

    @property
    def is_classvar(self):
        return self.startswith('typing.ClassVar[') or self == 'typing.ClassVar'

    @property
    def factory(self) -> Type:
        if self.is_typing:
            if self.is_list:
                return list
            elif self.is_dict:
                return dict
            else:
                return none_factory
        elif self.is_forward_ref:
            return none_factory
        else:
            return self._instance_type

    def __call__(self, *args, **kwargs):
        """
        Create a new instance of this type.
        """
        try:
            return self.factory(*args, **kwargs)
        except TypeError:
            raise


class AutoInitContext:
    """
    Represents a context in which autoinit works.

    Context stores singletons and customisations.

    Contexts are stacked. There is always one context in the stack by default which
    has no custom providers. All singletons initialised globally outside of any explicit contexts
    will be stored in this context.
    """

    NOT_SET = object()

    class _CurrentAutoInitContext:
        def __get__(self, instance, owner) -> AutoInitContext:
            assert instance is None
            return auto_init_context_stack.get()[-1]

    current: AutoInitContext = _CurrentAutoInitContext()

    def __init__(self, providers: Dict[Type, Any]=None, singleton_types: Set[Type]=None):
        self._providers = providers or {}
        self._singleton_types = singleton_types or set()
        self._singletons = {}

    def get_provider(self, instance_type: Type) -> Optional[Callable]:
        """
        Return a callable to be used to create a new instance
        of type `instance_type`.
        If the registered provider is not a callable, this will return a function
        that returns the provider.
        If there is no registered provider, this will return None.
        """
        provider = self._providers.get(instance_type, self.NOT_SET)
        if provider is self.NOT_SET:
            return None
        elif callable(provider):
            return provider
        else:
            return lambda: provider

    def get_instance(self, instance_type: Type, args: Tuple=None, kwargs: Dict=None) -> Any:
        """
        Create a new instance of type `instance_type`.
        If no custom provider is set and `default` is provided, `default` will be returned.
        Otherwise, `instance_type` will be called to create a new instance.
        """
        if instance_type in self._singleton_types and instance_type in self._singletons:
            return self._singletons[instance_type]

        provider = self.get_provider(instance_type)
        if provider is None:
            provider = InstanceType(instance_type)

        instance = provider(*(args or ()), **(kwargs or {}))
        if instance_type in self._singleton_types:
            self._singletons[instance_type] = instance
        return instance

    def has_singleton(self, instance_type: Type) -> bool:
        return instance_type in self._singletons

    def get_singleton(self, instance_type: Type) -> Any:
        return self._singletons[instance_type]

    def set_singleton(self, instance_type: Type, instance: Any):
        self._singletons[instance_type] = instance

    def auto_init(self, instance_type: Type, args: Tuple=None, kwargs: Dict=None, attrs: Dict=None) -> Any:
        """
        Auto-initialise an instance of the specified type.
        With this you can auto-initialise instance of "any" type without
        the need to decorate it with @auto_init_class.

        args and kwargs will be passed to the original initialiser of the instance.
        attrs will be passed to the auto-init's init_attrs.
        """
        instance = self.get_instance(instance_type=instance_type, args=args, kwargs=kwargs)
        init_attrs(instance, attrs=attrs or {})
        return instance

    def __enter__(self):
        if auto_init_context_stack.get() is None:
            auto_init_context_stack.set([])
        auto_init_context_stack.get().append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        stack = auto_init_context_stack.get()
        assert stack[-1] is self
        stack.pop()


auto_init_context_stack = ContextVar('auto_init_context_stack', default=[AutoInitContext()])


def collect_attrs(cls: Type):
    """
    Get names and types of all attributes in a class that will be auto-initialised on instance creation.
    """
    for k, v in get_type_hints(cls).items():
        instance_type = InstanceType(v)
        if instance_type.is_classvar:
            continue
        yield k, v


def init_attrs(instance: Any, attrs: Dict[str, Any], consume=True, auto_init=True):
    """
    Initialises attributes on instance from attrs dictionary.

    Skips attributes that have already been initialised.
    """
    for k, v in collect_attrs(instance.__class__):
        if k in attrs:
            if consume:
                setattr(instance, k, attrs.pop(k))
            else:
                setattr(instance, k, attrs[k])
        else:
            if auto_init:
                if hasattr(instance.__class__, k):
                    setattr(instance, k, getattr(instance.__class__, k))
                else:
                    setattr(instance, k, AutoInitContext.current.auto_init(v))


def auto_init_class(cls=None, singleton=False, repr=True, **cls_options):
    """
    Mark a class as auto-initialised.

    An auto-initialised class will have its type annotations parsed and interpreted as attribute declarations.
    All such attributes will be initialised on instance creation.

    The decoratored class is replaced with another class with the same name.

    The original class can have an __init__ method. It should accept keyword arguments.
    Anything that is not listed in the type annotations will be passed on to the original
    class's __init__ method AFTER init_attrs have run.

    """

    def decorator(c):

        if not isinstance(c, type):
            raise TypeError(f'Expected a type, got {c!r}')

        if '__new__' in c.__dict__:
            raise ValueError(f'Cannot safely auto-initialise {c!r} because it has a __new__ method')

        class C(c):
            _auto_init_attrs: ClassVar[List[str]]
            _auto_init_base: ClassVar[Type] = c

            _auto_init_attrs_called = None

            if singleton:
                _auto_init_singleton_instance = None

                def __new__(cls, *args, **kwargs):
                    if kwargs.pop('auto_init_base', False):
                        return cls._auto_init_base(*args, **kwargs)
                    if not AutoInitContext.current.has_singleton(cls):
                        provider = AutoInitContext.current.get_provider(cls)
                        if provider is not None:
                            AutoInitContext.current.set_singleton(cls, provider())
                        else:
                            AutoInitContext.current.set_singleton(cls, super(C, cls).__new__(cls))
                    return AutoInitContext.current.get_singleton(cls)

            else:

                def __new__(cls, *args, **kwargs):
                    if kwargs.pop('auto_init_base', False):
                        return cls._auto_init_base(*args, **kwargs)
                    provider = AutoInitContext.current.get_provider(cls)
                    if provider is not None:
                        return provider()
                    else:
                        return super(C, cls).__new__(cls)

            def __init__(self, *args, **kwargs):
                if not self._auto_init_attrs_called:
                    # When an auto_init_class inherits another, __init__ will
                    # be called in each of the classes. It is sufficient to
                    # execute init_attrs just in the final class as type annotations
                    # are collected from all the base classes.
                    self._auto_init_attrs_called = True
                    init_attrs(self, kwargs, consume=True, auto_init=True)
                super().__init__(*args, **kwargs)

            if '__repr__' not in c.__dict__ and repr is True:

                def __repr__(self):
                    attrs_str = ', '.join(f'{k}={getattr(self, k)!r}' for k in self._auto_init_attrs)
                    return f'<{c.__name__} {attrs_str}>'

            if '__str__' not in c.__dict__ and repr is True:

                def __str__(self):
                    return self.__repr__()

        C.__name__ = c.__name__
        C.__qualname__ = c.__qualname__
        C._auto_init_attrs = [k for k, _ in collect_attrs(c)]

        return C

    if cls is None:
        return decorator
    else:
        return decorator(cls)


def auto_init(instance_type: Type, args: Tuple=None, kwargs: Dict=None, attrs: Dict=None) -> Any:
    """
    Create and auto-initialise an instance of type `instance_type` within the current AutoInitContext.
    If you are outside of any explicit AutoInitContext, the global context will be used.
    """
    return AutoInitContext.current.auto_init(instance_type, args=args, kwargs=kwargs, attrs=attrs)
