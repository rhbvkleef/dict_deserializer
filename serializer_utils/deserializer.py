from typing import Optional

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


def deserialize(t, d, try_all=False):
    for sc in t.__subclasses__():
        if hasattr(sc, '_discriminators'):
            for discriminator in sc._discriminators:
                if not discriminator.check(d):
                    break
            else:
                try:
                    return deserialize(sc, d)
                except TypeError as e:
                    if not try_all:
                        raise e

    if hasattr(t, '_abstract') and t._abstract:
        raise TypeError('Cannot deserialize into {}: is abstract.'.format(t.__name__))

    instance = t()
    for k, rule in t.get_attrs().items():
        v = rule.validate(k, d[k] if k in d else None)
        setattr(instance, k, v)

    return instance
