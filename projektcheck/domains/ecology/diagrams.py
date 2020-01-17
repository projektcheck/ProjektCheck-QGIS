# -*- coding: utf-8 -*-
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.ticker as mticker
import pandas as pd
import matplotlib.pyplot as plt

from projektcheck.base.diagrams import MatplotDiagram
from settings import settings


class Leistungskennwerte(MatplotDiagram):
    def create(self, **kwargs):
        pass


class LeistungskennwerteDelta(MatplotDiagram):
    def create(self, **kwargs):
        pass
