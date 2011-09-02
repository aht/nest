#!/usr/bin/env python

#________________________________________________________________________
# Lexer


from ply import lex


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
		('oneline','exclusive'),
		('indent','exclusive'),
	)

	tokens = ("TAG TAG_ATTR COMMENT ATTR_EQ VALUE" +
			" STARTB STARTL STARTI END" +
			" CDATA ESCAPED WS").split()

	# We keep track of indentation levels using a stack where each
	# element is a tuple of number of tabs, number of spaces.

	# We wrap around lex to permit programmatic emission of extra tokens
	# which is necessary to handle NEST's shorthand styles and indentation.
	# This is implemented using a stack to keep track of the hand-emitted tokens.
	# A "real" token from lex is returned only when this stack is empty.

	def __init__(self, **kwargs):
		self.lex = lex.lex(object=self, **kwargs)
		self.lvl_stack = [(0, 0)]
		self.emitted = []

	def input(self, s):
		self.lex.input(s)

	def emit(self, type, value='\n'):
		t = lex.LexToken()
		t.type = type
		t.value = value
		t.lineno = self.lex.lineno
		t.lexpos = self.lex.lexpos
		self.emitted.append(t)

	def token(self):
		if self.emitted:
			return self.emitted.pop()
		else:
			return self.lex.token()

	def __iter__(self):
		def nexttok():
			while 1:
				t = self.token()
				if t is None:
					raise StopIteration
				else:
					yield t
		return nexttok()

	# check_endings should be called after recognizing a "real" END token
	# containing a newline.  The caller should determine the indentation level
	# after that END token then pass it to check_endings, which will inspect
	# the current lexer state and the indentation level stack to throw extra
	# END tokens that are pending, if any.

	def check_endings(self, tabs, spaces):
		while self.lex.lexstate == 'oneline':
			self.emit('END')
			self.lex.pop_state()
		if (tabs <= self.lvl_stack[-1][0]) and (spaces <= self.lvl_stack[-1][1]):
			try:
				idx = self.lvl_stack.index((tabs, spaces))
			except ValueError:
				raise LexError("dedenting to a bad indentation level", self.lex.lineno)
			for _ in range(idx, len(self.lvl_stack)-1):
				self.emit('END')
				self.lvl_stack.pop()
				self.lex.pop_state()
				while self.lex.lexstate == 'oneline':
					self.emit('END')
					self.lex.pop_state()

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

	def t_body_STARTI(self, t):
		r':[\r\n]+[ \t]+'
		t.lexer.pop_state()
		t.lexer.push_state('indent')
		tabs, spaces = t.value.count('\t'), t.value.count(' ')

		# We treat tabs and spaces orthogonally.  A new indentation level -- a tuple
		# of (tabs, spaces) -- is accepted only when one component increases
		# while the other stay the same. This way, it will be easier to recognize
		# indentation error when tabs and spaces are mixed -- accidentally or not.

		if ((tabs == self.lvl_stack[-1][0]) and (spaces > self.lvl_stack[-1][1])) \
		or ((tabs > self.lvl_stack[-1][0]) and (spaces == self.lvl_stack[-1][1])):
			self.lvl_stack.append((tabs, spaces))
		elif (tabs <= self.lvl_stack[-1][0]) and (spaces <= self.lvl_stack[-1][1]):
			raise LexError("an element's body must be more indented than its start tag", t.lexer.lineno)
		else:
			raise LexError("indentation not comparable to previous levels", t.lexer.lineno)
		t.lexer.lineno += t.value.count('\n')
		t.value = t.value[1:]
		return t

	def t_body_STARTB(self, t):
		r'[ \t\r\n]*<'
		t.lexer.pop_state()
		t.lexer.push_state('bracket')
		t.lexer.lineno += t.value.count('\n')
		t.value = t.value[:-1]
		return t

	# TODO: require space and write a separate empty body rule
	def t_body_STARTL(self, t):
		r'[ \t]*'
		t.lexer.pop_state()
		t.lexer.push_state('oneline')
		t.value = ''
		return t


	#________________
	# state: oneline

	def t_oneline_CDATA(self, t):
		r'[^\\\r\n]+'
		return t

	def t_oneline_END(self, t):
		r'[\r\n]+[\t ]*'
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
		return t

	def t_indent_END(self, t):
		r'[\r\n]+[\t ]*'
		tabs, spaces = t.value.count('\t'), t.value.count(' ')
		if (tabs, spaces) == self.lvl_stack[-1]:
			# not really a dedentation
			c = lex.LexToken()
			c.type = 'CDATA'
			c.value = t.value
			c.lineno = t.lineno
			c.lexpos = t.lexpos
			return c
		elif (tabs > self.lvl_stack[-1][0]) or (spaces > self.lvl_stack[-1][1]):
			raise LexError("indentation not comparable to previous levels", t.lexer.lineno)
		else:
			self.lvl_stack.pop()
			t.lexer.pop_state()
			self.check_endings(tabs, spaces)
			return t


def generate_lextab():
    import os
    dir = os.path.join(os.path.dirname(__file__), 'table')
    return Lexer(outputdir=dir, lextab='lextab', optimize=1)

try:
    from table import lextab
except ImportError:
    generate_lextab()

if __name__ == '__main__':
    generate_lextab()