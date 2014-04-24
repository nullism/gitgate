#!/usr/bin/env python
"""
Copyright (c) 2012, Aaron Meier
All rights reserved.

See LICENSE for more information.
"""
from distutils.core import setup
import os

from gitgate import __version__

setup(name='gitgate',
    version = __version__,
    description = 'Dead simple gatekeeping code review for Git',
    long_description = (
        "GitGate provides a GUI frontend (via Flask) for pre-merge code review."
    ),
    author = 'Aaron Meier',
    author_email = 'webgovernor@gmail.com',
    packages = ['gitgate'],
    package_dir={'gitgate':'gitgate'},
    package_data={'gitgate':['templates/*', 'static/bootstrap3/*/*', 'static/jquery/*.js']},
    scripts=['gitgate/scripts/gitgate'],
    url = 'http://gitgate.nullism.com',
    install_requires = ['peewee>=2.0', 'flask>=0.9', 'argparse>=1'],
    license = 'MIT',
    provides = 'gitgate'
)
