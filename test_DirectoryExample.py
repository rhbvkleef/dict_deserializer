import unittest
from typing import List, Optional, Tuple, Dict

from dict_deserializer.annotations import abstract
from dict_deserializer.deserializer import Deserializable, deserialize, Rule


@abstract
class Object(Deserializable):
    name: str

    def __repr__(self):
        return 'Object(name="{}")'.format(self.name)

    def __eq__(self, other):
        return isinstance(other, Object) and other.name == self.name


class User(Object):
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
    members: List[Object]

    def __repr__(self):
        return 'Group(super={}, members=[{}])'\
            .format(super(Group, self).__repr__(),
                    ','.join([m.__repr__() for m in self.members]))

    def __eq__(self, other):
        return isinstance(other, Group) and super(Group, self).__eq__(other)\
               and other.members == self.members


class NestedTypingStuff(Deserializable):
    test: List[Tuple[int, int, int]]

    def __str__(self):
        return "NestedTypingStuff(test={})".format(self.test)

    def __eq__(self, other):
        return isinstance(other, NestedTypingStuff) and self.test == other.test


class DictTest(Deserializable):
    test: Dict[int, List[Object]]

    def __str__(self):
        return "DictTest(test={})".format(self.test)

    def __eq__(self, other):
        if not isinstance(other, DictTest):
            return False

        other: DictTest

        for k, v in other.test.items():
            if k not in self.test:
                return False

            if not self.test[k].__eq__(v):
                return False
        return True


class TestLists(unittest.TestCase):
    def test_CorrectDeserializationForNestedWithTypeUnionsAndLists(self):
        # noinspection PyArgumentList
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
        with self.assertRaises(TypeError):
            deserialize(Rule(Object), {
                'name': 'Test'
            })

    def test_DeserializeTupleCorrect(self):
        # noinspection PyArgumentList
        self.assertEqual(
            NestedTypingStuff(test=[(1, 2, 3)]),
            deserialize(Rule(NestedTypingStuff), {
                "test": [
                    [
                        1, 2, 3
                    ]
                ]
            })
        )

    def test_DeserializeTupleFail(self):
        with self.assertRaises(TypeError):
            deserialize(Rule(NestedTypingStuff), {
                "test": [
                    [
                        1, 2
                    ]
                ]
            })

        with self.assertRaises(TypeError):
            deserialize(Rule(NestedTypingStuff), {
                "test": [
                    [
                        1, 2, "boo"
                    ]
                ]
            })

    def test_DictDeserialize(self):
        self.assertEqual(
            DictTest(test={
                1: [User(
                    name='Peter',
                    full_name='Peter Driebergen',
                    calling_name='Unknown')]
            }),
            deserialize(Rule(DictTest), {
                "test": {
                    1: [{
                        'name': 'Peter',
                        'full_name': 'Peter Driebergen',
                    }],
                }
            })
        )
