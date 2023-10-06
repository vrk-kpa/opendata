# coding: utf-8

from pylons import config
from .avoindata_signature import signature

"""
    A template file for datasets that have been deprecated.
"""


def messageBody(user, packages):
    deprecatedItems = []
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
      signature_en=signature('en'),
      signature_fi=signature('fi'),
      valid_till=packages[0]["valid_till"]
    )



subject = "Tietoaineistojesi viimeinen voimassaolopäivä Suomi.fi-avoindatassa umpeutui {valid_till} - You have datasets in Suomi.fi Open Data that were marked as deprecated on {valid_till}" # noqa

messageBodyTemplate = """
Hei,

Ylläpidät tietoaineistoja Suomi.fi-avoindatassa ja olet merkinnyt niille viimeisen voimassaolopäivän.

Alla listatut tietoaineistosi ovat vanhentuneet {valid_till}. Ilmoitimme sinulle tietoaineistojesi vanhentumisesta
ennen niiden viimeistä voimassaolopäivää. Voit vieläkin muuttaa tietoaineistojen voimassaoloa kirjautumalla palveluun, valitsemalla
datasetin jonka voimassaolo on umpeutumassa, ja päivittämällä arvon kentässä Viimeinen voimassaolopäivä tai päivittämällä
aineistosta uudemman version jolla on myöhempi viimeinen voimassaolopäivä.

Tietoaineistojasi ei edelleenkään poisteta palvelusta. Ne näkyvät palvelun käyttäjille vanhentuneina aineistona.
Jos sinulla on kysyttävää, opastamme sinua tarpeen vaatiessa osoitteessa avoindata@vrk.fi.

{signature_fi}

--
Hello,

You have uploaded a dataset or datasets in Suomi.fi Open Data and set an expiration date for the data.

The data sets below were marked as deprecated on {valid_till}. We notified you of the expiration prior to the date of expiration.

You can still extend the validity of your data set(s) by logging in the service, navigating to the expiring dataset, and updating the date in the  Valid until field.
Alternatively you can upload a newer version of the data set with a later expiration date in the service. Your data sets will not be removed from Suomi.fi Open Data.
Our users will see the data sets as expired.

Should you have any questions or need help, please get in touch with us at avoindata@vrk.fi.

{signature_en}

{deprecated}
---
""" # noqa

deprecatedItem = """---
Tietoaineisto - Dataset:
{title} ( {url} )"""
