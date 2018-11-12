from abc import ABC, abstractmethod


class Discriminator(ABC):
    """
    Base class for all discriminator.
    """
    @abstractmethod
    def check(self, d: dict):
        """
        Returns true or false, depending on whether the discriminator
        matches the provided class.

        :param d: the data
        :return: True when this class is valid, False otherwise.
        """
        return


class KeyValueDiscriminator(Discriminator):
    """
    Discriminates on key and optionally a value.
    """
    def __init__(self, key, value, has_value=True):
        self.key = key
        self.value = value
        self.has_value = has_value

    def __repr__(self):
        if self.has_value:
            return 'KeyValueDiscriminator(key={}, value={})'\
                .format(self.key, self.value)
        return 'KeyValueDiscriminator(key={})'.format(self.key)

    def check(self, d: dict):
        if self.key not in d:
            return False
        if self.has_value:
            return d[self.key] == self.value
        return True


class FunctionDiscriminator(Discriminator):
    """
    Discriminates according to a custom function.
    """
    def __init__(self, matcher):
        self.matcher = matcher

    def check(self, d: dict):
        return self.matcher(d)


_sentinel = object()


def discriminate(key=None, value=_sentinel, matcher=None):
    """
    Class level annotation to specify requirements of the raw datastructure
    in order to be allowed to deserialize into this class (or its subclasses).

    :param key: The key to discriminate against
    :param value: (Optionally) the value that the property designated by ``key``
        should hold
    :param matcher: (Optionally) a custom function to discriminate with.
    :return: A function that should wrap the class to be discriminated.
    """
    def _inner(cls):
        dc = None
        if key is not None:
            dc = KeyValueDiscriminator(key, value, value is not _sentinel)
        elif matcher is not None:
            dc = FunctionDiscriminator(matcher)

        if dc is None:
            return cls

        cls._discriminators.append(dc)

        return cls
    return _inner


def abstract(cls):
    """
    Declares that this class cannot be instanced. Only subclasses that are
    not declared abstract could be instanced.

    This is equivalent to setting the class property ``_abstract=True``.

    :param cls: The class that should be abstract
    :return: The same class
    """
    cls._abstract = True
    return cls


def validated(default=None):
    """
    Used to decorate a validator function. Can be used if one would want to
    constrain the value of a property. Of course, ``@property`` may be used as
    well. Throw a TypeError when validation fails.

    :param default: The default (initial) value of this property
    :return: the wrapper function.
    """
    def _wrapper(fn):
        # List is used because of stupid python scoping rules.
        iv = [default]

        def _getter(_):
            return iv[0]

        def _setter(self, val):
            fn(self, val)
            iv[0] = val

        return property(fget=_getter, fset=_setter)
    return _wrapper
