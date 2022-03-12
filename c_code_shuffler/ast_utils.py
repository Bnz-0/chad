import sys
from pycparser.c_ast import FuncDef, Decl, Struct
from pycparser import c_generator
from clexer.c_lexer import CLexer
from globals import GLOBALS

_GEN = c_generator.CGenerator()

code = _GEN.visit
file_name = lambda node: node.coord.file


def _is_struct(node):
	t = node
	while True:
		try:
			t = t.type
			if isinstance(t, Struct):
				return True
		except: return False


def _first_line_from_ast(node):
	# far from the perfection but it works on FuncDef
	if isinstance(node, FuncDef):
		def find_first_line(children):
			first_line = node.coord.line
			if len(children) == 0:
				return first_line
			for child in children:
				first_line = min(
					first_line,
					(child[1].coord.line if child[1].coord else first_line) or first_line,
					find_first_line(child[1].children())
				)
			return first_line

		return find_first_line(node.decl.children())

	return node.coord.line


def line(node, file = None):
	l = _first_line_from_ast(node)
	if isinstance(decl(node), Decl):
		node = decl(node)
		file = file or GLOBALS['file']
		kw = node.quals + node.storage + node.funcspec
		if _is_struct(node): kw.append('struct')
		while len(kw) > 0:
			for i in range(len(kw)):
				if kw[i] in file[l]:
					kw[i] = None
			kw = list(filter(lambda x: x is not None, kw))
			if len(kw) > 0: l -= 1
	return l


def decl(node):
	try:
		return node.decl
	except AttributeError:
		return node


def parse_comment(file):
	clex = CLexer()
	clex.build()
	clex.input(file.read())
	return [tok for tok in iter(clex.token, None) if tok.type in ('COMMENT', 'CPPCOMMENT')]
