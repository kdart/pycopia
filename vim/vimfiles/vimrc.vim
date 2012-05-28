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

set dir=~/.vim/tmp//
" following improves performance when using NFS. You might want to change
" it to someplace more private.
" set dir=/var/tmp//
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
set printencoding=utf-8
set popt=paper:letter

" Only do this part when compiled with support for autocommands
if has("autocmd")
  " In text files, always limit the width of text to 75 characters
  " When editing a file, always jump to the last cursor position
  autocmd BufReadPost * if line("'\"") | exe "'\"" | endif
endif

" Don't use Ex mode, use Q for formatting
map Q gq
inoremap <C-space> <C-x><C-o>

" Switch syntax highlighting on, when the terminal has colors
" Also switch on highlighting the last used search pattern.
if &t_Co > 2 || has("gui_running")
  syntax enable
  set hlsearch
  colorscheme kwdcolors
endif

filetype plugin on
filetype indent on

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
  autocmd BufNewFile            *.vala,*.vapi 0r ~/Templates/Vala.vala
  autocmd BufNewFile            *.html  0r      ~/Templates/HTML5.html
  autocmd BufNewFile            *.xhtml 0r      ~/Templates/XHTML.xhtml
  autocmd BufNewFile            *.c     0r      ~/Templates/C.c
  autocmd BufNewFile            *.py    0r      ~/Templates/Python.py
  autocmd BufNewFile            *.rst   0r      ~/Templates/RST.rst
  autocmd BufNewFile            *.txt   0r      ~/Templates/RST.rst
  autocmd BufNewFile            *.txt   :set tw=74 noai comments=nb:>
"  autocmd BufNewFile            /tmp/pico*   :set tw=72 noai comments=nb:>
augroup END

augroup vala
  autocmd BufRead,BufNewFile  *.vala,*.vapi set ft=vala
  autocmd FileType vala :so ~/.vim/vala.vim
augroup END


augroup email
  autocmd FileType mail :set tw=72 noai fo+=tcql comments=nb:>| :nmap q :wq<CR>| :imap <C-x> <Esc>:wq<CR>
augroup END


if v:progname == "mvim"
	set cursorcolumn
	gui
endif

" Enable menus in console vim, and control-{left,right} to change buffers.
if v:progname == "svim"
    source $VIMRUNTIME/menu.vim
    set wildmenu
    set cpo-=<
    set wcm=<C-Z>
    map <F4> :emenu <C-Z>
    nmap ZZ :bd<CR>
    if $TERM =~ "screen"
       nmap <Esc>[D  :bp<CR>
       nmap <Esc>[C  :bn<CR>
    elseif $TERM =~ "rxvt"
       nmap <Esc>Od  :bp<CR>
       nmap <Esc>OD  :bp<CR>
       nmap <Esc>[5C :bn<CR>
       nmap <Esc>Oc  :bn<CR>
    endif
endif


if &diff
   nmap ZZ :qall!<CR>
endif

function! SuperCleverTab()
    if strpart(getline('.'), 0, col('.') - 1) =~ '^\s*$'
        return "\<Tab>"
    else
        if &omnifunc != ''
            return "\<C-X>\<C-O>"
        elseif &dictionary != ''
            return "\<C-K>"
        else
            return "\<C-N>"
        endif
    endif
endfunction
 
inoremap <Tab> <C-R>=SuperCleverTab()<CR>

let g:snips_author = 'My Name'

