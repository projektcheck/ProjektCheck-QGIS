# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import random
import os

from projektcheck.base import Geopackage, Field


class GeopackageTest(unittest.TestCase):
    """Test geopackage backend"""

    @classmethod
    def setUpClass(cls):
        cls.backend = Geopackage()
        #workspaces = self.backend.workspaces
        #self.workspace = self.backend.get_workspace(workspaces[0])
        cls.workspace = cls.backend.create_workspace('test', overwrite=True)

    def setUp(self):
        fields = {
            'name': str,
            'value': float
        }
        self.table = self.workspace.create_table(
            'testtable', fields, geometry_type='Polygon', overwrite=True,
            defaults={'value': 0.0})
        self.table.add(name='row1', value=5)
        self.table.add(name='row2', value=5)
        self.table.add(name='row3', value=6)
        self.table.add(name='row4', value=0)

    def tearDown(self):
        pass

    def test_where(self):
        assert len(self.table) == 4
        self.table.where = 'value=6'
        assert len(self.table) == 1
        self.table.where = 'value=5'
        assert len(self.table) == 2

    def test_feature_filter(self):
        features = self.table.features()
        assert len(features) == 4
        assert len(features.filter(value=0)) == 1
        assert len(features.filter(value=6)) == 1
        assert len(features.filter(value=5)) == 2
        assert len(features.filter(value__lt=4)) == 1
        assert len(features.filter(value__gt=7)) == 0
        # test filter chain
        feat_f = features.filter(value__in=[5, 6])
        assert len(feat_f) == 3
        assert len(feat_f.filter(value=0)) == 0
        assert len(feat_f.filter(value__lt=4)) == 0
        assert len(feat_f.filter(value__gt=4)) == 3

        assert len(feat_f.filter(id=1)) == 1
        assert len(feat_f.filter(id=20)) == 0
        assert len(feat_f.filter(id__in=[1, 2])) == 2

    def test_cursor(self):
        for i, row in enumerate(self.table):
            row['value'] = i
            # test list
            self.table.update_cursor([i]*len(row))
            # test dict
            self.table.update_cursor(row)
        self.table.where = f'value={i}'
        assert len(self.table) == 1
        self.table.where = ''
        assert len(self.table)  == 4

        assert self.table[2]['value'] == 2
        assert self.table[0]['value'] == 0
        assert self.table[-1]['value'] == 3

    def test_add_delete(self):
        assert len(self.table) == 4
        self.table.add(value=7)
        for i in range(3):
            self.table.add(value=5)
        assert len(self.table) == 8
        n = self.table.delete_rows(value=5)
        assert n == 5
        assert len(self.table) == 3

    def test_pandas(self):
        a = self.table.as_pandas()

    def test_fields(self):
        self.table.add_field(Field(int, default=0, name='1'))
        self.table.add_field(Field(str, default='hallo', name='2'))
        self.table.add(geom=None)
        df = self.table.as_pandas()
        uq1 = df['1'].unique()
        uq2 = df['2'].unique()
        assert len(uq1) == 1
        assert uq1[0] == 0
        assert len(uq2) == 1
        assert uq2[0] == 'hallo'

    @classmethod
    def tearDownClass(cls):
        cls.workspace.close()
        os.remove('test.gpkg')

if __name__ == "__main__":
    suite = unittest.makeSuite(GeopackageTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
