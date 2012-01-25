from webhelpers.html import literal
from ckan.lib.helpers import icon

ORGANIZATION_LINK = '''<h3>%(link)s</h3>'''

HEAD_CODE = """
<link rel="stylesheet" href="/ckanext/qa/style.css" 
      type="text/css" media="screen" /> 
"""

def _(x):
    # TODO Need to link this to i18n._ but I can't seem to import it?
    return x

TEST_CODE = """
  <h3>Data = %s</h3>
"""

DL_HTML = """
  <dt>Quality</dt>
  <dd>%s</dd>
"""

def get_star_html(stars):
    if stars==0: 
        message = _('When we last checked, this resource was not available.'),
        return literal('<span class="star-rating hover-for-help semi-link"><span class="help-text">%s</span>404?</span>' % message)

    captions = [
        _('Available under an open license.'),
        _('Available as structured data (eg. Excel instead of a scanned table).'),
        _('Uses non-proprietary formats (e.g., CSV instead of Excel).'),
        _('Uses URIs to identify things, so that people can link to it.'),
        _('Linked to other data to provide context.')
        ]

    caption = ""
    for i in range(5,0,-1):
        fail = 'fail' if (i > stars) else ''
        text_stars = i * '&#9733'
        caption += literal('<span class="%s">%s&nbsp; "%s"</span>' % (fail, text_stars, captions[i-1]))

    star_icons = stars * icon('star')
    return literal('<span class="star-rating hover-for-help"><span class="help-text">%s</span><a href="http://lab.linkeddata.deri.ie/2010/star-scheme-by-example/" target="_blank">%s</a></span>' % (caption, star_icons))


