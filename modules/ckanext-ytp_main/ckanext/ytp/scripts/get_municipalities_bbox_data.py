import json
import time

from geopy.geocoders import Nominatim

from municipalities import FI_MUNICIPALITIES, SV_MUNICIPALITIES

"""
This script takes the names of all Finnish municipalitiy names (Swedish and Finnish),
combines them into a list and does a lookup for each municipality thorugh the Nomiatim
service. The service returns geographical data of which we save the bounding
box data for each municipality and its corresponding box to a dictionary.
The dictionary is then stored into a json data file. Geopy is needed for
this script since it is used for fetching the data from the Nominatim service.

https://nominatim.org/

More information about geopy:
https://geopy.readthedocs.io/en/stable/

This script can be used with other geocoders as well. Check Geopy docs for more info.
This script is not tested with anything else than the Nominatim geocoder.
"""


geolocator = Nominatim(user_agent='FinnishMunicipalities/v1')


def get_bbox(mun):
    location = geolocator.geocode(mun)
    return location.raw.get('boundingbox')


def run():
    munList = list(set(FI_MUNICIPALITIES + SV_MUNICIPALITIES))
    munData = {}

    for mun in munList:
        print(f'Getting: {mun}')
        munData[mun] = get_bbox(mun)
        time.sleep(2)  # Nominatim recommends max. 1 request/second.

    return munData


def write_file(munData):
    with open('bbox_data.json', 'w+', encoding='utf8') as file:
        data = json.dumps(munData, ensure_ascii=False)
        file.write(data)


if __name__ == '__main__':
    munData = run()
    print(munData)
    write_file(munData)
    print('Done!')
