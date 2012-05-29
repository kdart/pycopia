" Vim color file

" This color scheme uses a black background.
set background=dark

" First remove all existing highlighting.
hi clear
if exists("syntax_on")
  syntax reset
endif

let colors_name = "kwdcolors"

hi CursorColumn term=reverse ctermbg=DarkGrey guifg=grey90 guibg=Grey20
hi Cursor guibg=LimeGreen guifg=NONE
hi CursorLine term=underline cterm=underline guibg=Grey20
hi DiffAdd term=bold ctermfg=white ctermbg=darkblue guibg=#0000AA guifg=white
hi DiffChange term=reverse ctermfg=white ctermbg=black guibg=background guifg=White
hi DiffDelete term=underline ctermfg=black ctermbg=darkred guibg=#220000 guifg=grey
hi DiffText term=NONE cterm=reverse guifg=lightred guibg=#222200
hi Directory term=bold ctermfg=white guifg=White
hi ErrorMsg term=standout ctermbg=DarkBlue ctermfg=Grey guibg=Red guifg=White
hi FoldColumn term=standout ctermbg=Grey ctermfg=DarkBlue guibg=Grey guifg=DarkBlue
hi Folded term=standout ctermbg=Grey ctermfg=DarkBlue guibg=LightGrey guifg=DarkBlue
hi IncSearch term=reverse cterm=reverse gui=reverse
hi lCursor guibg=Cyan guifg=NONE
hi LineNr term=underline ctermfg=brown guifg=Brown
hi ModeMsg term=bold cterm=bold gui=bold
hi MoreMsg term=bold ctermfg=DarkGreen guifg=SeaGreen
hi NonText guibg=grey10
hi Normal ctermfg=Grey ctermbg=Black  guifg=grey90 guibg=black
hi Pmenu guifg=#c0c0c0 guibg=#404080
hi PmenuSbar ctermfg=cyan ctermbg=brown guifg=blue guibg=darkgray
hi PmenuSel guifg=#c0c0c0 guibg=#2050d0
hi PmenuThumb ctermfg=black ctermbg=grey guifg=#c0c0c0
hi Question term=standout ctermfg=DarkGreen guifg=DeepPink
hi Search term=reverse ctermfg=Black ctermbg=brown guibg=Yellow guifg=black
hi SpecialKey term=bold ctermfg=darkmagenta guifg=Blue
hi Spell term=bold ctermfg=darkmagenta guifg=Blue
hi SpellBad term=reverse ctermbg=red gui=undercurl guisp=Blue
hi SpellCap term=reverse ctermbg=blue gui=undercurl guisp=Red
hi SpellRare term=reverse ctermbg=magenta gui=undercurl guisp=Magenta
hi SpellLocal term=underline ctermfg=black ctermbg=yellow gui=undercurl guisp=Cyan
hi StatusLineNC term=reverse cterm=reverse gui=reverse
hi StatusLine term=reverse,bold cterm=reverse,bold gui=reverse,bold
hi Title term=bold ctermfg=DarkMagenta ctermbg=Black gui=bold guifg=Magenta
hi VertSplit term=reverse cterm=reverse gui=reverse
hi VisualNOS term=underline,bold cterm=underline,bold guibg=grey40 guifg=black
hi Visual term=reverse cterm=reverse gui=NONE guifg=black guibg=white
hi WarningMsg term=standout ctermfg=LightRed ctermbg=Black guifg=Red
hi WildMenu term=standout ctermbg=Yellow ctermfg=Black guibg=Yellow guifg=Black

" Colors for syntax highlighting
hi Comment cterm=NONE ctermfg=DarkCyan ctermbg=Black guifg=skyblue guibg=black
hi Constant cterm=NONE ctermfg=brown ctermbg=Black guifg=salmon guibg=black
hi Debug ctermfg=lightgreen ctermbg=Black guifg=#ff80ff
hi Define ctermfg=green ctermbg=Black guifg=#ff80ff
hi Error term=reverse ctermfg=LightRed ctermbg=DarkBlue guifg=White guibg=Red
hi Exception cterm=underline ctermfg=DarkRed ctermbg=Black  guifg=PaleVioletRed guibg=black
hi Identifier term=NONE ctermfg=white ctermbg=Black guifg=PeachPuff
hi Ignore ctermfg=blue ctermbg=Black  guifg=grey30
hi Keyword cterm=NONE ctermfg=DarkGreen ctermbg=Black guifg=green guibg=black
hi Library ctermfg=white ctermbg=Black guifg=NavajoWhite1
hi MatchParen term=reverse ctermfg=White ctermbg=black gui=bold guibg=black guifg=Yellow
hi PreProc ctermfg=green ctermbg=Black guifg=#ff80ff
hi Special ctermfg=DarkMagenta ctermbg=Black guifg=violet guibg=black
hi SpecialStatement term=bold ctermfg=lightgreen ctermbg=DarkRed guifg=black guibg=#00FA9A
hi Statement term=bold ctermfg=green ctermbg=Black  guifg=#00FA9A
hi Structure ctermfg=green guifg=green 
hi Todo  term=bold ctermfg=blue ctermbg=Grey guifg=Blue guibg=Yellow
hi Type term=underline ctermfg=DarkGreen ctermbg=Black gui=bold guifg=#60ff60
hi Underlined term=underline cterm=underline ctermfg=Grey ctermbg=Black gui=underline guifg=grey90


" vim: sw=2
