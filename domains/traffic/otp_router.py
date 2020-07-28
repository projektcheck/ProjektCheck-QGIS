# -*- coding: utf-8 -*-
from osgeo import ogr
from collections import OrderedDict
from scipy.sparse import csc_matrix
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsPoint,
                       QgsCoordinateTransform)
from scipy.sparse.csgraph import dijkstra
import numpy as np
import pandas as pd

from projektcheck.utils.polyline import PolylineCodec
from projektcheck.utils.spatial import Point
from projektcheck.utils.connection import Request
from projektcheck.settings import settings

requests = Request(synchronous=True)


class Route(object):
    """Route to a destination"""

    def __init__(self, route_id, source_id, nodes=[]):
        """
        Parameters
        ----------
        route_id : int
        """
        self.route_id = route_id
        self.source_id = source_id
        self.nodes = nodes
        self.weight = 0

    @property
    def source_node(self):
        if not len(self.nodes):
            return None
        return self.nodes[0]

    @property
    def destination_node(self):
        if not len(self.nodes):
            return None
        return self.nodes[-1]

    @property
    def node_ids(self):
        return [node.node_id for node in self.nodes]

    @property
    def links(self):
        links = []
        for i in range(len(self.nodes)):
            if i < len(self.nodes) - 1:
                link = Link(self.nodes[i], self.nodes[i+1], i)
                links.append(link)
        return links

class Routes(OrderedDict):
    """Routes-object"""

    def get_route(self, source, destination):
        """
        get route between given nodes

        Parameters
        ----------
        source : Node

        destination : Node

        Returns
        -------
        route
        """
        for route in self.values():
            if (source.node_id == route.nodes[0].node_id and
                destination.node_id == route.nodes[-1].node_id):
                return route
        return None

    def add_route(self, route_id, source_id, nodes=[]):
        """
        add  route with given route_id

        Parameters
        ----------
        route_id : int

        source_id : int

        Returns
        -------
        route
        """
        route = self.get(route_id)
        if route is None:
            route = Route(route_id, source_id, nodes)
            self[route_id] = route
        return route

    @property
    def source_nodes(self):
        """
        Return the source nodes of the routes

        Returns
        -------
        np.array()
        """
        return np.unique(np.array([route.source_node.node_id
                         for route in self.values()], dtype='i4'))

    def get_n_routes(self, source_id):
        return len([route.source_id for route in self.values()
                    if route.source_id == source_id])


class TransferNodes(OrderedDict):
    """TransferNodes-object"""


    #def __init__(self, areas):
        #super(TransferNodes, self).__init__()
        #self.areas = areas

    def get_node(self, node, route):
        """
        (add and) get transfer_node with given node_id

        Parameters
        ----------
        node

        route

        Returns
        -------
        transfer_node
        """
        transfer_node = self.get(node.node_id)
        if transfer_node is None:
            transfer_node = TransferNode(node)
            self[transfer_node.node_id] = transfer_node
        transfer_node.routes[route.route_id] = route
        return transfer_node

    @property
    def total_weights(self):
        """Total weights of all transfer nodes"""
        return float(sum((tn.weight for tn in self.values())))

    def get_total_weights(self, source_id):
        """Total weights of all transfer nodes"""
        total_weight = 0.0
        for tn in self.values():
            for route in tn.routes.values():
                if route.source_id == source_id:
                    total_weight += tn.weight
                    break
        return total_weight

    def calc_initial_weight(self):
        """calculate the initial weight based upon the number of routes"""
        for tn in self.values():
            tn.calc_initial_weight()
        self.assign_weights_to_routes()

    def assign_weights_to_routes(self):
        """
        adjust weights to 100% and assign to routes that pass the transfer node
        """
        total_weights = self.total_weights
        total_weights_sources = {}
        n_routes_sources = {}
        for tn in self.values():
            tn.weight /= total_weights
            for route in tn.routes.values():
                n_routes = n_routes_sources.get(route.source_id, 0)
                n_routes_sources[route.source_id] = n_routes + 1
        return
        for area in self.source_ids:
            total_weights_sources[area.source_id] = \
                self.get_total_weights(area.source_id)

        for tn in self.values():
            for route in tn.routes.values():
                n_routes_for_area = tn.get_n_routes_for_area(route.source_id)
                total_weight_area = total_weights_sources[route.source_id]
                route.weight = tn.weight / total_weight_area / n_routes_for_area


class Nodes(object):
    """Nodes"""
    def __init__(self, epsg=31467):
        self.dtype = np.dtype(dict(names=['node_id', 'x', 'y'],
                                   formats=['i4', 'd', 'd']))
        self.epsg = epsg
        self.p1 = 'epsg:4326'
        self.p2 = f'epsg:{self.epsg}'
        self.coords2nodes = OrderedDict()
        self.id2nodes = OrderedDict()
        self.serial = 0

    def add_coordinates(self, coord_list):
        """
        Add Nodes

        Parameters
        ----------
        coord_list : list of tuple of floats

        """
        nodes = []
        for coords in coord_list:
            node = self.coords2nodes.get(coords)
            if node is None:
                node = Point(coords[1], coords[0])
                node.node_id = self.serial
                self.coords2nodes[coords] = node
                self.id2nodes[node.node_id] = node
                self.serial += 1
            nodes.append(node)
        return nodes

    def get_id(self, point):
        """"""
        node_id = self.coords2nodes[(point.x, point.y)]
        return self.get_node(node_id)

    def get_node(self, node_id):
        """"""
        return self.id2nodes[node_id]

    @property
    def node_ids(self):
        return self.id2nodes.keys()

    @property
    def nodes(self):
        points = self.id2nodes.values()
        if points:
            ret = np.rec.fromrecords([(p.node_id, p.x, p.y) for p in points],
                                     dtype=self.dtype)
        else:
            ret = np.rec.array(np.empty((0, ), dtype=self.dtype))
        return ret

    def transform(self):
        """Transform"""
        tr = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(self.p1),
            QgsCoordinateReferenceSystem(self.p2),
            QgsProject.instance()
        )

        for i, node in enumerate(self):
            pnt = QgsPoint(node.x, node.y)
            pnt.transform(tr)
            node.x = pnt.x()
            node.y = pnt.y()

    def __iter__(self):
        """Iterator"""
        return iter(self.id2nodes.values())

    def __len__(self):
        return len(self.id2nodes)


class TransferNode(Point):
    """"""
    def __init__(self, node):
        self.node_id = node.node_id
        self.x = node.x
        self.y = node.y
        self.routes = Routes()
        self.weight = 0.0

    @property
    def n_routes(self):
        return len(self.routes)

    def get_n_routes(self, source_id):
        return sum([1 for route in self.routes.values()
                   if route.source_id == source_id])

    def calc_initial_weight(self):
        """calculate the initial weight based upon the number of routes"""
        self.weight = float(self.n_routes)


class Links(object):
    """all links"""
    def __init__(self):
        self.node_ids2link = OrderedDict()
        self.id2link = OrderedDict()
        self.serial = 0

    def __iter__(self):
        return iter(self.node_ids2link.values())

    def add_vertex(self, node1, node2):
        """"""
        node_ids = (node1.node_id, node2.node_id)
        node_ids_reversed = (node2.node_id, node1.node_id)
        link = self.node_ids2link.get(node_ids,
                                      self.node_ids2link.get(node_ids_reversed))
        if link is None:
            link = Link(node1, node2, self.serial)
            self.node_ids2link[node_ids] = link
            self.id2link[link.link_id] = link
            self.serial += 1
        return link

    def get_id(self, node_ids):
        """"""
        return self.node_ids2link[node_ids]

    def get_node(self, vertex_id):
        """"""
        return self.id2link[vertex_id]

    @property
    def vertex_ids(self):
        return self.id2link.keys()

    @property
    def node_ids(self):
        return np.rec.fromrecords([l.node_ids
                                   for l in self],
                                  names=['from_node', 'to_node'])

    def __len__(self):
        return len(self.id2link)

    @property
    def link_length(self):
        return np.array([l.length for l in self])


class Link(object):
    """A Vertex"""
    def __init__(self, from_node, to_node, vertex_id):
        self.from_node = from_node
        self.to_node = to_node
        self.link_id = vertex_id
        self.routes = set()
        self.weight = 0.0
        self.distance_from_source = 9999999

    def __repr__(self):
        return '->'.join([repr(self.from_node), repr(self.to_node)])

    def __hash__(self):
        return hash(((self.from_node.x, self.from_node.y),
                     (self.to_node.x, self.to_node.y)))

    @property
    def length(self):
        meter = np.sqrt((self.to_node.x - self.from_node.x) ** 2 +
                         (self.to_node.y - self.from_node.y) ** 2)
        return meter

    @property
    def node_ids(self):
        return (self.from_node.node_id, self.to_node.node_id)

    def add_route(self, route_id):
        """add route_id to route"""
        self.routes.add(route_id)

    def get_geom(self):
        """Create polyline from geometry"""
        if self.length:
            n1 = self.from_node
            n2 = self.to_node
            coord_list = [(n1.x, n1.y), (n2.x, n2.y)]
            line = ogr.Geometry(ogr.wkbLineString)
            for coords in coord_list:
                line.AddPoint(*coords)
            return line


class OTPRouter(object):
    router_epsg = 4326

    def __init__(self, distance=None, epsg=31467):
        self.router = settings.OTP_ROUTER_ID
        self.url = f'{settings.OTP_ROUTER_URL}/routers/{self.router}/plan'
        self.epsg = epsg
        self.dist = distance
        self.nodes = Nodes(epsg)
        self.links = Links()
        self.polylines = []
        self.routes = Routes()
        self.transfer_nodes = TransferNodes()
        self.nodes_have_been_weighted = False
        self.extent = (0.0, 0.0, 0.0, 0.0)
        self.route_counter = 0

    def __repr__(self):
        """A string representation"""
        text = 'OTPRouter with {n} nodes, {r} routes and {t} transfer nodes'
        return text.format(n=len(self.nodes), r=len(self.routes), t=len(
            self.transfer_nodes))

    def route(self, source, destination, source_id=None, route_id=None,
              mode='CAR'):
        """
        get a routing requset for route from source to destination

        Parameters
        ----------
        source : Point
        destination : Point
        mode : str, optional (default='CAR')

        Returns
        -------
        Route
            route
        """
        params = dict(routerId=self.router,
                      fromPlace=f'{source.y},{source.x}',
                      toPlace=f'{destination.y},{destination.x}',
                      mode=mode,
                      maxPreTransitTime=1200)
        r = requests.get(self.url, params=params, timeout=60000)
        r.raise_for_status()
        if source_id is None:
            source_id = source.id
        route = self.add_route(r.json(), source_id=source_id, route_id=route_id)
        return route

    def add_route(self, json, source_id=0, route_id=None):
        """
        Parse the geometry from a json

        Parameters
        ----------
        json : json-instance

        source_id : int, optional(default=0)
        """
        try:
            itinerary = json['plan']['itineraries'][0]
        except KeyError:
            return
        leg = itinerary['legs'][0]
        points = leg['legGeometry']['points']
        coord_list = PolylineCodec().decode(points)
        if len(coord_list) == 0:
            return
        coord_list = coord_list[:-1]

        nodes = self.nodes.add_coordinates(coord_list)

        source_node = nodes[0]
        destination_node = nodes[-1]

        route = self.routes.get_route(source_node, destination_node)

        if not route:
            route = self.routes.add_route(
                route_id if route_id is not None else self.route_counter,
                source_id, nodes=nodes
            )
            previous_node = None
            for node in nodes:
                if previous_node:
                    link = self.links.add_vertex(previous_node, node)
                    link.add_route(route.route_id)
                previous_node = node
            self.route_counter += 1

        return route

    def create_circle(self, source, dist=1000, n_segments=20):
        """
        Create a circle around source in a given distance
        and with the given number of segments

        Parameters
        ----------
        source : Point-instance

        dist : float
            the distance around the point

        n_segments : int
            the number of segments of the (nearly) circle

        """
        angel = np.linspace(0, np.pi*2, n_segments)
        x = source.x + dist * np.cos(angel)
        y = source.y + dist * np.sin(angel)
        destinations = np.vstack([x, y]).T

        return destinations

    def get_max_node_for_route(self, dist_vector, route_id):
        """
        get the max distant node for a given route_id

        Parameters
        ----------
        dist_vector
        route_id : int

        Returns
        -------
        transfer_node : Node
        """
        route = self.routes[route_id]
        node_ids = route.node_ids
        route_dist_vector = dist_vector[node_ids]

        idx = np.argmax(route_dist_vector)
        node_id = node_ids[idx]
        node = self.nodes.get_node(node_id)
        transfer_node = self.transfer_nodes.get_node(node, route)
        transfer_node.dist = route_dist_vector[idx]
        return transfer_node

    def get_max_nodes(self, dist_vector):
        """
        """
        # for several Teilflächen: use the maximum to one of the origins
        for route in self.routes.values():
            transfer_node = self.get_max_node_for_route(dist_vector,
                                                        route.route_id)

    def build_graph(self, distance=None):
        """Convert nodes and links to graph"""
        self.nodes.transform()
        data = self.links.link_length
        node_ids = self.links.node_ids
        row = node_ids.from_node
        col = node_ids.to_node
        N = len(self.nodes)
        mat = csc_matrix((data, (row, col)), shape=(N, N))
        dist_matrix = dijkstra(mat,
                               directed=True,
                               return_predecessors=False,
                               indices=self.routes.source_nodes,
                               )
        dist_vector = dist_matrix.min(axis=0)
        self.set_link_distance(dist_vector)
        if distance:
            dist_vector[dist_vector > distance] = np.NINF
        self.get_max_nodes(dist_vector)

    def remove_redundancies(self):
        '''
        remove transfer nodes and their routes that are part of another route
        '''

        redundant_nodes = []
        transfer_nodes = self.transfer_nodes.values()
        for transfer_node in transfer_nodes:
            is_redundant = False
            for tn in transfer_nodes:
                if (tn.node_id == transfer_node.node_id
                    or tn.node_id in redundant_nodes):
                    continue
                for route in tn.routes.values():
                    # transfer node is part of the route of
                    # another transfer node
                    in_route = np.in1d(transfer_node.node_id,
                                       route.nodes[:-1]).sum() != 0
                    if in_route:
                        redundant_nodes.append(transfer_node)
                        is_redundant = True
                        break
                if is_redundant:
                    break
        part_routes = []
        for node in redundant_nodes:
            self.transfer_nodes.pop(node.node_id, None)
            part_routes.extend(list(node.routes))

        part_routes = np.unique(part_routes)
        for route_id in redundant_nodes:
            self.routes.pop(route_id, None)

    def set_link_distance(self, dist_vector):
        """set distance to plangebiet for each link"""
        for link in self.links:
            node_id = link.to_node.node_id
            dist = dist_vector[node_id]
            link.distance_from_source = dist

    def get_polyline_features(self):
        """get a dataframe containing the polyline-features from the links"""
        fields = ['link_id', 'weight', 'distance_from_source', 'geom']
        df = pd.DataFrame(columns=fields)
        i = 0
        for link in self.links:
            geom = link.get_geom()
            if self.dist and link.distance_from_source >= self.dist:
                continue
            if geom:
                df.loc[i] = [link.link_id, link.weight,
                             link.distance_from_source, geom]
                i += 1
        return df

    def get_transfer_node_features(self):
        """get a dataframe containing the point-features from
        the transfer nodes"""
        fields = ['node_id', 'weight', 'geom', 'name']
        df = pd.DataFrame(columns=fields)
        counter = 1
        i = 0
        for node in self.transfer_nodes.values():
            name = 'Herkunfts-/Zielpunkt ' + str(counter)
            counter += 1
            geom = node.geom
            if geom:
                df.loc[i] = [node.node_id, node.weight * 100, geom, name]
                i += 1
        return df

    def get_node_features(self):
        """get a dataframe containing the point-features from all nodes"""
        fields = ['node_id', 'geom']
        df = pd.DataFrame(columns=fields)
        i = 0
        for node in self.nodes:
            geom = node.geom
            if geom:
                df.loc[i] = [node.node_id, geom]
                i += 1
        return df



