from rdflib import URIRef, BNode, Literal
from rdflib.namespace import RDF
from ckanext.dcat.profiles import RDFProfile, VCARD, DCAT, DCT, FOAF, SKOS
from ckanext.dcat.utils import resource_uri
from ckan.plugins import toolkit as p

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'vcard': VCARD,
    'foaf': FOAF,
    'skos': SKOS,
}


class AvoindataDCATAPProfile(RDFProfile):
    '''
    An RDF profile for Avoindata based on DCAT-AP 1.2.2.

    Supported dataset fields:
        Mandatory: dct:title, dct:description
        Recommended:  dcat:contactPoint, dcat:distribution, dcat:keyword
                      dct:publisher, dcat:theme
    '''

    #
    def parse_dataset(self, dataset_dict, dataset_ref):
        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)
        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # dct:title
        titles = (t for t in self._get_dataset_value(dataset_dict, 'title_translated').values() if t)

        for title in titles:
            g.add((dataset_ref, DCT.title, Literal(title)))

        # dct:description
        descriptions = (d for d in self._get_dataset_value(dataset_dict, 'notes_translated').values() if d)

        for description in descriptions:
            g.add((dataset_ref, DCT.description, Literal(description)))

        # dct:contactPoint
        contact_details = BNode()

        g.add((contact_details, RDF.type, VCARD.Organization))
        g.add((dataset_ref, DCAT.contactPoint, contact_details))

        self._add_triple_from_dict(dataset_dict, contact_details, VCARD.fn, 'maintainer')
        self._add_triple_from_dict(dataset_dict, contact_details, VCARD.hasEmail, 'maintainer_email',
                                   _type=URIRef, value_modifier=self._add_mailto)

        self._add_triple_from_dict(dataset_dict, contact_details, VCARD.hasUrl, 'maintainer_website', _type=URIRef)

        # dcat:distribution
        for resource_dict in self._get_dataset_value(dataset_dict, 'resources'):
            distribution = BNode()
            g.add((distribution, RDF.type, DCAT.Distribution))
            g.add((dataset_ref, DCAT.distribution, distribution))

            titles = (t for t in set(resource_dict.get('name_translated').values()) if t)
            for title in titles:
                g.add((distribution, DCT.title, Literal(title)))

            descriptions = (d for d in set(resource_dict.get('description_translated').values()) if d)
            for description in descriptions:
                g.add((distribution, DCT.description, Literal(description)))

            g.add((distribution, DCAT.accessUrl, URIRef(resource_uri(resource_dict))))

            resource_url = resource_dict.get('url')
            if resource_url:
                g.add((distribution, DCAT.downloadUrl, URIRef(resource_url)))

        # dcat:keyword
        keywords = set(
                keyword
                for keyword_language in dataset_dict.get('keywords', {}).values()
                for keyword in keyword_language)

        for keyword in keywords:
            g.add((dataset_ref, DCAT.keyword, Literal(keyword)))

        # dct:publisher
        context = {'user': p.c.user}
        organization = p.get_action('organization_show')(context, data_dict={'id': dataset_dict['owner_org']})

        publisher = URIRef(p.url_for(controller='organization', action='read', id=organization['id'], qualified=True))
        g.add((publisher, RDF.type, FOAF.Organization))
        g.add((dataset_ref, DCT.publisher, publisher))

        organization_titles = (t for t in organization.get('title_translated', {}).values() if t)

        for title in organization_titles:
            g.add((publisher, FOAF.name, Literal(title)))

        self._add_triple_from_dict(organization, publisher, FOAF.homepage, 'homepage')

        # dcat:theme
        groups = dataset_dict.get('groups', [])

        for group_item in groups:
            group_dict = p.get_action('group_show')(context, data_dict={'id': group_item['id']})
            theme = URIRef(p.url_for(controller='group', action='read', id=group_dict['id'], qualified=True))
            g.add((theme, RDF.type, SKOS.Concept))
            g.add((dataset_ref, DCAT.theme, theme))

            group_titles = (t for t in group_dict.get('title_translated', {}).values() if t)
            for title in group_titles:
                g.add((theme, SKOS.prefLabel, Literal(title)))
