import os
import logging

from nose.tools import raises, assert_equal

from ckanext.qa import tasks
from ckanext.qa.sniff_format import is_json

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('sniff')

class TestSniffFormat:
    @classmethod
    def setup_class(cls):
        # assemble a list of the test fixture data files
        cls.fixture_files = [] # (format_extension, filepath)
        fixture_data_dir = os.path.join(os.path.dirname(__file__), 'data')
        for filename in os.listdir(fixture_data_dir):
            format_extension = '.'.join(filename.split('.')[1:])
            filepath = os.path.join(fixture_data_dir, filename)
            cls.fixture_files.append((format_extension, filepath))

    def test_all(self):
        for format_, filepath in self.fixture_files:
            sniffed_format = tasks.sniff_file_format(filepath, log)
            print 'Testing %s %s' % (format_, filepath)
            assert sniffed_format, format_
            assert_equal(sniffed_format['extension'] or \
                         sniffed_format['display_name'].lower(), format_)

    @classmethod
    def check_format(cls, format, filename=None):
        for format_, filepath in cls.fixture_files:
            if format_ == format:
                if filename:
                    if filename in filepath:
                        break
                    else:
                        continue
                else:
                    break
        else:
            assert 0, format #Could not find fixture for format
        sniffed_format = tasks.sniff_file_format(filepath, log)
        assert sniffed_format, format_
        assert_equal(sniffed_format['extension'] or \
                     sniffed_format['display_name'].lower(), format_)

    def test_xls(self):
        self.check_format('xls', '10-p108-data-results')
    def test_xls1(self):
        self.check_format('xls', 'August-2010.xls')
    def test_xls2(self):
        self.check_format('xls', 'ukti-admin-spend-nov-2011.xls')
    def test_xls3(self):
        self.check_format('xls', 'decc_local_authority_data_xlsx.xls')
    def test_xls_zip(self):
        self.check_format('xls.zip')
    def test_rdf(self):
        self.check_format('rdf')
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
    def test_csv_zip(self):
        self.check_format('csv.zip', 'written_complains.csv.zip')
    def test_csv_zip1(self):
        self.check_format('csv.zip', 'cycle-area-list.csv.zip')
    def test_txt_zip(self):
        self.check_format('txt.zip')
    def test_xml_zip(self):
        self.check_format('xml.zip')
    def test_torrent(self):
        self.check_format('torrent')
    def test_psv(self):
        self.check_format('psv')
    def test_wms(self):
        self.check_format('wms')
    def test_ics(self):
        self.check_format('ics')

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

