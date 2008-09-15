if ! has("python")
  echomsg "*** no Python!"
  finish
endif

if exists("g:Python_loaded")
  finish
endif
:let g:Python_loaded = 1

" set Vim parameters that suite python best
set tm=2000

set formatoptions=croql ai smartindent nowrap comments=:# 
set cinwords=if,elif,else,for,while,try,except,finally,def,class 

" The 'NonText' highlighting will be used for 'eol', 'extends' and
" 'precedes'.  'SpecialKey' for 'tab' and 'trail'.
function PyUseSpaces()
	hi SpecialKey guifg=Red
	:set ts=4 sw=4 
	:set expandtab softtabstop=4 smarttab
	:set listchars=trail:·,extends:>,precedes:<,tab:*# list
endfunction

function PyUseTabs()
	hi SpecialKey guifg=Blue
	:set ts=4 sw=4 
	:set noexpandtab softtabstop=0 smarttab 
	:set nolist listchars=eol:$,trail:·,extends:>,precedes:<,tab:»·
endfunction

function GoogleSpaces()
	hi SpecialKey guifg=Red
	:set ts=2 sw=2 tw=74
	:set expandtab softtabstop=2 smarttab
	:set listchars=trail:·,extends:>,precedes:<,tab:*# list
endfunction

" by default, use spaces
:call GoogleSpaces()

" for running PyUnit
" setlocal efm=%C\ %.%#,%A\ \ File\ \"%f\"\\,\ line\ %l%.%#,%Z%[%^\ ]%\\@=%m
" setlocal makeprg=pyunittest

:python import sys, os
:python from pycopia.vimlib import *
" put VIMSERVER in environment for child python processes to use.
if has("gui_gtk") && has("gui_running")
	:py os.environ["VIMSERVER"] = vim.eval("v:servername")
endif

function! PyClean ()
	normal ma
	:retab
	:%s/\s\+$//eg
	normal 'a
endfunction

" function! PythonBalloon()
" 	python balloonhelp()
" 	return g:python_rv
" endfunction
" set bexpr=PythonBalloon()
" set ballooneval

nmenu Python.Syntax.Check\ (sy) :python syntax_check()<CR>
nmenu Python.Syntax.Use\ Spaces :call PyUseSpaces()<CR>
nmenu Python.Syntax.Use\ Tabs :call PyUseTabs()<CR>
nmenu Python.Syntax.Use\ Google :call GoogleSpaces()<CR>
nmenu Python.Syntax.No\ Tabs\ (:retab) :%retab<CR>
nmenu Python.Syntax.Clean\ (;cl) :call PyClean()<CR>
nmenu Python.Syntax.Tabify\ (:retab!) :%retab!<CR>
nmenu Python.Run.Run\ (be) :update<CR>:python execfile(vim.current.buffer.name, {}, {})<CR>
nmenu Python.Run.In\ term\ (ru) :update<CR>:python pyterm(vim.current.buffer.name, 0)<CR>
nmenu Python.Run.In\ term\ (interactive)(ri) :update<CR>:python pyterm(vim.current.buffer.name, 1)<CR>
nmenu Python.Run.Interactive\ shell\ (py) :python pyterm()<CR>
nmenu Python.Test.Run\ pyunit :make<CR>
nmenu Python.Evaluate\ Line\ (ev) :python print eval(vim.current.line)<CR>
vmenu Python.Range.Exec\ (ex) :python exec_vimrange(vim.current.range)<CR>
vmenu Python.Range.Exec\ in\ term\ (et) :python exec_vimrange_in_term(vim.current.range)<CR>

" execution/evaluation
nmap ;py :python pyterm()<CR>
nmap ;sy :python syntax_check()<CR>
nmap ;be :update<CR>:python execfile(vim.current.buffer.name, {}, {})<CR>
nmap ;ru :update<CR>:python pyterm(vim.current.buffer.name, 0)<CR>
nmap ;ri :update<CR>:python pyterm(vim.current.buffer.name, 1)<CR>
nmap ;ev :python print eval(vim.current.line)<CR>
nmap ;ex :python exec vim.current.line<CR>

vmap ;ex :python exec_vimrange(vim.current.range)<CR>
vmap ;et :python exec_vimrange_in_term(vim.current.range)<CR>
nmap ;el :python vim.current.line = str(eval(vim.current.line))<CR>

" convenient editing macros
nmap ;id :python insert_def()<CR>
nmap ;iv :python insert_viminfo()<CR>
nmap ;ia :python insert__all__()<CR>
nmap ;ed :python keyword_edit()<CR>
nmap ;vi :python keyword_view()<CR>
vmap ;ed :python visual_edit()<CR>
vmap ;vi :python visual_view()<CR>
vmap ;ht :python htmlhex_visual_selection()<CR>
nmap ;sp :python keyword_split()<CR>
nmap <F9> :python keyword_split()<CR>
" nmap K :python keyword_help()<CR>
nmap ;he :python keyword_help()<CR>
nmap ;in :python print get_indent_level()<CR>

" movement
map ;nd :python next_def()<CR>
map ;nc :python next_class()<CR>
map ;pd :python previous_def()<CR>
map ;pc :python previous_class()<CR>

" selections
map ;sc :python select_class()<CR>
map ;sd :python select_def()<CR>

" what shall it be? tabs or spaces?
nmap ;us :call PyUseSpaces()<CR>
nmap ;ut :call PyUseTabs()<CR>
nmap ;ug :call GoogleSpaces()<CR>

nmap ;ts :%retab<CR>
vmap ;ts :'<,'>retab<CR>
nmap ;st :%retab!<CR>
vmap ;st :'<,'>retab!<CR>
nmap ;cl :call PyClean()<CR>

