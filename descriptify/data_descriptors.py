import abc
import typing
import weakref

# Globals
# Sentinel
NO_DEFAULT_VALUE = object()

# Typing
Action = typing.Callable[[typing.Any], typing.Any]
Actions = typing.Union[Action, typing.Iterable[Action]]
ImmutableAction = typing.Callable[[typing.Any], None]
ImmutableActions = typing.Union[ImmutableAction, typing.Iterable[ImmutableAction]]


class Reference(typing.NamedTuple):
    """ Used in Slottable Data Descriptors to Reference an instance and its value."""
    reference: weakref.ref
    value: typing.Any


class AbstractDataDescriptor(abc.ABC):
    """ Abstract Base Class for Data Descriptors.

    Data Descriptors must implement __get__ and __set__, __set_name__ and __delete__ is optional.
    """

    @abc.abstractmethod
    def __get__(self, instance, owner=None):
        pass

    @abc.abstractmethod
    def __set__(self, instance, value):
        pass


class BaseSlottableDataDescriptor(AbstractDataDescriptor):
    """ Base class for making Slottable Data Descriptors.

    The SlottableDataDescriptor has the following advantages:

    1. Has instance specific storage
    2. Does not use the instance for storage, thus works with __slots__. Make sure __slots__ = ("__weakref__", )
    3. Handles non hashable instances
    4. Data storage is clean.

    Note:
        Must Include `__slots__ = "__weakref__"` to make the class work the slottable data descriptor.

    Example:
        >>> class Person:
        ...     __slots__ = "__weakref__"
        ...     first_name = BaseSlottableDataDescriptor()
        >>> person = Person()
        >>> person.first_name = "Raymond"
        >>> person.first_name
        'Raymond'
    """

    def __init__(self):
        self._references: typing.Dict[int, Reference] = {}

    def __set_name__(self, owner, name):
        self._property_name = name

    def __set__(self, instance, value):
        _weak_ref: weakref.ref = weakref.ref(instance, self._delete_reference)
        reference: Reference = Reference(_weak_ref, value)
        self._references[id(instance)] = reference

    def __get__(self, instance, owner=None) -> typing.Any:
        if instance is None:
            return self

        try:
            _reference: Reference = self._references[id(instance)]
            value: typing.Any = _reference.value
            return value
        except KeyError:
            raise AttributeError(
                f"{instance}.{self._property_name}", "has not been set with a value"
            ) from None

    def _find_weak_ref_key(self, weak_ref) -> typing.Any:
        for key, reference in self._references.items():
            if reference.reference is weak_ref:
                return key

    def _delete_reference(self, weak_ref):
        key = self._find_weak_ref_key(weak_ref)
        if key:
            del self._references[key]


class SlottableDefaultDataDescriptor(BaseSlottableDataDescriptor):
    """This data has the following advantages:

    1. Has instance specific storage
    2. Does not use the instance for storage, thus works with __slots__. Make sure __slots__ = ("__weakref__", )
    3. Handles non hashable instances
    4. Data storage is clean.

    Must Include `__slots__ = "__weakref__"` to make the class work the slottable data descriptor.

    Example:
        >>> class Person:
        ...     __slots__ = "__weakref__"
        ...     first_name = SlottableDefaultDataDescriptor(default_value='Raymond')
        >>> person = Person()
        >>> person.first_name
        'Raymond'
        >>> person.first_name = 'Guido'
        >>> person.first_name
        'Guido'


    """

    def __init__(self, *, default_value: typing.Any = NO_DEFAULT_VALUE):
        BaseSlottableDataDescriptor.__init__(self)
        self.default = default_value

    def __get__(self, instance, owner=None) -> typing.Any:
        value: typing.Any
        _default: typing.Any = self.default

        if _default is NO_DEFAULT_VALUE:
            value = BaseSlottableDataDescriptor.__get__(self, instance, owner)
            return value

        value_or_reference: Reference = self._references.get(id(instance), _default)

        if isinstance(value_or_reference, Reference):
            value = value_or_reference.value
        else:
            value = value_or_reference

        return value


class BaseDataDescriptor(AbstractDataDescriptor):
    def __set_name__(self, owner, name):
        self._property_name = name

    def __set__(self, instance, value):
        instance.__dict__[self._property_name] = value

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return instance.__dict__[self._property_name]
        except KeyError:
            raise AttributeError(
                f"{instance}.{self._property_name}", "has not been set with a value"
            ) from None


class DefaultDataDescriptor(BaseDataDescriptor):
    def __init__(self, *, default_value: typing.Any = NO_DEFAULT_VALUE):
        self.default = default_value

    def __get__(self, instance, owner=None):
        value: typing.Any
        _default: typing.Any = self.default

        if _default is NO_DEFAULT_VALUE:
            value = BaseDataDescriptor.__get__(self, instance, owner)
            return value

        value = instance.__dict__.get(self._property_name, _default)
        return value


class ActionsDescriptor(DefaultDataDescriptor):
    def __init__(self, *, default_value: typing.Any = NO_DEFAULT_VALUE, actions: Actions = None,
                 immutable_actions: ImmutableActions = None):
        DefaultDataDescriptor.__init__(self, default_value=default_value)
        self.immutable_actions: ImmutableActions = immutable_actions or ()
        self.actions: Actions = actions or ()

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value: Actions):
        if not isinstance(value, typing.Iterable):
            value = [value]

        self._actions = value

    @property
    def immutable_actions(self) -> typing.Iterable:
        return self._immutable_actions

    @immutable_actions.setter
    def immutable_actions(self, value: ImmutableActions):
        if not isinstance(value, typing.Iterable):
            value = [value]

        self._immutable_actions = value

    def _run_immutable_actions(self, instance, value) -> None:
        for immutable_action in self.immutable_actions:
            immutable_action(value)

    def _run_actions(self, instance, value: typing.Any) -> typing.Any:
        for action in self.actions:
            value = action(value)
        return value

    def __set__(self, instance, value: typing.Any):
        self._run_immutable_actions(instance, value)
        value = self._run_actions(instance, value)
        DefaultDataDescriptor.__set__(self, instance, value)


class SlottableActionsDescriptor(SlottableDefaultDataDescriptor):
    """This data has the following advantages:

    1. Has instance specific storage
    2. Does not use the instance for storage, thus works with __slots__. Make sure __slots__ = ("__weakref__", )
    3. Handles non hashable instances
    4. Data storage is clean.

    must include `__slots__ = "__weakref__"`

    Example:
        class Person:
            __slots__ = "__weakref__"
            first_name = SlottableDataDescriptor(actions=ValidateInstance(str),default_value="Raymond)
    """

    def __init__(self, *, default_value: typing.Any = NO_DEFAULT_VALUE, actions: Actions = None,
                 immutable_actions: ImmutableActions = None):
        SlottableDefaultDataDescriptor.__init__(self, default_value=default_value)
        self.immutable_actions: ImmutableActions = immutable_actions or ()
        self.actions: Actions = actions or ()

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value: Actions):
        if not isinstance(value, typing.Iterable):
            value = [value]

        self._actions = value

    @property
    def immutable_actions(self) -> typing.Iterable:
        return self._immutable_actions

    @immutable_actions.setter
    def immutable_actions(self, value: ImmutableActions):
        if not isinstance(value, typing.Iterable):
            value = [value]

        self._immutable_actions = value

    def _run_immutable_actions(self, instance, value: typing.Any) -> None:
        for immutable_action in self.immutable_actions:
            immutable_action(value)

    def _run_actions(self, instance, value: typing.Any):
        for action in self.actions:
            value = action(value)
        return value

    def __set__(self, instance, value):
        self._run_immutable_actions(instance, value)
        value = self._run_actions(instance, value)
        SlottableDefaultDataDescriptor.__set__(self, instance, value)
