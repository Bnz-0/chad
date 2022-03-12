#!/bin/env python3

import sys, os, re
from tempfile import TemporaryDirectory
from random import shuffle
from shutil import copytree, ignore_patterns
from pycparser import parse_file
import click
from globals import GLOBALS
from file_utils import File, list_source_files, extract_subpath, get_folder
from ast_utils import *


PP_PATTERN = re.compile(r"^(.*\*/)?\s*#")

@click.command()
@click.option("--all", "-a", "copy_all",
	is_flag=True,
	help="if SOURCE is a directory, copy the whole content of SOURCE into OUTPUT before doing the shuffle in the C source files."
)
@click.option("--compiler-option", "-c", "compiler_options",
	multiple=True,
	help="option to pass to the compiler"
)
@click.argument("source", required=True, type=click.Path(exists=True))
@click.argument("out_dir", required=False, type=click.Path())
def main(copy_all, compiler_options, source, out_dir):
	"""Shuffle the position of the functions in a C SOURCE file(s).
	If specified the resutl will be saved in the OUT_DIR directory, otherwise it will be printed in stdout.
	"""
	if out_dir:
		try: os.makedirs(out_dir)
		except FileExistsError: pass

	files = list_source_files(source) if os.path.isdir(source) else [File(source)]

	if copy_all and out_dir and os.path.isdir(source):
		copytree(source, out_dir, ignore=ignore_patterns('.git'), dirs_exist_ok=True)

	tmp_dir = None if out_dir else TemporaryDirectory()
	errc = 0
	for file in files:
		GLOBALS['file'] = file
		GLOBALS['comments'] = parse_comment(file)

		new_file = File(file.copy(
			os.path.join(out_dir, extract_subpath(source, file.path)) if out_dir else tmp_dir.name
		))

		try: shuffled = "\n".join(str(line) for line in shuffler(new_file, source, list(compiler_options)))
		except Exception as e:
			print(f"Failed to randomize the file {file.path}: {e}", file=sys.stderr)
			errc += 1
			continue

		if out_dir:
			with open(new_file.path, 'w+') as out_f:
				out_f.write(shuffled)
		else:
			print(shuffled)

	print(f"Randomized source files: {len(files)-errc}/{len(files)}", file=sys.stderr)
	if tmp_dir: tmp_dir.cleanup()


class CodeBlock:
	def __init__(self, file, start, end):
		self.file = file
		self.start = start
		self.end = end

	def lines(self):
		for i in range(self.start, self.end):
			yield self.file[i]

	def __str__(self):
		return "\n".join(self.file[self.start:self.end]) + '\n'

	def __repr__(self):
		return f"({self.start};{self.end})[{str(self)}]"


class FunctionBlock(CodeBlock):
	def __init__(self, file, node):
		self.file = file
		super().__init__(
			file,
			self._start_line(node),
			self._end_line(node)
		)

	def _start_line(self, node):
		comments = GLOBALS['comments']
		i = line(node, self.file)
		for comment in (comments[i] for i in range(len(comments)-1, 1, -1)):
			end = comment.coord_end()
			if end[0] == i-1:
				i = comment.coord_start()[0]
			if end[0] < i: break
		return i

	def _end_line(self, node):
		clex = CLexer()
		clex.build()
		i = line(node, self.file)
		brace_counter = -1
		while i <= len(self.file):
			clex.input(self.file[i])
			while True:
				tok = clex.token()
				if tok is None: break
				if tok.type == 'LBRACE':
					brace_counter += 1 if brace_counter != -1 else 2
				elif tok.type == 'RBRACE':
					brace_counter -= 1
				if brace_counter == 0:
					i += 1
					while i <= len(self.file) and len(self.file[i].strip()) == 0:
						i += 1 # includes also the empty lines below
					return i
			i += 1
		return i


class NodeIter:
	def __init__(self, ast, path):
		self._path = path
		self._ast = ast.ext
		self._i = 0

	def reset(self):
		self._i = 0

	def __iter__(self):
		self.reset()
		return self

	def __next__(self):
		while True:
			if self._i >= len(self._ast): raise StopIteration
			node = self._ast[self._i]
			self._i += 1
			if file_name(node) == self._path:
				break
		return node


def shuffler(file, source_path, compiler_options):
	ast = parse_file(
		file.path,
		use_cpp = True,
		cpp_path = "gcc",
		cpp_args = [
				"-E",
				rf"-I{GLOBALS['fake_header_path']}",
				rf"-I{get_folder(source_path)}"
			]
			+ [rf"-D{define}" for define in GLOBALS['custom_defines']]
			+ compiler_options
	)

	last_pp_line = len(file)
	while last_pp_line >= 0 and (
			re.search(PP_PATTERN, file[last_pp_line]) is None or
			any(
				last_pp_line == c.coord_start()[0] and file[last_pp_line].find('#') > c.coord_start()[1] or
				c.coord_start()[0] < last_pp_line < c.coord_end()[0]
				#NB: the "pre-processor after a comment" case is managed by the PP_PATTERN
				for c in GLOBALS['comments']
			)
		):
		last_pp_line -= 1

	func_blocks = [] # list of FunctionBlock
	func_decls = [] # list of generated node to declare all the functions
	nodes = NodeIter(ast, file.path)
	while True:
		try:
			node = next(nodes)
			if line(node) <= last_pp_line:
				continue
			if isinstance(node, FuncDef):
				func_blocks.append(FunctionBlock(file, node))
				func_decls.append(code(decl(node))+";")
		except StopIteration:
			break

	generic_blocks = [] if len(func_blocks) > 0 else [CodeBlock(file, 1, len(file)+1)]
	a = b = 0
	for fb in func_blocks:
		b = fb.start
		block = CodeBlock(file, a, b)
		if any(len(l.strip()) > 0 for l in block.lines()):
			generic_blocks.append(block)
		a = fb.end

	shuffle(func_blocks)
	return generic_blocks + func_decls + [''] + func_blocks


if __name__ == "__main__":
    main()
