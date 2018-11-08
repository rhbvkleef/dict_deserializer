from typing import Optional, Union, List

from typeguard import check_type


class Rule:
    @staticmethod
    def to_rule(tpe):
        if isinstance(tpe, Rule):
            return tpe
        return Rule(tpe)

    def __init__(self, type, default=None):
        self.type = type
        self.default = default

    def __repr__(self):
        return "Rule(type={}, default={})".format(self.type, self.default)

    def validate(self, key, value):
        check_type(key, value, self.type)
        if value is None:
            value = self.default

        return value


class BaseMeta(type):
    def __new__(mcs, name, bases, namespace):
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


def rbase(cls, ls=None):
    if ls is None:
        ls = []

    if len(cls.__bases__) > 0:
        for k in cls.__bases__:
            ls.append(k)
            rbase(k, ls)

    return ls


def _is_valid(key: str, value):
    return not key.startswith('_') and not callable(value) and not isinstance(value, classmethod) and\
           not isinstance(value, staticmethod) and not isinstance(value, property)


class Deserializable(metaclass=BaseMeta):
    @classmethod
    def get_attrs(cls):
        fields = {}
        defaults = {}
        rl = list(reversed(rbase(cls)))
        rl.append(cls)
        for c in rl:
            for k in c.__dict__:
                if _is_valid(k, c.__dict__[k]):
                    defaults[k] = c.__dict__[k]
                    fields[k] = Rule(Optional[type(defaults[k])], default=defaults[k])

        for k in cls.__annotations__:
            if k in defaults and not _is_valid(k, defaults[k]):
                continue

            rule = Rule.to_rule(cls.__annotations__[k])
            if k in defaults:
                rule.default = defaults[k]
            fields[k] = rule

        return fields


def get_deserialization_classes(t, d, try_all=True) -> List[type]:
    candidates = []
    for sc in t.__subclasses__():
        if hasattr(sc, '_discriminators'):
            for discriminator in sc._discriminators:
                if not discriminator.check(d):
                    # Invalid
                    break
            else:
                # All were valid
                try:
                    candidates.extend(get_deserialization_classes(sc, t, try_all))
                except TypeError as e:
                    if not try_all:
                        raise e
    if not getattr(t, '_abstract', True):
        candidates.append(t)

    return candidates


def deserialize(rule: Rule, data, try_all=True, key='$'):
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
        raise TypeError('{} did not match any of {} for key {}.'.format(type(data), rule.type.__args__, key))

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
            result.append(deserialize(Rule(t), v, try_all, '{}.{}'.format(key, i)))
        return result

    if issubclass(rule.type, Deserializable):
        if not isinstance(data, dict):
            raise TypeError('Cannot deserialize non-dict into class.')

        classes = get_deserialization_classes(rule.type, data, try_all)

        for cls in classes:
            try:
                instance = cls()
                for k, r in cls.get_attrs().items():
                    v = deserialize(r, data[k] if k in data else r.default, try_all, key='{}.{}'.format(key, k))
                    setattr(instance, k, v)

                return instance
            except TypeError as e:
                if not try_all:
                    raise e

        raise TypeError('Unable to find matching non-abstract (sub)type of {} with key {}.'.format(rule.type, key))

    raise TypeError('Unable to find a deserialization candidate for {} with key {}.'.format(rule, key))