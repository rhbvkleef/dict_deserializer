import setuptools
import dict_deserializer

from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)

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
    url="https://github.com/rhbvkleef/dict_deserializer",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Development Status :: 4 - Beta",
    ],
)
