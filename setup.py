#!/bin/python
from setuptools import setup

setup(
    name='ABNTMount',
    author="Gab0",
    version='0.4',
    packages=['ABNTMount'],
    license='GPLv2',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts':
        ["ABNTM=ABNTMount.ABNTMount:main"]
        }
)
