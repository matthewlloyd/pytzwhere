#!/usr/bin/python

try:
    import json
except ImportError:
    import simplejson as json
import datetime
import math
import os
import pickle
from collections import defaultdict
from shapely.geometry import Point, Polygon


class tzwhere(object):
    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1

    def __init__(self, filename=None, read_pickle=False, write_pickle=False):
        # By default, use the data file in our package directory
        if filename is None:
            filename = os.path.join(os.path.dirname(__file__), 'tz_world_compact.json')

        input_file = open(filename, 'r')

        if read_pickle:
            print 'Reading pickle input file: %s' % filename
            featureCollection = pickle.load(input_file)
        else:
            print 'Reading json input file: %s' % filename
            featureCollection = json.load(input_file)

        input_file.close()

        if write_pickle:
            print 'Writing pickle output file: %s' % PICKLE_FILENAME
            f = open(PICKLE_FILENAME, 'w')
            pickle.dump(featureCollection, f, pickle.HIGHEST_PROTOCOL)
            f.close()

        self.timezoneNamesToPolygons = defaultdict(tuple)
        for feature in featureCollection['features']:
            if feature['geometry']['type'] != 'Polygon':
                continue
            polys = feature['geometry']['coordinates']
            if not polys:
                continue
            tzname = feature['properties']['TZID']

            all_polys = []
            for raw_poly in polys:
                # WPS84 coordinates are [long, lat], while many conventions are [lat, long]
                assert len(raw_poly) % 2 == 0
                poly = []
                for i in xrange(0, len(raw_poly), 2):
                    lng, lat = raw_poly[i], raw_poly[i + 1]
                    poly.append( (lat, lng) )
                all_polys.append(tuple(poly))
            self.timezoneNamesToPolygons[tzname] += tuple(all_polys)

        self.timezoneLongitudeShortcuts = [defaultdict(list) for i in xrange(360)]
        self.timezoneLatitudeShortcuts = [defaultdict(list) for i in xrange(180)]
        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
                lngs = [x[1] for x in poly]
                minLng, maxLng = map(self._to_shortcut_lon, [min(lngs), max(lngs)])
                for i in xrange(minLng, maxLng + 1):
                    self.timezoneLongitudeShortcuts[i][tzname].append(polyIndex)

                lats = [x[0] for x in poly]
                minLat, maxLat = map(self._to_shortcut_lat, [min(lats), max(lats)])
                for i in xrange(minLat, maxLat + 1):
                    self.timezoneLatitudeShortcuts[i][tzname].append(polyIndex)

        # Convert things to tuples to save memory.
        for i in xrange(len(self.timezoneLatitudeShortcuts)):
            for tzname in self.timezoneLatitudeShortcuts[i]:
                self.timezoneLatitudeShortcuts[i][tzname] = tuple(self.timezoneLatitudeShortcuts[i][tzname])
        for i in xrange(len(self.timezoneLongitudeShortcuts)):
            for tzname in self.timezoneLongitudeShortcuts[i]:
                self.timezoneLongitudeShortcuts[i][tzname] = tuple(self.timezoneLongitudeShortcuts[i][tzname])

    def _to_shortcut_lat(self, deg):
        return int((deg + 90.0) / self.SHORTCUT_DEGREES_LATITUDE)

    def _to_shortcut_lon(self, deg):
        return int((deg + 180.0) / self.SHORTCUT_DEGREES_LONGITUDE)

    def tzNameAt(self, latitude, longitude, find_closest=False):
        latTzOptions = self.timezoneLatitudeShortcuts[self._to_shortcut_lat(latitude)]
        latSet = set(latTzOptions.keys())
        lngTzOptions = self.timezoneLongitudeShortcuts[self._to_shortcut_lon(longitude)]
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet)
        closest_tz = None
        closest_dist = None
        point = Point(latitude, longitude)
        for tzname in possibleTimezones:
            # lazily convert to Polygon instances, which are expensive to construct
            if isinstance(self.timezoneNamesToPolygons[tzname][0], tuple):
                self.timezoneNamesToPolygons[tzname] = map(lambda p: Polygon(p), self.timezoneNamesToPolygons[tzname])
            polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]))
            for polyIndex in polyIndices:
                poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                if poly.contains(point):
                    return tzname
                if find_closest:
                    dist = poly.distance(point)
                    if closest_dist is None or dist < closest_dist:
                        closest_dist = dist
                        closest_tz = tzname
        if find_closest:
            return closest_tz
