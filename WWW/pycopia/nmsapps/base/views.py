# python
# vim:ts=2:sw=2:softtabstop=2:smarttab:expandtab

from pycopia.nmsapps import core, _


TITLE = _("Network Management System")

def main(request):
  resp = core.ResponseDocument(request, title=TITLE,
                stylesheet="base.css")
  resp.header.add_header(1, TITLE)
  resp.fill_nav(resp.config.DEFAULTNAV)
  return resp.finalize()


def error(request):
  code = request.GET["code"]
  ref = request.META["HTTP_REFERER"]
  resp = core.ResponseDocument(request, title="%s %s." % (_("Error"), code), 
      stylesheet="base.css")
  resp.content.add_para().add_anchor(href=ref).add_text(_("Go back."))
  return resp.finalize()

