" dtd editing help

iab EN <!ENTITY
iab EL <!ELEMENT
iab AT <!ATTLIST

iab pcdata #PCDATA
iab empty EMPTY
iab any ANY

" attribute defaults
iab required #REQUIRED
iab implied #IMPLIED
iab fixed #FIXED

" attribute types
iab cdata CDATA
iab id ID
iab idref IDREF
iab idrefs IDREFS
iab entity ENTITY
iab entities ENTITIES
iab nmtoken NMTOKEN
iab nmtokens NMTOKENS

" macros
imap ;en <!ENTITY name value ><ESC>bbcw
nmap ;en i;en
imap ;el <!ELEMENT NAME (contentspec) ><ESC>4bcw
nmap ;el i;el
imap ;at <!ATTLIST NAME<ESC>o><ESC>k02wcw
nmap ;at i;at
imap ;ai NAME CDATA #IMPLIED<ESC>0cw
nmap ;ai i;ai
imap ;co <!-- COM --><ESC>bbcw
nmap ;co i;co

