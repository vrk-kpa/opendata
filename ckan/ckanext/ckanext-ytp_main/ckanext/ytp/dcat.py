import six
import json
import threading
import uuid
import urllib
import string
from rdflib import URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, XSD
from ckanext.dcat.profiles import RDFProfile, VCARD, DCAT, DCT, FOAF, SKOS, ADMS, SPDX, LOCN, GSP, SCHEMA
from ckanext.dcat.processors import RDFSerializer
from ckanext.dcat.utils import resource_uri, url_quote, url_to_rdflib_format, catalog_uri
from ckan.plugins import toolkit as p
import ckan.lib.helpers as h

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

    def _basic_fields_graph(self, dataset_ref, dataset_dict):
        items = [
            ('identifier', SCHEMA.identifier, None, Literal),
            ('title', SCHEMA.name, None, Literal),
            ('notes', SCHEMA.description, None, Literal),
            ('version', SCHEMA.version, ['dcat_version'], Literal),
            ('issued', SCHEMA.datePublished, ['metadata_created'], Literal),
            ('modified', SCHEMA.dateModified, ['metadata_modified'], Literal),
            ('license', SCHEMA.license, ['license_url', 'license_title'], Literal),
        ]
        self._add_triples_from_dict(dataset_dict, dataset_ref, items)

        items = [
            ('issued', SCHEMA.datePublished, ['metadata_created'], Literal),
            ('modified', SCHEMA.dateModified, ['metadata_modified'], Literal),
        ]

        self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        # Dataset URL
        dataset_url =  h.url_for('{}.read'.format(dataset_dict.get('type', 'dataset')),
                                 id=dataset_dict['name'])
        self.g.add((dataset_ref, SCHEMA.url, Literal(dataset_url)))

    def _parse_apiset(self, dataset_dict, dataset_ref):
        g = self.g
        endpoint_urls = BNode()
        for resource_dict in dataset_dict.get('resources', []):
            g.add((endpoint_urls, DCAT.endpointURL, uriref(resource_dict.get('url'))))
        g.add((dataset_ref, DCAT.endpointURL, endpoint_urls))
        access_rights = dataset_dict.get('access_rights_translated', None)
        if access_rights and instanceof(access_rights, dict):
            rights_statement = BNode()
            access_rights_value = access_rights.values()
            g.add((rights_statement, RDF.type, DCT.RightsStatement))
            g.add((rights_statement, DCT.description, Literal('\n\n'.join(access_rights_value))))
            g.add((dataset_ref, DCT.rights, rights_statement))

    def _parse_showcase(self, dataset_dict, dataset_ref):
        g = self.g
        showcase_url = h.url_for('{}.read'.format(dataset_dict.get('type', 'dataset')),
                                 id=dataset_dict.get('name'))
        g.add((dataset_ref, ADFI.DataUserInterface, uriref(showcase_url)))

        if dataset_dict.get('platform', None):
            platform = BNode()
            g.add((dataset_ref, ADFI.platform, platform))

            for showcase_platform in dataset_dict.get('platform'):
                g.add((platform, ADFI.platform, Literal(showcase_platform)))

        creator = BNode()
        g.add((dataset_ref, DCT.creator, creator))
        g.add((creator, FOAF.name, Literal(dataset_dict.get('author'))))

        organization = {
                        'title': dataset_dict.get('author'),
                        'homepage': dataset_dict.get('author_website'),
                       }
        publisher = URIRef(organization.get('homepage', ''))
        g.add((dataset_ref, DCT.publisher, publisher))
        g.add((publisher, FOAF.name, Literal(organization.get('title', ''))))

        self._add_triple_from_dict(organization, publisher, FOAF.homepage, 'homepage')

        if dataset_dict.get('author_website', None):
            g.add((creator, FOAF.homepage, uriref(dataset_dict.get('author_website'))))

        if dataset_dict.get('application_website', None):
            g.add((dataset_ref, DCAT.landingPage, uriref(dataset_dict.get('application_website'))))
        
        if dataset_dict.get('store_urls', None):
            distributor = BNode()
            g.add((dataset_ref, ADFI.distributor, distributor))

            for store_url in dataset_dict.get('store_urls'):
                store_url.strip()
                try:
                    pieces = urllib.parse.urlparse(store_url)
                    if all([pieces.scheme, pieces.netloc]) and \
                        set(pieces.netloc) <= set(string.ascii_letters + string.digits + '-.') and \
                        pieces.scheme in ['http', 'https']:
                            document = URIRef(url_quote(store_url.encode('utf-8')))
                            g.add((document, RDF.type, FOAF.Document))
                            g.add((distributor, DCAT.accessURL, document))
                except ValueError:
                    log.debug('Invalid store url (%s) in showcase %s', store_url, dataset_dict.get('id'))

        if dataset_dict.get('image_url', None):
            g.add((dataset_ref, ADFI.applicationIcon, uriref(dataset_dict.get('image_url'))))

        preview_medias = []

        for x in range(1, 4):
            if dataset_dict.get('image_{}_display_url'.format(x), None):
                preview_medias.append(dataset_dict.get('image_{}_display_url'.format(x)))
        
        if len(preview_medias) > 0:
            previewMedia = BNode()
            g.add((dataset_ref, ADFI.previewMedia, previewMedia))

            for preview_media in preview_medias:
                g.add((previewMedia, ADFI.previewMedia, uriref(preview_media)))


        if dataset_dict.get('archived', None):
            g.add((dataset_ref, ADFI.archived, uriref(dataset_dict.get('archived'))))


    def parse_dataset(self, dataset_dict, dataset_ref):
        return dataset_dict


    def graph_from_dataset(self, dataset_dict, dataset_ref):
        g = self.g

        for prefix, namespace in namespaces.items():
            g.bind(prefix, namespace)

        self._basic_fields_graph(dataset_ref, dataset_dict)

        # Flatten extras
        for extra in dataset_dict.get('extras', []):
            key = extra['key']
            if key not in dataset_dict:
                dataset_dict[key] = extra['value']

        dataset_type = dataset_dict.get('type', None)

        dcat_type = DCAT.Dataset

        if  dataset_type == 'apiset':
            dcat_type = DCAT.DataService
            self._parse_apiset(dataset_dict, dataset_ref)
        elif dataset_type == 'showcase':
            dcat_type = ADFI.Showcase
            self._parse_showcase(dataset_dict, dataset_ref)
        else:
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
            
            international_benchmarks = dataset_dict.get('international_benchmarks', [])
            if len(international_benchmarks) > 0:
                benchmarks_bnode = BNode()
                g.add((dataset_ref, DCT.theme, benchmarks_bnode))
                for international_benchmark in international_benchmarks:
                    g.add((benchmarks_bnode, DCT.title, Literal(international_benchmark)))

        g.add((dataset_ref, RDF.type, dcat_type))

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

            geographical_accuracy = resource_dict.get('geographical_accuracy', None)
            if geographical_accuracy:
                g.add((distribution, DCAT.spatialResolutionInMeters, Literal(geographical_accuracy, datatype=XSD.decimal)))

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
                    g.add((period, DCAT.startDate, Literal(temporal_coverage_from, datatype=XSD.date)))
                if temporal_coverage_to:
                    g.add((period, DCAT.endDate, Literal(temporal_coverage_to, datatype=XSD.date)))

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
                g.add((period, DCAT.startDate, Literal(valid_from, datatype=XSD.date)))
            if valid_till:
                g.add((period, DCAT.endDate, Literal(valid_till, datatype=XSD.date)))

        # dct:issued
        date_released = dataset_dict.get('date_released') or dataset_dict.get('metadata_created')

        if date_released:
            issued_date = Literal(date_released, datatype=XSD.date)
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
        location = BNode()
        g.add((catalog_ref, DCT.spatial, location))
        g.add((location, RDF.type, DCT.Location))
        g.add((location, DCT.spatial, Literal(spatial)))

        issued = '2014-09-15'
        g.add((catalog_ref, DCT.issued, Literal(issued, datatype=XSD.date)))

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


def dataset_uri(dataset_dict):
    '''
    Returns an URI for the dataset
    This will be used to uniquely reference the dataset on the RDF
    serializations.
    The value will be the first found of:
        1. The value of the `uri` field
        2. The value of an extra with key `uri`
        3. `catalog_uri()` + '/dataset/' + `id` field
    Check the documentation for `catalog_uri()` for the recommended ways of
    setting it.
    Returns a string with the dataset URI.
    '''

    uri = dataset_dict.get('uri')
    if not uri:
        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'uri' and extra['value'] != 'None':
                uri = extra['value']
                break
    if not uri and dataset_dict.get('id'):
        uri = '{0}/{1}/{2}'.format(catalog_uri().rstrip('/'),
                                       dataset_dict.get('type', 'dataset'),
                                       urllib.parse.quote(dataset_dict['id']))
    if not uri:
        uri = '{0}/{1}/{2}'.format(catalog_uri().rstrip('/'),
                                       dataset_dict.get('type', 'dataset'),
                                       str(uuid.uuid4()))
        log.warning('Using a random id for dataset URI')

    return uri


class AvoindataSerializer(RDFSerializer):
    '''
    A CKAN to RDF serializer based on rdflib
    Supports different profiles which are the ones that will generate
    the RDF graph.
    '''


    def graph_from_dataset(self, dataset_dict):
        '''
        Given a CKAN dataset dict, creates a graph using the loaded profiles
        The class RDFLib graph (accessible via `serializer.g`) will be updated
        by the loaded profiles.
        Returns the reference to the dataset, which will be an rdflib URIRef.
        '''

        dataset_ref = URIRef(dataset_uri(dataset_dict))

        for profile_class in self._profiles:
            profile = profile_class(self.g, self.compatibility_mode)
            profile.graph_from_dataset(dataset_dict, dataset_ref)

        return dataset_ref

    def serialize_catalog(self, catalog_dict=None, dataset_dicts=None,
                          _format='xml', pagination_info=None):
        '''
        Returns an RDF serialization of the whole catalog
        `catalog_dict` can contain literal values for the dcat:Catalog class
        like `title`, `homepage`, etc. If not provided these would get default
        values from the CKAN config (eg from `ckan.site_title`).
        If passed a list of CKAN dataset dicts, these will be also serializsed
        as part of the catalog.
        **Note:** There is no hard limit on the number of datasets at this
        level, this should be handled upstream.
        The serialization format can be defined using the `_format` parameter.
        It must be one of the ones supported by RDFLib, defaults to `xml`.
        `pagination_info` may be a dict containing keys describing the results
        pagination. See the `_add_pagination_triples()` method for details.
        Returns a string with the serialized catalog
        '''

        catalog_ref = self.graph_from_catalog(catalog_dict)
        if dataset_dicts:
            for dataset_dict in dataset_dicts:
                dataset_ref = self.graph_from_dataset(dataset_dict)

                cat_ref = self._add_source_catalog(catalog_ref, dataset_dict, dataset_ref)
                if not cat_ref and dataset_dict.get('type', None) == 'apiset':
                    self.g.add((catalog_ref, DCAT.dataservice, dataset_ref))
                elif not cat_ref and dataset_dict.get('type', None) == 'showcase':
                    self.g.add((catalog_ref, ADFI.showcase, dataset_ref))
                elif not cat_ref:
                    self.g.add((catalog_ref, DCAT.dataset, dataset_ref))

        if pagination_info:
            self._add_pagination_triples(pagination_info)

        if not _format:
            _format = 'xml'
        _format = url_to_rdflib_format(_format)
        output = self.g.serialize(format=_format)

        return output
