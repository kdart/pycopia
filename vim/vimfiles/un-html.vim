" SECTION 1: Setup menus and associated mapped keyboard shortcuts
"
"" Menu HTML Tags
"
""" Comment:
if has("gui")
  unmenu HTML\ Tags.Comment\ \ \ \ \ ;cm
endif
unmap	;cm
unmap!	;cm
"
""" Name Anchor:
if has("gui")
  unmenu HTML\ Tags.Name\ Anchor\ ;an
endif
unmap	;an
unmap!	;an
"
""" Href Anchor:
if has("gui")
  unmenu HTML\ Tags.Href\ Anchor\ ;ah
endif
unmap	;ah
unmap!	;ah
"
""" Image:
if has("gui")
  unmenu HTML\ Tags.Image\ \ \ \ \ \ \ ;im
endif
unmap	;im
unmap!	;im
"
""" Break:
if has("gui")
  unmenu HTML\ Tags.Break\ \ \ \ \ \ \ ;br
endif
unmap	;br
unmap!	;br
"
""" Horizontal Rule:
if has("gui")
  unmenu HTML\ Tags.Rule\ \ \ \ \ \ \ \ ;hr
endif
unmap	;hr
unmap!	;hr
"
""" Headings Sub-Menu
"""" H1 Heading
if has("gui")
  unmenu HTML\ Tags.Headings.H1\ \ ;h1
endif
unmap	;h1
unmap!	;h1
"
"""" H2 Heading
if has("gui")
  unmenu HTML\ Tags.Headings.H2\ \ ;h2
endif
unmap	;h2
unmap!	;h2
"
"""" H3 Heading
if has("gui")
  unmenu HTML\ Tags.Headings.H3\ \ ;h3
endif
unmap	;h3
unmap!	;h3
"
"""" H4 Heading
if has("gui")
  unmenu HTML\ Tags.Headings.H4\ \ ;h4
endif
unmap	;h4
unmap!	;h4
"
"""" H5 Heading
if has("gui")
  unmenu HTML\ Tags.Headings.H5\ \ ;h5
endif
unmap	;h5
unmap!	;h5
"
"""" H6 Heading
if has("gui")
  unmenu HTML\ Tags.Headings.H6\ \ ;h6
endif
unmap	;h6
unmap!	;h6
"
"
""" Format:
" Address format
if has("gui")
  unmenu HTML\ Tags.Formats.Address\ \ \ \ \ ;ad
endif
unmap	;ad
unmap!	;ad
"
" Bold format
if has("gui")
  unmenu HTML\ Tags.Formats.Bold\ \ \ \ \ \ \ \ ;bo
endif
unmap	;bo
unmap!	;bo
"
" Big format
if has("gui")
  unmenu HTML\ Tags.Formats.Bigger\ \ \ \ \ \ ;bi
endif
unmap	;bi
unmap!	;bi
"
" Blink format - you might take this out to discourage use
if has("gui")
  unmenu HTML\ Tags.Formats.Blink\ \ \ \ \ \ \ ;bk
endif
unmap	;bk
unmap!	;bk
"
" Blockquote format
if has("gui")
  unmenu HTML\ Tags.Formats.Blockquote\ \ ;bl
endif
unmap	;bl
unmap!	;bl
"
" Center format
if has("gui")
  unmenu HTML\ Tags.Formats.Center\ \ \ \ \ \ ;ce
endif
unmap	;ce
unmap!	;ce
"
" Cite format
if has("gui")
  unmenu HTML\ Tags.Formats.Cite\ \ \ \ \ \ \ \ ;ci
endif
unmap	;ci
unmap!	;ci
"
" Code format
if has("gui")
  unmenu HTML\ Tags.Formats.Code\ \ \ \ \ \ \ \ ;co
endif
unmap	;co
unmap!	;co
"
" Definition format
if has("gui")
  unmenu HTML\ Tags.Formats.Definition\ \ ;df
endif
unmap	;df
unmap!	;df
"
" Emphasis format
if has("gui")
  unmenu HTML\ Tags.Formats.Emphasis\ \ \ \ ;em
endif
unmap	;em
unmap!	;em
"
" Italics format
if has("gui")
  unmenu HTML\ Tags.Formats.Italics\ \ \ \ \ ;it
endif
unmap	;it
unmap!	;it
"
" Keyboard format
if has("gui")
  unmenu HTML\ Tags.Formats.Keyboard\ \ \ \ ;kb
endif
unmap	;kb
unmap!	;kb
"
" No break format
if has("gui")
  unmenu HTML\ Tags.Formats.No\ Break\ \ \ \ ;nb
endif
unmap	;nb
unmap!	;nb
"
" Pre format
if has("gui")
  unmenu HTML\ Tags.Formats.Preformat\ \ \ ;pr
endif
unmap	;pr
unmap!	;pr
"
" Strike format
if has("gui")
  unmenu HTML\ Tags.Formats.Strike\ \ \ \ \ \ ;sk
endif
unmap	;sk
unmap!	;sk
"
" Sample format
if has("gui")
  unmenu HTML\ Tags.Formats.Sample\ \ \ \ \ \ ;sa
endif
unmap	;sa
unmap!	;sa
"
" Small format
if has("gui")
  unmenu HTML\ Tags.Formats.Smaller\ \ \ \ \ ;sm
endif
unmap	;sm
unmap!	;sm
"
" Strong format
if has("gui")
  unmenu HTML\ Tags.Formats.Strong\ \ \ \ \ \ ;st
endif
unmap	;st
unmap!	;st
"
" Subscript format
if has("gui")
  unmenu HTML\ Tags.Formats.Subscript\ \ \ ;sb
endif
unmap	;sb
unmap!	;sb
"
" Superscript format
if has("gui")
  unmenu HTML\ Tags.Formats.Superscript\ ;sp
endif
unmap	;sp
unmap!	;sp
"
" Typewriter heading
if has("gui")
  unmenu HTML\ Tags.Formats.Typerwriter\ ;tt
endif
unmap	;tt
unmap!	;tt
"
" Underline heading
if has("gui")
  unmenu HTML\ Tags.Formats.Underline\ \ \ ;uu
endif
unmap	;uu
unmap!	;uu
"
" Variable format
if has("gui")
  unmenu HTML\ Tags.Formats.Variable\ \ \ \ ;vv
endif
unmap	;vv
unmap!	;vv
"
""" List Sub-Menu
"""" list Item -
if has("gui")
  unmenu HTML\ Tags.List.List\ Item\ \ \ \ \ \ \ ;li
endif
unmap	;li
unmap!	;li
"
"""" list Header
if has("gui")
  unmenu HTML\ Tags.List.List\ Header\ \ \ \ \ ;lh
endif
unmap	;lh
unmap!	;lh
"
"""" Unordered List
if has("gui")
  unmenu HTML\ Tags.List.Unordered\ List\ \ ;ul
endif
unmap	;ul
unmap!	;ul
"
"""" Ordered List
if has("gui")
  unmenu HTML\ Tags.List.Ordered\ List\ \ \ \ ;ol
endif
unmap	;ol
unmap!	;ol
"
"""" Directory List
if has("gui")
  unmenu HTML\ Tags.List.Directory\ List\ \ ;di
endif
unmap	;di
unmap!	;di
"
"""" Menu List
if has("gui")
  unmenu HTML\ Tags.List.Menu\ List\ \ \ \ \ \ \ ;mu
endif
unmap	;mu
unmap!	;mu
"
"""" Definition Item
if has("gui")
  unmenu HTML\ Tags.List.Definition\ \ \ \ \ \ ;dt
endif
unmap	;dt
unmap!	;dt
"
"""" Definition list
if has("gui")
  unmenu HTML\ Tags.List.Definition\ List\ ;dl
endif
unmap	;dl
unmap!	;dl
"
" SECTION 2: macros unassociated with menus
" ABBREV (3.0)
unmap!	;ab
" ACRONYM (3.0)
unmap!	;ac
" AU (Author) (3.0)
unmap!	;au
" BANNER (3.0)
unmap!	;ba
" BASE (head)
unmap!	;bh
" BASEFONT (Netscape)
unmap!	;bf
" BODY
unmap!	;bd
" CAPTION (3.0)
unmap!	;ca
" CREDIT (3.0)
unmap!	;cr
" DD (definition for definition list)
unmap!	;dd
" DEL (deleted text) (3.0)
unmap!	;de
" DIV (document division) (3.0)
unmap!	;dv
" FIG (figure) (3.0)
unmap!	;fi
" FN (footnote) (3.0)
unmap!	;fn
" FONT (Netscape)
unmap!	;fo
" HEAD
unmap!	;he
" HTML (3.0)
unmap!	;ht
" INS (inserted text) (3.0)
unmap!	;in
" LANG (language context) (3.0)
unmap!	;la
" LINK (head)
unmap!	;lk
" META (head)
unmap!	;me
" NOTE (3.0)
unmap!	;no
" OVERLAY (figure overlay image) (3.0)
unmap!	;ov
" P (paragraph)
unmap!	;pp
" Q (quote) (3.0)
unmap!	;qu
" RANGE (3.0) (head)
unmap!	;ra
" STYLE (3.0)
unmap!	;sn
" TAB (3.0)
unmap!	;ta
" TITLE (head)
unmap!	;ti
" WBR (word break) (Netscape)
unmap!	;wb
" Special Characters
unmap!	;&
unmap!	;cp
"   this causes an error on my system
"unmap!	;"
unmap!	;<
unmap!	;>
"
"
" SECTION 3: Additional Autocommands
"
" should these be unset ? - TODO
"
""" read in skeleton file
":au BufNewFile		*.html	0r 	~/.vim/skeleton.html
""" Setup browser to display when writing files
":au BufWritePost	*.html		!netscape -remote 'openFile(%:p)'
""" Change modification data in first 30 lines of file (from vim help)
":au BufWritePre *.html 			ks|1,30g/Last modification: /normal f:lD:read !datekJ's
