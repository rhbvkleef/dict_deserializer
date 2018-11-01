# Dictionary Deserializer

Dictionary deserializer is a project built to convert dictionaries into
composite classes in an intuitive way. Special attention was also paid
to being friendly to static type-checkers and IDE autocompletes.

## Limitations

This library uses the `typing` module extensively. It does, however, only
support some of its types. This is a list of verified composite types:

* `Union` (Including `Optional`)
* `List`
* `Any`

It supports these types as terminal types:

* `int`
* `float`
* `str`
* `NoneType`
* `bool`
