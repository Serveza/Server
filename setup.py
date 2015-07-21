#!/usr/bin/env python
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    REQUIREMENTS = [line.strip() for line in f]

ENTRY_POINTS = {
    'console_scripts': [
        'serveza-server = serveza.scripts.run:entry',
        'serveza-resetdb = serveza.scripts.resetdb:main',
    ],
}

setup(
    name='serveza-server',
    version='0.1',

    packages=find_packages(),
    install_requires=REQUIREMENTS,

    entry_points=ENTRY_POINTS,
)
