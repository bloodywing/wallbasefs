#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='wallbasefs',
      version='0.2.1',
      provides=['wallbasefs'],
      description='A Fuse Filesystem that mounts your wallbase.cc favorites',
      author='Pierre Geier "epicmuffin"',
      author_email='muffin@tastyespresso.de',
      url='https://github.com/bloodywing',
      packages=['wallbasefs'],
      keywords='filesystem http web',
      entry_points={
      'console_scripts': [
          'wallbasefs = wallbasefs.wallbasefs:main',
      ]
      },
      dependency_links=[
          'https://github.com/bloodywing/pywallbase/zipball/master#egg=wallbase-0.2.1', 'https://github.com/terencehonles/fusepy/zipball/master#egg=fusepy-2.0.2'],
      license='Emailware',
      install_requires=['configobj', 'wallbase', 'fusepy'],
      classifiers='''\
Development Status :: 4 - Beta
Intended Audience :: End Users/Desktop
License :: Public Domain
Operating System :: POSIX
Programming Language :: Python :: 2.7
Topic :: System :: Filesystems
      '''.splitlines(),)
