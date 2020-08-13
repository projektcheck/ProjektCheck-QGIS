# -*- coding: utf-8 -*-
'''
***************************************************************************
    otp_router.py
    ---------------------
    Date                 : December 2019
    Copyright            : (C) 2019 by Christoph Franke, Max Bohnet
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

routing from and to project areas, calculation of traffic load
'''

__author__ = 'Christoph Franke'
__date__ = '12/12/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import os
from qgis.core import QgsPoint
from qgis.core import (QgsGeometry, QgsPoint, QgsProject,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform)
import numpy as np

from projektcheck.utils.spatial import Point
from projektcheck.domains.traffic.otp_router import OTPRouter
from projektcheck.base.domain import Worker
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.traffic.tables import (
    Connectors, RouteLinks, Ways, Itineraries, TransferNodes, TrafficLoadLinks)

from projektcheck.settings import settings


class TransferNodeCalculation(Worker):
    '''
    The transfer nodes are calculated by merging the shortest paths to points
    placed on two circles around the inner circle.
    '''
    # radius of outer circle (additional to inner circle)
    outer_circle = 2000
    # number of destination points on outer and middle ring to route to
    n_segments = 24

    def __init__(self, project, distance=1000, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project the areas and their connectors are in
        distance : int, optional
            the radius in meters of the inner ring the transfer nodes are
            located in, defaults to 1000 m
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.otp_pickle_file = os.path.join(project.path, 'otpgraph.pickle')
        self.project = project
        self.distance = distance
        self.areas = Teilflaechen.features(project=project)
        self.connectors = Connectors.features(project=project)
        self.itineraries = Itineraries.features(project=project, create=True)
        self.transfer_nodes = TransferNodes.features(project=project,
                                                     create=True)

    def work(self):
        self.calculate_transfer_nodes()

    def calculate_transfer_nodes(self):
        '''
        calculate the position and weights of the initial transfer nodes
        '''
        # tbx settings
        inner_circle = self.distance
        mid_circle = inner_circle + 500
        outer_circle = inner_circle + self.outer_circle

        # calculate routes
        project_epsg = settings.EPSG
        otp_router = OTPRouter(distance=inner_circle, epsg=project_epsg)

        self.itineraries.delete()

        for i, area in enumerate(self.areas):
            self.log(f'Suche Routen ausgehend von Teilfläche {area.name}...')
            connector = self.connectors.get(id_teilflaeche=area.id)
            qpoint = connector.geom.asPoint()
            source = Point(id=area.id, x=qpoint.x(), y=qpoint.y(),
                           epsg=project_epsg)

            # calculate segments around centroid
            inner_dest = otp_router.create_circle(
                source, dist=mid_circle, n_segments=self.n_segments)
            outer_dest = otp_router.create_circle(
                source, dist=outer_circle, n_segments=self.n_segments)
            destinations = np.concatenate([inner_dest, outer_dest])
            source.transform(otp_router.router_epsg)

            # calculate the routes to the segments
            for (x, y) in destinations:
                destination = Point(x, y, epsg=project_epsg)
                destination.transform(otp_router.router_epsg)
                otp_router.route(source, destination)
            self.set_progress(80 * (i + 1) / len(self.areas))

        otp_router.build_graph(distance=inner_circle)
        otp_router.remove_redundancies()

        self.log('Berechne Herkunfts- und Zielpunkte aus den Routen...')
        otp_router.transfer_nodes.calc_initial_weight()

        transfer_nodes_df = otp_router.get_transfer_node_features()
        self.transfer_nodes.delete()
        transfer_nodes_df['fid'] = range(1, len(transfer_nodes_df) + 1)
        self.transfer_nodes.update_pandas(transfer_nodes_df)

        for transfer_node in otp_router.transfer_nodes.values():
            tn_idx = transfer_nodes_df['node_id'] == transfer_node.node_id
            tn_id = transfer_nodes_df[tn_idx]['fid'].values[0]
            for route in transfer_node.routes.values():
                points = [QgsPoint(node.x, node.y) for node in route.nodes]
                polyline = QgsGeometry.fromPolyline(points)
                self.itineraries.add(geom=polyline, route_id=route.route_id,
                                     transfer_node_id=tn_id)


class Routing(Worker):
    '''
    Distribution of the additional traffic produced by the project areas between
    the shortest paths from and to transfer nodes located on an inner circle
    around the traffic connectors.
    '''

    def __init__(self, project, recalculate=False, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project the areas and their connectors are in
        recalculate : bool, optional
            recalculate the shortest paths, defaults to only
            distributing the traffic on the already calculated routes
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.project = project
        self.areas = Teilflaechen.features(project=project)
        self.connectors = Connectors.features(project=project)
        self.itineraries = Itineraries.features(project=project, create=True)
        self.links = RouteLinks.features(project=project, create=True)
        self.traffic_load = TrafficLoadLinks.features(project=project,
                                                      create=True)
        self.transfer_nodes = TransferNodes.features(project=project)
        self.ways = Ways.features(project=project, create=True)
        self._recalculate = recalculate

    def work(self):
        if not self._recalculate:
            self.calculate_ways()
            self.route_transfer_nodes()
            self.calculate_traffic_load()
        else:
            self.calculate_traffic_load()

    def calculate_ways(self):
        '''
        calculate and store the additional ways per type of use of the areas
        '''
        # get ways per type of use
        ways_tou = {}
        self.ways.delete()
        self.log('Prüfe Wege...')
        for area in self.areas:
            if area.nutzungsart == 0:
                continue
            entry = ways_tou.get(area.nutzungsart)
            if not entry:
                entry = ways_tou[area.nutzungsart] = [0, 0]
            entry[0] += area.wege_gesamt
            entry[1] += area.wege_miv
        for tou, (wege_gesamt, wege_miv) in ways_tou.items():
            if wege_gesamt == 0:
                continue
            miv_anteil = round(100 * wege_miv / wege_gesamt) # \
                # if wege_gesamt > 0 else 0
            self.ways.add(wege_gesamt=wege_gesamt, nutzungsart=tou,
                          miv_anteil=miv_anteil)

    def route_transfer_nodes(self):
        '''
        routing between transfer nodes and area connectors
        '''
        self.links.delete()
        project_epsg = settings.EPSG
        #route_ids = {}
        otp_router = OTPRouter(epsg=project_epsg)
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(OTPRouter.router_epsg),
            QgsCoordinateReferenceSystem(project_epsg),
            QgsProject.instance()
        )
        for i, area in enumerate(self.areas):
            self.log(f'Suche Routen zwischen Teilfläche {area.name} und den '
                     'Herkunfts- und Zielpunkten...')
            connector = self.connectors.get(id_teilflaeche=area.id)
            qpoint = connector.geom.asPoint()
            pcon = Point(id=area.id, x=qpoint.x(), y=qpoint.y(),
                         epsg=project_epsg)
            pcon.transform(OTPRouter.router_epsg)
            for transfer_node in self.transfer_nodes:
                qpoint = transfer_node.geom.asPoint()
                pnode = Point(id=transfer_node.id, x=qpoint.x(), y=qpoint.y(),
                              epsg=project_epsg)
                pnode.transform(otp_router.router_epsg)
                out_route = otp_router.route(pcon, pnode)
                in_route = otp_router.route(pnode, pcon)
                for route in out_route, in_route:
                    if not route:
                        continue
                    for link in route.links:
                        geom = QgsGeometry()
                        from_id = link.from_node.node_id
                        to_id = link.to_node.node_id
                        lg = link.get_geom()
                        if from_id == to_id or not lg:
                            continue
                        geom.fromWkb(lg.ExportToWkb())
                        geom.transform(transform)
                        self.links.add(from_node_id=from_id, to_node_id=to_id,
                                       transfer_node_id=transfer_node.id,
                                       area_id=area.id, geom=geom)
            self.set_progress(80 * (i + 1) / len(self.areas))

    def calculate_traffic_load(self):
        '''
        distribute the traffic to the shortest paths
        '''
        self.traffic_load.delete()

        self.log('Verteile das Verkehrsaufkommen...')

        df_links = self.links.to_pandas()
        df_links['wege_miv'] = 0

        for way in self.ways:
            nutzungsart = way.nutzungsart
            miv_gesamt_new = way.miv_anteil * way.wege_gesamt / 100
            areas_tou = self.areas.filter(nutzungsart=nutzungsart)
            miv_gesamt_old = sum(area.wege_miv for area in areas_tou)
            if miv_gesamt_old == 0:
                continue
            for area in areas_tou:
                idx = df_links['area_id'] == area.id
                df_links.loc[idx, 'wege_miv'] = (miv_gesamt_new * area.wege_miv
                                                 / miv_gesamt_old)
        self.areas.filter()

        df_transfer = self.transfer_nodes.to_pandas(columns=['fid', 'weight'])
        df_weighted = df_links.merge(
            df_transfer, how='left', left_on='transfer_node_id', right_on='fid')
        # ways include back and forth
        df_weighted['wege_miv'] /= 2
        df_weighted['weight'] /= 100
        df_weighted['trips'] = df_weighted['wege_miv'] * df_weighted['weight']
        # linked nodes without direction
        df_weighted['dirless'] = ['{}-{}'.format(*sorted(t))
                                  for t in zip(df_weighted['from_node_id'],
                                               df_weighted['to_node_id'])]
        df_grouped = df_weighted.groupby('dirless')
        for i, group in df_grouped:
            self.traffic_load.add(trips=group['trips'].sum(),
                                  geom=group['geom'].values[0])
