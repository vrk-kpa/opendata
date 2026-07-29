from ckan.tests.factories import Organization

from faker import Faker

fake = Faker()


class OpendataOrganization(Organization):
    title_translated = {
        'fi': fake.sentence(nb_words=5)
    }
