import unittest
from typing import List, Optional

from dict_deserializer.annotations import abstract
from dict_deserializer.deserializer import Deserializable, deserialize, Rule


@abstract
class Object(Deserializable):
    def __init__(self, name=None):
        self.name = name

    name: str

    def __repr__(self):
        return 'Object(name="{}")'.format(self.name)

    def __eq__(self, other):
        return isinstance(other, Object) and other.name == self.name


class User(Object):
    def __init__(self, full_name=None, calling_name=None, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.full_name = full_name
        self.calling_name = calling_name

    full_name: str
    calling_name: Optional[str] = 'Unknown'

    def __repr__(self):
        if self.calling_name is None:
            return 'User(super={}, full_name="{}")'\
                .format(super(User, self).__repr__(), self.full_name)
        return 'User(super={}, full_name="{}", calling_name="{}")'\
            .format(super(User, self).__repr__(),
                    self.full_name, self.calling_name)

    def __eq__(self, other):
        return isinstance(other, User) and super(User, self).__eq__(other) and\
            other.full_name == self.full_name and\
            other.calling_name == self.calling_name


class Group(Object):
    def __init__(self, members=None, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        self.members = members

    members: List[Object]

    def __repr__(self):
        return 'Group(super={}, members=[{}])'\
            .format(super(Group, self).__repr__(),
                    ','.join([m.__repr__() for m in self.members]))

    def __eq__(self, other):
        return isinstance(other, Group) and super(Group, self).__eq__(other)\
               and other.members == self.members


class TestLists(unittest.TestCase):
    def test_CorrectDeserializationForNestedWithTypeUnionsAndLists(self):
        self.assertEqual(
            Group(
                name='IAPC',
                members=[
                    User(name='Rolf', full_name='Rolf van Kleef', calling_name='Unknown'),
                    Group(name='Syscom', members=[
                        User(name='Kevin', full_name='Kevin Alberts', calling_name='Kevin'),
                    ]),
                ],
            ),
            deserialize(Rule(Object), {
                'name': 'IAPC',
                'members': [
                    {'name': 'Rolf', 'full_name': 'Rolf van Kleef'},
                    {'name': 'Syscom', 'members': [
                        {'name': 'Kevin', 'full_name': 'Kevin Alberts', 'calling_name': 'Kevin'},
                    ]},
                ],
            })
        )

    def test_FailDeserializeWithInvalidTypes(self):
        with self.assertRaises(TypeError):
            deserialize(Rule(Object), {
                'name': 'Karel',
                'full_name': 0.0,
            })

        with self.assertRaises(TypeError):
            deserialize(Rule(Object), {
                'name': 'Rolf',
                'full_name': 'Rolf van Kleef',
                'calling_name': False,
            })

    def test_DeserializeIntoAbstract(self):
        with self.assertRaises(TypeError) as ctx:
            deserialize(Rule(Object), {
                'name': 'Test'
            })