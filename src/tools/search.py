from osgeo import gdal
import requests
import numpy as np
import urllib3
import math

from src.tools import gis

API_URL = 'https://api.developmentseed.org/landsat'
AWS_LS8_URL = 'http://landsat-pds.s3.amazonaws.com/L8'
WGS84_EPSG = 4326


class NDVITimeseries:
    def __init__(self, longitude: float, latitude: float, min_cloud: int=0, max_cloud: int=100):
        self.longitude = longitude
        self.latitude = latitude
        self.min_cloud = min_cloud
        self.max_cloud = max_cloud

    def search_landsat(self, min_date: str, max_date: str, limit: int) -> dict:
        query = self._query_builder(min_date, max_date, limit)
        response = requests.get(query)

        if response.status_code != 200:
            print('Bad URL!! {}'.format(query))

        else:
            result_list = response.json()['results']

            data = {}
            for i, result in enumerate(result_list):
                search_result = {}

                date = result['date']
                cloud_cover = result['cloudCover']
                scene_id = result['sceneID']
                thumbnail_url = result['thumbnail']
                ndvi = self._get_ndvi_from_aws(scene_id)

                search_result['date'] = date
                search_result['cloud_cover'] = cloud_cover
                search_result['scene_id'] = scene_id
                search_result['thumbnail_url'] = thumbnail_url
                search_result['ndvi'] = ndvi

                data[i] = search_result

            return data

    def _query_builder(self, min_date, max_date, limit: int) -> str:
        dates = 'acquisitionDate:[{}+TO+{}]'.format(min_date, max_date)
        clouds = 'cloudCoverFull:[{}+TO+{}]'.format(self.min_cloud, self.max_cloud)

        upper_latitude = 'upperLeftCornerLatitude:[{}+TO+1000]'.format(self.latitude)
        lower_latitude = 'lowerRightCornerLatitude:[-1000+TO+{}]'.format(self.latitude)
        left_longitude = 'lowerLeftCornerLongitude:[-1000+TO+{}]'.format(self.longitude)
        right_longitude = 'upperRightCornerLongitude:[{}+TO+1000]'.format(self.longitude)

        query = '{}+AND+{}+AND+{}+AND+{}+AND+{}+AND+{}'.format(
            dates, clouds, upper_latitude, lower_latitude, left_longitude, right_longitude)

        return "{}?search={}&limit={}".format(API_URL, query, limit)

    def _get_ndvi_from_aws(self, scene_id: str) -> float:
        path, row = scene_id[3:6], scene_id[6:9]

        bands = [5, 4]

        meta_data = self._get_aws_meta(scene_id, path, row)

        data = []
        for band in bands:
            url = self._aws_url_builder(scene_id, path, row, band)

            image_dataset = gdal.Open(url)
            prorjection = image_dataset.GetProjection()
            epsg_out = prorjection.split('"EPSG",')[-1].strip(']').strip('"')

            lng2, lat2 = gis.convert_coords(self.longitude, self.latitude, WGS84_EPSG, epsg_out)
            x, y = gis.world_to_pixel(image_dataset, lng2, lat2)

            digital_number = image_dataset.ReadAsArray(y, x, 1, 1).astype('float32')

            reflectance = self._radiance2reflectance(digital_number, band, meta_data)

            data.append(reflectance)

        ndvi = (data[0] - data[1]) / (data[0] + data[1])

        return ndvi

    @staticmethod
    def _get_aws_meta(scene_id: str, path: int, row: int) -> str:
        meta_url = '{}/{}/{}/{}/{}_MTL.txt'.format(
            AWS_LS8_URL, path, row, scene_id, scene_id)
        # TODO update to Python3
        meta_data = urllib3.urlopen(meta_url).readlines()

        return meta_data

    @staticmethod
    def _aws_url_builder(scene_id: str, path: int, row: int, band: int) -> str:
        url = '/vsicurl/{}/{}/{}/{}/{}_B{}.TIF'.format(
            AWS_LS8_URL, path, row, scene_id, scene_id, band)

        return url

    def _radiance2reflectance(self, digital_number: float, band: int, meta_data: str) -> float:
        """ Conversion Top Of Atmosphere planetary reflectance
        REF: http://landsat.usgs.gov/Landsat8_Using_Product.php
        Following function based on work by Vincent Sarago:
        https://github.com/vincentsarago/landsatgif/blob/master/landsat_gif.py
        :param digital_number: digital number value
        :param band:
        :param meta_data:
        :return:
        """

        mp = float(self._landsat_extract_mtl(meta_data, "REFLECTANCE_MULT_BAND_{}".format(band)))
        ap = float(self._landsat_extract_mtl(meta_data, "REFLECTANCE_ADD_BAND_{}".format(band)))
        se = math.radians(float(self._landsat_extract_mtl(meta_data, "SUN_ELEVATION")))

        reflect_toa = (np.where(digital_number > 0, (mp * digital_number + ap) / math.sin(se), 0))

        return reflect_toa

    @staticmethod
    def _landsat_extract_mtl(meta_data: list, param: str) -> str:
        """ Extract Parameters from MTL file """
        for line in meta_data:
            data = line.split(' = ')
            if (data[0]).strip() == param:
                return (data[1]).strip()
