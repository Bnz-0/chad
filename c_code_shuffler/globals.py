import sys, os

GLOBALS = {
	'fake_header_path': f"{os.path.join(os.path.dirname(__file__), 'fake_libc_include')}",
	'custom_defines': [
		"__attribute__(x)=",
		"__extension__=",
		"__GNUC_PREREQ(x,y)=0",
		"__glibc_clang_prereq(x,y)=0",
		"__THROW=",
		"__END_DECLS=",
		"__BEGIN_DECLS=",
	],
	'source_ext': ['.c'],
	'file': None,
	'comments': [],
}
