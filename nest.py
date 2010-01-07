#!/usr/bin/env python

"""
Parsers for NEST (Notation for Expressing Structrured Text)

Functions:
  etree -- parse a NEST string to an ElementTree
  xml -- parse a NEST string to a XML string
  xhtml -- parse a NEST string to a XML string with a XHTML 1.0 Strict prolog
"""

__version__ = '0.0.1'

import re
import lex, yacc

from xml.sax.saxutils import escape, quoteattr

try:
	from xml.etree.cElementTree import ElementTree, Element, Comment
except ImportError:
	from xml.etree.ElementTree import ElementTree, Element, Comment


#________________________________________________________________________
# Lexer

class LexError(Exception):
	def __init__(self, msg, lineno):
		self.msg, self.lineno = msg, lineno
	def __str__(self):
		return '%s at line %s' % (self.msg, self.lineno)

class Lexer(object):
	states = (
		('attr','exclusive'),
		('body', 'exclusive'),
		('bracket','exclusive'),
		('oneword', 'exclusive'),
		('oneline','exclusive'),
		('indent','exclusive'),
	)

	tokens = ("TAG TAG_ATTR COMMENT ATTR_EQ VALUE " +
			"START1 START2 START3 START4 START5 END " + 
			"CDATA ESCAPED WS").split()

	# We keep track of indentation levels using a stack where each
	# element is a tuple of number of tabs, number of spaces.

	# We wrap around lex to permit programmatic emission of extra tokens
	# which is necessary to handle NEST's shorthand styles and indentation.
	# This is implemented using a stack to keep track of the hand-emitted tokens.
	# A "real" token from lex is returned only when this stack is empty.

	def __init__(self, **kwargs):
		self.lexer = lex.lex(object=self, **kwargs)
		self.lvl_stack = [(0, 0)]
		self.emitted = []

	def input(self, s):
		self.lexer.input(s)

	def emit(self, type, value='\n'):
		t = lex.LexToken()
		t.type = type
		t.value = value
		t.lineno = self.lexer.lineno
		t.lexpos = self.lexer.lexpos
		self.emitted.append(t)

	def token(self):
		if self.emitted:
			return self.emitted.pop()
		else:
			return self.lexer.token()

	def __iter__(self):
		def nexttok():
			while 1:
				t = self.token()
				if t is None:
					raise StopIteration
				else:
					yield t
		return nexttok()

	# check_endings should be called after recognizing a "real" END token containing a newline.
	# The caller should determine the indentation level after that END token
	# then pass it to check_endings, which will inspect the current lexer state
	# and the indentation level stack to throw extra END tokens that are pending, if any.

	def check_endings(self, tabs, spaces):
		while self.lexer.lexstate in ('oneword', 'oneline'):
			self.emit('END')
			self.lexer.pop_state()
		if (tabs <= self.lvl_stack[-1][0]) and (spaces <= self.lvl_stack[-1][1]):
			try:
				idx = self.lvl_stack.index((tabs, spaces))
			except ValueError:
				raise LexError("dedenting to a bad indentation level", self.lexer.lineno)
			for _ in range(idx, len(self.lvl_stack)-1):
				self.emit('END')
				self.lvl_stack.pop()
				self.lexer.pop_state()
				while self.lexer.lexstate in ('oneword', 'oneline'):
					self.emit('END')
					self.lexer.pop_state()

	t_INITIAL_CDATA = r'[^\\]+'

	def t_ANY_ESCAPED(self, t):
		r'\\[\\<> ]'
		t.value = t.value[1]
		return t

	def t_ANY_COMMENT(self, t):
		r'\\(--+|==+)'
		t.lexer.push_state('body')
		t.value = ''
		return t

	def t_ANY_TAG_ATTR(self, t):
		r'\\[^ \t\r\n\[\]<>:]+[ \t\r\n]*\['
		t.lexer.push_state('attr')
		t.lexer.lineno += t.value.count('\n')
		t.value = t.value[1:-1]
		return t

	def t_ANY_TAG(self, t):
		r'\\[^ \t\r\n\[\]<>:]+'
		t.lexer.push_state('body')
		t.value = t.value[1:]
		return t

	def t_ANY_error(self, t):
		raise LexError("illegal character '%s'" % t.value[0], t.lexer.lineno)

	#________________
	# state: attr

	t_attr_ignore_WS = r'[ \t\r\n]+'

	def t_attr_ATTR_EQ(self, t):
		r'[^ \=\]]+[ \t\n\r]*='
		t.value = t.value[:-1].rstrip()
		return t

	def t_attr_VALUE(self, t):
		r'(\'[^\']*\')|("[^"]*")|[^= \\\t\r\n\]]+'
		if t.value[0] == t.value[-1] and t.value[0] in '\'"':
			t.value = t.value[1:-1]
		return t

	def t_attr_END_ATTR(self, t):
		r'\]'
		t.lexer.pop_state()
		t.lexer.push_state('body')
		pass

	#________________
	# state: body

	def t_body_START1(self, t):
		r':[\r\n]+[ \t]+'
		t.lexer.pop_state()
		t.lexer.push_state('indent')
		tabs, spaces = t.value.count('\t'), t.value.count(' ')

		# We treat tabs and spaces orthogonally.  A new indentation level -- a tuple
		# of (tabs, spaces) -- is accepted only when one component increases
		# while the other stay the same. This way, it will be easier to recognize
		# indentation error when tabs and spaces are accidentally mixed.

		if ((tabs == self.lvl_stack[-1][0]) and (spaces > self.lvl_stack[-1][1])) \
		or ((tabs > self.lvl_stack[-1][0]) and (spaces == self.lvl_stack[-1][1])):
			## new indentation level
			self.lvl_stack.append((tabs, spaces))
		elif (tabs <= self.lvl_stack[-1][0]) and (spaces <= self.lvl_stack[-1][1]):
			raise LexError("an element's body must be more indented its start tag", t.lexer.lineno)
		else:
			raise LexError("indentation not comparable to the previous level", t.lexer.lineno)

		t.lexer.lineno += t.value.count('\n')
		t.value = t.value[1:]
		return t

	def t_body_START2(self, t):
		r':[ \t]*'
		t.lexer.pop_state()
		t.lexer.push_state('oneline')
		t.value = ''
		return t

	def t_body_START3(self, t):
		r'[ \t\r\n]*<'
		t.lexer.pop_state()
		t.lexer.push_state('bracket')
		t.lexer.lineno += t.value.count('\n')
		t.value = t.value[:-1]
		return t

	def t_body_START4(self, t):
		r'[ \t]+'
		t.lexer.pop_state()
		t.lexer.push_state('oneword')
		t.value = ''
		return t

	# oneword style with empty body
	def t_body_START5(self, t):
		r'[\r\n]+[ \t]*'
		t.lexer.pop_state()
		self.emit('END')
		self.check_endings(t.value.count('\t'), t.value.count(' '))
		t.lexer.lineno += t.value.count('\n')
		t.value = ''
		return t

	#________________
	# state: oneword

	def t_oneword_CDATA(self, t):
		r'[^\\ \t\r\n]+'
		return t

	def t_oneword_END(self, t):
		r'[ \t\r\n]+'
		t.lexer.pop_state()
		while t.lexer.lexstate == 'oneword':
			self.emit('END')
			t.lexer.pop_state()
		nl = t.value.count('\n')
		if nl:
			indent = re.match(r'.*[\r\n]+([ \t]*)', t.value).group(1)
			self.check_endings(indent.count('\t'), indent.count(' '))
		t.lexer.lineno += nl
		t.value = ''
		return t

	#________________
	# state: oneline

	def t_oneline_CDATA(self, t):
		r'[^\\\r\n]+'
		return t

	def t_oneline_END(self, t):
		r'[\r\n]+[\t]*'
		t.lexer.pop_state()
		self.check_endings(t.value.count('\t'), t.value.count(' '))
		t.lexer.lineno += t.value.count('\n')
		return t

	#________________
	# state: bracket

	def t_bracket_CDATA(self, t):
		r'[^\\>]+'
		t.lexer.lineno += t.value.count('\n')
		return t

	def t_bracket_END(self, t):
		r'>'
		t.lexer.pop_state()
		t.value = ''
		return t

	#________________
	# state: indent

	def t_indent_CDATA(self, t):
		r'[^\\\r\n]+'
		t.value += '\n' + '\t' * self.lvl_stack[-1][0] + ' ' * self.lvl_stack[-1][1]
		return t

	def t_indent_END(self, t):
		r'[\r\n]+[\t ]*'
		tabs, spaces = t.value.count('\t'), t.value.count(' ')
		if (tabs, spaces) == self.lvl_stack[-1]:
			pass
		elif (tabs > self.lvl_stack[-1][0]) or (spaces > self.lvl_stack[-1][1]):
			raise LexError("indentation not comparable the previous level", t.lexer.lineno)
		else:
			self.lvl_stack.pop()
			t.lexer.pop_state()
			self.check_endings(tabs, spaces)
			return t


# Use this to regenerate the table
# lexer = Lexer(outputdir='table', lextab='lextab', optimize=1)

from table import lextab

lexer = Lexer(lextab=lextab, optimize=1)


#________________________________________________________________________
# Parsers

class YaccError(Exception):
	def __init__(self, msg, lineno):
		self.msg, self.lineno = msg, lineno
	def __str__(self):
		return '%s at line %s' % (self.msg, self.lineno)

class XMLBuilder(object):
	def __init__(self, lexer=None, **kwargs):
		if lexer:
			self.lexer = lexer
		else:
			self.lexer = Lexer()
		self.tokens = self.lexer.tokens
		self.parser = yacc.yacc(module=self, **kwargs)

	def parse(self, input, prolog='', **kwargs):
		"""Parse a NEST string to XML with an optional prolog"""
		return prolog + self.parser.parse(input, lexer=self.lexer, **kwargs)

	def p_content11(self, p):
		'''content : content element
		           | content comment'''
		p[0] = p[1] + p[2]
	
	def p_content10(self, p):
		'''content : content cdata'''
		p[0] = p[1] + escape(p[2])

	def p_content00(self, p):
		'''content : cdata'''
		p[0] = escape(p[1])

	def p_content01(self, p):
		'''content : element
		           | comment'''
		p[0] = p[1]

	def p_element_attr1(self, p):
		'''element : TAG_ATTR avlist START1 content END
		           | TAG_ATTR avlist START2 content END
		           | TAG_ATTR avlist START3 content END
		           | TAG_ATTR avlist START4 content END'''
		p[0] = '<%s %s>%s%s</%s>%s' % (p[1], p[2], p[3], p[4], p[1], p[5])

	def p_element_attr0(self, p):
		'''element : TAG_ATTR avlist START1 END
		           | TAG_ATTR avlist START3 END
		           | TAG_ATTR avlist START4 END
		           | TAG_ATTR avlist START5 END'''
		p[0] = '%s<%s %s />%s' % (p[3], p[1], p[2], p[4])

	def p_element1(self, p):
		'''element : TAG START1 content END
		           | TAG START2 content END
		           | TAG START3 content END
		           | TAG START4 content END'''
		p[0] = '<%s>%s%s</%s>%s' % (p[1], p[2], p[3], p[1], p[4])

	def p_element0(self, p):
		'''element : TAG START1 END
		           | TAG START3 END
		           | TAG START4 END
		           | TAG START5 END'''
		p[0] = '%s<%s />%s' % (p[2], p[1], p[3])

	def p_comment1(self, p):
		'''comment : COMMENT START1 content END
		           | COMMENT START2 content END
		           | COMMENT START3 content END
		           | COMMENT START4 content END'''
		p[0] = ''

	def p_comment0(self, p):
		'''comment : COMMENT START1 END
		           | COMMENT START3 END
		           | COMMENT START4 END
		           | COMMENT START5 END'''
		p[0] = ''

	def p_avlist(self, p):
		'avlist : avlist attrvalue'
		p[0] = p[1] + ' ' + p[2]

	def p_avlist0(self, p):
		'avlist : attrvalue'
		p[0] = p[1]

	def p_attrvalue(self, p):
		'attrvalue : ATTR_EQ value'
		p[0] = p[1] + '=' + quoteattr(p[2])
	
	def p_value(self, p):
		'''value : value VALUE
		         | value ESCAPED'''
		p[0] = p[1] + p[2]
	
	def p_value0(self, p):
		'''value : VALUE
		         | ESCAPED'''
		p[0] = p[1]

	def p_cdata(self, p):
		'''cdata : cdata ESCAPED
		         | cdata CDATA'''
		p[0] = p[1] + p[2]
		
	def p_cdata0(self, p):
		'''cdata : CDATA
		         | ESCAPED'''
		p[0] = p[1]
	
	def p_START2_error(self, p):
		'''element : TAG START2 END
		           | TAG_ATTR avlist START2 END
		           | COMMENT START2 END'''
		raise YaccError("empty body not allowed in oneline form", p.lineno(1))
	
	def p_error(self, t):
		if t:
			raise YaccError("token %s" % t.type, t.lineno)
		else:
			raise YaccError("unexpected EOF", '$')


from table import xmlbuilder

xml = XMLBuilder(lexer=lexer,
		tabmodule=xmlbuilder,
	).parse

XHTML1_Strict = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
'''

from functools import partial

xhtml = partial(xml, prolog=XHTML1_Strict)
xhtml.__doc__ = "Parse a NEST string to XML with a XHTML 1.0 Strict !DOCTYPE prolog"


class EtreeBuilder(object):
	def __init__(self, lexer=None, **kwargs):
		if lexer:
			self.lexer = lexer
		else:
			self.lexer = Lexer()
		self.tokens = self.lexer.tokens
		self.parser = yacc.yacc(module=self, **kwargs)

	def parse(self, input, **kwargs):
		"Parse a NEST string to an ElementTree"
		e = self.parser.parse(input, lexer=self.lexer, **kwargs)
		return ElementTree(e)

	def p_element_attr1(self, p):
		'''element : TAG_ATTR avlist START1 content END
		           | TAG_ATTR avlist START2 content END
		           | TAG_ATTR avlist START3 content END
		           | TAG_ATTR avlist START4 content END'''
		p[0] = Element(p[1], **dict(p[2]))
		for i, e in enumerate(p[4]):
			if isinstance(e, basestring):
				if i == 0:
					p[0].text = e
				else:
					last.tail = e
			else:
				p[0].append(e)
				last = e

	def p_element_attr0(self, p):
		'''element : TAG_ATTR avlist START1 END
		           | TAG_ATTR avlist START3 END
		           | TAG_ATTR avlist START4 END
		           | TAG_ATTR avlist START5 END'''
		p[0] = Element(p[1], **dict(p[2]))

	def p_element1(self, p):
		'''element : TAG START1 content END
		           | TAG START2 content END
		           | TAG START3 content END
		           | TAG START4 content END'''
		p[0] = Element(p[1])
		for i, e in enumerate(p[3]):
			if isinstance(e, basestring):
				if i == 0:
					p[0].text = e
				else:
					last.tail = e
			else:
				p[0].append(e)
				last = e

	def p_element0(self, p):
		'''element : TAG START1 END
		           | TAG START3 END
		           | TAG START4 END
		           | TAG START5 END'''
		p[0] = Element(p[1])

	def p_comment1(self, p):
		'''comment : COMMENT START1 content END
		           | COMMENT START2 content END
		           | COMMENT START3 content END
		           | COMMENT START4 content END'''
		p[0] = Comment(p[3])

	def p_comment0(self, p):
		'''comment : COMMENT START1 END
		           | COMMENT START3 END
		           | COMMENT START4 END
		           | COMMENT START5 END'''
		p[0] = Comment()

	def p_content11(self, p):
		'''content : content element
		           | content comment'''
		p[1].append(p[2])
		p[0] = p[1]

	def p_content10(self, p):
		'''content : content cdata'''
		# p[1][-1] must be an element
		p[1][-1].tail = p[2]
		p[0] = p[1]

	def p_content0(self, p):
		'''content : element
		           | comment
		           | cdata'''
		p[0] = [p[1]]

	def p_avlist(self, p):
		'avlist : avlist attrvalue'
		p[0] = p[1].append(p[2])

	def p_avlist0(self, p):
		'avlist : attrvalue'
		p[0] = [p[1]]

	def p_attrvalue(self, p):
		'attrvalue : ATTR_EQ value'
		p[0] = p[1], p[2]

	def p_value(self, p):
		'''value : value VALUE
		         | value ESCAPED'''
		p[0] = p[1] + p[2]

	def p_value0(self, p):
		'''value : VALUE
		         | ESCAPED'''
		p[0] = p[1]

	def p_cdata(self, p):
		'''cdata : cdata ESCAPED
		         | cdata CDATA'''
		p[0] = p[1] + p[2]

	def p_cdata0(self, p):
		'''cdata : CDATA
		         | ESCAPED'''
		p[0] = p[1]

	def p_START2_error(self, p):
		'''element : TAG START2 END
		           | TAG_ATTR avlist START2 END
		           | COMMENT START2 END'''
		raise YaccError("empty body not allowed in oneline form", p.lineno(1))

	def p_error(self, t):
		if t:
			raise YaccError("token %s" % t.type, t.lineno)
		else:
			raise YaccError("unexpected EOF", '$')


from table import etreebuilder

etree = EtreeBuilder(lexer=lexer,
		tabmodule=etreebuilder,
	).parse
