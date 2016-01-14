import os
import logging

from nose.tools import assert_equal

from ckanext.qa.sniff_format import sniff_file_format, is_json, is_ttl, turtle_regex

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('ckan.sniff')


class TestSniffFormat:
    @classmethod
    def setup_class(cls):
        # Assemble a list of the test fixture data files.
        # They MUST have a file extension equal to the format they will be correctly
        # sniffed as. e.g. .xls  or  .xls.zip
        cls.fixture_files = [] # (format_extension, filepath)
        fixture_data_dir = os.path.join(os.path.dirname(__file__), 'data')
        for filename in os.listdir(fixture_data_dir):
            format_extension = '.'.join(filename.split('.')[1:])
            filepath = os.path.join(fixture_data_dir, filename)
            cls.fixture_files.append((format_extension, filepath))

    @classmethod
    def assert_file_has_format_sniffed_correctly(cls, format_extension, filepath):
        '''Given a filepath, checks the sniffed format matches the format_extension.'''
        expected_format = format_extension
        sniffed_format = sniff_file_format(filepath, log)
        assert sniffed_format, expected_format
        expected_format_without_zip = expected_format.replace('.zip', '')
        assert_equal(sniffed_format['format'].lower(), expected_format_without_zip)

        expected_container = None
        if expected_format.endswith('.zip'):
            expected_container = 'ZIP'
        elif expected_format.endswith('.gzip'):
            expected_container = 'ZIP'  # lumped together with zip for simplicity now
        assert_equal(sniffed_format.get('container'), expected_container)

    #def test_all(self):
    #    for format_extension, filepath in self.fixture_files:
    #        self.assert_file_has_format_sniffed_correctly(format_extension, filepath)

    @classmethod
    def check_format(cls, format, filename=None):
        for format_extension, filepath in cls.fixture_files:
            if format_extension == format:
                if filename:
                    if filename in filepath:
                        break
                    else:
                        continue
                else:
                    break
        else:
            assert 0, format #Could not find fixture for format
        cls.assert_file_has_format_sniffed_correctly(format_extension, filepath)

    def test_xls(self):
        self.check_format('xls', '10-p108-data-results')
    def test_xls1(self):
        self.check_format('xls', 'August-2010.xls')
    def test_xls2(self):
        self.check_format('xls', 'ukti-admin-spend-nov-2011.xls')
    def test_xls3(self):
        self.check_format('xls', 'decc_local_authority_data_xlsx.xls')
    def test_xls_zip(self):
        self.check_format('xls.zip', 'telephone-network-data.xls.zip')
    def test_rdf(self):
        self.check_format('rdf', '300911---EH---organogram---ver1.rdf')
    def test_rdf2(self):
        self.check_format('rdf', 'ukk1202-36000.rdf')
    def test_pdf(self):
        self.check_format('pdf')
    def test_kml(self):
        self.check_format('kml')
    def test_rdfa(self):
        self.check_format('rdfa')
    def test_doc(self):
        self.check_format('doc')
    def test_json(self):
        self.check_format('json')
    def test_ods(self):
        self.check_format('ods')
    def test_odt(self):
        self.check_format('odt')
    def test_odp(self):
        self.check_format('odp')
    def test_ppt(self):
        self.check_format('ppt')
    def test_csv(self):
        self.check_format('csv', 'elec00.csv')
    def test_csv1(self):
        self.check_format('csv', 'spendover25kdownloadSep.csv')
    def test_csv2(self):
        self.check_format('csv', '311011.csv')
    def test_csv3(self):
        self.check_format('csv', 'FCOServices_TransparencySpend_May2011.csv')
    def test_csv4(self):
        self.check_format('csv', 'iwfg09_Phos_river_200911.csv')
    def test_csv5(self):
        self.check_format('csv', '9_sus_fisheries_201003.csv')
    def test_csv6(self):
        self.check_format('csv', 'Inpatients_MHA_Machine_readable_dataset_1011.csv')
    def test_shp(self):
        self.check_format('shp')
    def test_html(self):
        self.check_format('html', 'index.html')
    def test_html1(self):
        self.check_format('html', '6a7baac6-d363-4a9d-8e9d-e584f38c05c3.html')
    def test_html2(self):
        self.check_format('html', 'hourly_means.html')
    def test_xml(self):
        self.check_format('xml', 'jobs.xml')
    def test_xml1(self):
        self.check_format('xml', '082010CreditorInvoicesover500.xml')
    def test_xml2(self):
        self.check_format('xml', 'DfidProjects-trunc.xml')
    def test_iati(self):
        self.check_format('iati')
    def test_rss(self):
        self.check_format('rss')
    def test_txt(self):
        self.check_format('txt')
    def test_txt_2(self):
        self.check_format('txt', 'terrible_csv.txt')
    def test_csv_zip(self):
        self.check_format('csv.zip', 'written_complains.csv.zip')
    def test_csv_zip1(self):
        self.check_format('csv.zip', 'cycle-area-list.csv.zip')
    def test_txt_zip(self):
        self.check_format('txt.zip')
    def test_xml_zip(self):
        self.check_format('xml.zip')
    #def test_torrent(self):
    #    self.check_format('torrent')
    def test_psv(self):
        self.check_format('psv')
    def test_wms_1_3(self):
        self.check_format('wms', 'afbi_get_capabilities.wms')
    def test_wms_1_1_1(self):
        self.check_format('wms', 'oldham_get_capabilities.wms')
    #def test_ics(self):
    #    self.check_format('ics')
    def test_ttl1(self):
        self.check_format('ttl', 'turtle.ttl')
    def test_ttl2(self):
        self.check_format('ttl', 'turtle-imd-education-score-2010.ttl')
    def test_ttl3(self):
        self.check_format('ttl', 'turtle-homelessness-acceptances-per-1000.ttl')

def test_is_json():
    assert is_json('5', log)
    assert is_json('-5', log)
    assert is_json('-5.4', log)
    assert is_json('-5.4e5', log)
    assert is_json('-5.4e-5', log)
    assert not is_json('4.', log)
    assert is_json('"hello"', log)
    assert not is_json('hello"', log)
    assert is_json('["hello"]', log)
    assert not is_json('"hello"]', log)
    assert is_json('[5]', log)
    assert is_json('[5, 6]', log)
    assert is_json('[5,6]', log)
    assert is_json('["cat", 6]', log)
    assert is_json('{"cat": 6}', log)
    assert is_json('{"cat":6}', log)
    assert is_json('{"cat": "bob"}', log)
    assert is_json('{"cat": [1, 2]}', log)
    assert is_json('{"cat": [1, 2], "dog": 5, "rabbit": "great"}', log)
    assert not is_json('{"cat": [1, 2}]', log)
    assert is_json('[{"cat": [1]}, 2]', log)

    # false positives of the algorithm:
    #assert not is_json('[{"cat": [1]}2, 2]', log)

def test_turtle_regex():
    template = '<subject> <predicate> %s .'
    assert turtle_regex().search(template % '<url>')
    assert turtle_regex().search(template % '"a literal"')
    assert turtle_regex().search(template % '"translation"@ru')
    assert turtle_regex().search(template % '"literal type"^^<http://www.w3.org/2001/XMLSchema#string>')
    assert turtle_regex().search(template % '"literal typed with prefix"^^xsd:string')
    assert turtle_regex().search(template % "'single quotes'")
    assert turtle_regex().search(template % '"""triple quotes but not multiline"""')
    assert turtle_regex().search(template % "'''triple quotes but not multiline'''")
    assert turtle_regex().search(template % '12')
    assert turtle_regex().search(template % '1.12')
    assert turtle_regex().search(template % '.12')
    assert turtle_regex().search(template % '12E12')
    assert turtle_regex().search(template % '-4.2E-9')
    assert turtle_regex().search(template % 'false')
    assert turtle_regex().search(template % '_:blank_node')
    assert turtle_regex().search('<s> <p> <o> ;\n <p> <o> .')
    assert turtle_regex().search('<s> <p> <o>;<p> <o>.')
    # Include triples which are part of a nest:
    assert turtle_regex().search('<s> <p> <o> ;')
    assert turtle_regex().search('<s> <p> <o>;')
    assert turtle_regex().search(' ;<p> <o>.')
    assert turtle_regex().search(';\n<p> <o>.')
    assert turtle_regex().search(';\n<p> <o>;')
    assert not turtle_regex().search('<s> <p> <o>. rubbish')
    assert not turtle_regex().search(template % 'word')
    assert not turtle_regex().search(template % 'prefix:node')


def test_is_ttl__num_triples():
    triple = '<subject> <predicate> <object>; <predicate> <object>.'
    assert not is_ttl('\n'.join([triple]*2), log)
    assert is_ttl('\n'.join([triple]*5), log)

