import json
from rdflib import URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, XSD
from ckanext.dcat.profiles import RDFProfile, VCARD, DCAT, DCT, FOAF, SKOS, ADMS, SPDX
from ckanext.dcat.utils import resource_uri
from ckan.plugins import toolkit as p

ADFI = Namespace('http://avoindata.fi/ns#')

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'vcard': VCARD,
    'foaf': FOAF,
    'skos': SKOS,
    'adms': ADMS,
    'xsd': XSD,
    'spdx': SPDX,
    'adfi': ADFI
}


def as_dict(value):
    if type(value) is dict:
        return value
    elif type(value) in (str, unicode):
        return as_dict(json.loads(value))
    else:
        raise ValueError()


def get_dict(d, key):
    return as_dict(d.get(key, {}))


class AvoindataDCATAPProfile(RDFProfile):
    '''
    An RDF profile for Avoindata based on DCAT-AP 1.2.2.

    Supported dataset fields:
        Mandatory: dct:title, dct:description
        Recommended:  dcat:contactPoint, dcat:distribution, dcat:keyword
                      dct:publisher, dcat:theme
        Optional: dcat:landingPage, dct:spatial, dct:accuralPeriodicity, dct:type,
                  dct:identifier, dct:temporal, dct:issued, dct:rights

    Supported distribution fields:
        Mandatory: dct:accessUrl
        Recommended: dct:description
        Optional: dct:title, dct:downloadUrl, adms:status, dct:license, dct:format,
                  dcat:byteSize, dcat:temporalResolution, spdx:checksum
    '''

    #
    def parse_dataset(self, dataset_dict, dataset_ref):
        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)
        g.add((dataset_ref, RDF.type, ADFI.Dataset))

        # dct:title
        titles = set(t for t in get_dict(dataset_dict, 'title_translated').values() if t)

        if not titles:
            titles.add(dataset_dict.get('title', ''))

        for title in titles:
            g.add((dataset_ref, DCT.title, Literal(title)))

        # dct:description
        descriptions = set(d for d in get_dict(dataset_dict, 'notes_translated').values() if d)

        if not descriptions:
            descriptions.add(dataset_dict.get('notes', ''))

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
        for resource_dict in dataset_dict.get('resources', []):
            resource_dict = as_dict(resource_dict)
            distribution = BNode()
            g.add((distribution, RDF.type, ADFI.Distribution))
            g.add((dataset_ref, DCAT.distribution, distribution))

            # dct:title
            titles = set(t for t in get_dict(resource_dict, 'name_translated').values() if t)

            if not titles:
                titles.add(resource_dict.get('title', ''))

            for title in titles:
                g.add((distribution, DCT.title, Literal(title)))

            # dct:description
            descriptions = set(d for d in get_dict(resource_dict, 'description_translated').values() if d)

            if not descriptions:
                descriptions.add(dataset_dict.get('description', ''))

            for description in descriptions:
                g.add((distribution, DCT.description, Literal(description)))

            # dct:rights
            copyright_notices = set(n for n in get_dict(dataset_dict, 'copyright_notice_translated').values() if n)

            if copyright_notices:
                rights_statement = BNode()
                g.add((rights_statement, RDF.type, DCT.RightsStatement))
                g.add((rights_statement, DCT.description, Literal('\n\n'.join(copyright_notices))))
                g.add((distribution, DCT.rights, rights_statement))

            # dcat:accessUrl
            g.add((distribution, DCAT.accessURL, URIRef(resource_uri(resource_dict))))

            # dcat:downloadUrl
            resource_url = resource_dict.get('url')
            if resource_url:
                g.add((distribution, DCAT.downloadURL, URIRef(resource_url)))

            # adms:status
            maturity = resource_dict.get('maturity')

            if maturity:
                status = BNode()
                g.add((status, RDF.type, SKOS.Concept))
                g.add((status, SKOS.prefLabel, Literal(maturity)))
                g.add((distribution, ADMS.status, status))

            # dct:license
            license_url = dataset_dict.get('license_url')

            if license_url:
                license_ref = URIRef(license_url)
                g.add((license_ref, RDF.type, DCT.LicenseDocument))
                g.add((distribution, DCT.license, license_ref))

            # dct:format
            file_format = resource_dict.get('format')

            if file_format:
                media_type = BNode()
                g.add((media_type, RDF.type, DCT.MediaTypeOrExtent))
                g.add((media_type, RDF.value, Literal(file_format)))
                g.add((distribution, DCT['format'], media_type))

            # dct:conformsTo
            position_info = resource_dict.get('position_info')

            if position_info:
                standard = BNode()
                g.add((standard, RDF.type, DCT.Standard))
                g.add((standard, RDF.value, Literal(position_info)))
                g.add((distribution, DCT.conformsTo, standard))

            # dcat:byteSize
            file_size = resource_dict.get('size')

            if file_size:
                g.add((distribution, DCAT.byteSize, Literal(file_size, datatype=XSD.decimal)))

            # spdx:checksum
            checksum_value = resource_dict.get('sha256')

            if checksum_value:
                checksum = BNode()
                g.add((checksum, RDF.type, SPDX.Checksum))
                g.add((checksum, SPDX.checksumValue, Literal(checksum_value)))
                g.add((checksum, SPDX.algorithm, SPDX.checksumAlgorithm_sha1))
                g.add((distribution, SPDX.checksum, checksum))

            # dct:temporal
            temporal_coverage_from = resource_dict.get('temporal_coverage_from')
            temporal_coverage_to = resource_dict.get('temporal_coverage_to')

            if temporal_coverage_from or temporal_coverage_to:
                period = BNode()
                g.add((distribution, DCT.temporal, period))
                g.add((period, RDF.type, DCT.PeriodOfTime))
                if temporal_coverage_from:
                    g.add((period, DCAT.startDate, Literal(temporal_coverage_from)))
                if temporal_coverage_to:
                    g.add((period, DCAT.endDate, Literal(temporal_coverage_to)))

            # dcat:temporalResolution
            temporal_granularities = set(t for lang in get_dict(resource_dict, 'temporal_granularity').values()
                                         for t in lang if t)

            if temporal_granularities:
                g.add((distribution, DCAT.temporalResolution,
                       Literal(', '.join(temporal_granularities), datatype=XSD.duration)))

        # dcat:keyword
        keywords = set(
                keyword
                for keyword_language in get_dict(dataset_dict, 'keywords').values()
                for keyword in keyword_language)

        for keyword in keywords:
            g.add((dataset_ref, DCAT.keyword, Literal(keyword)))

        # dct:publisher
        context = {'user': p.c.user}
        organization = p.get_action('organization_show')(context, data_dict={'id': dataset_dict['owner_org']})

        publisher = URIRef(p.url_for(controller='organization', action='read', id=organization['id'], qualified=True))
        g.add((publisher, RDF.type, FOAF.Agent))
        g.add((dataset_ref, DCT.publisher, publisher))

        organization_titles = (t for t in get_dict(organization, 'title_translated').values() if t)

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

            group_titles = (t for t in get_dict(group_dict, 'title_translated').values() if t)
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
        update_frequencies = set(u for lang in get_dict(dataset_dict, 'update_frequency').values() for u in lang if u)

        if update_frequencies:
            accrual_periodicity = BNode()
            g.add((accrual_periodicity, RDF.type, DCT.Frequency))
            g.add((accrual_periodicity, RDF.value, Literal(', '.join(update_frequencies))))
            g.add((dataset_ref, DCT.accrualPeriodicity, accrual_periodicity))

        # dct:type
        content_types = set(t for lang in get_dict(dataset_dict, 'content_type').values() for t in lang if t)

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
        date_released = dataset_dict.get('metadata_created')

        if date_released:
            issued_date = Literal(date_released)
            g.add((dataset_ref, DCT.issued, issued_date))

    def graph_from_catalog(self, catalog_dict, catalog_ref):

        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        g.add((catalog_ref, RDF.type, ADFI.Catalog))

        # Basic fields
        title = p.config.get('ckan.site_title', '')
        g.add((catalog_ref, DCT.title, Literal(title)))

        description = p.config.get('ckan.site_description', '')
        g.add((catalog_ref, DCT.description, Literal(description)))

        homepage = URIRef(p.config.get('ckan.site_url', ''))
        g.add((catalog_ref, FOAF.homepage, homepage))

        language = p.config.get('ckan.locale_default', 'en')
        linguistic_system = URIRef('http://id.loc.gov/vocabulary/iso639-1/%s' % language)
        g.add((catalog_ref, DCT.language, linguistic_system))

        publisher = URIRef(p.config.get('ckan.site_url', ''))
        g.add((publisher, FOAF.name, Literal(p.config.get('ckan.site_title'))))
        g.add((catalog_ref, DCT.publisher, publisher))

        # Dates
        modified = self._last_catalog_modification()
        if modified:
            self._add_date_triple(catalog_ref, DCT.modified, modified)
