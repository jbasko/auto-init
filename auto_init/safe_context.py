from typing import Any, Callable, Dict, List, Optional, Tuple, Type, get_type_hints

import dataclasses
from contextvars import ContextVar


class CreationFailed(Exception):
    pass


class InitialisationFailed(Exception):
    pass


class AutoInitContext:

    _PRIMITIVE_BUILTIN_TYPES = (
        str,
        bytes,
        int,
        bool,
        float,
    )

    # A factory is a callable that returns an instance of the type against which the factory
    # has been registered.
    # Instances returned by factory are still injected any missing attributes as deemed
    # necessary by auto-init
    _factories: Dict[Type, Callable]

    # Fixed instances that are always returned when an instance of the particular type is requested.
    _instances: Dict[Type, Any]

    # Stack of types, instances of which are being initialised.
    # If we are instantiating a type when another instance of this type
    # is requested, we will always return None unless the instance_type
    # is marked as a singleton and we have an instance (regardless
    # of its initialisation state) available.
    _pending_types: List[Type]

    # Cache of type hints
    _type_hints: Dict[Type, Dict[str, Type]]

    # List of types for which, if requested, a single instance is created upon the first
    # request and then returned every time a new instance is requested.
    _singleton_types: Dict[Type, Type]

    # Registry of singletons. This is different from _instances in that objects in _singletons are
    # created and initialised by the context whereas _instances are supplied by the user of this context.
    _singletons: Dict[Type, "_InitState"] = {}

    def __init__(self):
        self._factories = {}
        self._instances = {}
        self._pending_types = []
        self._type_hints = {}
        self._singleton_types = {}
        self._singletons = {}

    def is_custom_provided_type(self, instance_type: Type):
        return (
            instance_type in self._factories or
            instance_type in self._singleton_types or
            instance_type in self._instances
        )

    def register_singleton(self, instance_type: Type, factory: Callable=None):
        """
        Register a type for which only a single instance should be created.
        """
        assert not self.is_custom_provided_type(instance_type)
        self._singleton_types[instance_type] = factory or instance_type

    def register_factory(self, instance_type: Type, factory: Callable):
        """
        Register a callable that should be used to create a new instance of type ``instance_type``.
        """
        assert not self.is_custom_provided_type(instance_type)
        self._factories[instance_type] = factory

    def register_instance(self, instance: Any, instance_type: Type=None):
        """
        Register an instance that is always returned when a new instance of type ``instance_type`` is requested.
        """
        if instance_type is None:
            instance_type = type(instance)
        assert not self.is_custom_provided_type(instance_type)
        self._instances[instance_type] = instance

    def get_instance(self, instance_type: Type):
        """
        Provides an instance of the specified type.
        It could be a new instance or an existing instance depending on the context.
        """
        if instance_type in self._instances:
            return self._instances[instance_type]

        instance, init_state = self._create_instance(instance_type)
        if init_state is not None:
            assert init_state.initialised
        return instance

    def init_instance(self, instance):
        """
        Initialise attributes of an existing instance.
        """
        instance_type = instance.__class__
        type_hints = self._get_type_hints(instance_type)

        self._pending_types.append(instance_type)

        init_state = _InitState(
            instance_type,
            instance,
        )

        if instance_type in self._singleton_types:
            self._singletons[instance_type] = init_state

        try:
            for attr_name, attr_type in type_hints.items():

                # Do not initialise already initialised attributes
                if hasattr(instance, attr_name):
                    continue

                attr_value, attr_init_state = self._create_instance(attr_type)
                setattr(init_state.instance, attr_name, attr_value)
                if attr_init_state is not None:
                    init_state.dependencies.append(attr_init_state)

            if init_state.has_dependencies_resolved():
                init_state._initialised = True
                self._pending_types.remove(instance_type)

            return init_state.instance, init_state

        except (CreationFailed, InitialisationFailed):
            raise

        except Exception as e:
            raise InitialisationFailed(
                f"Initialisation of {init_state.instance_type} failed with an exception: {e!r}"
            ) from e

    def _new_instance(self, instance_type: Type):
        try:
            instance_type = InstanceType(instance_type)
            return instance_type()
        except Exception as e:
            raise CreationFailed(
                f"Creation of instance of type {instance_type.original_type} failed with an "
                f"exception: {e!r}"
            ) from e

    def _create_instance(self, instance_type: Type) -> Tuple[Any, Optional["_InitState"]]:
        if instance_type in self._PRIMITIVE_BUILTIN_TYPES:
            return self._new_instance(instance_type), None

        if instance_type in self._instances:
            return self._instances[instance_type], None

        # The type that will be used to create the actual instance.
        actual_instance_type: Type = instance_type

        if instance_type in self._singleton_types:
            actual_instance_type = self._singleton_types[instance_type]
            if instance_type in self._singletons:
                singleton_init_state = self._singletons[instance_type]
                return singleton_init_state.instance, singleton_init_state

        if instance_type in self._factories:
            instance = self._factories[instance_type]()
            return instance, None

        type_hints = self._get_type_hints(instance_type)

        if dataclasses.is_dataclass(instance_type):
            # Inject only the required attributes
            required = {}
            for f in dataclasses.fields(instance_type):  # type: dataclasses.Field
                if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
                    required[f.name] = self.get_instance(type_hints[f.name])
            instance = instance_type(**required)
            return instance, None

        if not type_hints:
            instance = self._new_instance(actual_instance_type)
            if instance_type in self._singleton_types:
                # Singletons need to have InitState for consistent storage in self._singletons
                self._singletons[instance_type] = _InitState(instance_type, instance, initialised=True)
                return instance, self._singletons[instance_type]
            return instance, None

        if instance_type in self._pending_types:
            # We are already initialising an instance of this type so must be a circular reference.
            return None, None

        instance = self._new_instance(instance_type)
        return self.init_instance(instance)

    def _get_type_hints(self, instance_type: Type) -> Dict[str, Type]:
        """
        Returns type hints for the specified instance type.
        """
        if instance_type not in self._type_hints:
            if InstanceType(instance_type).is_typing:
                # Do not attempt to get type hints from typing.* classes because it doesn't work in Python 3.7
                # and we are not expecting anything useful anyway.
                self._type_hints[instance_type] = {}
            else:
                self._type_hints[instance_type] = dict(get_type_hints(instance_type))
        return self._type_hints[instance_type]

    def __enter__(self):
        if auto_init_context_stack.get() is None:
            auto_init_context_stack.set([])
        auto_init_context_stack.get().append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stack = auto_init_context_stack.get()
        assert stack[-1] is self
        stack.pop()


auto_init_context_stack = ContextVar('auto_init_context_stack', default=[AutoInitContext()])


class _InitState:
    """
    Represents the initialisation state of an instance of non-primitive type `instance_type`.
    """
    def __init__(self, instance_type: Type, instance: Any, *, created: bool=True, initialised: bool=False):
        self.instance_type = instance_type
        self.instance = instance
        self.created = created
        self._initialised = initialised
        self.dependencies: List[_InitState] = []

    @property
    def initialised(self):
        return (
            self.created and
            self._initialised and
            self.has_dependencies_resolved()
        )

    def has_dependencies_resolved(self, stack=None):
        if not self.dependencies:
            return True
        if stack:
            if self in stack:
                # Circular dependency
                return True
        else:
            stack = []
        check_stack = stack + [self]
        for d in self.dependencies:
            resolved = d.has_dependencies_resolved(stack=check_stack)
            if not resolved:
                return False
        return True

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.instance_type.__name__!r}>'


def none_factory():
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
    def original_type(self) -> Type:
        return self._instance_type

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
    def is_tuple(self):
        return self.startswith('typing.Tuple[') or self == 'typing.Tuple'

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
