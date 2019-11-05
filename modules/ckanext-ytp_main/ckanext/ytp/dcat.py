from rdflib import URIRef, BNode, Literal
from rdflib.namespace import RDF, XSD
from ckanext.dcat.profiles import RDFProfile, VCARD, DCAT, DCT, FOAF, SKOS, ADMS
from ckanext.dcat.utils import resource_uri
from ckan.plugins import toolkit as p

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'vcard': VCARD,
    'foaf': FOAF,
    'skos': SKOS,
    'adms': ADMS,
    'xsd': XSD
}


class AvoindataDCATAPProfile(RDFProfile):
    '''
    An RDF profile for Avoindata based on DCAT-AP 1.2.2.

    Supported dataset fields:
        Mandatory: dct:title, dct:description
        Recommended:  dcat:contactPoint, dcat:distribution, dcat:keyword
                      dct:publisher, dcat:theme
        Optional: dcat:landingPage, dct:spatial, dct:accuralPeriodicity, dct:type,
                  dct:identifier, dct:temporal, dct:issued

    Supported distribution fields:
        Mandatory: dct:accessUrl
        Recommended: dct:description
        Optional: dct:title, dct:downloadUrl, adms:status, dct:license, dct:format,
                  dcat:byteSize
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

            # dct:title
            titles = (t for t in set(resource_dict.get('name_translated').values()) if t)
            for title in titles:
                g.add((distribution, DCT.title, Literal(title)))

            # dct:description
            descriptions = (d for d in set(resource_dict.get('description_translated').values()) if d)
            for description in descriptions:
                g.add((distribution, DCT.description, Literal(description)))

            # dcat:accessUrl
            g.add((distribution, DCAT.accessUrl, URIRef(resource_uri(resource_dict))))

            # dcat:downloadUrl
            resource_url = resource_dict.get('url')
            if resource_url:
                g.add((distribution, DCAT.downloadUrl, URIRef(resource_url)))

            # adms:status
            maturity = resource_dict.get('maturity')

            if maturity:
                status = Literal(maturity)
                g.add((distribution, ADMS.status, status))

            # dct:license
            license_url = dataset_dict.get('license_url')

            if license_url:
                license_ref = URIRef(license_url)
                g.add((distribution, DCT.license, license_ref))

            # dct:format
            file_format = resource_dict.get('format')

            if file_format:
                media_type = Literal(file_format)
                g.add((distribution, DCT['format'], media_type))

            # dcat:byteSize
            file_size = resource_dict.get('file_size')

            if file_size:
                g.add((distribution, DCAT.byteSize, Literal(file_size)))

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

        # dcat:landingPage
        external_urls = (u for u in dataset_dict.get('external_urls', []) if u)

        for external_url in external_urls:
            document = URIRef(external_url)
            g.add((document, RDF.type, FOAF.Document))
            g.add((dataset_ref, DCAT.landingPage, document))

        # dct:spatial
        geographical_coverages = set(g for g in dataset_dict.get('geographical_coverage', []) if g)

        for geographical_coverage in geographical_coverages:
            location = BNode()
            g.add((dataset_ref, DCT.spatial, location))
            g.add((location, RDF.type, DCT.Location))
            g.add((location, DCAT.centroid, Literal(geographical_coverage)))

        # dct:accuralPeriodicity
        update_frequencies = set(u for lang in dataset_dict.get('update_frequency', {}).values() for u in lang if u)

        for update_frequency in update_frequencies:
            g.add((dataset_ref, DCT.accrualPeriodicity, Literal(update_frequency)))

        # dct:type
        content_types = set(t for lang in dataset_dict.get('content_type', {}).values() for t in lang if t)

        for content_type in content_types:
            concept = Literal(content_type)
            g.add((dataset_ref, DCT.type, concept))

        # dct:identifier
        g.add((dataset_ref, DCT.identifier, Literal(dataset_dict.get('id'))))

        # dct:temporal
        valid_from = dataset_dict.get('valid_from')
        valid_till = dataset_dict.get('valid_till')

        if valid_from or valid_till:
            period = BNode()
            g.add((dataset_ref, DCT.temporal, period))
            g.add((period, RDF.type, DCT.PeriodOfTime))
            if valid_from:
                g.add((period, DCAT.startDate, Literal(valid_from)))
            if valid_till:
                g.add((period, DCAT.endDate, Literal(valid_till)))

        # dct:issued
        date_released = dataset_dict.get('date_released')

        if date_released:
            issued_date = Literal(date_released)
            g.add((dataset_ref, DCT.issued, issued_date))
            g.add((issued_date, RDF.type, XSD.DateTime))
