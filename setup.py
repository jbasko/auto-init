#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="auto-init",
    version="0.0.5",  # also in __init__.py
    url="https://github.com/jbasko/auto-init",
    license="MIT",
    author="Jazeps Basko",
    author_email="jazeps.basko@gmail.com",
    maintainer="Jazeps Basko",
    maintainer_email="jazeps.basko@gmail.com",
    description="Dependency injection thanks to type hints in Python 3.6+",
    keywords="dependency injection type hinting typing",
    long_description=read("README.rst"),
    packages=["auto_init"],
    python_requires=">=3.6.0",
    extras_require={
        ':python_version=="3.6"': [
            "dataclasses",
            "contextvars",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
    ],
)
