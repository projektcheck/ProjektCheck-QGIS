# -*- coding: utf-8 -*-
import subprocess
import os
import sys
from collections import OrderedDict
import pandas as pd
import numpy as np
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.PyQt.Qt import QVariant
from qgis.core import (QgsField, QgsVectorLayer, QgsVectorFileWriter,
                       QgsFeature, QgsProject)

from projektchecktools.utils.spatial import google_geocode
from projektchecktools.base.dialogs import Dialog
from projektchecktools.domains.marketcompetition.markets import (
    Supermarket, ReadMarketsWorker)
from settings import settings


DEFAULT_NAME = 'maerkte_vorlage'


class MarketTemplateImportWorker(ReadMarketsWorker):

    def __init__(self, file_path, project, epsg=4326, truncate=False,
                 parent=None):
        super().__init__(project=project, parent=parent)
        self.project = project
        self.file_path = file_path
        self.truncate = truncate

    def work(self):
        name, ext = os.path.splitext(os.path.split(self.file_path)[1])
        extensions = [v[0] for v in MarketTemplate.template_types.values()]
        idx = extensions.index(ext)
        template_type = MarketTemplate.template_types.keys()[idx]
        template = MarketTemplate(template_type, self.file_path,
                                  epsg=self.epsg)
        self.log('Lese Datei ein...')
        markets = template.get_markets()
        markets = self.parse_meta(markets, field='kette')
        markets = self.vkfl_to_betriebstyp(markets)
        self.log(f'Schreibe {len(markets)} Märkte in die Datenbank...')
        self.markets_to_db(markets, truncate=self.truncate)
        self.log('Aktualisiere die AGS der Märkte...')
        self.set_ags()


class MarketTemplateCreateDialog(Dialog):
    ui_file = 'create_template.ui'

    def __init__(self):
        super().__init__(self.ui_file, modal=False)

    def setupUi(self):
        self.template_type_combo.addItems(MarketTemplate.template_types.keys())

        self.browse_button.clicked.connect(self.browse_path)
        self.ok_button.clicked.connect(self.create_template)
        self.cancel_button.clicked.connect(self.reject)

    def create_template(self):
        typ = self.template_type_combo.currentText()
        template = MarketTemplate(typ, self.path_edit.text(),
                                  epsg=settings.EPSG)
        success = template.create()
        if success:
            template.open()
            self.close()
        else:
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Beim Schreiben des Templates ist ein Fehler aufgetreten.\n'
                'Bitte prüfen Sie die Schreibrechte im gewählten Ordner')

    def browse_path(self):
        typ = self.template_type_combo.currentText()
        ext = MarketTemplate.template_types[typ][0]
        path, f = QFileDialog.getSaveFileName(
            self, 'Speichern unter',
            os.path.join(self.path_edit.text(), DEFAULT_NAME + ext),
            f'{typ} (*{ext})'
        )
        if not path:
            return
        self.path_edit.setText(path)


class MarketTemplate(object):
    '''
    class for managing templates holding markets as inputs for the Tool
    'Standortkonkurrenz'

    Parameters
    ----------
        template_type : str,
            type of file to use as template
            (for options see keys of class variable 'template_types')
        path : str,
            the path to write to and read the templates from
        filename : str, optional (defaults to 'maerkte_vorlage.<extension>')
            name of the file
        epsg : int, optional (defaults to 4326)
            the projection (required to write shapefiles)
    '''

    template_types = {
        'CSV-Datei': ('.csv', 'ProjektCheck_Anleitung_WB7_Erfassungsvorlage_Maerkte_CSVDatei_befuellen.pdf'),
        'Exceldatei': ('.xlsx', 'ProjektCheck_Anleitung_WB7_Erfassungsvorlage_Maerkte_Exceldatei_befuellen.pdf'),
        'Shapefile': ('.shp', 'ProjektCheck_Anleitung_WB7_Erfassungsvorlage_Maerkte_ShapeFile_befuellen.pdf')
     }

    _required_fields = OrderedDict([
        (u'Name', str),
        (u'Kette', str)
    ])

    _address_fields = OrderedDict([
        (u'Ort', str),
        (u'PLZ', str),
        (u'Straße', str),
        (u'Hausnummer', int)
    ])

    _option_1 = {u'Vkfl_m²': int}
    _option_2 = {u'BTyp': int}

    _seperator = 'SEMICOLON'

    def __init__(self, template_type, file_path, epsg=4326):
        self.template_type = template_type

        if template_type not in self.template_types.keys():
            raise Exception('unknown type of template')

        self.file_path = file_path

        self.epsg = epsg

        self.fields = self._required_fields.copy()
        if self.template_type in ['CSV-Datei', 'Exceldatei']:
            self.fields.update(self._address_fields)
        self.fields.update(self._option_1)

    def create(self):
        '''create the template file, overwrites if already exists'''
        layer = self._create_template_layer(self.fields, epsg=self.epsg)
        try:
            if self.template_type == 'CSV-Datei':
                self._export_to_csv(layer, self.file_path, self._seperator)
            elif self.template_type == 'Exceldatei':
                self._export_to_xlsx(layer, self.file_path)
            elif self.template_type == 'Shapefile':
                self._export_to_shape_file(layer, self.file_path)
        # actually never seems to happen, QgsVectorFileWriter always seems
        # to return 0 (on success and failure) not throwing anything
        except QgsVectorFileWriter.WriterError:
            return False

        return True

    def open(self):
        '''open the file (externally with default app if not a shape file)'''
        if self.template_type == 'Exceldatei':
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', self.file_path))
            elif os.name == 'nt':
                os.startfile(self.file_path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', self.file_path))
        elif self.template_type == 'CSV-Datei':
            subprocess.Popen(r'explorer /select,"{}"'
                             .format(os.path.normpath(self.file_path)))
        elif self.template_type == 'Shapefile':
            name = os.path.splitext(os.path.split(self.file_path)[1])[0]
            layer = QgsVectorLayer(self.file_path, name, 'ogr')
            QgsProject.instance().addMapLayer(layer)

    @staticmethod
    def _create_template_layer(fields, epsg=4326):
        layer = QgsVectorLayer(f'Point?crs=EPSG:{epsg}', 'template', 'memory')
        pr = layer.dataProvider()
        for field_name, typ in fields.items():
            qtyp = QVariant.Int if typ == int else QVariant.String
            qfield = QgsField(field_name, qtyp)
            pr.addAttributes([qfield])
        layer.updateFields()
        return layer

    @staticmethod
    def _export_to_csv(layer, file_path, seperator='SEMICOLON'):
        QgsVectorFileWriter.writeAsVectorFormat(
            layer, file_path, 'utf-8', layer.crs(), 'CSV',
            layerOptions=[f'SEPARATOR={seperator}'])
            # , layerOptions='GEOMETRY=AS_XYZ')

    @staticmethod
    def _export_to_xlsx(layer, file_path):
        # needs at least one feature to write the header (empty one is fine)
        layer.dataProvider().addFeature(QgsFeature())
        QgsVectorFileWriter.writeAsVectorFormat(
            layer, file_path, 'utf-8', layer.crs(), 'xlsx')

    @staticmethod
    def _export_to_shape_file(layer, file_path):
        QgsVectorFileWriter.writeAsVectorFormat(
            layer, file_path, 'utf-8', layer.crs(), 'ESRI Shapefile')

    def get_markets(self):
        '''read and return the markets from file'''
        if self.template_type == 'CSV-Datei':
            df = None
            for encoding in ['utf-8-sig', 'ISO-8859-1']:
                try:
                    df = pd.DataFrame.from_csv(
                        self.file_path, sep=self._delimiter,
                        encoding=encoding)
                    break
                except:
                    continue
            if df is None:
                raise Exception(u'Es gibt ein Problem mit der '
                                u'Zeichenkodierung der CSV-Datei!')
            df = df.reset_index()
        elif self.template_type == 'Exceldatei':
            df = pd.read_excel(self.file_path)
        elif self.template_type == 'Shapefile':
            columns = [f.name for f in arcpy.ListFields(self.file_path)]
            cursor = arcpy.da.SearchCursor(self.file_path, columns)
            rows = [row for row in cursor]
            del cursor
            df = pd.DataFrame.from_records(rows, columns=columns)
        else:
            raise Exception('unknown type of template')
        required = self._required_fields.keys()
        if self.template_type in ['CSV-Datei', 'Exceldatei']:
            required += self._address_fields.keys()
        if np.in1d(required, df.columns).sum() < len(required):
            raise LookupError('missing fields in given file')
        markets = self._df_to_markets(df)
        return markets

    def _df_to_markets(self, df):
        markets = []
        api_key = config.google_api_key
        for i, (idx, row) in enumerate(df.iterrows()):
            address = ''
            name, kette, vkfl = row['Name'], row['Kette'], row[u'Vkfl_m²']
            if self.template_type in ['CSV-Datei', 'Exceldatei']:
                for field in self._address_fields.keys():
                    address += u' {}'.format(row[field])
                arcpy.AddMessage(u'Geocoding {name} {address}...'.format(
                    name=name, address=address))
                location, msg = google_geocode(address, api_key=api_key)
                if location is None:
                    arcpy.AddMessage(u'Fehler: {msg}'.format(msg=msg))
                    continue
                lat, lon = location
                market = Supermarket(i, lon, lat, name, kette, vkfl=vkfl,
                                     adresse=address, epsg=4326)
                market.transform(self.epsg)
            else:
                x, y = row['SHAPE']
                market = Supermarket(i, x, y, name, kette, vkfl=vkfl,
                                     epsg=self.epsg)
            markets.append(market)
        return markets
