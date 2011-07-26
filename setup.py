#!/usr/bin/env python

import os
import sys

from distutils.core import setup

__dir__ = os.path.realpath(os.path.dirname(__file__))

sys.path.insert(0, __dir__)
try:
    import nest
finally:
    del sys.path[0]

classifiers = """
Development Status :: 3 - Alpha
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Utilities
"""

__doc__ = """Notation for Expressing Structured Text (NEST) is a markup language
with the same semantics as XML but is designed to be more readable
and easier to write by hand.
"""

setup(
	name = 'nest',
	version = nest.__version__,
	description = nest.__doc__.split('\n')[1],
	long_description = __doc__,
	author = 'Anh Hai Trinh',
	author_email = 'moc.liamg@hnirt.iah.hna:otliam'[::-1],
	keywords='html xml structured-text',
	url = 'http://github.com/aht/nest',
	platforms=['any'],
	classifiers=filter(None, classifiers.split("\n")),
	py_modules = ['nest'],
	scripts=['script/n2x', 'script/x2n'],
)
