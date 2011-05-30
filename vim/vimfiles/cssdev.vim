if ! has("python")
  echomsg "*** no Python!"
  finish
endif

if exists("g:cssdev_loaded")
  finish
endif
:let g:cssdev_loaded = 1


set ts=4 sw=4 tw=100 expandtab softtabstop=4 smarttab
set formatoptions=crql cino=(8 ai smartindent
set comments=s1:/*,mb:*,ex:*/,b://
set iskeyword=@,#,48-57,_,^;
set omnifunc=csscomplete#CompleteCSS

if has("gui_gtk") && has("gui_running")
	:python from pycopia.vimlib.cssdev import *
	:py os.environ["VIMSERVER"] = vim.eval("v:servername")
endif

vmap ;ec :python edit_color_visual_selection()<CR>

vmenu Css.Range.Edit\ Color\ (ec) :python edit_color_visual_selection()<CR>

