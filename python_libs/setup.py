import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "ansible-barn",
    version = "0.0.1",
    author = "Sander Descamps",
    author_email = "sander_descamps@hotmail.com",
    description = ("An dynamic inventory which can easily be integrated in custom on-premise tools"),
    license = "GNU General Public License v3.0",
    keywords = "Ansible Barn inventory dynamic",
    url = "https://github.com/sanderdescamps/ansible-barn",
    packages=['ansible_barn', 'tests'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)