import os

from projektcheck.utils.spatial import Point
from projektcheck.domains.traffic.otp_router import OTPRouter
from projektcheck.base.domain import Worker
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.traffic.tables import (Connectors, Links, Nodes,
                                                 TransferNodes, Ways)
import pandas as pd

from settings import settings


class Routing(Worker):
    outer_circle = 2000
    n_segments = 24

    def __init__(self, project, distance=1000, recalculate=False, parent=None):
        super().__init__(parent=parent)
        self.otp_pickle_file = os.path.join(project.path, 'otpgraph.pickle')
        self.project = project
        self.distance = distance
        self.areas = Teilflaechen.features(project=project)
        self.connectors = Connectors.features(project=project)
        self.links = Links.features(project=project, create=True)
        self.ways = Ways.features(project=project, create=True)
        self.nodes = Nodes.features(project=project, create=True)
        self.transfer_nodes = TransferNodes.features(project=project,
                                                     create=True)
        self._recalculate = recalculate

    def work(self):
        if not self._recalculate:
            self.initial_calculation()
        else:
            self.recalculate()

    def initial_calculation(self):
        # tbx settings
        inner_circle = self.distance
        outer_circle = inner_circle + self.outer_circle

        # calculate routes
        project_epsg = settings.EPSG
        otp_router = OTPRouter(distance=inner_circle, epsg=project_epsg)
        r_id = 0

        # get ways per type of use
        ways_tou = {}
        self.ways.delete()
        for area in self.areas:
            if area.nutzungsart == 0:
                continue
            entry = ways_tou.get('area.nutzungsart')
            if not entry:
                entry = ways_tou[area.nutzungsart] = [0, 0]
            entry[0] += area.wege_gesamt
            entry[1] += area.wege_miv
        for tou, (wege_gesamt, wege_miv) in ways_tou.items():
            miv_anteil = round(100 * wege_miv / wege_gesamt) \
                if wege_gesamt > 0 else 0
            self.ways.add(wege_gesamt=wege_gesamt, nutzungsart=tou,
                          miv_anteil=miv_anteil)

        for i, area in enumerate(self.areas):
            self.log(f"Suche Routen ausgehend von Teilfläche {area.name}...")
            #if area.wege_miv == 0:
                #self.log('...wird übersprungen, da keine Wege im '
                         #'MIV zurückgelegt werden')
                #continue
            connector = self.connectors.get(id_teilflaeche=area.id)
            qpoint = connector.geom.asPoint()
            otp_router.areas.add_area(area.id, trips=area.wege_miv)
            source = Point(x=qpoint.x(), y=qpoint.y(), epsg=project_epsg)

            # calculate segments around centroid
            destinations = otp_router.create_circle(source, dist=outer_circle,
                                           n_segments=self.n_segments)
            source.transform(otp_router.router_epsg)
            # calculate the routes to the segments
            for (x, y) in destinations:
                destination = Point(x, y, epsg=project_epsg)
                destination.transform(otp_router.router_epsg)
                json = otp_router.get_routing_request(source, destination)
                otp_router.decode_coords(json, route_id=r_id, source_id=area.id)
                r_id += 1
            self.set_progress(60 * (i + 1) / len(self.areas))

        otp_router.nodes.transform()
        self.log("berechne Zielknoten...")
        self.set_progress(60)
        otp_router.nodes_to_graph(meters=inner_circle)
        otp_router.transfer_nodes.calc_initial_weight()
        self.log("berechne Gewichte...")
        self.set_progress(70)
        otp_router.calc_vertex_weights()
        self.log("schreibe Ergebnisse...")
        links_df = otp_router.get_polyline_features()
        self.links.delete()
        self.links.update_pandas(links_df)
        nodes_df = otp_router.get_node_features()
        self.nodes.delete()
        self.nodes.update_pandas(nodes_df)
        transfer_nodes_df = otp_router.get_transfer_node_features()
        self.transfer_nodes.delete()
        self.transfer_nodes.update_pandas(transfer_nodes_df)
        otp_router.dump(self.otp_pickle_file)

    def recalculate(self):
        otp_router = OTPRouter.from_dump(self.otp_pickle_file)

        o_trans_nodes = otp_router.transfer_nodes
        for transfer_node in self.transfer_nodes:
            o_trans_nodes[transfer_node.node_id] = transfer_node.weight

        self.log("berechne Neugewichtung...")
        self.set_progress(70)
        o_trans_nodes.assign_weights_to_routes()
        otp_router.calc_vertex_weights()
        self.log("schreibe Ergebnisse...")
        links_df = otp_router.get_polyline_features()
        self.links.delete()
        self.links.update_pandas(links_df)
        otp_router.nodes_have_been_weighted = True
        self._extent = otp_router.extent
        otp_router.dump(self.otp_pickle_file)

