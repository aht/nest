import lex

tokens = ("BACKSLASH START_ATTR END_ATTR START END " + 
		"NAME TEXT COMMENT " +
		"WS NL COLON EQ DASH").split()

t_BACKSLASH = r'\\'

t_START_ATTR = r'\['
t_END_ATTR = r'\]'

t_START = '<'
t_END = '>'

t_NL = r'[\n\r]+'
t_EQ = '='
t_DASH = '-'

t_COMMENT = r'\\(-|=)+'

def t_NAME(t):
	r'[a-zA-Z][a-zA-Z._\-]*'
	return t

def t_COLON(t):
	':'
	return t

def t_TEXT(t):
	r'[^\[=\]\\<>\n\r]+'
	return t

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

lexer = lex.lex()

if __name__ == '__main__':
	lex.runmain()
