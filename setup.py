#!/bin/python
from setuptools import setup, find_packages

setup(
    name='ABNTMount',
    author="Gab0",
    version='0.6',
    packages=find_packages(),
    license='GPLv2',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts':
        ["ABNTM=ABNTMount.ABNTMount:main"]
        }
)
