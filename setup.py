#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name="wallbasefs",
      version="0.1a",
      provides=['wallbasefs'],
      description="A Fuse Filesystem that mounts your wallbase.cc favorites",
      author="Pierre Geier 'epicmuffin'",
      author_email="muffin@tastyespresso.de",
      url="https://github.com/bloodywing",
      packages=["wallbasefs"],
      install_requires=["requests", "fuse"])
