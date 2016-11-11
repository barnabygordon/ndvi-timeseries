import requests
from osgeo import gdal
import numpy as np
from pyproj import Proj, transform

api_url = 'https://api.developmentseed.org/landsat'


def search_landsat(lng, lat, min_date, max_date, limit):

    query = _query_builder(lng, lat, min_date, max_date)

    r = requests.get('%s?search=%s&limit=%s' % (api_url, query, int(limit)))

    r_status = r.status_code

    print r_status
    if r_status != 200:

        print 'Bad URL!!'
        print query

    else:
        r_result = r.json()['results']

        data = {}

        count = 0
        for result in r_result:

            search_result = {}

            date = result['date']
            cloud_cover = result['cloudCover']
            scene_id = result['sceneID']
            thumbnail_url = result['thumbnail']
            ndvi = _aws_get_ndvi(scene_id, lng, lat)

            search_result['date'] = date
            search_result['cloud_cover'] = cloud_cover
            search_result['scene_id'] = scene_id
            search_result['thumbnail_url'] = thumbnail_url
            search_result['ndvi'] = ndvi

            data[count] = search_result

            count += 1

        return data


def _query_builder(lng, lat, min_date, max_date):

    min_cloud, max_cloud = -1, 20

    dates = 'acquisitionDate:[%s+TO+%s]' % (min_date, max_date)

    clouds = 'cloudCoverFull:[%s+TO+%s]' % (min_cloud, max_cloud)

    UlLat = 'upperLeftCornerLatitude:[%s+TO+1000]' % (lat)
    LrLat = 'lowerRightCornerLatitude:[-1000+TO+%s]' % (lat)
    LlLng = 'lowerLeftCornerLongitude:[-1000+TO+%s]' % (lng)
    UrLng = 'upperRightCornerLongitude:[%s+TO+1000]' % (lng)

    query = '%s+AND+%s+AND+%s+AND+%s+AND+%s+AND+%s' % (dates, clouds, UlLat, LrLat, LlLng, UrLng)

    return query


def _aws_get_ndvi(scene_id, lng, lat):

    bands = [5, 4]
    data = []

    for band in bands:

        url = _aws_url_builder(scene_id, band)

        src = gdal.Open(url)
        prj = src.GetProjection()
        epsg_out = prj.split('"EPSG",')[-1].strip(']').strip('"')

        lng2, lat2 = _convert_coords(lng, lat, 4326, epsg_out)

        x, y = _world2pixel(src, lng2, lat2)

        pixel = src.ReadAsArray(y, x, 1, 1).astype('float32')

        data.append(pixel)

    ndvi = (data[0] - data[1]) / (data[0] + data[1])

    return ndvi


def _aws_url_builder(scene_id, band):

    path, row = scene_id[3:6], scene_id[6:9]

    url = '/vsicurl/http://landsat-pds.s3.amazonaws.com/L8/%s/%s/%s/%s_B%s.TIF' % (path, row, scene_id, scene_id, band)

    return url


def _convert_coords(lng, lat, epsg_in, epsg_out):

    inProj = Proj(init='epsg:%s' % (epsg_in))
    outProj = Proj(init='epsg:%s' % (epsg_out))
    x1, y1 = lng, lat
    x2, y2 = transform(inProj, outProj, x1, y1)

    return x2, y2


def _world2pixel(src, lng, lat):

    gt = src.GetGeoTransform()

    ulX, ulY = gt[0], gt[3]
    xDist = gt[1]

    x = np.round((lng - ulX) / xDist).astype(np.int)
    y = np.round((ulY - lat) / xDist).astype(np.int)

    return x, y

