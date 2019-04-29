from pylons import config
from avoindata_signature import signature

"""
    A template file for datasets that have been deprecated.
"""


def messageBody(user, packages):
    deprecatedItems = []
    # TODO: setup email translation based on user preferred language.

    for package in packages:
        url = "%s/data/fi/dataset/%s" % (config['ckan.site_url'], package["id"])
        deprecatedItems.append(
            deprecatedItem.format(
                title=package["title"],
                url=url,
                valid_till=package["valid_till"],
            )
        )

    return messageBodyTemplate.format(
      deprecated='\n'.join(deprecatedItems),
      signature=signature,
    )


subject = u"Some of your datasets have deprecated"

messageBodyTemplate = u"""
List of deprecated datasets

{deprecated}
---

{signature}
"""

deprecatedItem = u"""---
Dataset:
{title} ( {url} )"""
