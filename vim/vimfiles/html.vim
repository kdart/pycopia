" will use Python to implement some editing functions
" vim:ts=4:sw=4:softtabstop=0:smarttab

:python from pycopia import vimlib
:python from pycopia.vimlib import vimhtml

:set mps+=<:>

vmap	;ta	:py vimhtml.text_to_table()<CR>
nmap	;ht	:py vimhtml.htmlify()<CR>
vmap	;ht	:py vimhtml.htmlify()<CR>
vmap	;un :py vimhtml.unhtmlify()<CR>
nmap	;ti	:%!tidy -i -asxhtml -utf8<CR>
vmap	;ti	:`<,`>!tidy -i -xml -utf8<CR>
vmap	;hx :py vimlib.htmlhex_visual_selection()<CR>

" SECTION 1: Setup menus and associated mapped keyboard shortcuts

"" Menu HTML Tags

""" Comment:
"	normal		new comment on previous line
"	visual		wrap visual selection in comment
"	insert		insert comment at cursor position
nmenu HTML\ Tags.Comment\ \ \ \ \ ;cm  :py vimhtml.commentline()<CR>
vmenu HTML\ Tags.Comment\ \ \ \ \ ;cm  :py vimhtml.comment_visual_selection()<CR>
imenu HTML\ Tags.Comment\ \ \ \ \ ;cm  <!--   --><Esc>5ha
nmap	;cm	:py vimhtml.commentline()<CR>
vmap	;cm	:py vimhtml.comment_visual_selection()<CR>
imap	;cm	<!--   --><Esc>5ha
"
" P (paragraph)
nmap	;pp O<p><CR></p><Esc>O
vmap	;pp <Esc>`>a</p><Esc>`<i<p><Esc>
imap	;pp <p>TEXT</p><Esc>3bcw
"
""" Name Anchor:
"	normal		creates name anchor on previous line
"	visual		wrap name anchor around current visual selection
"	insert		insert name anchor at cursor position
nmap	;an	O<a name="NAME"><Esc>2bcw
vmap	;an	<Esc>`>a"><Esc>`<i<a NAME="<Esc>l
imap	;an	<a name="NAME"><Esc>2bcw
"
""" Href Anchor:
"	normal		creates href anchor on previous line
"	visual		wraps href anchor around current visual selection
"	insert		inserts href anchor at cursor position
nmap	;ah	O<a href="URL">tag</a><Esc>5bcw
vmap	;ah	<Esc>`>a</a><Esc>`<i<a href="URL"><Esc>2bcw
imap	;ah	<a href="URL">tag</a><Esc>5bcw
"
""" Image:
"	normal		creates image on previous line
"	visual		creates image around current visual selection ??
"	insert		inserts image at cursor position
nmenu HTML\ Tags.Image\ \ \ \ \ \ \ ;im O<IMG src="URL" alt="IMAGE"><Esc>6bcw
vmenu HTML\ Tags.Image\ \ \ \ \ \ \ ;im <Esc>`>a" alt="IMAGE"><Esc>`<i<IMG src="><Esc>l
imenu HTML\ Tags.Image\ \ \ \ \ \ \ ;im <IMG src="URL" alt="IMAGE"><Esc>6bcw
nmap	;im	O<img src="URL" alt="IMAGE" /><Esc>6bcw
vmap	;im	<Esc>`>a" alt="IMAGE" /><Esc>`<i<img src="<Esc>l
imap	;im	<img src="URL" alt="IMAGE" /><Esc>6bcw
"
""" Break:
"	normal		creates break on previous line
"	visual		creates break before selection
"	insert		inserts break at cursor
nmenu HTML\ Tags.Break\ \ \ \ \ \ \ ;br	O<br><Esc>
vmenu HTML\ Tags.Break\ \ \ \ \ \ \ ;br	<Esc>`<i<br><Esc>
imenu HTML\ Tags.Break\ \ \ \ \ \ \ ;br	<br>
nmap	;br	O<br /><Esc>
vmap	;br	<Esc>`<i<br /><Esc>
imap	;br	<br />
"
""" Horizontal Rule:
"	normal		creates rule on previous line
"	visual		inserts rule before selection
"	insert		inserts rule at cursor
nmenu HTML\ Tags.Rule\ \ \ \ \ \ \ \ ;hr	O<hr><Esc>
vmenu HTML\ Tags.Rule\ \ \ \ \ \ \ \ ;hr	<Esc>`<i<hr><CR><Esc>
imenu HTML\ Tags.Rule\ \ \ \ \ \ \ \ ;hr	<hr><CR>
nmap	;hr	O<hr /><CR><Esc>
vmap	;hr	<Esc>`<i<hr /><CR><Esc>
imap	;hr	<hr /><CR>
"
""" Headings Sub-Menu
"	normal		creates selected heading on previous line
"	visual		creates selected heading around visual selection
"	insert		inserts selected heading at cursor position
"
"""" H1 Heading
nmenu HTML\ Tags.Headings.H1\ \ ;h1	O<h1>HEADING</h1><Esc>3bcw
vmenu HTML\ Tags.Headings.H1\ \ ;h1	<Esc>`>a</h1><Esc>`<i<h1><Esc>l
imenu HTML\ Tags.Headings.H1\ \ ;h1	<h1>HEADING</h1><Esc>3bcw
nmap	;h1	O<h1>HEADING</h1><Esc>3bcw
vmap	;h1	<Esc>`>a</h1><Esc>`<i<h1><Esc>l
imap	;h1	<h1>HEADING</h1><Esc>3bcw
"
"""" H2 Heading
nmenu HTML\ Tags.Headings.H2\ \ ;h2	O<h2>HEADING</h2><Esc>3bcw
vmenu HTML\ Tags.Headings.H2\ \ ;h2	<Esc>`>a</h2><Esc>`<i<h2><Esc>l
imenu HTML\ Tags.Headings.H2\ \ ;h2	<h2>HEADING</h2><Esc>3bcw
nmap	;h2	O<h2>HEADING</h2><Esc>3bcw
vmap	;h2	<Esc>`>a</h2><Esc>`<i<h2><Esc>l
imap	;h2	<h2>HEADING</h2><Esc>3bcw
"
"""" H3 Heading
nmenu HTML\ Tags.Headings.H3\ \ ;h3	O<h3>HEADING</h3><Esc>3bcw
vmenu HTML\ Tags.Headings.H3\ \ ;h3	<Esc>`>a</h3><Esc>`<i<h3><Esc>l
imenu HTML\ Tags.Headings.H3\ \ ;h3	<h3>HEADING</h3><Esc>3bcw
nmap	;h3	O<H3>HEADING</H3><Esc>3bcw
vmap	;h3	<Esc>`>a</H3><Esc>`<i<H3><Esc>l
imap	;h3	<H3>HEADING</H3><Esc>3bcw
"
"""" H4 Heading
nmenu HTML\ Tags.Headings.H4\ \ ;h4	O<h4>HEADING</h4><Esc>3bcw
vmenu HTML\ Tags.Headings.H4\ \ ;h4	<Esc>`>a</h4><Esc>`<i<h4><Esc>l
imenu HTML\ Tags.Headings.H4\ \ ;h4	<h4>HEADING</h4><Esc>3bcw
nmap	;h4	O<h4>HEADING</h4><Esc>3bcw
vmap	;h4	<Esc>`>a</h4><Esc>`<i<h4><Esc>l
imap	;h4	<h4>HEADING</h4><Esc>3bcw
"
"""" H5 Heading
nmenu HTML\ Tags.Headings.H5\ \ ;h5	O<h5>HEADING</h5><Esc>3bcw
vmenu HTML\ Tags.Headings.H5\ \ ;h5	<Esc>`>a</h5><Esc>`<i<h5><Esc>l
imenu HTML\ Tags.Headings.H5\ \ ;h5	<h5>HEADING</h5><Esc>3bcw
nmap	;h5	O<h5>HEADING</h5><Esc>3bcw
vmap	;h5	<Esc>`>a</h5><Esc>`<i<h5><Esc>l
imap	;h5	<h5>HEADING</h5><Esc>3bcw
"
"""" H6 Heading
nmenu HTML\ Tags.Headings.H6\ \ ;h6	O<h6>HEADING</h6><Esc>3bcw
vmenu HTML\ Tags.Headings.H6\ \ ;h6	<Esc>`>a</h6><Esc>`<i<h6><Esc>l
imenu HTML\ Tags.Headings.H6\ \ ;h6	<h6>HEADING</h6><Esc>3bcw
nmap	;h6	O<h6>HEADING</h6><Esc>3bcw
vmap	;h6	<Esc>`>a</h6><Esc>`<i<h6><Esc>l
imap	;h6	<h6>HEADING</h6><Esc>3bcw
"
""" Format:
"	normal		creates selected format on previous line
"	visual		creates selected format around visual selection
"	insert		creates selected format at cursor position
"
" Address format
nmap	;ad	O<address>TEXT</address><Esc>3bcw
vmap	;ad	<Esc>`>a</address><Esc>`<i<address><Esc>l
imap	;ad	<address>TEXT</address><Esc>3bcw
"
" Bold format
nmap	;bo	O<b>TEXT</b><Esc>3bcw
vmap	;bo	<Esc>`>a</b><Esc>`<i<b><Esc>l
imap	;bo	<b>TEXT</b><Esc>3bcw
"
" Big format
nmenu HTML\ Tags.Formats.Bigger\ \ \ \ \ \ ;bi	O<big>TEXT</big><Esc>3bcw
vmenu HTML\ Tags.Formats.Bigger\ \ \ \ \ \ ;bi	<Esc>`>a</big><Esc>`<i<big><Esc>l
imenu HTML\ Tags.Formats.Bigger\ \ \ \ \ \ ;bi	<big>TEXT</big><Esc>3bcw
nmap	;bi	O<big>TEXT</big><Esc>3bcw
vmap	;bi	<Esc>`>a</big><Esc>`<i<big><Esc>l
imap	;bi	<big>TEXT</big><Esc>3bcw
"

" Blockquote format
nmap	;bl	O<blockquote>TEXT</blockquote><Esc>3bcw
vmap	;bl	<Esc>`>a</blockquote><Esc>`<i<blockquote><Esc>l
imap	;bl	<blockquote>TEXT</blockquote><Esc>3bcw
"
" Center format
nmenu HTML\ Tags.Formats.Center\ \ \ \ \ \ ;ce	O<center>TEXT</center><Esc>3bcw
vmenu HTML\ Tags.Formats.Center\ \ \ \ \ \ ;ce	<Esc>`>a</center><Esc>`<i<center><Esc>l
imenu HTML\ Tags.Formats.Center\ \ \ \ \ \ ;ce	<center>TEXT</center><Esc>3bcw
nmap	;ce	O<center>TEXT</center><Esc>3bcw
vmap	;ce	<Esc>`>a</center><Esc>`<i<center><Esc>l
imap	;ce	<center>TEXT</center><Esc>3bcw
"
" Cite format
nmenu HTML\ Tags.Formats.Cite\ \ \ \ \ \ \ \ ;ci	O<CITE>TEXT</CITE><Esc>3bcw
vmenu HTML\ Tags.Formats.Cite\ \ \ \ \ \ \ \ ;ci	<Esc>`>a</CITE><Esc>`<i<CITE><Esc>l
imenu HTML\ Tags.Formats.Cite\ \ \ \ \ \ \ \ ;ci	<CITE>TEXT</CITE><Esc>3bcw
nmap	;ci	O<CITE>TEXT</CITE><Esc>3bcw
vmap	;ci	<Esc>`>a</CITE><Esc>`<i<CITE><Esc>l
imap	;ci	<CITE>TEXT</CITE><Esc>3bcw
"
" Code format
nmenu HTML\ Tags.Formats.Code\ \ \ \ \ \ \ \ ;co	O<code>TEXT</code><Esc>3bcw
vmenu HTML\ Tags.Formats.Code\ \ \ \ \ \ \ \ ;co	<Esc>`>a</code><Esc>`<i<code><Esc>l
imenu HTML\ Tags.Formats.Code\ \ \ \ \ \ \ \ ;co	<code>TEXT</code><Esc>3bcw
nmap	;co	O<code>TEXT</code><Esc>3bcw
vmap	;co	<Esc>`>a</code><Esc>`<i<code><Esc>l
imap	;co	<code>TEXT</code><Esc>3bcw
"
" Definition format
nmenu HTML\ Tags.Formats.Definition\ \ ;df	O<dfn>TEXT</dfn><Esc>3bcw
vmenu HTML\ Tags.Formats.Definition\ \ ;df	<Esc>`>a</dfn><Esc>`<i<dfn><Esc>l
imenu HTML\ Tags.Formats.Definition\ \ ;df	<dfn>TEXT</dfn><Esc>3bcw
nmap	;df	O<dfn>TEXT</dfn><Esc>3bcw
vmap	;df	<Esc>`>a</dfn><Esc>`<i<dfn><Esc>l
imap	;df	<dfn>TEXT</dfn><Esc>3bcw
"
" Emphasis format
nmenu HTML\ Tags.Formats.Emphasis\ \ \ \ ;em	O<em>TEXT</em><Esc>3bcw
vmenu HTML\ Tags.Formats.Emphasis\ \ \ \ ;em	<Esc>`>a</em><Esc>`<i<em><Esc>l
imenu HTML\ Tags.Formats.Emphasis\ \ \ \ ;em	<em>TEXT</em><Esc>3bcw
nmap	;em	O<em>TEXT</em><Esc>3bcw
vmap	;em	<Esc>`>a</em><Esc>`<i<em><Esc>l
imap	;em	<em>TEXT</em><Esc>3bcw
"
" Italics format
nmenu HTML\ Tags.Formats.Italics\ \ \ \ \ ;it	O<i>TEXT</i><Esc>3bcw
vmenu HTML\ Tags.Formats.Italics\ \ \ \ \ ;it	<Esc>`>a</i><Esc>`<i<i><Esc>l
imenu HTML\ Tags.Formats.Italics\ \ \ \ \ ;it	<i>TEXT</i><Esc>3bcw
nmap	;it	O<i>TEXT</i><Esc>3bcw
vmap	;it	<Esc>`>a</i><Esc>`<i<i><Esc>l
imap	;it	<i>TEXT</i><Esc>3bcw
"
" Keyboard format
nmenu HTML\ Tags.Formats.Keyboard\ \ \ \ ;kb	O<kbd>TEXT</kbd><Esc>3bcw
vmenu HTML\ Tags.Formats.Keyboard\ \ \ \ ;kb	<Esc>`>a</kbd><Esc>`<i<kbd><Esc>l
imenu HTML\ Tags.Formats.Keyboard\ \ \ \ ;kb	<kbd>TEXT</kbd><Esc>3bcw
nmap	;kb	O<kbd>TEXT</kbd><Esc>3bcw
vmap	;kb	<Esc>`>a</kbd><Esc>`<i<kbd><Esc>l
imap	;kb	<kbd>TEXT</kbd><Esc>3bcw
"
" No break format
nmenu HTML\ Tags.Formats.No\ Break\ \ \ \ ;nb	O<nobr>TEXT</nobr><Esc>3bcw
vmenu HTML\ Tags.Formats.No\ Break\ \ \ \ ;nb	<Esc>`>a</nobr><Esc>`<i<nobr><Esc>l
imenu HTML\ Tags.Formats.No\ Break\ \ \ \ ;nb	<nobr>TEXT</nobr><Esc>3bcw
nmap	;nb	O<nobr>TEXT</nobr><Esc>3bcw
vmap	;nb	<Esc>`>a</nobr><Esc>`<i<nobr><Esc>l
imap	;nb	<nobr>TEXT</nobr><Esc>3bcw
"
" Pre format
nmenu HTML\ Tags.Formats.Preformat\ \ \ ;pr	O<pre>TEXT</pre><Esc>3bcw
vmenu HTML\ Tags.Formats.Preformat\ \ \ ;pr	<Esc>`>a</pre><Esc>`<i<pre><Esc>l
imenu HTML\ Tags.Formats.Preformat\ \ \ ;pr	<pre>TEXT</pre><Esc>3bcw
nmap	;pr	O<pre>TEXT</pre><Esc>3bcw
vmap	;pr	<Esc>`>a</pre><Esc>`<i<pre><Esc>l
imap	;pr	<pre>TEXT</pre><Esc>3bcw
"
" Strike format
nmenu HTML\ Tags.Formats.Strike\ \ \ \ \ \ ;sk	O<strike>TEXT</strike><Esc>3bcw
vmenu HTML\ Tags.Formats.Strike\ \ \ \ \ \ ;sk	<Esc>`>a</strike><Esc>`<i<strike><Esc>l
imenu HTML\ Tags.Formats.Strike\ \ \ \ \ \ ;sk	<strike>TEXT</strike><Esc>3bcw
nmap	;sk	O<strike>TEXT</strike><Esc>3bcw
vmap	;sk	<Esc>`>a</strike><Esc>`<i<strike><Esc>l
imap	;sk	<strike>TEXT</strike><Esc>3bcw
"
" Sample format
nmenu HTML\ Tags.Formats.Sample\ \ \ \ \ \ ;sa	O<samp>TEXT</samp><Esc>3bcw
vmenu HTML\ Tags.Formats.Sample\ \ \ \ \ \ ;sa	<Esc>`>a</samp><Esc>`<i<samp><Esc>l
imenu HTML\ Tags.Formats.Sample\ \ \ \ \ \ ;sa	<samp>TEXT</samp><Esc>3bcw
nmap	;sa	O<samp>TEXT</samp><Esc>3bcw
vmap	;sa	<Esc>`>a</samp><Esc>`<i<samp><Esc>l
imap	;sa	<samp>TEXT</samp><Esc>3bcw
"
" Small format
nmenu HTML\ Tags.Formats.Smaller\ \ \ \ \ ;sm	O<small>TEXT</small><Esc>3bcw
vmenu HTML\ Tags.Formats.Smaller\ \ \ \ \ ;sm	<Esc>`>a</small><Esc>`<i<small><Esc>l
imenu HTML\ Tags.Formats.Smaller\ \ \ \ \ ;sm	<small>TEXT</small><Esc>3bcw
nmap	;sm	O<small>TEXT</small><Esc>3bcw
vmap	;sm	<Esc>`>a</small><Esc>`<i<small><Esc>l
imap	;sm	<small>TEXT</small><Esc>3bcw
"
" Strong format
nmenu HTML\ Tags.Formats.Strong\ \ \ \ \ \ ;st	O<strong>TEXT</strong><Esc>3bcw
vmenu HTML\ Tags.Formats.Strong\ \ \ \ \ \ ;st	<Esc>`>a</strong><Esc>`<i<strong><Esc>l
imenu HTML\ Tags.Formats.Strong\ \ \ \ \ \ ;st	<strong>TEXT</strong><Esc>3bcw
nmap	;st	O<strong>TEXT</strong><Esc>3bcw
vmap	;st	<Esc>`>a</strong><Esc>`<i<strong><Esc>l
imap	;st	<strong>TEXT</strong><Esc>3bcw
"
" Subscript format
nmenu HTML\ Tags.Formats.Subscript\ \ \ ;sb	O<sub>TEXT</sub><Esc>3bcw
vmenu HTML\ Tags.Formats.Subscript\ \ \ ;sb	<Esc>`>a</sub><Esc>`<i<sub><Esc>l
imenu HTML\ Tags.Formats.Subscript\ \ \ ;sb	<sub>TEXT</sub><Esc>3bcw
nmap	;sb	O<sub>TEXT</sub><Esc>3bcw
vmap	;sb	<Esc>`>a</sub><Esc>`<i<sub><Esc>l
imap	;sb	<sub>TEXT</sub><Esc>3bcw
"
" Superscript format
nmenu HTML\ Tags.Formats.Superscript\ ;sp	O<sup>TEXT</sup><Esc>3bcw
vmenu HTML\ Tags.Formats.Superscript\ ;sp	<Esc>`>a</sup><Esc>`<i<sup><Esc>l
imenu HTML\ Tags.Formats.Superscript\ ;sp	<sup>TEXT</sup><Esc>3bcw
nmap	;sp	O<sup>TEXT</sup><Esc>3bcw
vmap	;sp	<Esc>`>a</sup><Esc>`<i<sup><Esc>l
imap	;sp	<sup>TEXT</sup><Esc>3bcw
"
" Typewriter heading
nmenu HTML\ Tags.Formats.Typerwriter\ ;tt	O<TT>TEXT</TT><Esc>3bcw
vmenu HTML\ Tags.Formats.Typerwriter\ ;tt	<Esc>`>a</TT><Esc>`<i<TT><Esc>l
imenu HTML\ Tags.Formats.Typerwriter\ ;tt	<TT>TEXT</TT><Esc>3bcw
nmap	;tt	O<tt>TEXT</tt><Esc>3bcw
vmap	;tt	<Esc>`>a</tt><Esc>`<i<tt><Esc>l
imap	;tt	<tt>TEXT</tt><Esc>3bcw
"
" Underline heading
nmenu HTML\ Tags.Formats.Underline\ \ \ ;uu	O<U>TEXT</U><Esc>3bcw
vmenu HTML\ Tags.Formats.Underline\ \ \ ;uu	<Esc>`>a</U><Esc>`<i<U><Esc>l
imenu HTML\ Tags.Formats.Underline\ \ \ ;uu	<U>TEXT</U><Esc>3bcw
nmap	;uu	O<u>TEXT</u><Esc>3bcw
vmap	;uu	<Esc>`>a</u><Esc>`<i<u><Esc>l
imap	;uu	<u>TEXT</u><Esc>3bcw
"
" Variable format
nmenu HTML\ Tags.Formats.Variable\ \ \ \ ;vv	O<var>TEXT</var><Esc>3bcw
vmenu HTML\ Tags.Formats.Variable\ \ \ \ ;vv	<Esc>`>a</var><Esc>`<i<var><Esc>l
imenu HTML\ Tags.Formats.Variable\ \ \ \ ;vv	<var>TEXT</var><Esc>3bcw
nmap	;vv	O<var>TEXT</var><Esc>3bcw
vmap	;vv	<Esc>`>a</var><Esc>`<i<var><Esc>l
imap	;vv	<var>TEXT</var><Esc>3bcw
"
""" List Sub-Menu
"	normal		creates selected item on previous line
"	visual		creates selected item around visual selection
"	insert		creates selected item at cursor position

"""" list Item -
nmap	;li	O<li>ITEM</li><Esc>3bcw
vmap	;li	<Esc>`<i<li><Esc>`>a</li><Esc>
imap	;li	<li>ITEM</li><Esc>3bcw
"
"""" Unordered List
nmap	;ul	O<ul><CR>  <li>ITEM</li><CR><BS><BS></ul><Esc>6bcw
vmap	;ul	:py vimhtml.unordered_list()<CR>
imap	;ul	<CR><ul><CR>  <li>ITEM</li><CR><BS><BS></ul><Esc>6bcw
"
"""" Ordered List
nmap	;ol	O<ol><CR>  <li>ITEM</li><CR><BS><BS></ol><Esc>6bcw
vmap	;ol	:py vimhtml.ordered_list()<CR>
imap	;ol	<CR><ol><CR>  <li>ITEM</li><CR><BS><BS></ol><Esc>6bcw
"

"""" Directory List
nmap	;di	O<dir><CR>  <li>LIST ITEM<CR><BS><BS></dir><Esc>4b2cw
vmap	;di	<Esc>`>a<CR></dir><Esc>:'<+1,'>+1s/^/    <li>/<CR>`<i<dir><CR>    <li><Esc>/<li><.dir><CR>4x4X
imap	;di	<CR><dir><CR>  <li>LIST ITEM<CR><BS><BS></dir><Esc>4b2cw
"
"""" Menu List
nmap	;mu	O<mu><CR>  <li>LIST ITEM<CR><BS><BS></mu><Esc>4b2cw
vmap	;mu	<Esc>`>a<CR></mu><Esc>:'<+1,'>+1s/^/    <li>/<CR>`<i<mu><CR>    <li><Esc>/<li><.mu><CR>4x4X
imap	;mu	<CR><mu><CR>  <li>LIST ITEM<CR><BS><BS></mu><Esc>4b2cw
"
"""" Definition Item
"	dt an dd are the same menu item - though dd can be called via the ;dd macro 
"	below.  this assumes you will always want a dd with every dd.
nmenu HTML\ Tags.List.Definition\ \ \ \ \ \ ;dt	O<dt>TERM<CR><dd>DEFINITION<Esc>5bcw
vmenu HTML\ Tags.List.Definition\ \ \ \ \ \ ;dt	<Esc>`>a<CR><dd>DEFINITION <Esc>`<i<dt><Esc>5wcw
imenu HTML\ Tags.List.Definition\ \ \ \ \ \ ;dt	<dt>TERM<CR><dd>DEFINITION<Esc>5bcw
nmap	;dt	O<dt>TERM</dt><CR><dd>DEFINITION</dd><Esc>5bcw
vmap	;dt	<Esc>`>a<CR><dd>DEFINITION</dd> <Esc>`<i<DT><Esc>5wcw
imap	;dt	<dt>TERM</dt><CR><dd>DEFINITION</dd><Esc>5bcw
"
"""" Definition list
nmenu HTML\ Tags.List.Definition\ List\ ;dl	O<dl><CR>  <li>LIST ITEM<CR><BS><BS></dl><Esc>4b2cw
vmenu HTML\ Tags.List.Definition\ List\ ;dl	<Esc>`>a<CR>    <dd>DEFINITION<CR><BS><BS><BS><BS></dl><Esc>`<i<dl><CR>    <dt><Esc>l
imenu HTML\ Tags.List.Definition\ List\ ;dl	<CR><dl><CR>  <li>LIST ITEM<CR><BS><BS></dl><Esc>4b2cw
nmap	;dl	O<dl><CR>  <li>LIST ITEM<CR><BS><BS></dl><Esc>4b2cw
"vmap	;dl	<Esc>`>a<CR></dl><Esc>`<i<dl><CR>  <li><Esc>l
vmap	;dl	<Esc>`>o</dl><Esc>`<O<dl><Esc>:'<,'>s/^/   <dt>/<CR>:'<,'>s/$/<\/dt>  <dd>DD<\/dd>/<CR>
imap	;dl	<CR><dl><CR>  <dt>LIST ITEM<\dt><CR><BS><BS></dl><Esc>4b2cw


" SECTION 2: macros unassociated with menus

" ABBREV (3.0)
map!	;ab	<abbrev></abbrev><Esc>bhhi
" ACRONYM (3.0)
map!	;ac <acronym></acronym><Esc>bhhi
" AU (Author) (3.0)
map!	;au <au></au><eSC>bhhi
" BANNER (3.0)
map!	;ba <banner></banner><Esc>bhhi
" BASE (head)
map!	;bh <base href=""><Esc>hi
" BASEFONT (Netscape)
map!	;bf <basefont size=><eSc>i
" BODY
map!	;bd <body><CR></body><Esc>O
" CAPTION (3.0)
map!	;ca <caption></caption><Esc>bhhi
" CREDIT (3.0)
map!	;cr <credit></credit><Esc>bhhi
" DD (definition for definition list)
map!	;dd <dd></dd><Esc>bhhi
" DEL (deleted text) (3.0)
map!	;de <del></del><Esc>bhhi
" DIV (document division) (3.0)
map!	;dv <div></div><Esc>bhhi
" FIG (figure) (3.0)
map!	;fi <fig src=""></fig><Esc>?"<CR>i
" FN (footnote) (3.0)
map!	;fn <fn></fn><Esc>bhhi
" FONT (Netscape)
map!	;fo <font size=></font><Esc>bhhhi
" HEAD
map!	;he <head><CR></head><Esc>O
" INS (inserted text) (3.0)
map!	;in <ins></ins><Esc>bhhi
" LANG (language context) (3.0)
map!	;la <lang lang=""></lang><Esc>?"<CR>i
" LINK (head)
map!	;lk <link href=""><Esc>hi
" META (head)
map!	;me <meta name="" content=""><Esc>?""<CR>??<CR>a
" NOTE (3.0)
map!	;no <note></note><Esc>bhhi
" OVERLAY (figure overlay image) (3.0)
map!	;ov <overlay src=""><Esc>hi
" Q (quote) (3.0)
map!	;qu <q></q><Esc>hhhi
" RANGE (3.0) (head)
map!	;ra <range from="" until=""><Esc>Bhi
" STYLE (3.0)
map!	;sn <style notation=""><CR></style><Esc>k/"<CR>a
" TAB (3.0)
map!	;ta <tab>
" TITLE (head)
map!	;ti <title></title><Esc>bhhi
" WBR (word break) (Netscape)
map!	;wb <wbr>
" Special Characters
map!	;& 	&amp;
map!	;cp 	&copy;
map!	;" 	&quot;
map!	;< 	&lt;
map!	;> 	&gt;


