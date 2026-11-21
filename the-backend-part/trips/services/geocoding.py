"""Turn a place name such as "Chicago, IL" into coordinates (Photon / OpenStreetMap, no key)."""
from dataclasses import dataclass

import requests

from .errors import TripPlanningError

GEOCODE_URL = 'https://photon.komoot.io/api/'
TIMEOUT_SECONDS = 20
HEADERS = {'User-Agent': 'HaulSafe-assessment/1.0'}


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lng: float


def geocode(text):
    text = (text or '').strip()
    if not text:
        raise TripPlanningError('Origin and destination are required.')

    try:
        response = requests.get(
            GEOCODE_URL,
            params={'q': text, 'limit': 10, 'lang': 'en'},
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        features = response.json().get('features', [])
    except (requests.RequestException, ValueError):
        raise TripPlanningError('The geocoding service is unavailable. Please try again.', status=502)

    # the assessment is about US truck routes: take the first US result
    us = [f for f in features if f['properties'].get('countrycode') == 'US']
    if not us:
        raise TripPlanningError(f'Could not find a location called "{text}".')

    feature = us[0]
    props = feature['properties']
    lng, lat = feature['geometry']['coordinates']  # GeoJSON order is [lng, lat]
    label = ', '.join(p for p in (props.get('name'), props.get('state')) if p) or text
    return Place(name=label, lat=lat, lng=lng)