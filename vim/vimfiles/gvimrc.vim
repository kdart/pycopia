" The commands in this are executed when the GUI is started.
" Copy this to ~/.gvimrc if you want to use it.

set visualbell
set number

set encoding=utf-8
set guifont=Andale\ Mono\ 10

set lines=58
set columns=100

" Make command line two lines high
set cmdheight=3
set listchars=eol:$,trail:·,extends:>,precedes:<,tab:»·

set background="dark"

  " Switch on syntax highlighting.
syntax enable

  " Switch on search pattern highlighting.
set hlsearch
:map <F7> :set hls!<CR>

  " Hide the mouse pointer while typing
set mousehide
set mousefocus

" set kp=devhelp\ -s 
set dict=/usr/share/dict/words

colorscheme kwdcolors

if v:progname == "mvim"
	map <M-Left> :bp<CR>
	map <M-Right> :bn<CR>
	map <M-Del> :bd<CR>
	map ZZ :bd<CR>
endif

