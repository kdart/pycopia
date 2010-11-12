" Mostly the .vimrc file for Keith Dart. 
" You have to manually copy this to $HOME/.vimrc if you want to use it.

if has("python")
	python import sys
	python import os
	python import vim
	python sys.argv = [vim.eval("v:progname")] 
endif

set nocompatible	" Use Vim defaults (much better!)
set bs=2		" allow backspacing over everything in insert mode
" set ai
set nobackup		" keep a backup file
set viminfo='20,\"90,h,%	" read/write a .viminfo file
set history=500
" set ruler		" show the cursor position all the time
set statusline=%<%f%m%r%y%=%b\ 0x%B\ \ %l,%c%V\ %P
set laststatus=2  " always a status line

" following improves performance when using NFS. You might want to change
" it to someplace more private.
set dir=/var/tmp//
" set undodir=~/.vim/tmp/undo//
set hidden

set incsearch
set ignorecase
set smartcase

set scrolloff=3

" GUI options that need to be set here first
set guioptions-=T
set guioptions+=t

set encoding=utf-8

" Only do this part when compiled with support for autocommands
if has("autocmd")
  " In text files, always limit the width of text to 75 characters
  " When editing a file, always jump to the last cursor position
  autocmd BufReadPost * if line("'\"") | exe "'\"" | endif
endif

" Don't use Ex mode, use Q for formatting
map Q gq

" Switch syntax highlighting on, when the terminal has colors
" Also switch on highlighting the last used search pattern.
if &t_Co > 2 || has("gui_running")
  syntax enable
  set hlsearch
  colorscheme kwdcolors
endif

augroup cprog
  " Remove all cprog autocommands
  au!

  " When starting to edit a file:
  "   For C and C++ files set formatting of comments and set C-indenting on.
  "   For other files switch it off.
  "   Don't change the order, it's important that the line with * comes first.
  autocmd FileType *      set formatoptions=tcql nocindent comments&
  autocmd FileType c,cpp  set formatoptions=croql cindent comments=sr:/*,mb:*,el:*/,://
augroup END

augroup pycopia
  autocmd FileType python :so $VIM/vimfiles/pydev.vim
  autocmd FileType pyrex  :so $VIM/vimfiles/pydev.vim
  autocmd FileType html	:so $VIM/vimfiles/html.vim
  autocmd FileType xhtml	:so $VIM/vimfiles/html.vim
  autocmd FileType dtd	:so $VIM/vimfiles/xml_dtd.vim
  autocmd FileType xml	:so $VIM/vimfiles/xml.vim
  autocmd FileType javascript  :so $VIM/vimfiles/jsdev.vim
  autocmd FileType css  :so $VIM/vimfiles/cssdev.vim
augroup END

augroup newfile 
  au!
  autocmd BufNewFile            *.html  0r      ~/Templates/HTML4.html
  autocmd BufNewFile            *.xhtml 0r      ~/Templates/XHTML.xhtml
  autocmd BufNewFile            *.c     0r      ~/Templates/C.c
  autocmd BufNewFile            *.py    0r      ~/Templates/Python.py
augroup END


" augroup text
"  autocmd BufRead /tmp/pico* :set tw=72 comments=rb:> noai
"  autocmd FileType text :set tw=74 noai | menu Edit.Spell\ Check :update<CR>:!aspell check %<CR>:e! %<CR>
"  autocmd FileType structuredtext :so $VIM/vimfiles/structuredtext.vim
" augroup END

augroup email
  autocmd FileType mail :set tw=72 noai fo+=tcql comments=nb:>| :nmap q :wq<CR>| :imap <C-x> <Esc>:wq<CR>
augroup END


if v:progname == "mvim"
	set cursorcolumn
	gui
endif

" Enable menus in screen vim (invoke vim as svim with symlink), and switch
" buffers with control arrow.
if v:progname == "svim"
	source $VIMRUNTIME/menu.vim
	set wildmenu
	set cpo-=<
	set wcm=<C-Z>
	map <F4> :emenu <C-Z>
	set hidden
       nmap <Esc>[5D :bp<CR>
       nmap <Esc>Od  :bp<CR>
       nmap <Esc>OD  :bp<CR>
       nmap <Esc>[5C :bn<CR>
       nmap <Esc>Oc  :bn<CR>
       nmap <Esc>OC  :bn<CR>
       nmap <Esc>[3~ :bd<CR>
       nmap ZZ :bd<CR>
endif

