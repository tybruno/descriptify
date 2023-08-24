import typing
import abc


class AbstractNonDataDescriptor(abc.ABC):
    """ Abstract Base Class for Non Data Descriptors.

    Non Data Descriptors must implement __get__, __set_name__ is optional.
    """

    @abc.abstractmethod
    def __get__(self, instance, owner=None):
        pass


class BaseNonDataDescriptor(AbstractNonDataDescriptor):
    def __init__(self, value: typing.Any):
        AbstractNonDataDescriptor.__init__(self)
        self._value = value

    def __set_name__(self, owner, name):
        self._property_name = name

    def __get__(self, instance, owner=None):
        return self._value


class ReadOnly(BaseNonDataDescriptor):
    def __set__(self, instance, value):
        raise AttributeError(f"{instance}.{self._property_name}", "is read only.")
