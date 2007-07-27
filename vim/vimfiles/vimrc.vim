" Mostly the .vimrc file for Keith Dart. 
" You have to manually copy this to $VIM/vimfilesrc if you want to use it.

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
  autocmd FileType html	:so $VIM/vimfiles/html.vim
  autocmd FileType dtd	:so $VIM/vimfiles/xml_dtd.vim
  autocmd FileType xml	:so $VIM/vimfiles/xml.vim
  autocmd FileType javascript  :so $VIM/vimfiles/jsdev.vim
augroup END

augroup newfile 
  au!
  autocmd BufNewFile            *.html  0r      $VIM/vimfiles/html_template.html
  autocmd BufNewFile            *.c     0r      $VIM/vimfiles/c_template.c
  autocmd BufNewFile            *.py    0r      $VIM/vimfiles/py_template.py
augroup END


" augroup text
"  autocmd BufRead /tmp/pico* :set tw=72 comments=rb:> noai
"  autocmd FileType text :set tw=74 noai | menu Edit.Spell\ Check :update<CR>:!aspell check %<CR>:e! %<CR>
"  autocmd FileType structuredtext :so $VIM/vimfiles/structuredtext.vim
" augroup END

augroup email
  autocmd FileType mail :set tw=72 noai fo+=tcql comments=nb:>| :nmap q :wq<CR>| :imap <C-x> <Esc>:wq<CR>
augroup END


 augroup gzip
  " Remove all gzip autocommands
  au!

  " Enable editing of gzipped files
  "	  read:	set binary mode before reading the file
  "		uncompress text in buffer after reading
  "	 write:	compress file after writing
  "	append:	uncompress file, append, compress file
  autocmd BufReadPre,FileReadPre	*.gz set bin
  autocmd BufReadPost,FileReadPost	*.gz let ch_save = &ch|set ch=2
  autocmd BufReadPost,FileReadPost	*.gz '[,']!gunzip
  autocmd BufReadPost,FileReadPost	*.gz set nobin
  autocmd BufReadPost,FileReadPost	*.gz let &ch = ch_save|unlet ch_save
  autocmd BufReadPost,FileReadPost	*.gz execute ":doautocmd BufReadPost " . expand("%:r")

  autocmd BufWritePost,FileWritePost	*.gz !mv <afile> <afile>:r
  autocmd BufWritePost,FileWritePost	*.gz !gzip <afile>:r

  autocmd FileAppendPre			*.gz !gunzip <afile>
  autocmd FileAppendPre			*.gz !mv <afile>:r <afile>
  autocmd FileAppendPost		*.gz !mv <afile> <afile>:r
  autocmd FileAppendPost		*.gz !gzip <afile>:r
 augroup END

if v:progname == "mvim"
	set cursorcolumn
	gui
endif


" Enable menus in screen vim, and switch buffers with control arrow.
if v:progname == "svim"
	source $VIMRUNTIME/menu.vim
	set wildmenu
	set cpo-=<
	set wcm=<C-Z>
	map <F4> :emenu <C-Z>
	set hidden
        nmap <Esc>[5D :bp<CR>                                                                                                       
        nmap <Esc>[5C :bn<CR>                                                                                                       
        nmap <Esc>[3^ :bd<CR>                                                                                                       
        nmap ZZ :bd<CR>                                                                                                             
endif

