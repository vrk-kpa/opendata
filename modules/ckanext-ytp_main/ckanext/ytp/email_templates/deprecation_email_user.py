from pylons import config
from avoindata_signature import signature
from ckan.common import _

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
                dateset_translation=_("Dataset")
            )
        )

    return messageBodyTemplate.format(
      deprecated='\n'.join(deprecatedItems),
      signature=signature,
      valid_till=packages[0]["valid_till"]
    )


subject = _(u"You have datasets in Avoindata.fi that were marked as deprecated on {valid_till}")

messageBodyTemplate = _(u"""
Hello,

You have uploaded a dataset or datasets in Avoindata.fi and set an expiration date for the data.

The data sets below were marked as deprecated a month ago, on {valid_till}. We notified you of the
expiration prior to the date of expiration.

You can still extend the validity of your data set(s) by logging in the service, navigating to the
expiring dataset, and updating the date in the  Valid until field.

Alternatively you can upload a newer version of the data set with a later expiration date in the
service. Your data sets will not be removed from Avoindata.fi.

Our users will see the data sets as expired.

Should you have any questions or need help, please get in touch with us at avoindata@vrk.fi.

{signature}

{deprecated}
---
""")

deprecatedItem = u"""---
{dataset_translation}:
{title} ( {url} )"""
