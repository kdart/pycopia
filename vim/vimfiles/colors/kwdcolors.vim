" Vim color file

" This color scheme uses a black background.

" First remove all existing highlighting.
set background=dark
hi clear
if exists("syntax_on")
  syntax reset
endif

let colors_name = "mycolors"

hi Normal ctermfg=7 ctermbg=0  guifg=grey90 guibg=black
hi Cursor guibg=LimeGreen guifg=NONE
hi lCursor guibg=Cyan guifg=NONE
hi NonText guibg=grey10
hi ErrorMsg term=standout ctermbg=1 ctermfg=7 guibg=Red guifg=White
hi Search term=reverse ctermbg=3 ctermfg=0 guibg=Yellow guifg=black
hi Visual term=reverse cterm=reverse gui=NONE guifg=black guibg=white
hi VisualNOS term=underline,bold cterm=underline,bold guibg=grey40 guifg=black
hi IncSearch term=reverse cterm=reverse gui=reverse
hi ModeMsg term=bold cterm=bold gui=bold
hi StatusLine term=reverse,bold cterm=reverse,bold gui=reverse,bold
hi StatusLineNC term=reverse cterm=reverse gui=reverse
hi VertSplit term=reverse cterm=reverse gui=reverse
hi DiffText term=reverse cterm=bold ctermbg=Red gui=bold guibg=Red
hi Directory term=bold ctermfg=DarkBlue guifg=Blue
hi LineNr term=underline ctermfg=Brown guifg=Brown
hi MoreMsg term=bold ctermfg=DarkGreen guifg=SeaGreen
hi Question term=standout ctermfg=DarkGreen guifg=DeepPink
hi SpecialKey term=bold ctermfg=DarkBlue guifg=Blue
hi Title term=bold cterm=bold ctermfg=5 ctermbg=0 gui=bold guifg=Magenta
hi WarningMsg term=standout cterm=bold ctermfg=1 ctermbg=0 guifg=Red
hi WildMenu term=standout ctermbg=Yellow ctermfg=Black guibg=Yellow guifg=Black
hi Folded term=standout ctermbg=Grey ctermfg=DarkBlue guibg=LightGrey guifg=DarkBlue
hi FoldColumn term=standout ctermbg=Grey ctermfg=DarkBlue guibg=Grey guifg=DarkBlue
hi DiffAdd term=bold ctermbg=LightBlue guibg=LightBlue guibg=Black
hi DiffChange term=bold ctermbg=LightMagenta guibg=LightMagenta guifg=Black
hi DiffDelete term=bold ctermfg=Blue ctermbg=LightCyan guibg=LightCyan guifg=Black
hi CursorColumn term=reverse ctermbg=8 guifg=grey90 guibg=Grey20
hi CursorLine term=underline cterm=underline guibg=Grey20

" Colors for syntax highlighting
hi Constant cterm=NONE ctermfg=3 ctermbg=0 guifg=salmon guibg=black
hi Special cterm=bold ctermfg=5 ctermbg=0 guifg=violet guibg=black
hi Comment cterm=NONE ctermfg=6 ctermbg=0 guifg=skyblue guibg=black
hi Exception cterm=underline ctermfg=3 ctermbg=0  guifg=PaleVioletRed guibg=black
hi Library cterm=bold ctermfg=6 ctermbg=0 guifg=NavajoWhite1
hi Identifier term=NONE ctermfg=6 ctermbg=0 guifg=PeachPuff
hi Keyword cterm=NONE ctermfg=2 ctermbg=0 guifg=green guibg=black
hi Statement term=bold cterm=bold ctermfg=3 ctermbg=0  guifg=#00FA9A
hi SpecialStatement term=bold cterm=bold ctermfg=3 ctermbg=0 guifg=black guibg=#00FA9A
hi PreProc ctermfg=9 guifg=#ff80ff
hi Type term=underline ctermfg=10 gui=bold guifg=#60ff60
hi Underlined term=underline cterm=underline ctermfg=9 gui=underline guifg=grey90
hi MatchParen term=reverse ctermfg=White ctermbg=Black gui=bold guibg=black guifg=Yellow
hi Ignore ctermfg=0 guifg=grey90
hi Error term=reverse ctermfg=15 ctermbg=12 guifg=White guibg=Red
hi Todo  term=standout ctermfg=0 ctermbg=14 guifg=Blue guibg=Yellow
hi Define ctermfg=9 guifg=#ff80ff



" vim: sw=2
