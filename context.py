import sys, os
import random as R
import subprocess
from glob import glob
from collections.abc import Iterable
import numpy as np
from sympy import symbols, expand, Mul, Pow, Integer
from xeger import Xeger
# from ctfg import CTX_FILES_OPT, expand_paths

sys.path.append(os.path.join(os.path.dirname(__file__), "c_code_shuffler"))
from c_code_shuffler.ccshuffler import shuffler
from c_code_shuffler.file_utils import File

#### python's built-in ####
int = int
float = float
bool = bool
list = list
dict = dict
set = set
hex = hex
bin = bin
oct = oct

#### char sets ####

class CharRange(Iterable):

	def __init__(self, *args):
		if len(args) != 2:
			raise ValueError("Expected 2 arguments: [start; end], got " + str(len(args)))
		self._start, self._end = ord(args[0]), ord(args[1])
		self.n = 0

	def __add__(self, s):
		return CharCollenction(self, s)

	def __radd__(self, s):
		return CharCollenction(s, self)

	def __getitem__(self, i):
		if i >= len(self): raise IndexError()
		return chr(self._start + i)

	def __iter__(self):
		self.n = 0
		return self

	def __next__(self):
		try:
			v = self[self.n]
			self.n += 1
			return v
		except IndexError:
			raise StopIteration()

	def __len__(self):
		return self._end - self._start + 1

	def __str__(self):
		return "".join(self)

	def __repr__(self):
		return f"CharRange [{chr(self._start)}; {chr(self._end)}]"


class CharCollenction(CharRange):

	def __init__(self, *args):
		if len(args) == 0: raise ValueError("Expected at least 1 agruments, got 0")
		self._collections = args
		self.n = 0

	def __getitem__(self, i):
		if i >= len(self): raise IndexError()
		offset = n = 0
		while i-offset >= len(self._collections[n]):
			offset += len(self._collections[n])
			n += 1
		return self._collections[n][i-offset]

	def __len__(self):
		if not hasattr(self, '_cached_len'):
			self._cached_len = sum(len(c) for c in self._collections)
		return self._cached_len

	def __repr__(self):
		return f"CharCollenction({','.join(repr(c) for c in self._collections)})"


numeric = CharRange('0','9')
alpha_lowercase = CharRange('a','z')
alpha_uppercase = CharRange('A','Z')
alpha = alpha_uppercase + alpha_lowercase
alphanumeric = alpha + numeric
readable = alphanumeric + "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
printable = readable + " \t\n\r\x0b\x0c" # form string.printable

#### other sets ####

hexspeak = [
	0xdead,
	0xb000,
	0xcafe,
	0xbabe,
	0xbeef,
	0xf00d,
	0xc0de,
	0xba5eba11,
	0xb01dface,
	0xca11ab1e,
	0xca55e77e,
	0xdeadbea7,
	0xf01dab1e,
	0xf005ba11,
	0x0ddba11,
	0x5ca1ab1e,
	0x7e1eca57,
	0xadd,
	0xaf10a7,
	0xba1b0a,
	0xbee,
	0xb1ab,
	0xb100d,
	0xcab1e5,
	0xb007ab1e,
	0xc1a55,
	0xc0d,
	0xdeadfa11,
	0xdecade,
	0x5ea,
	0xc0ffe,
	0x5e1ec7ed,
	0x50f7ba11,
	0x7ea,
	0x50f7,
	0x50fa
]

#### number utilities ####

def rand_int(a=-2**31, z=2**31-1):
	if a > z: raise ValueError("min value cannot be greater than max")
	return R.randint(a, z)

def rand_uint(a=0, z=2**32-1):
	if a < 0: raise ValueError("unsigned number cannot be lower than 0")
	return rand_int(a, z)

def rand_float(a, z):
	return R.uniform(a, z)

rand_char = lambda a=-2**7, z=2**7-1: rand_int(a, z)
rand_uchar = lambda a=0, z=2**8-1: rand_uint(a, z)
rand_short = lambda a=-2**15, z=2**15-1: rand_int(a, z)
rand_ushort = lambda a=0, z=2**16-1: rand_uint(a, z)
rand_long = lambda a=-2**63, z=2**63-1: rand_int(a, z)
rand_ulong = lambda a=0, z=2**64-1: rand_uint(a, z)

def rand_scanf_safe_int(bytes_len=4, unsigned=False):
	# because scanf parsing a string "matches a sequence of non-white-space characters"
	# this generates an integer byte-by-byte to be sure to not incude any non-white-space characters
	return sum(
		rand_int(33, 255 if unsigned else 127) << (i*8)
		for i in range(bytes_len)
	)

#### string utilities ####

def rand_str(min_len, max_len=0, c_set=alphanumeric, repeat=True):
	max_len = max_len or min_len
	s_len = rand_int(min_len, max_len)
	if not repeat:
		if max_len > len(c_set):
			raise ValueError("max_len cannot be higher than the length of the c_set")
		c_set = list(c_set)
		R.shuffle(c_set)
		return "".join(c_set[0:s_len])
	return "".join(R.choice(c_set) for _ in range(s_len))

re2str = lambda regex, limit=10: Xeger(limit).xeger(regex)

#### collection utilities ####

choose_one = R.choice

def remove_one(l):
	i = R.randint(0, len(l)-1)
	v = l[i]
	del l[i]
	return v

def rand_n_int(range_, n):
	return [rand_int(*range_) for _ in range(n)]

def rand_n_float(range_, n):
	return [rand_float(*range_) for _ in range(n)]

#### os utilities ####

def run_cmd(cmd):
	result = subprocess.run(["bash", "-c", cmd], check=False, capture_output=True)
	return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')

def check_solution(cmd, flag):
	instance_id = os.path.basename(os.getcwd())
	print(clr(f"=== Testing {instance_id}'s solution ({os.path.basename(os.path.dirname(os.getcwd()))}) ===", fg='yellow', style='bold'))
	log(clr(f"Looking for flag={flag}", fg='yellow'))
	out, _ = run_cmd(cmd)
	for line in out.split("\n"):
		if flag in line:
			print(
				clr(line, style='bold') + "\n" +
				clr("=== Flag found! ===", fg='green', style='bold')
			)
			return
		log(line)
	print(clr("=== ERROR: flag not found ===", fg='red', style='bold'))
	sys.exit(1) # interrupts the creation of other instances to avoid too much noise

#### other utilities ####

class Polynomial:
	def __init__(self, degree, points=None, values_range=(-10,10)):
		rand_value = lambda: rand_float(*values_range)
		if points is not None:
			while len(points) < degree+1:
				new_p = (rand_value(), rand_value())
				if all(new_p[0] != p[0] for p in points): points.append(new_p)
			self.values = list(np.linalg.solve(
				np.array([ [p[0]**d for d in range(degree+1)] for p in points ]),
				np.array([ p[1] for p in points ])
			))
		else:
			self.values = [rand_value() for _ in range(degree+1)]

	def __call__(self, x):
		return sum(v*x**deg for deg,v in enumerate(self.values))

	def to_str(self, x_name, use_pow=False, rand_pos=False):
		str_values = [
			"{0:+}".format(v) + (deg!=0 and ("*"+(use_pow and f"pow({self.x_name}, {deg})" or "*".join(x_name for _ in range(deg)))) or "")
			for deg,v in enumerate(self.values)
		]
		if rand_pos: R.shuffle(str_values)
		return " ".join(str_values)


class IntPolynomial(Polynomial):
	_extract_value = {
		Integer: lambda arg: int(arg),
		Mul: lambda arg: int(arg.args[0]),
		Pow: lambda arg: 1,
	}
	_extract_deg = {
		Integer: lambda _: 0,
		Mul: lambda arg: int(arg.args[1].args[1]) if isinstance(arg.args[1], Pow) else 1,
		Pow: lambda arg: int(arg.args[1]),
	}

	def __init__(self, solutions, offset=0):
		x = symbols('x')
		exp = 1
		for sol in solutions:
			exp *= (x - sol)
		self.values = [0]*(len(solutions)+1)
		for arg in expand(exp + offset).args:
			v = IntPolynomial._extract_value[type(arg)](arg)
			deg = IntPolynomial._extract_deg[type(arg)](arg)
			self.values[deg] = v


def ccshuffler(files, compiler_options = []):
	for file in expand_paths(files):
		shuffled = "\n".join(str(line) for line in shuffler(File(file), file, compiler_options))
		with open(file, 'w') as f:
			f.write(shuffled)
