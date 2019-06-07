from pctools.utils.singleton import Singleton
from pctools.config import Config


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
    def __init__(self):
        self.load()

    def load(self):
        self.config = Config()
        # ToDo: load projects from disk
        for name in ['test1', 'test2', 'test3']:
            project = Project(name)
            self._projects[project.name] = project

    @property
    def projects(self):
        return self._projects.values()

    @property
    def active_project(self):
        if self.config.active_project:
            return self._projects[self.config.active_project]
        return None

    @active_project.setter
    def active_project(self, project):
        self.config.active_project = project.name




