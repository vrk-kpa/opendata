import six
import json
import threading
from rdflib import URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, XSD
from ckanext.dcat.profiles import RDFProfile, VCARD, DCAT, DCT, FOAF, SKOS, ADMS, SPDX, LOCN, GSP
from ckanext.dcat.utils import resource_uri, url_quote
from ckan.plugins import toolkit as p

import logging
log = logging.getLogger(__name__)

ADFI = Namespace('http://avoindata.fi/ns#')
GEODCAT = Namespace('http://data.europa.eu/930/#')
namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'vcard': VCARD,
    'foaf': FOAF,
    'skos': SKOS,
    'adms': ADMS,
    'xsd': XSD,
    'spdx': SPDX,
    'adfi': ADFI,
    'locn': LOCN,
    'gsp': GSP,
    'geodcat': GEODCAT,
}


def as_dict(value):
    if type(value) is dict:
        return value
    elif type(value) in (str, six.text_type):
        return as_dict(json.loads(value))
    else:
        raise ValueError()


def get_dict(d, key):
    return as_dict(d.get(key, {}))


def uriref(uri, *args, **kwargs):
    return URIRef(url_quote(uri.encode('utf-8')), *args, **kwargs)


thread_local = threading.local()
thread_local.organization_list = []
thread_local.group_list = []


def get_organization(org_id):
    if hasattr(thread_local, 'organization_list'):
        organization = next((organization for organization in thread_local.organization_list
                             if organization['id'] == org_id), None)
    else:
        organization = None

    # If organization does not exist in previously fetched list, use organization_show to fetch it
    if not organization:
        organization = p.get_action('organization_show')({}, {'id': org_id,
                                                              'include_users': False,
                                                              'include_dataset_count': False,
                                                              'include_groups': False,
                                                              'include_tags': False,
                                                              'include_followers': False})
    return organization


def get_group(group_id):
    if hasattr(thread_local, 'group_list'):
        group = next((group for group in thread_local.group_list if group['id'] == group_id), None)
    else:
        group = None

    # If group does not exist in previously fetched list, use group_show to fetch it
    if not group:
        group = p.get_action('group_show')({}, {'id': group_id})
    return group


class AvoindataDCATAPProfile(RDFProfile):
    '''
    An RDF profile for Avoindata based on DCAT-AP 2.0.0 extension at
    <https://www.avoindata.fi/ns/#>

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
                  dcat:byteSize, dcat:temporalResolution, spdx:checksum, dct:rights,
                  dct:conformsTo
    '''

    #
    def parse_dataset(self, dataset_dict, dataset_ref):
        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        g = self.g

        for prefix, namespace in namespaces.items():
            g.bind(prefix, namespace)
        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # Flatten extras
        for extra in dataset_dict.get('extras', []):
            key = extra['key']
            if key not in dataset_dict:
                dataset_dict[key] = extra['value']

        # dct:title
        titles = set(t for t in list(get_dict(dataset_dict, 'title_translated').values()) if t)

        if not titles:
            titles.add(dataset_dict.get('title', ''))

        for title in titles:
            g.add((dataset_ref, DCT.title, Literal(title)))

        # dct:description
        descriptions = set(d for d in list(get_dict(dataset_dict, 'notes_translated').values()) if d)

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

        contact_email = dataset_dict.get('contact_email')
        if contact_email:
            g.add((dataset_ref, DCAT.contactPoint, uriref(contact_email)))

        # dcat:distribution
        for resource_dict in dataset_dict.get('resources', []):
            resource_dict = as_dict(resource_dict)
            distribution = BNode()
            g.add((distribution, RDF.type, DCAT.Distribution))
            g.add((dataset_ref, DCAT.distribution, distribution))

            # dct:title
            titles = set(t for t in list(get_dict(resource_dict, 'name_translated').values()) if t)

            if not titles:
                titles.add(resource_dict.get('title', ''))

            for title in titles:
                g.add((distribution, DCT.title, Literal(title)))

            # dct:description
            descriptions = set(d for d in list(get_dict(resource_dict, 'description_translated').values()) if d)

            if not descriptions:
                descriptions.add(dataset_dict.get('description', ''))

            for description in descriptions:
                g.add((distribution, DCT.description, Literal(description)))

            # dct:rights
            copyright_notices = set(n for n in list(get_dict(dataset_dict, 'copyright_notice_translated').values()) if n)

            if copyright_notices:
                rights_statement = BNode()
                g.add((rights_statement, RDF.type, DCT.RightsStatement))
                g.add((rights_statement, DCT.description, Literal('\n\n'.join(copyright_notices))))
                g.add((distribution, DCT.rights, rights_statement))

            # dcat:accessUrl
            g.add((distribution, DCAT.accessURL, uriref(resource_uri(resource_dict))))

            # dcat:downloadUrl
            resource_url = resource_dict.get('url')
            if resource_url:
                g.add((distribution, DCAT.downloadURL, uriref(resource_url)))

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
                license_ref = uriref(license_url)
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
                g.add((standard, DCT.identifier, Literal(position_info)))
                g.add((distribution, DCT.conformsTo, standard))

            spatial_reference_system = dataset_dict.get('spatial-reference-system')
            if spatial_reference_system:
                standard = BNode()
                g.add((standard, RDF.type, DCT.Standard))
                g.add((standard, DCT.identifier, Literal(spatial_reference_system)))
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
            temporal_granularities = set(t for lang in list(get_dict(resource_dict, 'temporal_granularity').values())
                                         for t in lang if t)

            if temporal_granularities:
                g.add((distribution, DCAT.temporalResolution,
                       Literal(', '.join(temporal_granularities), datatype=XSD.duration)))

        # dcat:keyword
        keywords = set(
                keyword
                for keyword_language in list(get_dict(dataset_dict, 'keywords').values())
                for keyword in keyword_language)

        for keyword in keywords:
            g.add((dataset_ref, DCAT.keyword, Literal(keyword)))

        # dct:publisher
        organization = get_organization(dataset_dict['owner_org'])

        # If organization is not approved, it won't be available in organization list
        if organization:
            publisher = URIRef(p.url_for(controller='organization', action='read', id=organization['id'], qualified=True))
            g.add((publisher, RDF.type, FOAF.Agent))
            g.add((dataset_ref, DCT.publisher, publisher))

            organization_titles = (t for t in list(get_dict(organization, 'title_translated').values()) if t)

            for title in organization_titles:
                g.add((publisher, FOAF.name, Literal(title)))

            self._add_triple_from_dict(organization, publisher, FOAF.homepage, 'homepage')

        # dcat:theme
        groups = dataset_dict.get('groups', [])

        for group_item in groups:
            group_id = group_item['id'] if isinstance(group_item, dict) else group_item
            group_dict = get_group(group_id)
            theme = URIRef(p.url_for(controller='group', action='read', id=group_dict['id'], qualified=True))
            g.add((theme, RDF.type, SKOS.Concept))
            g.add((dataset_ref, DCAT.theme, theme))

            group_titles = (t for t in list(get_dict(group_dict, 'title_translated').values()) if t)
            for title in group_titles:
                g.add((theme, SKOS.prefLabel, Literal(title)))

        # dcat:landingPage
        external_urls = dataset_dict.get('external_urls', [])
        if isinstance(external_urls, six.text_type):
            try:
                external_urls = json.loads(external_urls)
            except json.JSONDecodeError:
                external_urls = []
        external_urls = (u for u in external_urls if u)

        for external_url in external_urls:
            # some external urls have whitespace in them
            external_url = external_url.strip()
            document = URIRef(url_quote(external_url.encode('utf-8')))
            g.add((document, RDF.type, FOAF.Document))
            g.add((dataset_ref, DCAT.landingPage, document))

        # dct:spatial
        locations = []
        geographical_coverages = set(g for g in dataset_dict.get('geographical_coverage', []) if g)

        for geographical_coverage in geographical_coverages:
            locations.append((DCT.identifier, Literal(geographical_coverage)))

        bbox_field_names = ['bbox-south-lat', 'bbox-west-long', 'bbox-north-lat', 'bbox-east-long']
        bbox_fields = [dataset_dict.get(field) for field in bbox_field_names]

        if all(bbox_fields):
            log.debug('bbox fields are present: %s', bbox_fields)
            from lxml import etree
            gml = 'http://www.opengis.net/gml/3.2.1#'
            nsmap = {'gml': gml}
            envelope = etree.Element(etree.QName(gml, 'Envelope'),
                                     srsName='http://www.opengis.net/def/crs/OGC/1.3/CRS84',
                                     nsmap=nsmap)
            lowerCorner = etree.SubElement(envelope, etree.QName(gml, 'lowerCorner'), nsmap=nsmap)
            upperCorner = etree.SubElement(envelope, etree.QName(gml, 'upperCorner'), nsmap=nsmap)
            lowerCorner.text = ' '.join(bbox_fields[:2])
            upperCorner.text = ' '.join(bbox_fields[2:])

            locations.append((DCAT.bbox, Literal(etree.tostring(envelope))))

        spatial_field = dataset_dict.get('spatial')
        if spatial_field:
            log.debug('spatial field is present: %s', spatial_field)
            locations.append((LOCN.geometry, Literal(spatial_field, datatype=GSP.geoJSONLiteral)))

        if dataset_dict.get('name') == 'keski-suomen-maakuntakaavayhdistelma7':
            from pprint import pformat
            log.debug(pformat(dataset_dict))

        if locations:
            location = BNode()
            g.add((dataset_ref, DCT.spatial, location))
            g.add((location, RDF.type, DCT.Location))
            for prop, value in locations:
                g.add((location, prop, value))

        # geodcat:custodian
        responsible_party = dataset_dict.get('responsible-party')
        if responsible_party:
            try:
                custodians_data = json.loads(responsible_party)
                custodians_data = custodians_data if type(custodians_data) is list else [custodians_data]
                for custodian_data in custodians_data:
                    custodian = BNode()
                    g.add((custodian, RDF.type, FOAF.Agent))
                    custodian_fields = [('name', FOAF.name), ('email', VCARD.hasEmail)]

                    for field, prop in custodian_fields:
                        value = custodian_data.get(field)
                        if value:
                            g.add((custodian, prop, Literal(value)))

                    g.add((dataset_ref, GEODCAT.custodian, custodian))
            except ValueError:
                log.debug('Invalid JSON value in field responsible-party')

        # dct:accuralPeriodicity
        update_frequencies = set(u for lang in list(get_dict(dataset_dict, 'update_frequency').values()) for u in lang if u)
        spatial_frequency_of_update = dataset_dict.get('frequency-of-update')

        if spatial_frequency_of_update:
            update_frequencies.add(spatial_frequency_of_update)

        if update_frequencies:
            accrual_periodicity = BNode()
            g.add((accrual_periodicity, RDF.type, DCT.Frequency))
            g.add((accrual_periodicity, RDF.value, Literal(', '.join(update_frequencies))))
            g.add((dataset_ref, DCT.accrualPeriodicity, accrual_periodicity))

        # dct:type
        content_types = set(t for lang in list(get_dict(dataset_dict, 'content_type').values()) for t in lang if t)

        if content_types:
            concept = BNode()
            g.add((concept, RDF.type, SKOS.Concept))
            for content_type in content_types:
                g.add((concept, SKOS.prefLabel, Literal(content_type)))
            g.add((dataset_ref, DCT.type, concept))

        # dct:identifier
        g.add((dataset_ref, DCT.identifier, Literal(dataset_dict.get('id'))))

        # dct:temporal
        valid_from = dataset_dict.get('valid_from') or dataset_dict.get('temporal-extent-begin')
        valid_till = dataset_dict.get('valid_till') or dataset_dict.get('temporal-extent-end')

        if valid_from or valid_till:
            period = BNode()
            g.add((dataset_ref, DCT.temporal, period))
            g.add((period, RDF.type, DCT.PeriodOfTime))
            if valid_from:
                g.add((period, DCAT.startDate, Literal(valid_from)))
            if valid_till:
                g.add((period, DCAT.endDate, Literal(valid_till)))

        # dct:issued
        date_released = dataset_dict.get('dataset-reference-date') or dataset_dict.get('metadata_created')

        if date_released:
            issued_date = Literal(date_released)
            g.add((dataset_ref, DCT.issued, issued_date))

    def graph_from_catalog(self, catalog_dict, catalog_ref):
        # Fetch organization list for graph_from_dataset to use

        context = {'user': p.c.user}
        thread_local.organization_list = \
            p.get_action('organization_list')(context, {"all_fields": True, "include_extras": True,
                                                        "include_dataset_count": False})
        thread_local.group_list = p.get_action('group_list')(context, {"all_fields": True, "include_extras": True,
                                                                       "include_dataset_count": False})
        g = self.g

        for prefix, namespace in namespaces.items():
            g.bind(prefix, namespace)

        g.add((catalog_ref, RDF.type, DCAT.Catalog))

        # Basic fields
        title = p.config.get('ckan.site_title', '')
        g.add((catalog_ref, DCT.title, Literal(title)))

        description = ('Suomen kansallinen avoimen datan portaali. Avoindata.fi on kaikille tarkoitettu palvelu avoimen '
                       'datan julkaisemiseen ja hyödyntämiseen. Den finska nationella dataportalen för öppna data. '
                       'Avoindata.fi är en tjänst för att publicera och utnyttja öppna data. The Finnish national open data '
                       'portal. Opendata.fi is a service for publishing and utilising open data for everyone.')
        g.add((catalog_ref, DCT.description, Literal(description)))

        spatial = 'koko Suomi, hela Finland, entire Finland'
        g.add((catalog_ref, DCT.spatial, Literal(spatial)))

        issued = '15.09.2014'
        g.add((catalog_ref, DCT.issued, Literal(issued)))

        homepage = URIRef(p.config.get('ckan.site_url', ''))
        g.add((catalog_ref, FOAF.homepage, homepage))

        language = p.config.get('ckan.locale_default', 'en')
        linguistic_system = URIRef('http://id.loc.gov/vocabulary/iso639-1/%s' % language)
        g.add((linguistic_system, RDF.type, DCT.LinguisticSystem))
        g.add((catalog_ref, DCT.language, linguistic_system))

        publisher = BNode()
        g.add((publisher, RDF.type, FOAF.Organization))
        g.add((publisher, FOAF.hasSite, URIRef(p.config.get('ckan.site_url', ''))))
        name = u'Digi- ja väestötietovirasto, Myndigheten för digitalisering och befolkningsdata, the Finnish Digital Agency'
        g.add((publisher, FOAF.name, Literal(name)))
        g.add((catalog_ref, DCT.publisher, publisher))

        # Dates
        modified = self._last_catalog_modification()
        if modified:
            self._add_date_triple(catalog_ref, DCT.modified, modified)
