from collections import namedtuple

name = 'Dictionary deserializer'
version = '0.0.6'
description = "Dictionary deserializer is a package that aides in the " \
              "deserializing of JSON (or other structures) that are " \
              "converted to dicts, into composite classes."

author = namedtuple('Author', ['name', 'email'])(
    name='Rolf van Kleef',
    email='pypi@rolfvankleef.nl'
)
