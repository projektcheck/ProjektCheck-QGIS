import os
import sys
import json
import shutil

from pctools.utils.singleton import Singleton
from pctools.backend import Geopackage

APPDATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'Projekt-Check-QGIS')

DEFAULT_SETTINGS = {
    'active_project': u'',
    'project_path': os.path.join(APPDATA_PATH, 'Projekte')
}


class Settings:
    __metaclass__ = Singleton
    _settings = {}
    # write changed config instantly to file
    _write_instantly = True

    def __init__(self, filename='projektcheck-config.txt'):

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
        if config_file is None:
            config_file = self.config_file
        try:
            with open(config_file, 'r') as f:
                self._settings = json.load(f)
        except:
            self._settings = DEFAULT_SETTINGS.copy()
            print('Error while loading config. Using default values.')

    def write(self, config_file=None):
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

    def __init__(self, name):
        self.name = name

    @property
    def areas(self):
        # ToDo: from disk
        return [u'fläche1', u'fläche2', u'fläche3']

    def close(self):
        pass

    def __str__(self):
        return f'Project {self.name}'


class ProjectManager:
    __metaclass__ = Singleton
    _projects = {}
    settings = settings
    _required_settings = ['BASE_PATH', 'BASEDATA_PATH', 'TEMPLATE_PATH']

    def __init__(self):

        # check settings
        missing = []
        for required in self._required_settings:
            if required not in self.settings:
                missing.append(required)
        if missing:
            raise Exception(f'{missing} have to be set')

        self.basedata = Geopackage(base_path=settings.BASEDATA_PATH, read_only=True)
        self.projectdata = Geopackage()
        self.load()

    def load(self):

        if settings.project_path:
            self.projectdata.base_path = settings.project_path
        for name in self._get_projects():
            project = Project(name)
            self._projects[project.name] = project

    def create_project(self, name):
        target_folder = os.path.join(settings.project_path, name)
        shutil.copytree(settings.TEMPLATE_PATH, 'project', target_folder)
        project = Project(name)
        self._projects[project.name] = project
        return project

    def _get_projects(self):
        '''
        returns all available projects inside the project folder
        '''
        base_path = settings.project_path
        if not os.path.exists(base_path):
            return []
        project_folders = [f for f in os.listdir(base_path)
                           if os.path.isdir(os.path.join(base_path, f))]
        return sorted(project_folders)

    @property
    def projects(self):
        return self._projects.values()

    @property
    def active_project(self):
        if self.settings.active_project:
            return self._projects.get(self.settings.active_project, None)
        return None

    @active_project.setter
    def active_project(self, project):
        self.settings.active_project = project.name






