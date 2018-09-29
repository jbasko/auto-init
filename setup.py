#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='auto-init',
    version='0.0.1',
    packages=['auto_init'],
    url='https://github.com/jbasko/auto-init',
    license='MIT',
    author='Jazeps Basko',
    author_email='jazeps.basko@gmail.com',
    maintainer='Jazeps Basko',
    maintainer_email='jazeps.basko@gmail.com',
    description='Dataclasses reinvented, dependency injection, Python 3.7+',
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
)
