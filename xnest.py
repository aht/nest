#!/usr/bin/env python

import re
import sys
import lex, yacc

#________________________________________________________________________
# Lexer

class Lexer(object):
	states = (
		('attr','exclusive'),
		('body', 'exclusive'),
		('bracket','exclusive'),
		('oneword', 'exclusive'),
		('oneline','exclusive'),
		('indent','exclusive'),
	)

	tokens = ("TAG TAG_ATTR ATTR EQ VALUE END_ATTR " +
			"START1 START2 START3 START4 END " + 
			"CDATA ESCAPED").split()
  
	def __init__(self, **kwargs):
		self.lexer = lex.lex(object=self, **kwargs)
		self.lvl_stack = [0]
		self.emitted = []

	def emit(self, type, value=None):
		t = lex.LexToken()
		t.type = type
		t.value = value
		t.lineno = self.lexer.lineno
		t.lexpos = self.lexer.lexpos
		self.emitted.append(t)

	def input(self, s):
		self.lexer.input(s)

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

	def t_ESCAPED(self, t):
		r'\\\\'
		return t

	def t_ANY_TAG_ATTR(self, t):
		r'\\[^ \t\r\n\[\]<>:]+[ \t\r\n]*\['
		t.value = t.value[1:]
		t.lexer.push_state('attr')
		t.lexer.lineno += t.value.count('\n')
		return t

	def t_ANY_TAG(self, t):
		r'\\[^ \t\r\n\[\]<>:]+'
		t.value = t.value[1:]
		t.lexer.push_state('body')
		return t

	def t_ANY_error(self, t):
			print "Illegal character '%s'" % t.value[0]
			t.lexer.skip(1)

	#________________
	# attr

	t_attr_ATTR = r'[^\= \t\n\r]+'
	t_attr_EQ = '='
	t_attr_VALUE = r'(\'.*\')|(".*")|[^= \t\r\n\]]+'
	t_attr_ignore = ' \t\r\n'

	def t_attr_END_ATTR(self, t):
		r'\]'
		t.lexer.pop_state()
		t.lexer.push_state('body')
		return t

	#________________
	# body

	def t_body_START1(self, t):
		r':[\r\n]+[\t]+'
		t.lexer.lineno += t.value.count('\n')
		t.lexer.pop_state()
		t.lexer.push_state('indent')
		lvl = t.value.count('\t')
		if lvl > self.lvl_stack[-1]:
			self.lvl_stack.append(lvl)
		return t

	def t_body_START2(self, t):
		r':'
		t.lexer.pop_state()
		t.lexer.push_state('oneline')
		return t

	def t_body_START3(self, t):
		r'[ \t\r\n]*<'
		t.lexer.pop_state()
		t.lexer.push_state('bracket')
		t.lexer.lineno += t.value.count('\n')
		return t

	def t_body_START4(self, t):
		r'[ \t]+'
		t.lexer.pop_state()
		t.lexer.push_state('oneword')
		return t

	# empty body
	def t_body_END(self, t):
		r'[\r\n]+'
		t.lexer.lineno += t.value.count('\n')
		t.lexer.pop_state()
		return t

	#________________
	# oneword

	def t_oneword_CDATA(self, t):
		r'[^\\ \t\r\n]+'
		return t

	def t_oneword_END(self, t):
		r'[ \t\r\n]+'
		t.lexer.lineno += t.value.count('\n')
		t.lexer.pop_state()
		while t.lexer.lexstate == 'oneword':
			self.emit('END')
			t.lexer.pop_state()
		return t

	#________________
	# oneline

	def t_oneline_CDATA(self, t):
		r'[^\\\r\n]+'
		return t

	def t_oneline_END(self, t):
		r'[\r\n]+'
		t.lexer.pop_state()
		t.lexer.lineno += t.value.count('\n')
		return t

	#________________
	# bracket

	def t_bracket_CDATA(self, t):
		r'[^\\>]+'
		return t

	def t_bracket_END(self, t):
		r'>[ \t\r\n]*'
		t.lexer.pop_state()
		t.lexer.lineno += t.value.count('\n')
		return t

	#________________
	# indent

	def t_indent_CDATA(self, t):
		r'[^\\\r\n]+'
		t.value += '\n'
		return t

	def t_indent_END(self, t):
		r'[\r\n]+[\t]*'
		t.lexer.lineno += t.value.count('\n')
		lvl = t.value.count('\t')
		if lvl == self.lvl_stack[-1]:
			pass
		else:
			i = self.lvl_stack.index(lvl)
			for lvl in range(i+1, len(self.lvl_stack)-1):
				self.emit('END')
				self.lvl_stack.pop()
				t.lexer.pop_state()
			return t


#________________________________________________________________________
# Parser

class Parser(object):
	def __init__(self, lexer=None, **kwargs):
		if lexer:
			self.lexer = lexer
		else:
			self.lexer = Lexer()
		self.tokens = self.lexer.tokens
		self.parser = yacc.yacc(module=self, **kwargs)

	def parse(self, code):
		return self.parser.parse(code, lexer=self.lexer)

	def p_element(self, p):
		'''element : TAG body
							 | TAG empty_body'''
		p[0] = '<%s>%s</%s>' % (p[1], p[2], p[1])

	def p_body(self, p):
		'''body : START1 content END
		        | START2 content END
		        | START3 content END
		        | START4 content END'''
		p[0] = p[1] + p[2] + p[3]

	def p_empty_body(self, p):
		'''empty_body : START1 END
		              | START2 END
		              | START3 END
		              | START4 END'''
		p[0] = p[1] + p[2]

	def p_content(self, p):
		'''content : content element
		           | content cdata'''
		p[0] = p[1] + p[2]

	def p_content0(self, p):
		'''content : element
		           | cdata'''
		p[0] = p[1]

	def p_cdata(self, p):
		'''cdata : cdata ESCAPED
		         | cdata CDATA'''
		p[0] = p[1] + p[2]

	def p_cdata0(self, p):
		'cdata : CDATA'
		p[0] = p[1]


#________________________________________________________________________
# Main

if __name__ == '__main__':
	lexer = Lexer()
	if len(sys.argv) >= 2 and sys.argv[1] == '-l':
		lexer.input(sys.stdin.read())
		for t in lexer:
			print t
	else:
		parser = Parser(lexer=lexer)
		print parser.parse(sys.stdin.read())
