# NDVI Time Series

A tool for automatically calculating NDVI (Normalised Difference Vegetation Index) based on a given coordinate.

This method uses Landsat-8 imagery which is freely available at [AWS](https://aws.amazon.com/public-data-sets/landsat/).

Without calibration:
![alt text](https://github.com/BarnabyGordon/ndvi-timeseries/blob/master/figures/without_calibration.png)

## Usage

- The provided coordinate must in WGS84 (EPSG: 4326)
- A start and end date must be provided (YYYY-MM-DD)
- The number of acquisitions of interest should also be give (will take longer to process the greater this value)

## Dependencies

- GDAL
- Numpy
- PyProj
- Requests