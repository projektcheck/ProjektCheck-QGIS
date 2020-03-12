import os
import sys
import json
import shutil
import sys
from collections import OrderedDict

from projektchecktools.utils.singleton import Singleton
from projektchecktools.base.database import Field
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
    'check_data_on_start': True
}


class Settings:
    '''
    singleton for accessing and storing global settings in files

    Attributes
    ----------
    active_project : str
        the name of the active project
    project_path : str
        path to project folders
    '''
    __metaclass__ = Singleton
    _settings = {}
    # write changed config instantly to file
    _write_instantly = True

    def __init__(self, filename='projektcheck-config.txt'):
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

    def read(self, config_file=None):
        '''
        read settings from file

        Parameters
        ----------
        config_file : str, optional
            path to file with settings, self.config_file used if None,
            by default None
        '''
        if config_file is None:
            config_file = self.config_file
        try:
            with open(config_file, 'r') as f:
                self._settings = json.load(f)
        except:
            self._settings = DEFAULT_SETTINGS.copy()
            print('Error while loading config. Using default values.')

    def write(self, config_file=None):
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
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self._settings:
            return self._settings[name]
        raise AttributeError

    def __setattr__(self, name, value):
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

    def __contains__(self, item):
        return item in self.__dict__ or item in self._settings

    def on_change(self, attribute, callback):
        if attribute not in self._callbacks:
            self._callbacks[attribute] = []
        self._callbacks[attribute].append(callback)

    def remove_listeners(self, attribute):
        if attribute in self._callbacks:
            self._callbacks.pop(attribute)

settings = Settings()


class Project:
    '''
    single project
    '''
    settings = settings

    def __init__(self, name, path=''):
        self.name = name
        self.groupname = f'Projekt "{self.name}"'
        path = path or settings.project_path
        self.path = os.path.join(path, name)

    @property
    def basedata(self):
        return ProjectManager().basedata

    def remove(self):
        self.close()
        if os.path.exists(self.path):
            shutil.rmtree(self.path)

    def close(self):
        pass

    def __repr__(self):
        return f'Project {self.name}'


class ProjectManager:
    '''
    singleton for accessing/changing projects and their data

    Attributes
    ----------
    projects : list
        available projects
    active_project: Project
        active project
    '''
    __metaclass__ = Singleton
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
        self.load()

    def load(self):
        '''
        load settings and projects
        '''
        success = self.load_basedata()
        if not success:
            raise FileNotFoundError('basedata not found')
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

    def check_basedata(self, path=None):
        # ToDo: check if all files are there
        version_server = self.server_version()
        current_v = self.local_version(path or self.settings.basedata_path)
        if not current_v:
            return 0, 'Es wurden keine lokalen Basisdaten gefunden'
        if current_v['version'] < version_server['version']:
            return 1, (f'Neue Basisdaten (Stand: {version_server["date"]}) '
                       f'sind verfügbar (lokaler Stand: {current_v["date"]})')
        return 2, ('Die Basisdaten sind auf dem neuesten Stand '
                   f'({current_v["date"]})')

    def set_local_version(self, version, path=None):
        path = path or self.settings.basedata_path
        if not os.path.exists(path):
            os.makedirs(path)
        fp = os.path.join(path, 'basedata.json')
        with open(fp, 'w') as f:
            json.dump(version, f, indent=4, separators=(',', ': '))

    def local_version(self, path):
        if not os.path.exists(path):
            return
        fp = os.path.join(path, 'basedata.json')
        if not os.path.exists(fp):
            return
        try:
            with open(fp, 'r') as f:
                ret = json.load(f)
        except:
            return None
        return ret

    def server_version(self):
        request = Request(synchronous=True)
        try:
            res = request.get(f'{settings.BASEDATA_URL}/basedata.json')
        except ConnectionError:
            # ToDo: handle error
            return
        if res.status_code != 200:
            return
        return res.json()

    @property
    def _v_basedata(self):
        # return date and version from file
        return self._local_version(self.settings.basedata_path)

    @_v_basedata.setter
    def _v_basedata(self, attr):
        # ToDo: set version in file
        pass

    def load_basedata(self):
        self.basedata = None
        base_path = self.settings.basedata_path
        if not os.path.exists:
            return False
        self.basedata = Geopackage(
            base_path=base_path,
            read_only=True)
        # ToDo: remove basedata from settings (still there out of convenience)
        self.settings.BASEDATA = self.basedata
        return True

    def create_project(self, name, create_folder=True):
        '''
        create a new project

        Parameters
        ----------
        name : str
            name of the project
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

    def remove_project(self, project):
        #self.active_project = None
        if isinstance(project, str):
            project = self._projects[project]
        project.remove()
        if project.name in self._projects:
            del(self._projects[project.name])

    def _get_projects(self):
        base_path = self.settings.project_path
        if not os.path.exists(base_path):
            return []
        project_folders = [f for f in os.listdir(base_path)
                           if os.path.isdir(os.path.join(base_path, f))]
        return sorted(project_folders)

    @property
    def projects(self):
        return list(self._projects.values())

    def reset_projects(self):
        self._projects = {}
        for name in self._get_projects():
            project = Project(name)
            self._projects[project.name] = project

    @property
    def active_project(self):
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
    manages project related database tables

    auto created
    define fields
    define Meta
    '''

    @classmethod
    def get_table(cls, project=None, create=False):
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
    def features(cls, project=None, create=False):
        return cls.get_table(project=project, create=create).features()

    @classmethod
    def _fields(cls):
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
    def _create(cls, name, workspace, geometry_type=None):
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
        workspace - name of workspace
        name - name of table
        database - type of database, by default Geopackage
        geom - type of geometry (Polygon, LineString)
        '''


class ProjectLayer(Layer):
    def __init__(self, layername, data_path, groupname='', project=None,
                 prepend=True):
        self.project = project or ProjectManager().active_project
        groupname = f'{self.project.groupname}/{groupname}' if groupname \
            else self.project.groupname
        super().__init__(layername, data_path, prepend=prepend,
                         groupname=groupname)
        self.root.setItemVisibilityChecked(True)

    @classmethod
    def find(cls, label, groupname='', project=None):
        project = project or ProjectManager().active_project
        groupname = f'{project.groupname}/{groupname}' if groupname \
            else project.groupname if project else None
        return Layer.find(label, groupname=groupname)

    @classmethod
    def add_group(cls, groupname, project=None, prepend=True):
        project = project or ProjectManager().active_project
        groupname = f'{project.groupname}/{groupname}'
        return Layer.add_group(groupname, prepend=prepend)

    def draw(self, style_file=None, label='', checked=True, filter=None,
             read_only=True, redraw=True, prepend=False, expanded=True):
        style_path = os.path.join(settings.TEMPLATE_PATH, 'styles', style_file)\
            if style_file else None
        layer = super().draw(style_path=style_path, label=label,
                             checked=checked, filter=filter, redraw=redraw,
                             prepend=prepend, expanded=expanded)
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
