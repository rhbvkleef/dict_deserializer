from typing import Optional, Union, List, Tuple, Dict

from typeguard import check_type


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
        return "Rule(type={}, default={})".format(self.type, self.default)

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


class BaseMeta(type):
    """
    Metaclass for all Deserializable
    """
    def __new__(
            mcs: 'BaseMeta', name: str, bases: Tuple[type], namespace: dict)\
            -> type:

        namespace['_discriminators'] = []
        namespace['_abstract'] = False

        cls = type.__new__(mcs, name, bases, namespace)

        for b in bases:
            if b is object:
                continue

            if hasattr(b, '__annotations__'):
                annotations = dict(b.__annotations__)
                annotations.update(cls.__annotations__)
                cls.__annotations__ = annotations

        return cls


def rbase(cls: type, ls: List[type]=None) -> List[type]:
    """
    Get all base classes for cls.
    """
    if ls is None:
        ls = []

    if len(cls.__bases__) > 0:
        for k in cls.__bases__:
            ls.append(k)
            rbase(k, ls)

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
           not isinstance(value, classmethod) and\
           not isinstance(value, staticmethod) and \
           not isinstance(value, property)


class Deserializable(metaclass=BaseMeta):
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
        rl = list(reversed(rbase(cls)))
        rl.append(cls)
        for c in rl:
            for k in c.__dict__:
                if _is_valid(k, c.__dict__[k]):
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
    :return:
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


def deserialize(rule: Rule, data, try_all: bool=True, key: str='$'):
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
    # In case of primitive types, attempt to assign.
    try:
        return rule.validate(key, data)
    except TypeError:
        pass

    if type(rule.type) is type(Union):
        for arg in rule.type.__args__:
            try:
                v = deserialize(Rule(arg), data, try_all, key)
                if v is None:
                    v = rule.default
                return v
            except TypeError:
                pass
        raise TypeError('{} did not match any of {} for key {}.'
                        .format(type(data), rule.type.__args__, key))

    if type(rule.type) is type(List):
        if len(rule.type.__args__) != 1:
            raise TypeError(
                'Cannot handle list with 0 or more than 1 type arguments.')
        if type(data) != list:
            raise TypeError(
                'Cannot deserialize non-list into list.')
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

    if issubclass(rule.type, Deserializable):
        if not isinstance(data, dict):
            raise TypeError('Cannot deserialize non-dict into class.')

        classes = get_deserialization_classes(rule.type, data, try_all)

        for cls in classes:
            try:
                instance = cls()
                for k, r in cls.get_attrs().items():
                    v = deserialize(
                        r,
                        data[k] if k in data else r.default,
                        try_all,
                        key='{}.{}'.format(key, k)
                    )
                    setattr(instance, k, v)

                return instance
            except TypeError as e:
                if not try_all:
                    raise e

        raise TypeError('Unable to find matching non-abstract (sub)type of '
                        '{} with key {}.'.format(rule.type, key))

    raise TypeError('Unable to find a deserialization candidate for '
                    '{} with key {}.'.format(rule, key))
