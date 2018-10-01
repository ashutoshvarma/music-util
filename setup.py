import io
import os

from setuptools import find_packages, setup

#Package metadata
NAME = 'musicutil'
DESCRIPTION = "Python library for searching and downloading songs from various source."
URL = "https://github.com/ashutoshvarma/music-util"
EMAIL = "ashutoshvarma11@live.com"
AUTHOR = "Ashutosh Varma"
REQUIRES_PYTHON = '>=3.6.0'
VERSION = "0.1.3-alpha3"

# What packages are required for this module to be executed?
REQUIRED = [
    'beautifulsoup4','requests', 'html5lib', 'spotipy'
]

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests',)),
   
    install_requires=REQUIRED,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)