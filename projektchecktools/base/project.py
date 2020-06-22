import os
from glob import glob
import sys
import json
import shutil
import sys
from collections import OrderedDict
from operator import itemgetter
from typing import Tuple, List

from projektchecktools.utils.singleton import Singleton
from projektchecktools.base.database import (Field, Table, FeatureCollection,
                                             Workspace)
from projektchecktools.base.geopackage import Geopackage
from projektchecktools.base.layers import Layer, TileLayer
from projektchecktools.utils.connection import Request

if sys.platform in ['win32', 'win64']:
    p = os.getenv('LOCALAPPDATA')
# Mac OS and Linux
else:
    p = os.path.expanduser('~')# , 'Library/Application Support/')
APPDATA_PATH = os.path.join(p, 'Projekt-Check-QGIS')

DEFAULT_SETTINGS = {
    'active_project': u'',
    'project_path': os.path.join(APPDATA_PATH, 'Projekte'),
    'basedata_path': os.path.join(APPDATA_PATH, 'Basisdaten'),
    'check_data_on_start': True,
    'disclaimer_read': False,
    'show_result_layer_info': True
}


class Settings(metaclass=Singleton):
    '''
    singleton for accessing and storing global settings in files

    Attributes
    ----------
    active_project : str
        the name of the active project
    project_path : str
        path to project folders
    '''
    _settings = {}
    # write changed config instantly to file
    _write_instantly = True

    def __init__(self, filename: str = 'projektcheck-config.txt'):
        '''
        Parameters
        ----------
        filename : str, optional
            name of file in APPDATA path to store settings in
            by default 'projektcheck-config.txt'
        '''
        if not os.path.exists(APPDATA_PATH):
            os.mkdir(APPDATA_PATH)

        self.config_file = os.path.join(APPDATA_PATH, filename)
        self._callbacks = {}
        self.active_coord = (0, 0)
        if os.path.exists(self.config_file):
            self.read()
            # add missing Parameters
            changed = False
            for k, v in DEFAULT_SETTINGS.items():
                if k not in self._settings:
                    self._settings[k] = v
                    changed = True
            if changed:
                self.write()

        # write default config, if file doesn't exist yet
        else:
            self._settings = DEFAULT_SETTINGS.copy()
            self.write()

    def read(self, config_file: str = None):
        '''
        read settings from file

        Parameters
        ----------
        config_file : str, optional
            path to file with settings, self.config_file used if None,
            by default None

        Raises
        ----------
        Exception
            file could not be read (e.g. wrong format, not existing)
        '''
        if config_file is None:
            config_file = self.config_file
        try:
            with open(config_file, 'r') as f:
                self._settings = json.load(f)
        except:
            self._settings = DEFAULT_SETTINGS.copy()
            print('Error while loading config. Using default values.')

    def write(self, config_file: str = None):
        '''
        write current settings to file

        Parameters
        ----------
        config_file : str, optional
            path to file with settings, self.config_file used if None,
            by default None
        '''
        if config_file is None:
            config_file = self.config_file

        with open(config_file, 'w') as f:
            config_copy = self._settings.copy()
            # pretty print to file
            json.dump(config_copy, f, indent=4, separators=(',', ': '))

    # access stored config entries like fields
    def __getattr__(self, name: str):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self._settings:
            return self._settings[name]
        raise AttributeError

    def __setattr__(self, name: str, value: object):
        if name in self._settings:
            self._settings[name] = value
            if self._write_instantly:
                self.write()
            if name in self._callbacks:
                for callback in self._callbacks[name]:
                    callback(value)
        else:
            self.__dict__[name] = value
        #if name in self._callbacks:
            #for callback in self._callbacks[name]:
                #callback(value)

    def __repr__(self):
        ret = ['{} - {}'.format(k, str(v)) for k, v in self.__dict__.items()
               if not callable(v) and not k.startswith('_')]
        ret.extend([f'{v} - {k}' for k, v in self._settings.items()])
        return '\n'.join(ret)

    def __contains__(self, item: str):
        return item in self.__dict__ or item in self._settings

    def on_change(self, attribute: str, callback: object):
        '''
        register callback function to be called on configuration
        attribute change

        Parameters
        ----------
        attribute : str
            name of the attribute
        callback : function
            function to call if value of attribute has changed,
            function should expect the value as a parameter
        '''
        if attribute not in self._callbacks:
            self._callbacks[attribute] = []
        self._callbacks[attribute].append(callback)

    def remove_listeners(self, attribute: str):
        '''
        remove all callback functions of an configuration attribute

        Parameters
        ----------
        attribute : str
            name of the attribute
        '''
        if attribute in self._callbacks:
            self._callbacks.pop(attribute)

settings = Settings()


class Project:
    '''
    single project holding paths to base and project data

    Attributes
    ----------
    path : str
        the full path to the local project folder containing the project data
    '''
    settings = settings


    def __init__(self, name: str, path: str = ''):
        '''
        Parameters
        ----------
        name : str
            name of the project, equals the name of folder so make sure
            it only contains characters supported by the OS for folders
        path : str, optional
            the path to the project, the full path will be path + name, defaults
            to the project path in the settings
        '''
        self.name = name
        self.groupname = f'Projekt "{self.name}"'
        path = path or settings.project_path
        self.path = os.path.join(path, name)

    @property
    def basedata(self):
        '''
        the base data (same for all projects)
        '''
        return ProjectManager().basedata

    @property
    def data(self):
        '''
        the project data
        '''
        return Geopackage(base_path=self.path, read_only=False)

    def remove(self):
        '''
        remove the project and its folder
        '''
        self.close()
        if os.path.exists(self.path):
            shutil.rmtree(self.path)

    def close(self):
        '''
        close the project
        '''
        # ToDo: is there anything to do on closing a project?
        pass

    def __repr__(self):
        return f'Project {self.name}'


class ProjectManager(metaclass=Singleton):
    '''
    singleton for accessing/changing projects and their data

    Attributes
    ----------
    projects : list
        available projects
    active_project: Project
        active project
    '''
    _projects = {}
    settings = settings
    _required_settings = ['BASEDATA_URL', 'EPSG']

    def __init__(self):
        # check settings
        missing = []
        for required in self._required_settings:
            if required not in self.settings:
                missing.append(required)
        if missing:
            raise Exception(f'{missing} have to be set')
        self.basedata = None
        self.basedata_version = None
        self._server_versions = None
        self.load()

    def load(self):
        '''
        load settings and list of projects
        '''
        if self.settings.project_path:
            project_path = self.settings.project_path
            if project_path and not os.path.exists(project_path):
                try:
                    os.makedirs(project_path)
                except:
                    pass
            if not os.path.exists(project_path):
                self.settings.project_path = project_path = ''
        self.reset_projects()

    def check_basedata(self, path: str = None) -> Tuple[int, str]:
        '''
        validate the local base data

        Parameters
        ----------
        path : str, optional
            base data path to check, defaults to the currently set path

        Returns
        ----------
        (int, str)
            status code and validation message
            codes:
            -1 - connection error
             0 - no local data
             1 - local data outdated
             2 - local data up to date
        '''
        # ToDo: check if all files are there
        if not self.server_versions:
            return -1, ('Der Server mit den Basisdaten ist nicht verfügbar.\n\n'
                        'Möglicherweise hat sich die URL des Servers geändert. '
                        'Bitte prüfen Sie, ob eine neue Projekt-Check-Version '
                        'im QGIS-Pluginmanager verfügbar ist.'
        #'Ist dies nicht der Fall, wenden Sie sich bitte an das ILS (oder so)'
                        )
        newest_server_v = self.server_versions[0]
        local_versions = self.local_versions(
            path or self.settings.basedata_path)
        if not local_versions:
            return 0, 'Es wurden keine lokalen Basisdaten gefunden'
        newest_local_v = local_versions[0]
        if newest_server_v['version'] > newest_local_v['version']:
            return 1, (f'Neue Basisdaten (v{newest_server_v["version"]} '
                       f'{newest_server_v["date"]}) '
                       f'sind verfügbar (lokal: v{newest_local_v["version"]} '
                       f'{newest_local_v["date"]})')
        return 2, ('Die Basisdaten sind auf dem neuesten Stand '
                   f'(v{newest_local_v["version"]} {newest_local_v["date"]})')

    def add_local_version(self, version_meta: dict, path: str = None):
        '''
        register a new local base data version, creates a
        folder path + version number

        Parameters
        ----------
        version_meta : dict
            metadata of version as dictionary as supplied by server,
            containing properties:
            version - number of version
            date - original date of creation of base data
            file - file name on server
        '''
        path = path or self.settings.basedata_path
        p = os.path.join(path, str(version_meta['version']))
        if not os.path.exists(p):
            os.makedirs(p)
        fp = os.path.join(p, 'basedata.json')
        with open(fp, 'w') as f:
            json.dump(version_meta, f, indent=4, separators=(',', ': '))

    def local_versions(self, path: str) -> List[dict]:
        '''
        get metadata of all local base data versions

        Returns
        -------
        list
            metadata of each found base data version as dictionaries,
            sorted by version number (newest first), containing properties:
            version - number of version
            date - original date of creation of base data
            file - file name on server
        '''
        if not os.path.exists(path):
            return
        versions = []
        subfolders = glob(f'{path}/*/')
        for folder in subfolders:
            fp = os.path.join(folder, 'basedata.json')
            if os.path.exists(fp):
                try:
                    with open(fp, 'r') as f:
                        v = json.load(f)
                    v['path'] = folder
                    versions.append(v)
                except:
                    pass
        return sorted(versions, key=itemgetter('version'), reverse=True)

    @property
    def server_versions(self) -> List[dict]:
        '''
        request server for available base data version

        Returns
        -------
        list
            metadata of each found base data version as dictionaries,
            sorted by version number (newest first), containing properties:
            version - number of version
            date - original date of creation of base data
            file - file name on server

        Raises
        -------
        ConnectionError
            can't establish connection to server or metadata file is not
            available
        '''
        if self._server_versions:
            return self._server_versions
        try:
            request = Request(synchronous=True)
            # metadata url
            res = request.get(f'{settings.BASEDATA_URL}/v_basedata.json')
        except ConnectionError:
            return
        if res.status_code != 200:
            return
        return sorted(res.json(), key=itemgetter('version'), reverse=True)

    def load_basedata(self, version: int = None) -> bool:
        '''
        set base data with version number active

        Parameters
        ----------
        version : int, optional
            number of version to load, defaults to newest available version
            (by number)

        Returns
        ----------
        bool
            whether loading was successful or not
        '''
        if version is not None and version == self.basedata_version:
            return True
        self.basedata = None
        base_path = self.settings.basedata_path
        local_versions = self.local_versions(base_path)
        if not local_versions:
            return False
        if not version:
            # take newest version available locally
            local_version = local_versions[0]
        else:
            lv = [v['version'] for v in local_versions]
            if version not in lv:
                return False
            local_version = local_versions[lv.index(version)]
        path = local_version['path']
        if not os.path.exists(path):
            return False
        self.basedata = Geopackage(base_path=path, read_only=True)
        self.basedata_version = local_version['version']
        return True

    def create_project(self, name: str, create_folder: bool = True):
        '''
        create a new project

        Parameters
        ----------
        name : str
            name of the project
        create_folder : bool, optional
            create a folder for the project data if True, defaults to creating
            a folder
        '''
        if not self.settings.project_path:
            return
        target_folder = os.path.join(self.settings.project_path, name)
        project = Project(name)
        self._projects[project.name] = project
        #shutil.copytree(os.path.join(settings.TEMPLATE_PATH, 'project'),
                        #target_folder)
        if create_folder and not os.path.exists(target_folder):
            os.mkdir(target_folder)
        return project

    def remove_project(self, project: Project):
        '''
        remove a project physically
        '''
        #self.active_project = None
        if isinstance(project, str):
            project = self._projects[project]
        project.remove()
        if project.name in self._projects:
            del(self._projects[project.name])

    def _get_projects(self) -> str:
        '''
        get list of project names in project path
        '''
        base_path = self.settings.project_path
        if not os.path.exists(base_path):
            return []
        project_folders = [f for f in os.listdir(base_path)
                           if os.path.isdir(os.path.join(base_path, f))]
        return sorted(project_folders)

    @property
    def projects(self) -> List[Project]:
        '''
        list of available projects
        '''
        return list(self._projects.values())

    def reset_projects(self):
        '''
        reloads the project list in currently set project folder
        '''
        self._projects = {}
        for name in self._get_projects():
            project = Project(name)
            self._projects[project.name] = project

    @property
    def active_project(self):
        '''
        active project, if not defined else, all read/write access of project
        data will be done in this project
        '''
        if self.settings.active_project:
            return self._projects.get(self.settings.active_project, None)
        return None

    @active_project.setter
    def active_project(self, project):
        if project and project.name not in self._projects:
            self._projects[project.name] = project
        self.settings.active_project = project.name if project else ''


class ProjectTable:
    '''
    manages project-related database tables (django-style),
    Tables defined this way will be automatically created with defined fields
    (defined by class attributes), ids are created automatically

    possible meta data (defined by Meta class):
        workspace - name of the workspace, defaults to 'default'
        name      - name of the table, defaults to class name in lower case
        database  - type of database, defaults to Geopackage
        geom      - geometry type (wkb geometry type string e.g. Polygon,
                    LineString), defaults to unspecified (decided when
                    saving geometries)

    e.g.

    class Example(ProjectTable):
        name = Field(str, 0)
        number = Field()

        class Meta:
            name = 'example name'
            workspace = 'examples'
            geom = 'Point'
    '''

    @classmethod
    def get_table(cls, project: Project = None, create: bool = False) -> Table:
        '''
        get a table defined in the ProjectTable style

        Parameters
        ----------
        project : Project, optional
            the project the table belongs to, defaults to the active project
        create : bool, optional
            create the table if not existing, defaults to not creating the table
            but raising an error if not found

        Returns
        ----------
        Table
            the table matching project and definition resp. the newly created
            table (create == True)

        Raises
        ----------
        FileNotFoundError
            table not found (create == False)
        '''
        project = project or ProjectManager().active_project
        Database = getattr(cls.Meta, 'database', Geopackage)
        workspace_name = getattr(cls.Meta, 'workspace', 'default')
        table_name = getattr(cls.Meta, 'name', cls.__name__.lower())
        geometry_type = getattr(cls.Meta, 'geom', None)
        database = Database(project.path, read_only=False)
        workspace = database.get_or_create_workspace(workspace_name)
        try:
            fields, defaults = cls._fields()
            table = workspace.get_table(table_name, field_names=fields.keys())
            table_fields = [f.name for f in table.fields()]
            for field_name, typ in fields.items():
                if field_name not in table_fields:
                    table.add_field(Field(typ, name=field_name,
                                          default=defaults.get(field_name)))
        except FileNotFoundError as e:
            if not create:
                raise e
            table = cls._create(table_name, workspace,
                                geometry_type=geometry_type)
        return table

    @staticmethod
    def _where(kwargs):
        pass

    @classmethod
    def features(cls, project: Project = None, create: bool = False
                 ) -> FeatureCollection:
        '''
        get rows of the table as feature collection

        Parameters
        ----------
        project : Project, optional
            the project the table belongs to, defaults to active project
        create : bool, optional
            create the table if not existing, defaults to not creating the table
        '''
        return cls.get_table(project=project, create=create).features()

    @classmethod
    def _fields(cls) -> Tuple[dict, dict]:
        '''
        datatypes and default values of fields
        '''
        cls.extra()
        types = OrderedDict()
        defaults = OrderedDict()
        for k, v in cls.__dict__.items():
            if not isinstance(v, Field):
                continue
            name = k if not v.name else v.name
            if name == 'id':
                raise ValueError("keyword 'id' is reserved and can't be "
                                 "used as a field name")
            types[k] = v.datatype
            defaults[k] = v.default
        return types, defaults

    @classmethod
    def _create(cls, name: str, workspace: Workspace,
                geometry_type: str = None):
        '''
        create a table with field defined by class attributes
        '''
        types, defaults = cls._fields()
        return workspace.create_table(name, fields=types,
                                      defaults=defaults,
                                      geometry_type=geometry_type,
                                      epsg=settings.EPSG)

    @classmethod
    def extra(cls):
        '''
        override to add extra fields on runtime
        '''
        pass

    class Meta:
        '''
        metadata of table

        workspace - name of the workspace, defaults to 'default'
        name      - name of the table, defaults to class name in lower case
        database  - type of database, defaults to Geopackage
        geom      - geometry type (wkb geometry type string e.g. Polygon,
                    LineString), defaults to unspecified (decided when
                    saving geometries)
        '''


class ProjectLayer(Layer):
    def __init__(self, layername, data_path, groupname='', project=None,
                 prepend=True):
        self.project = project or ProjectManager().active_project
        groupname = f'{self.project.groupname}/{groupname}' if groupname \
            else self.project.groupname
        super().__init__(layername, data_path, prepend=prepend,
                         groupname=groupname)
        self.parent.setItemVisibilityChecked(True)

    @classmethod
    def find_group(cls, groupname):
        project = ProjectManager().active_project
        if not project:
            return
        groupname = f'{project.groupname}/{groupname}' if groupname \
            else project.groupname if project else None
        return super().find_group(groupname)

    @classmethod
    def add_group(cls, groupname, project=None, prepend=True):
        project = project or ProjectManager().active_project
        groupname = f'{project.groupname}/{groupname}'
        return Layer.add_group(groupname, prepend=prepend)

    def draw(self, style_file=None, label='', checked=True, filter=None,
             read_only=True, redraw=True, prepend=False, expanded=True,
             uncheck_siblings=False):
        style_path = os.path.join(settings.TEMPLATE_PATH, 'styles', style_file)\
            if style_file else None
        layer = super().draw(style_path=style_path, label=label,
                             checked=checked, filter=filter, redraw=redraw,
                             prepend=prepend, expanded=expanded,
                             uncheck_siblings=uncheck_siblings)
        layer.setReadOnly(read_only)
        return layer

    @classmethod
    def from_table(cls, table, groupname='', prepend=True):
        data_path = f'{table.workspace.path}|layername={table.name}'
        return ProjectLayer(table.name, data_path=data_path,
                            groupname=groupname, prepend=prepend)


class OSMBackgroundLayer(TileLayer):

    def __init__(self, groupname='', prepend=False):

        url = ('type=xyz&url=https://a.tile.openstreetmap.org//{z}/{x}/{y}.png'
               f'&crs=EPSG{settings.EPSG}')
        super().__init__(url, groupname=groupname, prepend=prepend)

    def draw(self, checked=True):
        super().draw('OpenStreetMap', checked=checked)


class TerrestrisBackgroundLayer(TileLayer):

    def __init__(self, groupname='', prepend=False):

        url = (f'crs=EPSG:{settings.EPSG}&dpiMode=7&format=image/png'
               '&layers=OSM-WMS&styles=&url=http://ows.terrestris.de/osm-gray/'
               'service')
        super().__init__(url, groupname=groupname, prepend=prepend)

    def draw(self, checked=True):
        super().draw('Terrestris', checked=checked, expanded=False)
