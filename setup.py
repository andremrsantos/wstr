#! /usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='wstr',
    version='0.0.1',
    license='MIT',
    description='Web interface for running STRUCTURE',
    author='André M. Ribeiro-dos-Santos',
    author_email='andremrsantos@gmail.com',
    packages=find_packages("src"),
    include_package_data=True,
    package_dir={"": "src"},
    install_requires=[
        'Flask',
        'sortedcontainers',
        'uWSGI',
        'peewee']
)
