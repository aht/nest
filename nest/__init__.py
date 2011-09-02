"""
Parsers for NEST (Notation for Expressing Structrured Text).

Functions:
  etree -- parse a NEST string to an ElementTree
  xml -- parse a NEST string to a XML string
  xhtml -- parse a NEST string to a XML string with a XHTML 1.0 Strict prolog
"""

__version__ = '0.0.2'

from lexer import LexError
from parser import xml, xhtml, etree, YaccError