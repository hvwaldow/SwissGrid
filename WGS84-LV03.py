# Harald von Waldow <hvw@alumni.ethz.ch>
# Center for Climate Systems Modelling / ETHZ 
# 2015-03-02

import os
import numpy as np
import pyproj as pp
import requests
from random import uniform


class Convert(object):

    '''
    Conversion between "old" SwissGrid LV03 and lonlat (WGS84).
    Documentation: http://www.swisstopo.admin.ch/internet/swisstopo/en/home/topics/survey.html

    Two methods:
    1. Online REST-service of swisstopo:
    http://www.swisstopo.admin.ch/internet/swisstopo/en/home/products/software/products/m2m.html

    2. Using the PROJ.4 - package:
    http://trac.osgeo.org/proj/
    For good results it is cruical that the shiftfile provided by swisstopo is used.
    Some effort is expended to locate and/or download it.
    In case of failure, go hunting for 'chenyx06etrs.gsb'.

    The main method is *convert(points, typ=proj4)*
    '''

    def __init__(self):
        self.nadgrid_name = 'chenyx06etrs.gsb'
        self.url_CHENyx06 = ('http://www.swisstopo.admin.ch/internet/swisstopo/' +
                             'en/home/products/software/products/chenyx06.parsys' +
                             '.00011.downloadList.29885.DownloadFile.tmp/' +
                             'chenyx06etrs.gsb')
        self.lv03params = {'proj': 'somerc',
                           'lat_0': 46.95240555555556,
                           'lon_0': 7.439583333333333,
                           'k_0': 1,
                           'x_0': 600000.0,
                           'y_0': 200000.0,
                           'ellps': 'bessel',
                           'units': 'm',
                           'nadgrids': 'chenyx06etrs.gsb',
                           'no_defs': True}
        self.wgs84params = {'proj': 'latlon',
                            'ellps': 'WGS84',
                            'datum': 'WGS84',
                            'no_defs': True}
        self.rest_urls = {'wgs84tolv03': "http://tc-geodesy.bgdi.admin.ch/reframe/wgs84tolv03",
                          'lv03towgs84': "http://tc-geodesy.bgdi.admin.ch/reframe/lv03towgs84"}

        self.check_nadgrid()

    def _set_proj_lib_to_cwd(self, locpath):
        '''
        Sets PROJ_LIB correctly (for shiftfile in cwd)
        '''
        if "PROJ_LIB" in os.environ:
            if not os.getcwd() in os.environ["PROJ_LIB"].split(':'):
                os.environ["PROJ_LIB"] += ':' + os.getcwd()
        else:
            os.environ["PROJ_LIB"] = os.getcwd()
        print("Using shiftfile {}".format(locpath))
        print("PROJ_LIB: {}".format(os.environ["PROJ_LIB"]))

    def _set_nadgrid_to_cwd(self):
        '''
        If shiftfile is in current working directory, set PROJ_LIB
        accordingly. Else try to download the shiftfile.
        '''
        locpath = os.path.join(os.getcwd(), self.nadgrid_name)
        chunk_size = 2**20
        if not os.path.isfile(locpath):
            print("No shiftfile found. Trying to download")
            r = requests.get(self.url_CHENyx06, stream=True)
            with open(locpath, 'wb') as fh:
                for chunk in r.iter_content(chunk_size):
                    fh.write(chunk)
            r.raise_for_status()
            print("Download succesful!")
        self._set_proj_lib_to_cwd(locpath)
        return()

    def check_nadgrid(self):
        '''
        Checks whether the shiftfile can be found in a directory
        contained in $PROJ_LIB
        '''
        try:
            proj_path = os.environ["PROJ_LIB"]
            plocs = [os.path.join(x, self.nadgrid_name)
                     for x in proj_path.split(':')]
            plocs = [x for x in plocs if os.path.isfile(x)]
            if len(plocs) > 0:
                print("Found shiftfile: {}".format(plocs[0]))
                print("PROJ_LIB: {}".format(os.environ["PROJ_LIB"]))
                return()
            else:
                self._set_nadgrid_to_cwd()
        except KeyError:
            self._set_nadgrid_to_cwd()

    def _restconvert(self, points, direction):
        res = []
        resurl = self.rest_urls[direction]
        for p in [("{:.14f}".format(x[0]), "{:.14f}".format(x[1])) for x in points]:
            payload = dict(zip(('easting', 'northing'), p)
                           + [('format', 'json')])
            r = requests.get(resurl, params=payload)
            r.raise_for_status()
            oneres = r.json()
            res.append((float(oneres['easting']), float(oneres['northing'])))
        return(res)

    def convert(self, points, typ='proj4'):
        '''
        *points* is a list of tuples (easting, northing).
        *type* can equal 'proj4' or 'rest' and determines the
        method of conversion.
        The direction of conversion is guessed automatically.
        '''
        lv03 = pp.Proj(self.lv03params)
        wgs84 = pp.Proj(self.wgs84params)
        if (max([np.abs(x[0]) for x in points]) > 360. or
            max([np.abs(x[1]) for x in points]) > 90.):
            p1 = lv03
            p2 = wgs84
            direction = 'lv03towgs84'
        else:
            p1 = wgs84
            p2 = lv03
            direction = 'wgs84tolv03'
        if typ == 'rest':
            res = self._restconvert(points, direction)
        else:
            res = [pp.transform(p1, p2, *point) for point in points]
        return(res)

    def _gen_testpoints(self, direction, n):
        borders = {'wgs84tolv03': [(6., 46.), (10., 47.)],
                   'lv03towgs84': [(490000.0, 95295.0), (792960.0, 264177.0)]}
        lonlat = zip(*borders[direction])
        lons = [uniform(*lonlat[0]) for i in range(0, n)]
        lats = [uniform(*lonlat[1]) for i in range(0, n)]
        return(zip(lons, lats))

    def check_conversion(self, n):
        '''
        Compares conversions in both directions (difference REST / PROJ.4).
        Uses *n* randomly generated points in or close by Switzerland.
        '''
        res = {'lv03towgs84': {'rest': None, 'proj4': None},
               'wgs84tolv03': {'rest': None, 'proj4': None}}
        points = {}
        for direction in ['lv03towgs84', 'wgs84tolv03']:
            points[direction] = self._gen_testpoints(direction, n)
            for typ in ['rest', 'proj4']:
                res[direction][typ] = self.convert(points[direction], typ=typ)
        diffs = {}
        for direction in ['lv03towgs84', 'wgs84tolv03']:
            diffa = list(np.array(res[direction]['proj4'])
                         - np.array(res[direction]['rest']))
            diffb = np.array([np.sqrt(np.dot(p,p)) for p in diffa])
            diffs[direction] = diffb
        return([diffs, points])

if __name__ == '__main__':
    C = Convert()
    res, points = C.check_conversion(10)
    print('''
    The distances between the points converted with REST
    and PROJ.4, respectively. Distances are calculated as square root
    of the inner product. In the case of a lon-lat coordinate system, this
    makes little sense, but gives an impression of the accuracy nontheless.
    ''')
    print(res)
