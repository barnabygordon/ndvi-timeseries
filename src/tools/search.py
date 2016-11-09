import requests

api_url = 'https://api.developmentseed.org/landsat'

query = 'acquisitionDate:[2014-01-01+TO+2016-01-01]+AND+cloudCoverFull:[-1+TO+20]+AND+upperLeftCornerLatitude:[52+TO+1000]+AND+lowerRightCornerLatitude:[-1000+TO+52]+AND+lowerLeftCornerLongitude:[-1000+TO+48]+AND+upperRightCornerLongitude:[48+TO+1000]'

limit = 1

def search_landsat(lng, lat):

	r_object = requests.get('%s?search=%s&limit=%s' % (api_url, query, limit))
	r_status = r.status_code
	r_result = r.json()['results'][0]

	return r