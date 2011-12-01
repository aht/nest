#!/usr/bin/env python

#________________________________________________________________________
# Parsers

from lexer import nest_lexer

from ply import yacc
from xml.sax.saxutils import escape, quoteattr

try:
	from xml.etree.cElementTree import ElementTree, Element, Comment
except ImportError:
	from xml.etree.ElementTree import ElementTree, Element, Comment


class YaccError(Exception):
	def __init__(self, msg, lineno):
		self.msg, self.lineno = msg, lineno
	def __str__(self):
		return '%s at line %s' % (self.msg, self.lineno)


class XMLBuilder(object):
	def __init__(self, **kwargs):
		self.lexer = nest_lexer
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
		'''element : TAG_ATTR avlist STARTI content END
		           | TAG_ATTR avlist STARTL content END
		           | TAG_ATTR avlist STARTB content END'''
		p[0] = '<%s %s>%s%s</%s>%s' % (p[1], p[2], p[3], p[4], p[1], p[5])

	def p_element_attr0(self, p):
		'''element : TAG_ATTR avlist STARTI END
		           | TAG_ATTR avlist STARTL END
		           | TAG_ATTR avlist STARTB END'''
		p[0] = '%s<%s %s />%s' % (p[3], p[1], p[2], p[4])

	def p_element1(self, p):
		'''element : TAG STARTI content END
		           | TAG STARTL content END
		           | TAG STARTB content END'''
		p[0] = '<%s>%s%s</%s>%s' % (p[1], p[2], p[3], p[1], p[4])

	def p_element0(self, p):
		'''element : TAG STARTI END
		           | TAG STARTL END
		           | TAG STARTB END'''
		p[0] = '%s<%s />%s' % (p[2], p[1], p[3])

	def p_comment1(self, p):
		'''comment : COMMENT STARTI content END
		           | COMMENT STARTL content END
		           | COMMENT STARTB content END'''
		p[0] = ''

	def p_comment0(self, p):
		'''comment : COMMENT STARTI END
		           | COMMENT STARTL END
		           | COMMENT STARTB END'''
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
	
	def p_error(self, t):
		if t:
			raise YaccError("token %s" % t.type, t.lineno)
		else:
			raise YaccError("unexpected EOF", '$')


class EtreeBuilder(object):
	def __init__(self, **kwargs):
		self.lexer = nest_lexer
		self.tokens = self.lexer.tokens
		self.parser = yacc.yacc(module=self, **kwargs)

	def parse(self, input, **kwargs):
		"Parse a NEST string to an ElementTree"
		e = self.parser.parse(input, lexer=self.lexer, **kwargs)
		return ElementTree(e)

	def p_element_attr1(self, p):
		'''element : TAG_ATTR avlist STARTI content END
		           | TAG_ATTR avlist STARTL content END
		           | TAG_ATTR avlist STARTB content END'''
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
		'''element : TAG_ATTR avlist STARTI END
		           | TAG_ATTR avlist STARTL END
		           | TAG_ATTR avlist STARTB END'''
		p[0] = Element(p[1], **dict(p[2]))

	def p_element1(self, p):
		'''element : TAG STARTI content END
		           | TAG STARTL content END
		           | TAG STARTB content END'''
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
		'''element : TAG STARTI END
		           | TAG STARTL END
		           | TAG STARTB END'''
		p[0] = Element(p[1])

	def p_comment1(self, p):
		'''comment : COMMENT STARTI content END
		           | COMMENT STARTL content END
		           | COMMENT STARTB content END'''
		p[0] = Comment(p[3])

	def p_comment0(self, p):
		'''comment : COMMENT STARTI END
		           | COMMENT STARTL END
		           | COMMENT STARTB END'''
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

	def p_error(self, t):
		if t:
			raise YaccError("token %s" % t.type, t.lineno)
		else:
			raise YaccError("unexpected EOF", '$')


def generate_xmlbuilder():
    import os
    dir = os.path.join(os.path.dirname(__file__), 'table')
    return XMLBuilder(outputdir=dir, tabmodule='xmlbuilder')

try:
    from table import xmlbuilder
    xml = XMLBuilder(tabmodule=xmlbuilder).parse
except ImportError:
    xml = generate_xmlbuilder().parse


from functools import partial
XHTML1_Strict = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
'''
xhtml = partial(xml, prolog=XHTML1_Strict)
xhtml.__doc__ = "Parse a NEST string to XML with a XHTML 1.0 Strict !DOCTYPE prolog"


def generate_etreebuilder():
    import os
    dir = os.path.join(os.path.dirname(__file__), 'table')
    return EtreeBuilder(outputdir=dir, tabmodule='etreebuilder')

try:
    from table import etreebuilder
    etree = EtreeBuilder(tabmodule=etreebuilder).parse
except ImportError:
    etree = generate_etreebuilder().parse


if __name__ == '__main__':
    generate_xmlbuilder()
    generate_etreebuilder()
