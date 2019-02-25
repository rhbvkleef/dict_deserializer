# Dictionary deserializer
[![ReadTheDocs](https://readthedocs.org/projects/dict-deserializer/badge/?version=latest&style=flat)](https://dict-deserializer.rtfd.io)
[![GitHub issues](https://img.shields.io/github/issues/rhbvkleef/dict_deserializer.svg)](https://github.com/rhbvkleef/dict_deserializer)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/rhbvkleef/dict_deserializer.svg)](https://github.com/rhbvkleef/dict_deserializer)
[![PyPI](https://img.shields.io/pypi/v/dictionary-deserializer.svg)](https://pypi.org/project/Dictionary-deserializer/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dictionary-deserializer.svg)](https://pypi.org/project/Dictionary-deserializer/)
[![GitHub](https://img.shields.io/github/license/rhbvkleef/dict_deserializer.svg)](https://opensource.org/licenses/BSD-3-Clause)

Dictionary deserializer is a project built to convert dictionaries into
composite classes in an intuitive way. Special attention was also paid
to being friendly to static type-checkers and IDE autocompletes.

It is expected that this library is used together with a JSON-to-dict
deserializer like `json.loads`.

## Installation

In order to use it, simply add the dependency `dictionary-deserializer` to your
requirements file:

### Pipenv

```bash
pipenv install dictionary-deserializer
```

### Pip

```bash
pip install dictionary-deserializer
pip freeze > requirements.txt
```

## Design

This project was originally meant as a proof of concept, to be used to find
other projects that would be able to replace this, with the required feature
set. That project was not found, and therefore, this project was expanded.

### Requirements

* Use type hints for type validation
* Allow polymorphism
    * Through `typing.Union`s
    * Through subclassing
* Support a large part of the `typing` module's types
* Allow validations on values
* Be able to validate and deserialize _any_ compliant JSON structure
* Be compatible with static type checkers and IDE hinting
* Have a small impact on existing code starting to use this library

## Examples

None of this code is actually useful if you don't understand how to use it. It
is very simple. Here are some examples:

### Specifying a structure

```python
from typing import Optional

from dict_deserializer.deserializer import Deserializable

class User(Deserializable):
    email: str                  # Type must be a string
    username: str               # Type must be a string
    password: Optional[str]     # Type must either be a string or a None
```

### Deserialization

```python
from dict_deserializer.deserializer import deserialize, Rule

# Successful
deserialize(Rule(User), {
    'email': 'pypi@rolfvankleef.nl',
    'username': 'rkleef',
})

# Fails because optional type is wrong
deserialize(Rule(User), {
    'email': 'pypi@rolfvankleef.nl',
    'username': 'rkleef',
    'password': 9.78,
})
```

### Polymorphic structures
```python
from typing import Optional, Any, List

from dict_deserializer.deserializer import Deserializable
from dict_deserializer.annotations import abstract

@abstract
class DirectoryObject(Deserializable):
    name: str
    meta: Any

class User(DirectoryObject):
    full_name: str
    first_name: Optional[str]

class Group(DirectoryObject):
    members: List[DirectoryObject]
```

If you deserialize into `Rule(DirectoryObject)`, the matching class will
automatically be selected. If none of the subclasses match, an error is thrown
since the DirectoryObject is declared abstract.

If you want to discriminate not by field names or types, but by their values,
one can choose to define a `@discriminator` annotation.

### Value validations

The syntax for validating the value of a key is currently a bit weird. It is
incompatible with existing syntax for defaults, but the type syntax is the same.

Example:

```python
from typing import Optional

from dict_deserializer.deserializer import Deserializable
from dict_deserializer.annotations import validated

class Test(Deserializable):
    name: Optional[str]
    
    @validated(default='Unknown')
    def name(self, value):
        if len(value) > 20:
            raise TypeError('Name may not be longer than 20 characters.')

```

## Limitations

This library uses the `typing` module extensively. It does, however, only
support some of its types. This is a list of verified composite types:

* `Union` (Including `Optional`)
* `Dict`
* `List`
* `Tuple`
* `Any`
* `dict_deserializer.deserializer.Deserializable`
* `dict`
* `list`

It supports these types as terminal types:

* `int`
* `float`
* `str`
* `NoneType`
* `bool`

## Planned features

* NamedTuples
    * The anonymous namedtuple and the class-namedtuples with (optionally) type annotations.
* Dataclasses
* A way to allow deserializing into a class not extending `Deserializable`
* Enums
* Sets
    * From lists
