from pyproj import Proj, transform
import numpy as np


def convert_coords(longitude, latitude, epsg_in, epsg_out):
    in_proj = Proj(init='epsg:{}'.format(epsg_in))
    out_proj = Proj(init='epsg:{}'.format(epsg_out))
    x2, y2 = transform(in_proj, out_proj, longitude, latitude)

    return x2, y2


def world_to_pixel(image_dataset, longitude, latitude):
    geotransform = image_dataset.GetGeoTransform()

    ulx, uly = geotransform[0], geotransform[3]
    x_dist = geotransform[1]

    x = np.round((longitude - uly) / x_dist).astype(np.int)
    y = np.round((uly - latitude) / x_dist).astype(np.int)

    return x, y