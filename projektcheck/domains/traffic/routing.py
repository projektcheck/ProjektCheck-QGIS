import os

from projektcheck.utils.spatial import Point
from projektcheck.domains.traffic.otp_router import OTPRouter
from projektcheck.base.domain import Worker
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.traffic.tables import (Connectors, Links, Nodes,
                                                 TransferNodes)
import pandas as pd

from settings import settings


class Routing(Worker):
    outer_circle = 2000
    n_segments = 24

    def __init__(self, project, distance=1000, parent=None):
        super().__init__(parent=parent)
        self.project = project
        self.distance = distance
        self.areas = Teilflaechen.features(project=project)
        self.connectors = Connectors.features(project=project)
        self.links = Links.features(project=project, create=True)
        self.nodes = Nodes.features(project=project, create=True)
        self.transfer_nodes = TransferNodes.features(project=project, create=True)

    #def add_outputs(self):
        ## Add Layers
        #self.output.add_layer('verkehr', 'Anbindungspunkte',
                              #featureclass='Anbindungspunkte',
                              #template_folder='Verkehr', zoom=False)
        #self.output.add_layer('verkehr', 'links',
                              #featureclass='links',
                              #template_folder='Verkehr',
                              #name='Zusätzliche PKW-Fahrten', zoom=False,
                              #symbology_classes=(15, 'weight'))
        #self.output.add_layer('verkehr', 'Zielpunkte',
                              #featureclass='Zielpunkte',
                              #template_folder='Verkehr',
                              #name='Herkunfts-/Zielpunkte',
                              #zoom=True, zoom_extent=self._extent)

    def work(self):
        self.initial_calculation()

    def initial_calculation(self):
        # tbx settings
        inner_circle = self.distance
        outer_circle = inner_circle + self.outer_circle

        # calculate routes
        project_epsg = settings.EPSG
        o = OTPRouter(distance=inner_circle, epsg=project_epsg)
        r_id = 0
        for area in self.areas:
            self.log(f"Suche Routen ausgehend von Teilfläche {area.name}...")
            if area.wege_miv == 0:
                self.log('...wird übersprungen, da keine Wege im '
                         'MIV zurückgelegt werden')
                continue
            connector = self.connectors.get(id_teilflaeche=area.id)
            qpoint = connector.geom.asPoint()
            o.areas.add_area(area.id, trips=area.wege_miv)
            source = Point(x=qpoint.x(), y=qpoint.y(), epsg=project_epsg)

            # calculate segments around centroid
            destinations = o.create_circle(source, dist=outer_circle,
                                           n_segments=self.n_segments)
            source.transform(o.router_epsg)
            # calculate the routes to the segments
            for (x, y) in destinations:
                destination = Point(x, y, epsg=project_epsg)
                destination.transform(o.router_epsg)
                json = o.get_routing_request(source, destination)
                o.decode_coords(json, route_id=r_id, source_id=area.id)
                r_id += 1

        o.nodes.transform()
        o.nodes_to_graph(meters=inner_circle)
        self.log("berechne Zielknoten...")
        o.transfer_nodes.calc_initial_weight()
        self.log("berechne Gewichte...")
        o.calc_vertex_weights()
        self.log("schreibe Ergebnisse...")
        links_df = o.get_polyline_features()
        self.links.delete()
        self.links.update_pandas(links_df)
        nodes_df = o.get_node_features()
        self.nodes.delete()
        self.nodes.update_pandas(nodes_df)
        transfer_nodes_df = o.get_transfer_node_features()
        self.transfer_nodes.delete()
        self.transfer_nodes.update_pandas(transfer_nodes_df)
        #o.dump(self.folders.get_otp_pickle_filename(check=False))

