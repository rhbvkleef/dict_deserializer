import unittest

from dict_deserializer.annotations import validated
from dict_deserializer.deserializer import Deserializable, deserialize, Rule


class Object(Deserializable):
    name: str

    @validated()
    def name(self, value):
        if len(value) > 10:
            raise TypeError("Maximum name length is 20 characters")

    def __repr__(self):
        return 'Object(name="{}")'.format(self.name)

    def __eq__(self, other):
        return isinstance(other, Object) and other.name == self.name


class TestLists(unittest.TestCase):
    def test_SetWrongTypeShouldFail(self):
        with self.assertRaises(TypeError):
            deserialize(Rule(Object), {
                'name': 8
            })

    def test_SetWrongValueShouldFail(self):
        with self.assertRaises(TypeError):
            deserialize(Rule(Object), {
                'name': 'abcdefghijklmnopqrstuvwxyz'
            })

    def test_SetCorrectValueShouldSucceed(self):
        self.assertEqual(
            Object(name='Rolf'),
            deserialize(Rule(Object), {
               'name': 'Rolf'
            }, try_all=False)
        )
