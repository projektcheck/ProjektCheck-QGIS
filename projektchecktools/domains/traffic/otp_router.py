# -*- coding: utf-8 -*-

import requests
from pickle import dump, load
from osgeo import ogr
from collections import OrderedDict
from scipy.sparse import csc_matrix
from pyproj import Proj, transform
from scipy.sparse.csgraph import dijkstra
import numpy as np
import pandas as pd
import os

from projektchecktools.utils.polyline import PolylineCodec
from projektchecktools.utils.spatial import Point


class Route(object):
    """Route to a destination"""

    def __init__(self, route_id, source_id):
        """
        Parameters
        ----------
        route_id : int
        """
        self.route_id = route_id
        self.source_id = source_id
        self.node_ids = np.array([], dtype='i4')
    @property
    def source_node(self):
        if not len(self.node_ids):
            return None
        return self.node_ids[0]


class Routes(OrderedDict):
    """Routes-object"""

    def get_route(self, route_id, source_id):
        """
        (add and) get route with given route_id

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
            route = Route(route_id, source_id)
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
        return np.unique(np.array([route.source_node
                         for route in self.values()], dtype='i4'))

    def get_n_routes_for_area(self, source_id):
        return len([route.source_id
                    for route in self.values()
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
            transfer_node = TransferNode(node, self.areas)
            self[transfer_node.node_id] = transfer_node
        transfer_node.routes[route.route_id] = route
        return transfer_node

    @property
    def total_weights(self):
        """Total weights of all transfer nodes"""
        return float(sum((tn.weight for tn in self.values())))

    def get_total_area_weights(self, source_id):
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
        print('-------------------', total_weights)
        n_areas = len(self.areas)
        total_weights_areas = {}
        n_routes_areas = {}
        for tn in self.values():
            tn.weight /= total_weights
            for route in tn.routes.values():
                n_routes = n_routes_areas.get(route.source_id, 0)
                n_routes_areas[route.source_id] = n_routes + 1
        for area in self.areas.values():
            total_weights_areas[area.source_id] = \
                self.get_total_area_weights(area.source_id)

        for tn in self.values():
            for route in tn.routes.values():
                n_routes_for_area = tn.get_n_routes_for_area(route.source_id)
                total_weight_area = total_weights_areas[route.source_id]
                route.weight = tn.weight / total_weight_area / n_routes_for_area


class Nodes(object):
    """Nodes"""
    def __init__(self, epsg=31467):
        self.dtype = np.dtype(dict(names=['node_id', 'x', 'y'],
                                   formats=['i4', 'd', 'd']))
        self.epsg = epsg
        self.p1 = Proj(init='epsg:4326')
        self.p2 = Proj(init='epsg:{}'.format(self.epsg))
        self.coords2nodes = OrderedDict()
        self.id2nodes = OrderedDict()
        self.serial = 0
        self.links = Links()

    def add_points(self, coord_list, route):
        """
        Add Nodes, create link and add route_id to link

        Parameters
        ----------
        coord_list : list of tuple of floats

        route : int

        """
        previous_node = None
        node_ids = []
        for coords in coord_list:
            node = self.get_or_set_node_from_coord(coords)
            if previous_node:
                link = self.links.add_vertex(previous_node, node)
                link.add_route(route.route_id)
            previous_node = node
            node_ids.append(node.node_id)
        route.node_ids = np.array(node_ids, dtype='i4')

    def get_or_set_node_from_coord(self, coords):
        """
        get an existing node or add a new node from given coordinates

        Parameters
        ----------
        coords : tuple(float, float)
            (x, y)

        Returns
        -------
        node : Point-instance
        """
        node = self.coords2nodes.get(coords)
        if node is None:
            node = Point(coords[1], coords[0])
            node.node_id = self.serial
            self.coords2nodes[coords] = node
            self.id2nodes[node.node_id] = node
            self.serial += 1
        return node

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
        x, y = transform(self.p1, self.p2, self.nodes.x, self.nodes.y)
        for i, node in enumerate(self):
            node.x = x[i]
            node.y = y[i]

    def __iter__(self):
        """Iterator"""
        return iter(self.id2nodes.values())

    def __len__(self):
        return len(self.id2nodes)


class TransferNode(Point):
    """"""
    def __init__(self, node, areas):
        self.node_id = node.node_id
        self.x = node.x
        self.y = node.y
        self.routes = Routes()
        self.weight = 0.0
        self.areas = areas

    @property
    def n_routes(self):
        return len(self.routes)

    def get_n_routes_for_area(self, source_id):
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
    def __init__(self, node1, node2, vertex_id):
        self.node1 = node1
        self.node2 = node2
        self.link_id = vertex_id
        self.routes = set()
        self.weight = 0.0
        self.distance_from_source = 9999999

    def __repr__(self):
        return '->'.join([repr(self.node1), repr(self.node2)])

    def __hash__(self):
        return hash(((self.node1.x, self.node1.y),
                     (self.node2.x, self.node2.y)))

    @property
    def length(self):
        meter = np.sqrt((self.node2.x - self.node1.x) ** 2 +
                         (self.node2.y - self.node1.y) **2)
        return meter

    @property
    def node_ids(self):
        return (self.node1.node_id, self.node2.node_id)

    def add_route(self, route_id):
        """add route_id to route"""
        self.routes.add(route_id)

    def get_geom(self):
        """Create polyline from geometry"""
        if self.length:
            n1 = self.node1
            n2 = self.node2
            coord_list = [(n1.x, n1.y), (n2.x, n2.y)]
            line = ogr.Geometry(ogr.wkbLineString)
            for coords in coord_list:
                line.AddPoint(*coords)
            return line


class Area(object):
    """Teilfläche"""
    def __init__(self, source_id, trips=1):
        self.source_id = source_id
        self.trips = trips


class Areas(OrderedDict):
    """All Areas"""
    def add_area(self, source_id, trips=1):
        """"""
        self[source_id] = Area(source_id, trips)


class OTPRouter(object):
    url = r'https://projektcheck.ggr-planung.de/otp/routers/deutschland/plan'
    router = 'deutschland'
    router_epsg = 4326

    def __init__(self, distance=1000, epsg=31467):
        self.epsg = epsg
        self.dist = distance
        self.p1 = Proj(init=f'epsg:{self.router_epsg}')
        self.p2 = Proj(init='epsg:{}'.format(epsg))
        self.nodes = Nodes(epsg)
        self.polylines = []
        self.routes = Routes()
        self.areas = Areas()
        self.transfer_nodes = TransferNodes()
        self.transfer_nodes.areas = self.areas
        self.nodes_have_been_weighted = False
        self.extent = (0.0, 0.0, 0.0, 0.0)

    def dump(self, filename):
        """write myself to dumpfile"""
        with open(filename, 'wb') as f:
            dump(self, f, protocol=-1)

    @classmethod
    def from_dump(cls, filename, workspace=''):
        """"""
        with open(filename, 'rb') as f:
            self = load(f)
        if workspace:
            self.ws = workspace
        return self

    def __repr__(self):
        """A string representation"""
        text = 'OTPRouter with {n} nodes, {r} routes and {t} transfer nodes'
        return text.format(n=len(self.nodes), r=len(self.routes), t=len(
            self.transfer_nodes))

    def get_routing_request(self, source, destination, mode='CAR'):
        """
        get a routing requset for route from source to destination

        Parameters
        ----------
        source : Point
        destination : Point
        mode : str, optional (default='CAR')

        Returns
        -------
        json
        """
        params = dict(routerId=self.router,
                      fromPlace=f'{source.y},{source.x}',
                      toPlace=f'{destination.y},{destination.x}',
                      mode=mode,
                      maxPreTransitTime=1200)
        r = requests.get(self.url, params=params, verify=False)
        return r.json()

    def decode_coords(self, json, route_id, source_id=0):
        """
        Parse the geometry from a json

        Parameters
        ----------
        json : json-instance

        route_id : int

        source_id : int, optional(default=0)
        """
        try:
            itinerary = json['plan']['itineraries'][0]
        except KeyError:
            return
        leg = itinerary['legs'][0]
        points = leg['legGeometry']['points']
        coord_list = PolylineCodec().decode(points)
        route = self.routes.get_route(route_id, source_id)
        self.nodes.add_points(coord_list, route)
        if source_id not in self.areas:
            self.areas.add_area(source_id)

    def coord_list2polyline(self, coord_list):
        """
        create arcpy.Polyline from list of coordinates
        and append to polylines list

        Parameters
        ----------
        coord_list : list of tuples of coordinates


        """
        if not len(coord_list):
            return None
        geom = arcpy.Polyline(
            arcpy.Array([arcpy.Point(coords[1], coords[0])
                         for coords in coord_list]))
        self.polylines.append(geom)

    def insert_polyline(self, fc):
        """
        Insert polylines to fc

        Parameters
        ----------
        fc : str
            the path of the feature-class

        """
        sr = arcpy.SpatialReference(4326)
        fields = ['source', 'destination', 'SHAPE@']
        with arcpy.da.InsertCursor(fc, fields) as rows:
            for dest, geom in enumerate(self.polylines):
                if geom:
                    rows.insertRow((1, dest, geom))

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
        route_nodes = route.node_ids
        route_dist_vector = dist_vector[route_nodes]

        idx = np.argmax(route_dist_vector)
        node_id = route_nodes[idx]
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

    def nodes_to_graph(self, meters=600):
        """Convert nodes and links to graph"""
        data = self.nodes.links.link_length
        node_ids = self.nodes.links.node_ids
        row = node_ids.from_node
        col = node_ids.to_node
        N = len(self.nodes)
        mat = csc_matrix((data, (row, col)), shape=(N, N))
        source_nodes = self.routes.source_nodes
        dist_matrix = dijkstra(mat,
                               directed=True,
                               return_predecessors=False,
                               indices=self.routes.source_nodes,
                               )
        dist_vector = dist_matrix.min(axis=0)
        self.set_link_distance(dist_vector)
        dist_vector[dist_vector > meters] = np.NINF
        self.get_max_nodes(dist_vector)

    def set_link_distance(self, dist_vector):
        """set distance to plangebiet for each link"""
        for link in self.nodes.links:
            node_id = link.node2.node_id
            dist = dist_vector[node_id]
            link.distance_from_source = dist

    def calc_vertex_weights(self):
        """calc weight of link"""
        for link in self.nodes.links:
            link.weight = 0.
            for route_id in link.routes:
                route = self.routes[route_id]
                route_weight = route.weight
                area = self.areas[route.source_id]
                route_trips = route_weight * area.trips
                link.weight += route_trips

    def get_polyline_features(self):
        """get a dataframe containing the polyline-features from the links"""
        fields = ['link_id', 'weight', 'distance_from_source', 'geom']
        df = pd.DataFrame(columns=fields)
        i = 0
        for link in self.nodes.links:
            geom = link.get_geom()
            if geom and link.distance_from_source <= self.dist:
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
        equal_node_weight = round(100 / len(self.transfer_nodes), 1)
        for node in self.transfer_nodes.values():
            name = 'Herkunfts-/Zielpunkt ' + str(counter)
            counter += 1
            geom = node.geom
            if geom:
                df.loc[i] = [node.node_id, equal_node_weight, geom, name]
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



