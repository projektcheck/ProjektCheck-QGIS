'''
source: https://github.com/hicsail/polyline/

Copyright (c) 2014 Bruno M. Custódio
Copyright (c) 2019 Frederick Jansen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import itertools
import six
import math


class PolylineCodec(object):
    def _pcitr(self, iterable):
        return six.moves.zip(iterable, itertools.islice(iterable, 1, None))

    def _py2_round(self, x):
        # The polyline algorithm uses Python 2's way of rounding
        return int(math.copysign(math.floor(math.fabs(x) + 0.5), x))

    def _write(self, output, curr_value, prev_value, factor):
        curr_value = self._py2_round(curr_value * factor)
        prev_value = self._py2_round(prev_value * factor)
        coord = curr_value - prev_value
        coord <<= 1
        coord = coord if coord >= 0 else ~coord

        while coord >= 0x20:
            output.write(six.unichr((0x20 | (coord & 0x1f)) + 63))
            coord >>= 5

        output.write(six.unichr(coord + 63))

    def _trans(self, value, index):
        byte, result, shift = None, 0, 0

        while byte is None or byte >= 0x20:
            byte = ord(value[index]) - 63
            index += 1
            result |= (byte & 0x1f) << shift
            shift += 5
            comp = result & 1

        return ~(result >> 1) if comp else (result >> 1), index

    def decode(self, expression, precision=5, geojson=False):
        coordinates, index, lat, lng, length, factor = [], 0, 0, 0, len(expression), float(10 ** precision)

        while index < length:
            lat_change, index = self._trans(expression, index)
            lng_change, index = self._trans(expression, index)
            lat += lat_change
            lng += lng_change
            coordinates.append((lat / factor, lng / factor))

        if geojson is True:
            coordinates = [t[::-1] for t in coordinates]

        return coordinates

    def encode(self, coordinates, precision=5, geojson=False):
        if geojson is True:
            coordinates = [t[::-1] for t in coordinates]

        output, factor = six.StringIO(), int(10 ** precision)

        self._write(output, coordinates[0][0], 0, factor)
        self._write(output, coordinates[0][1], 0, factor)

        for prev, curr in self._pcitr(coordinates):
            self._write(output, curr[0], prev[0], factor)
            self._write(output, curr[1], prev[1], factor)

        return output.getvalue()
