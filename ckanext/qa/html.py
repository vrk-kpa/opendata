from webhelpers.html import literal
from ckan.lib.helpers import icon


HEAD_CODE = '''
<link rel="stylesheet" href="%scss/ckanext-qa.css"
      type="text/css" media="screen" />
'''

DL_HTML = '''
  <dt>Quality</dt>
  <dd>%s</dd>
'''


def _(x):
    # TODO Need to link this to i18n._ but I can't seem to import it?
    return x


def get_star_html(stars, reason):
    if stars == 0:
        return literal('<span class="star-rating no-stars">[%s]</span>' % reason)

    captions = [
        _('Available under an open license.'),
        _('Available as structured data (eg. Excel instead of a scanned table).'),
        _('Uses non-proprietary formats (e.g., CSV instead of Excel).'),
        _('Uses URIs to identify things, so that people can link to it.'),
        _('Linked to other data to provide context.')
        ]

    caption = ""
    for i in range(5, 0, -1):
        fail = 'fail' if (i > stars) else ''
        text_stars = i * '&#9733'
        caption += literal('<span class="%s">%s&nbsp; "%s"</span>' % (fail, text_stars, captions[i-1]))

    star_icons = stars * icon('star')
    return literal('<span class="star-rating hover-for-help"><span class="help-text">[%s] %s</span><a href="http://lab.linkeddata.deri.ie/2010/star-scheme-by-example/" target="_blank">%s</a></span>' % (reason, caption, star_icons))
