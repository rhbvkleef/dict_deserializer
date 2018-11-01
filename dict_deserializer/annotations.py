from abc import ABC, abstractmethod


class Discriminator(ABC):
    @abstractmethod
    def check(self, d: dict):
        return


class KeyValueDiscriminator:
    def __init__(self, key, value, has_value=True):
        self.key = key
        self.value = value
        self.has_value = has_value

    def __repr__(self):
        if self.has_value:
            return 'KeyValueDiscriminator(key={}, value={})'.format(self.key, self.value)
        return 'KeyValueDiscriminator(key={})'.format(self.key)

    def check(self, d: dict):
        if self.key not in d:
            return False
        if self.has_value:
            return d[self.key] == self.value
        return True


class FunctionDiscriminator:
    def __init__(self, matcher):
        self.matcher = matcher

    def check(self, d: dict):
        return self.matcher(d)


sentinel = object()


def discriminate(key=None, value=sentinel, matcher=None):
    def _inner(cls):
        dc = None
        if key is not None:
            dc = KeyValueDiscriminator(key, value, value is not sentinel)
        elif matcher is not None:
            dc = FunctionDiscriminator(matcher)

        if dc is None:
            return cls

        cls._discriminators.append(dc)

        return cls
    return _inner


def abstract(cls):
    cls._abstract = True
    return cls