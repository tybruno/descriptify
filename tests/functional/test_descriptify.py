import pytest
import descriptify


@pytest.fixture(
    params=[descriptify.ActionsDescriptor, descriptify.SlottableActionsDescriptor],
    ids=["AbstractDataDescriptor", "AbstractNonDataDescriptor"],
)
def action_descriptor(request):
    return request.param


class TestReadOnly:
    def test_read_only(self):
        class A:
            x: int = descriptify.ReadOnly(1)

        a = A()
        assert a.x == 1
        with pytest.raises(AttributeError):
            a.x = 2


class TestActionsDescriptorAndSlottableActionsDescriptor:
    def test_actions_descriptor(self, action_descriptor):
        def verify_length(value):
            if len(value) < 3:
                raise ValueError("value must have a length greater than 3.")
            if len(value) > 10:
                raise ValueError("value must have a length less than 10.")

        def verify_age(value):
            if not isinstance(value, int):
                raise TypeError("value must be an int.")
            if value < 0:
                raise ValueError("value must be greater than 0.")
            if value > 135:
                raise ValueError("value must be less than 135.")

        def verify_children(value):
            if not isinstance(value, int):
                raise TypeError("value must be an int.")
            if value < 0:
                raise ValueError("value must be greater than 0.")
            if value > 20:
                raise ValueError("value must be less than 20.")

        def sanitize_name(value):
            return value.title().strip()

        class Person:
            first_name = action_descriptor(
                immutable_actions=[verify_length], actions=[str.title, str.strip]
            )
            last_name = action_descriptor(actions=sanitize_name, default_value="")
            age = action_descriptor(immutable_actions=[verify_age])
            number_of_children = action_descriptor(
                immutable_actions=verify_children, default_value=None
            )

        bob = Person()

        assert bob.last_name == ""
        assert bob.number_of_children == None

        # Test attributes
        with pytest.raises(AttributeError):
            bob.first_name
        with pytest.raises(AttributeError):
            bob.age

        # Test Validation
        with pytest.raises(ValueError):
            bob.first_name = "toooooooooooooooooolong"
        with pytest.raises(TypeError):
            bob.first_name = 3

        with pytest.raises(ValueError):
            bob.age = -1
        with pytest.raises(TypeError):

            bob.age = "3"
        with pytest.raises(ValueError):
            bob.number_of_children = 21

        with pytest.raises(TypeError):
            bob.number_of_children = "2"

        _testing_first_name = "  BoB  "
        _testing_last_name = "  DyLaN  "
        _testing_age = 30
        _testing_number_of_children = 2

        _expected_first_name = _testing_first_name.title().strip()
        _expected_last_name = _testing_last_name.title().strip()
        _expected_age = _testing_age
        _expected_number_of_children = _testing_number_of_children

        bob.first_name = _testing_first_name
        bob.last_name = _testing_last_name
        bob.age = _testing_age
        bob.number_of_children = _testing_number_of_children

        assert bob.first_name == _expected_first_name
        assert bob.last_name == _expected_last_name
        assert bob.age == _expected_age
        assert bob.number_of_children == _expected_number_of_children

    def test_getting_instance(self, action_descriptor):
        descriptor = action_descriptor(actions=str.casefold)

        class Person:
            name: int = descriptor

        assert Person.name == descriptor
