import setuptools
import dict_deserializer

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=dict_deserializer.name,
    version=dict_deserializer.version,
    author=dict_deserializer.author.name,
    author_email=dict_deserializer.author.email,
    description=dict_deserializer.description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.iapc.utwente.nl/rkleef/serializer_utils",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Development Status :: 4 - Beta",
    ],
)
