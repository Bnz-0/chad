import os
from shutil import copyfile
from globals import GLOBALS

class File:
	def _lazy(func):
		def wrapper(self, *args, **kwargs):
			if self._file_by_line is None:
				self.load()
			return func(self, *args, **kwargs)
		return wrapper

	def __init__(self, path):
		self.path = path
		self._file_by_line = None

	def name(self):
		return os.path.basename(self.path)

	def load(self):
		with open(self.path, 'r') as f:
			self._file_by_line = f.read().split('\n')

	def copy(self, dest):
		if os.path.isdir(dest):
			dest = os.path.join(dest, self.name())
		if not os.path.exists(os.path.dirname(dest)):
			os.makedirs(os.path.dirname(dest))
		copyfile(self.path, dest)
		return dest

	@_lazy
	def read(self):
		return "\n".join(self._file_by_line)

	@_lazy
	def __getitem__(self, i):
		if isinstance(i, slice):
			return self._file_by_line[i.start-1 if i.start else None : i.stop-1 if i.stop else None]
		return self._file_by_line[i-1]

	@_lazy
	def __len__(self):
		return len(self._file_by_line)


def extract_subpath(root, subpath):
	common = os.path.commonpath([root, subpath])
	return subpath[len(common)+1:]

def get_folder(path):
	return path if os.path.isdir(path) else (os.path.dirname(path) or '.')

def list_source_files(path):
	files = []
	for root, _, filenames in os.walk(path):
		for file in (f for f in filenames if any(f.endswith(ext) for ext in GLOBALS['source_ext'])):
			files.append(File(os.path.join(root, file)))
	return files
