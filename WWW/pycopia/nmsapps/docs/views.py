# python
# vim:ts=2:sw=2:softtabstop=2:smarttab:expandtab

from pycopia.nmsapps import core, _


TITLE = _("Documentation")

def main(request):
  resp = core.ResponseDocument(request, title=TITLE)
  resp.fill_nav(resp.config.DEFAULTNAV)
  resp.header.add_header(1, TITLE)
  resp.content.new_para(_("In progress. Sorry."))
  return resp.finalize()

