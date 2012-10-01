import os
import logging

from nose.tools import raises, assert_equal

from ckanext.qa import tasks
from ckanext.qa.sniff_format import is_json

log = logging.getLogger('ckan.tests')

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
            assert sniffed_format, format_
            assert_equal(sniffed_format['extension'] or \
                         sniffed_format['display_name'].lower(), format_)

    @classmethod
    def check_format(cls, format):
        for format_, filepath in cls.fixture_files:
            if format_ == format:
                break
        else:
            assert 0, format #Could not find fixture for format
        sniffed_format = tasks.sniff_file_format(filepath, log)
        assert sniffed_format, format_
        assert_equal(sniffed_format['extension'] or \
                     sniffed_format['display_name'].lower(), format_)

    def test_xls(self):
        self.check_format('xls')
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
    def test_ppt(self):
        self.check_format('ppt')
    def test_csv(self):
        self.check_format('csv')
    def test_shp(self):
        self.check_format('shp')
    def test_html(self):
        self.check_format('html')
    def test_xml(self):
        self.check_format('xml')
    def test_rss(self):
        self.check_format('rss')
    def test_txt(self):
        self.check_format('txt')
    def test_csv_zip(self):
        self.check_format('csv.zip')

def test_is_json():
    assert is_json('5')
    assert is_json('-5')
    assert is_json('-5.4')
    assert is_json('-5.4e5')
    assert is_json('-5.4e-5')
    assert not is_json('4.')
    assert is_json('"hello"')
    assert not is_json('hello"')
    assert is_json('["hello"]')
    assert not is_json('"hello"]')
    assert is_json('[5]')
    assert is_json('[5, 6]')
    assert is_json('[5,6]')
    assert is_json('["cat", 6]')
    assert is_json('{"cat": 6}')
    assert is_json('{"cat":6}')
    assert is_json('{"cat": "bob"}')
    assert is_json('{"cat": [1, 2]}')
    assert is_json('{"cat": [1, 2], "dog": 5, "rabbit": "great"}')
    assert not is_json('{"cat": [1, 2}]')
    assert is_json('[{"cat": [1]}, 2]')

    # false positives of the algorithm:
    #assert not is_json('[{"cat": [1]}2, 2]')

