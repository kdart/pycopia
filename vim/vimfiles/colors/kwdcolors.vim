" Vim color file

" This color scheme uses a black background.

" First remove all existing highlighting.
set background=dark
hi clear
if exists("syntax_on")
  syntax reset
endif

let colors_name = "kwdcolors"

hi Normal ctermfg=Grey ctermbg=Black  guifg=grey90 guibg=black
hi Cursor guibg=LimeGreen guifg=NONE
hi lCursor guibg=Cyan guifg=NONE
hi NonText guibg=grey10
hi ErrorMsg term=standout ctermbg=DarkBlue ctermfg=Grey guibg=Red guifg=White
hi Search term=reverse ctermfg=Black ctermbg=DarkYellow guibg=Yellow guifg=black
hi Visual term=reverse cterm=reverse gui=NONE guifg=black guibg=white
hi VisualNOS term=underline,bold cterm=underline,bold guibg=grey40 guifg=black
hi IncSearch term=reverse cterm=reverse gui=reverse
hi ModeMsg term=bold cterm=bold gui=bold
hi StatusLine term=reverse,bold cterm=reverse,bold gui=reverse,bold
hi StatusLineNC term=reverse cterm=reverse gui=reverse
hi VertSplit term=reverse cterm=reverse gui=reverse
hi DiffText term=reverse ctermbg=Red gui=bold guibg=Red
hi Directory term=bold ctermfg=DarkBlue guifg=Blue
hi LineNr term=underline ctermfg=DarkYellow guifg=Brown
hi MoreMsg term=bold ctermfg=DarkGreen guifg=SeaGreen
hi Question term=standout ctermfg=DarkGreen guifg=DeepPink
hi SpecialKey term=bold ctermfg=DarkBlue guifg=Blue
hi Title term=bold ctermfg=DarkMagenta ctermbg=Black gui=bold guifg=Magenta
hi WarningMsg term=standout ctermfg=LightRed ctermbg=Black guifg=Red
hi WildMenu term=standout ctermbg=Yellow ctermfg=Black guibg=Yellow guifg=Black
hi Folded term=standout ctermbg=Grey ctermfg=DarkBlue guibg=LightGrey guifg=DarkBlue
hi FoldColumn term=standout ctermbg=Grey ctermfg=DarkBlue guibg=Grey guifg=DarkBlue
hi DiffAdd term=bold ctermfg=LightBlue ctermbg=Black guibg=LightBlue guibg=Black
hi DiffChange term=bold ctermbg=LightMagenta guibg=Black guifg=Black
hi DiffDelete term=bold ctermfg=LightRed ctermbg=Black guibg=LightCyan guifg=Black
hi CursorColumn term=reverse ctermbg=DarkGrey guifg=grey90 guibg=Grey20
hi CursorLine term=underline cterm=underline guibg=Grey20

" Colors for syntax highlighting
hi Constant cterm=NONE ctermfg=DarkYellow ctermbg=Black guifg=salmon guibg=black
hi Special ctermfg=DarkMagenta ctermbg=Black guifg=violet guibg=black
hi Comment cterm=NONE ctermfg=DarkCyan ctermbg=Black guifg=skyblue guibg=black
hi Exception cterm=underline ctermfg=DarkRed ctermbg=Black  guifg=PaleVioletRed guibg=black
hi Library ctermfg=DarkYellow ctermbg=Black guifg=NavajoWhite1
hi Identifier term=NONE ctermfg=DarkYellow ctermbg=Black guifg=PeachPuff
hi Keyword cterm=NONE ctermfg=DarkGreen ctermbg=Black guifg=green guibg=black
hi Statement term=bold ctermfg=DarkCyan ctermbg=Black  guifg=#00FA9A
hi SpecialStatement term=bold ctermfg=LightCyan ctermbg=DarkRed guifg=black guibg=#00FA9A
hi PreProc ctermfg=DarkBlue ctermbg=Black guifg=#ff80ff
hi Type term=underline ctermfg=DarkGreen ctermbg=Black gui=bold guifg=#60ff60
hi Underlined term=underline cterm=underline ctermfg=Grey ctermbg=Black gui=underline guifg=grey90
hi MatchParen term=reverse ctermfg=White ctermbg=DarkBlue gui=bold guibg=black guifg=Yellow
hi Ignore ctermfg=DarkYellow ctermbg=Black  guifg=grey90
hi Error term=reverse ctermfg=LightRed ctermbg=DarkBlue guifg=White guibg=Red
hi Todo  term=bold ctermfg=DarkBlue ctermbg=Grey guifg=Blue guibg=Yellow
hi Define ctermfg=DarkBlue ctermbg=Black guifg=#ff80ff



" vim: sw=2
