from typing import Optional, Union, List, Tuple, Dict, Any

from typeguard import check_type


def _type_to_str(t, default=None):
    if default is None:
        default = str(t)
    if type(t) == type:
        t: type
        return t.__name__
    return default


class Rule:
    """
    This class is primarily used as a container to store type information.
    """

    @staticmethod
    def to_rule(tpe) -> 'Rule':
        """
        Ensures type is a rule. Otherwise, it will be converted into a rule.

        :param tpe: The type/rule.
        :return: a Rule
        """
        if isinstance(tpe, Rule):
            return tpe
        return Rule(tpe)

    # noinspection PyShadowingBuiltins
    def __init__(self: 'Rule', type, default=None):
        self.type = type
        self.default = default

    def __repr__(self: 'Rule'):
        if self.default:
            return "Rule(type={}, default={})".format(self.type, self.default)
        return "Rule(type={})".format(self.type)

    def validate(self: 'Rule', key: str, value):
        """
        Returns the original value, a default value, or throws.
        :param key: The key of this field.
        :param value: Which value to validate.
        :return: value, default.
        """
        check_type(key, value, self.type)
        if value is None:
            value = self.default

        return value

    def error_string(self):
        return _type_to_str(self.type, default=self.__str__())


class DeserializableMeta(type):
    """
    Metaclass for all Deserializable
    """

    def __new__(
            mcs: 'DeserializableMeta', name: str, bases: Tuple[type],
            namespace: dict) \
            -> type:
        def auto_ctor(self, **kwargs):
            for k, v in type(self).get_attrs().items():
                setattr(self, k, kwargs.get(k))

        namespace['_discriminators'] = []
        namespace['_abstract'] = False
        namespace['__init__'] = auto_ctor

        cls = type.__new__(mcs, name, bases, namespace)

        for b in bases:
            if b is object:
                continue

            if hasattr(b, '__annotations__'):
                annotations = dict(b.__annotations__)
                annotations.update(cls.__annotations__)
                cls.__annotations__ = annotations

        return cls


def _rbase(cls: type, ls: List[type] = None) -> List[type]:
    """
    Get all base classes for cls.
    """
    if ls is None:
        ls = []

    if len(cls.__bases__) > 0:
        for k in cls.__bases__:
            ls.append(k)
            _rbase(k, ls)

    return ls


def _is_valid(key: str, value) -> bool:
    """
    Value is not a method and key does not start with an underscore.
    :param key: The name of the field
    :param value: The value of the field
    :return: Boolean.
    """
    return not key.startswith('_') and \
           not callable(value) and \
           not isinstance(value, classmethod) and \
           not isinstance(value, staticmethod) and \
           not isinstance(value, property)


class Deserializable(metaclass=DeserializableMeta):
    """
    Base class for all automagically deserializing classes.
    """

    @classmethod
    def get_attrs(cls) -> Dict[str, Rule]:
        """
        Returns a list of all type rules for the given class.

        :return: a dict from property to type rule.
        """
        fields = {}
        defaults = {}
        rl = list(reversed(_rbase(cls)))
        rl.append(cls)
        for c in rl:
            for k in c.__dict__:
                if isinstance(c.__dict__[k], property):
                    fields[k] = Rule(Any)
                elif _is_valid(k, c.__dict__[k]):
                    defaults[k] = c.__dict__[k]
                    fields[k] = Rule(Optional[type(defaults[k])],
                                     default=defaults[k])

        for k in cls.__annotations__:
            if k in defaults and not _is_valid(k, defaults[k]):
                continue

            rule = Rule.to_rule(cls.__annotations__[k])
            if k in defaults:
                rule.default = defaults[k]
            fields[k] = rule

        return fields


def get_deserialization_classes(t, d, try_all=True) -> List[type]:
    """
    Find all candidates that are a (sub)type of t, matching d.

    :param t: The type to match from.
    :param d: The dict to match onto.
    :param try_all: Whether to support automatic discrimination.
    :return: an ordered list of candidate classes to deserialize into.
    """
    candidates = []
    for sc in t.__subclasses__():
        if hasattr(sc, '_discriminators'):
            # noinspection PyProtectedMember
            for discriminator in sc._discriminators:
                if not discriminator.check(d):
                    # Invalid
                    break
            else:
                # All were valid
                try:
                    candidates.extend(
                        get_deserialization_classes(sc, t, try_all))
                except TypeError as e:
                    if not try_all:
                        raise e
    if not getattr(t, '_abstract', True):
        candidates.append(t)

    return candidates


def deserialize(rule: Rule, data, try_all: bool = True, key: str = '[root]'):
    """
    Converts the passed in data into a type that is compatible with rule.

    :param rule:
    :param data:
    :param try_all: Whether to attempt other subtypes when a TypeError has
        occurred. This is useful when automatically deriving discriminators.
    :param key: Used for exceptions and error reporting. Preferrably the full
        path to the current value.
    :return: An instance matching Rule.
    """
    # Deserialize primitives
    try:
        return rule.validate(key, data)
    except TypeError:
        pass

    # Deserialize type unions
    if type(rule.type) is type(Union):
        for arg in rule.type.__args__:
            try:
                v = deserialize(Rule(arg), data, try_all, key)
                if v is None:
                    v = rule.default
                return v
            except TypeError:
                pass
        raise TypeError('{} did not match any of {} for key <{}>.'
                        .format(type(data).__name__, rule.type.__args__, key))

    # Deserialize dicts
    if type(rule.type) is type(Dict) and getattr(rule.type, "__origin__", None) == Dict:
        if len(rule.type.__args__) != 2:
            raise TypeError('Cannot handle dicts with 0, 1 or more than two '
                            'type arguments '
                            'at <{}>'.format(key))

        if isinstance(data, dict):
            data: dict

            result = {}
            for k, v in data.items():
                dict_key = deserialize(
                    Rule(rule.type.__args__[0]),
                    k,
                    try_all,
                    '{}.{}'.format(key, k))

                dict_value = deserialize(
                    Rule(rule.type.__args__[1]),
                    v,
                    try_all,
                    '{}.{}'.format(key, dict_key))

                result[dict_key] = dict_value
            return result

    # Deserialize lists
    if type(rule.type) is type(List) and getattr(rule.type, "__origin__", None) == List:
        if len(rule.type.__args__) != 1:
            raise TypeError(
                'Cannot handle list with 0 or more than 1 type arguments '
                'at <{}>.'.format(key))
        if type(data) != list:
            raise TypeError(
                'Cannot deserialize {} into list '
                'at <{}>.'.format(type(data).__name__, key))
        data: list
        t = rule.type.__args__[0]
        result = []
        for i, v in enumerate(data):
            result.append(deserialize(
                Rule(t),
                v,
                try_all,
                '{}.{}'.format(key, i)
            ))
        return result

    # Deserialize tuples
    if type(rule.type) is type(Tuple):
        if not isinstance(data, list):
            raise TypeError(
                'Expected a list to convert to tuple, but got {}'
                'at <{}>'.format(_type_to_str(type(data)), key))

        data: list
        if len(rule.type.__args__) != len(data):
            raise TypeError(
                'Expected a list of {} elements, but got {} elements '
                'at <{}>.'.format(len(rule.type.__args__), len(data), key))

        return tuple(deserialize(Rule(v[0]), v[1], key="{}.{}".format(key, k))
                     for k, v in enumerate(zip(rule.type.__args__, data)))

    # Deserialize classes
    if issubclass(rule.type, Deserializable):
        if not isinstance(data, dict):
            raise TypeError(
                'Cannot deserialize non-dict into class instance '
                'at <>.'.format(key))

        data: dict

        classes = get_deserialization_classes(rule.type, data,
                                              try_all)

        cause = None

        for cls in classes:
            try:
                # Instantiate cls with parameters generated by
                # the list comprehension.
                # It loops through all defined attributes, and
                # defines it by recursively calling deserialize on
                # each of those attributes with the values found in
                # either data, or by using a default.
                return cls(**{k: deserialize(
                    r,
                    data[k] if k in data else r.default,
                    try_all,
                    key='{}.{}'.format(key, k)
                ) for k, r in cls.get_attrs().items()})
            except TypeError as e:
                if not try_all:
                    raise e
                else:
                    cause = e
            except ValueError as e:
                if not try_all:
                    raise e
                else:
                    cause = e

        raise TypeError('Unable to find matching non-abstract (sub)type of '
                        '{} with key <{}>. '
                        'Reason: {}'.format(rule.error_string(), key, cause))

    raise TypeError('Expected something of type {}, but got type {} '
                    'at <{}>.'.format(rule.error_string(), type(data).__name__,
                                      key))
