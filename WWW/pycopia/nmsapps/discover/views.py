
from pycopia.nmsapps import core, _


TITLE = _("Network Discovery")

def main(request):
  resp = core.ResponseDocument(request, title=TITLE)
  resp.header.add_header(1, TITLE)
  resp.fill_nav(resp.config.DEFAULTNAV)
  return resp.finalize()

