import requests
from osgeo import gdal

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

    ndvi = 0.8

    return ndvi