# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# REGIOPROJEKTCHECK
# project_lib.py
#
# Description:
# PROJECT URL: http://www.regioprojektcheck.de
#
# Author:
# ILS gGmbH / HCU Hamburg / GGR Planung
#
# LICENSE: The MIT License (MIT) Copyright (c) 2014 RPC Consortium
# ---------------------------------------------------------------------------
from os import listdir
import sys
from os.path import join, isdir, abspath, dirname, basename, exists
from os import mkdir, getenv
import json
from pctools.utils.singleton import Singleton

#BASE_PATH = os

DEFAULT_SETTINGS = {
    'active_project': u'',
    'epsg': 31467,
    'transformation': "DHDN_To_WGS_1984_5x",
    'max_area_distance': 1000,
    'google_api_key': ' AIzaSyDL32xzaNsQmB_fZGU9SF_FtnvJ4ZrwP8g',
    'project_folder': u''
}


class Config:
    __metaclass__ = Singleton
    _config = {}

    # write changed config instantly to file
    _write_instantly = True

    def __init__(self, filename='qgis-projektcheck-config.txt'):

        self.config_file = join(self.APPDATA_PATH, filename)
        self._callbacks = {}
        self.active_coord = (0, 0)
        if exists(self.config_file):
            self.read()
            # add missing Parameters
            changed = False
            for k, v in DEFAULT_SETTINGS.items():
                if k not in self._config:
                    self._config[k] = v
                    changed = True
            if changed:
                self.write()

        # write default config, if file doesn't exist yet
        else:
            self._config = DEFAULT_SETTINGS.copy()
            self.write()

    @property
    def APPDATA_PATH(self):
        path = join(getenv('LOCALAPPDATA'), 'Projekt-Check')
        if not exists(path):
            mkdir(path)
        return path

    def read(self, config_file=None):
        if config_file is None:
            config_file = self.config_file
        try:
            with open(config_file, 'r') as f:
                self._config = json.load(f)
        except:
            self._config = DEFAULT_SETTINGS.copy()
            print('Error while loading config. Using default values.')

    def write(self, config_file=None):
        if config_file is None:
            config_file = self.config_file

        with open(config_file, 'w') as f:
            config_copy = self._config.copy()
            # pretty print to file
            json.dump(config_copy, f, indent=4, separators=(',', ': '))

    # access stored config entries like fields
    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self._config:
            return self._config[name]
        raise AttributeError

    def __setattr__(self, name, value):
        if name in self._config:
            self._config[name] = value
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
        return repr(self._config)

    def on_change(self, attribute, callback):
        if attribute not in self._callbacks:
            self._callbacks[attribute] = []
        self._callbacks[attribute].append(callback)

    def remove_listeners(self, attribute):
        if attribute in self._callbacks:
            self._callbacks.pop(attribute)
