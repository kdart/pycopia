" Vim syntax file
" assumes Vim version 6.x

syntax clear

syn keyword pythonStatement	break continue del
syn keyword pythonStatement	except exec finally
syn keyword pythonStatement	pass print raise
syn keyword pythonStatement	return try
syn keyword pythonStatement	global assert yield
" syn keyword pythonStatement	def class nextgroup=pythonFunction skipwhite
" syn match   pythonFunction	"[a-zA-Z_][a-zA-Z0-9_]*" contained
" syn match   pythonSpecial	"__[a-zA-Z0-9]+__"
syn keyword pyTypedef          def class lambda
syn keyword pythonRepeat	for while
syn keyword pythonConditional	if elif else
syn keyword pythonOperator	and in is not or
syn keyword pythonPreCondit	import from as
syn match   pythonComment	"#.*$" contains=pythonTodo
syn keyword pythonTodo		contained TODO FIXME XXX

" strings
syn region pythonString		matchgroup=Normal start=+[uU]\='+ end=+'+ skip=+\\\\\|\\'+ contains=pythonEscape
syn region pythonString		matchgroup=Normal start=+[uU]\="+ end=+"+ skip=+\\\\\|\\"+ contains=pythonEscape
syn region pythonString		matchgroup=Normal start=+[uU]\="""+ end=+"""+ contains=pythonEscape
syn region pythonString		matchgroup=Normal start=+[uU]\='''+ end=+'''+ contains=pythonEscape
syn region pythonRawString	matchgroup=Normal start=+[uU]\=[rR]'+ end=+'+ skip=+\\\\\|\\'+
syn region pythonRawString	matchgroup=Normal start=+[uU]\=[rR]"+ end=+"+ skip=+\\\\\|\\"+
syn region pythonRawString	matchgroup=Normal start=+[uU]\=[rR]"""+ end=+"""+
syn region pythonRawString	matchgroup=Normal start=+[uU]\=[rR]'''+ end=+'''+
syn match  pythonEscape		+\\[abfnrtv'"\\]+ contained
syn match  pythonEscape		"\\\o\o\=\o\=" contained
syn match  pythonEscape		"\\x\x\+" contained
syn match  pythonEscape		"\(\\u\x\{4}\|\\U\x\{8}\)" contained
syn match  pythonEscape		"\\$"

if exists("python_highlight_all")
  let python_highlight_numbers = 1
  let python_highlight_builtins = 1
  let python_highlight_exceptions = 1
endif

" numbers (including longs and complex)
syn match   pythonNumber	"\<0x\x\+[Ll]\=\>"
syn match   pythonNumber	"\<\d\+[LljJ]\=\>"
syn match   pythonNumber	"\.\d\+\([eE][+-]\=\d\+\)\=[jJ]\=\>"
syn match   pythonNumber	"\<\d\+\.\([eE][+-]\=\d\+\)\=[jJ]\=\>"
syn match   pythonNumber	"\<\d\+\.\d\+\([eE][+-]\=\d\+\)\=[jJ]\=\>"

" Warn of any bad octals, or lowercase Ls for longs (I hate those).
syn match pySyntaxError    "\<0\o*[89]"
syn match pySyntaxWarning  "\<0x\x\+l"
syn match pySyntaxWarning  "\<[1-9]\d*l"
syn match pySyntaxWarning  "\<0\o\+\l"

" Try to help the C and Perl users out there.
syn match pySyntaxError    "\$\|@"
syn match pySyntaxError    "\(&&\|||\)"
syn match pySyntaxError    "/[/\*]"
syn match pySyntaxWarning "\(++\|--\|->\|=\~\)"
syn match pySyntaxWarning ";\s*$"

" builtin functions, types and objects, not really part of the syntax
syn keyword pythonBuiltin	Ellipsis None NotImplemented __import__ abs
syn keyword pythonBuiltin	apply buffer callable chr classmethod cmp
syn keyword pythonBuiltin	coerce compile complex delattr dict dir divmod
syn keyword pythonBuiltin	eval execfile file filter float getattr globals
syn keyword pythonBuiltin	hasattr hash hex id input int intern isinstance
syn keyword pythonBuiltin	issubclass iter len list locals long map max
syn keyword pythonBuiltin	min object oct open ord pow property range
syn keyword pythonBuiltin	raw_input reduce reload repr round setattr
syn keyword pythonBuiltin	slice staticmethod str super tuple type unichr
syn keyword pythonBuiltin	unicode vars xrange zip iter bool 
" following added by nmsbuiltins module
syn keyword pythonBuiltin	enumerate reorder pprint_list Print IF
syn keyword pythonBuiltin	Queue Stack removedups YES NO True False
syn keyword pythonBuiltin	mapstr Enum Enums add_exception Write str2hex  
syn keyword pythonBuiltin	curry newclass NULL unsigned unsigned64 sortedlist
syn keyword pythonBuiltin	sgn add2builtin 

" builtin exceptions and warnings
syn keyword pythonException	ArithmeticError AssertionError AttributeError
syn keyword pythonException	DeprecationWarning EOFError EnvironmentError
syn keyword pythonException	Exception FloatingPointError IOError
syn keyword pythonException	ImportError IndentiationError IndexError
syn keyword pythonException	KeyError KeyboardInterrupt LookupError
syn keyword pythonException	MemoryError NameError NotImplementedError
syn keyword pythonException	OSError OverflowError OverflowWarning
syn keyword pythonException	ReferenceError RuntimeError RuntimeWarning
syn keyword pythonException	StandardError StopIteration SyntaxError
syn keyword pythonException	SyntaxWarning SystemError SystemExit TabError
syn keyword pythonException	TypeError UnboundLocalError UnicodeError
syn keyword pythonException	UserWarning ValueError Warning WindowsError
syn keyword pythonException	ZeroDivisionError IndentationError

syn keyword pyDebug            __debug__
syn keyword pyBuiltinVariable  __bases__ __class__ __dict__ __doc__ __slots__
syn keyword pyBuiltinVariable  __file__ __name__ __methods__ __members__
syn keyword pyBuiltinVariable  __module__ __self__ self

" all of the special methods. So you know you got the right one. 8-)
syn keyword pySpecialMethod  __init__ __del__ __repr__ __str__ __iter__
syn keyword pySpecialMethod  __cmp__ __hash__ __nonzero__ __getstate__ __setstate__
syn keyword pySpecialMethod  __getattr__ __setattr__ __delattr__ __getattribute__
syn keyword pySpecialMethod  __call__ __new__ __get__
syn keyword pySpecialMethod  __len__ __getitem__ __setitem__ __delitem__
syn keyword pySpecialMethod  __getslice__ __setslice__ __delslice__
syn keyword pySpecialMethod  __add__ __sub__ __mul__ __div__ __mod__
syn keyword pySpecialMethod  __divmod__ __pow__ __lshift__ __rshift__
syn keyword pySpecialMethod  __and__ __xor__ __or__
syn keyword pySpecialMethod  __radd__ __rsub__ __rmul__ __rdiv__
syn keyword pySpecialMethod  __rmod__ __rdivmod__ __rpow__ __rlshift__
syn keyword pySpecialMethod  __rrshift__ __rand__ __rxor__ __ror__
syn keyword pySpecialMethod  __neg__ __pos__ __add__ __invert
syn keyword pySpecialMethod  __complex__ __int__ __long__ __float__
syn keyword pySpecialMethod  __oct__ __hex__ __invert__
syn keyword pySpecialMethod  __le__ __ge__ __eq__ __ne__ __lt__ __gt__
syn keyword pySpecialMethod  __coerce__
syn keyword pySpecialMethod  __floordiv__ __truediv__ __abs__ __rfloordiv__
syn keyword pySpecialMethod  __rtruediv__

" This is fast but code inside triple quoted strings screws it up. It
" is impossible to fix because the only way to know if you are inside a
" triple quoted string is to start from the beginning of the file. If
" you have a fast machine you can try uncommenting the "sync minlines"
" and commenting out the rest.
"syn sync match pythonSync grouphere NONE "):$"
"syn sync maxlines=200
"syn sync minlines=2000
syn sync minlines=1000

command -nargs=+ HiLink hi def link <args>

" The default methods for highlighting.  Can be overridden later
HiLink pythonStatement	Statement
"HiLink pythonFunction		Function
HiLink pythonConditional	Conditional
HiLink pythonRepeat		Repeat
HiLink pythonString		String
HiLink pythonRawString	String
HiLink pythonEscape		Special
HiLink pythonOperator		Operator
HiLink pythonPreCondit	PreCondit
HiLink pythonComment		Comment
HiLink pythonTodo		Todo
HiLink pythonNumber	Number
HiLink pythonBuiltin	Special
HiLink pythonException	Exception
HiLink pyTypedef           Structure
HiLink pySpecialMethod     Library
HiLink pythonSpecial     Library
HiLink pyDebug             Debug
HiLink pySyntaxError       Error
HiLink pySyntaxWarning     Error
HiLink pyBuiltinVariable   Library

delcommand HiLink

let b:current_syntax = "python"

" vim: ts=8
