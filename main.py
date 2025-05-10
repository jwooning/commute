#!/usr/bin/env python

import os
import sys
import datetime
import json

import pytz
import requests

MAPBOX_TOKEN_PATH = 'mapbox_token.txt'
LOG_DIR = 'out'

VALID_HOURS = [6, 7, 8, 9, 15, 16, 17, 18]
HOME = (4.2800987, 52.0903108)
WORK = (4.3139142, 52.0802853)
LOCS = {
  'Catshuis': HOME,
  'Paleis Noordeinde': (4.3058141, 52.0808956),
  'Paleis Het Loo': (5.9445656, 52.2341768),
  'Paleis Huis ten Bosch': (4.341751, 52.093172),
}

def log(line, fn='out.log'):
  path = os.path.join(os.path.dirname(__file__), LOG_DIR, fn)
  with open(path, 'a') as f:
    f.write(line)

def api_request(coordinates):
  with open(MAPBOX_TOKEN_PATH, 'r') as fp:
    mapbox_token = fp.read().strip()

  url = 'https://api.mapbox.com/directions/v5/mapbox/driving-traffic/'
  url += ';'.join([','.join([str(x) for x in coords]) for coords in coordinates])
  url += '?access_token=' + mapbox_token
  url += '&alternatives=true'
  url += '&annotations=distance,duration,congestion_numeric,closure'
  url += '&overview=full'
  url += '&geometries=geojson'

  resp = requests.get(url)

  if resp.status_code != 200:
    raise Exception(f'Failed api request: {resp.status_code}, {resp.text}')

  json_ = resp.json()
  return json_['routes']

def filter_route(r):
  res = {}

  res['duration'] = r['duration']
  res['duration_typical'] = r['duration_typical']
  res['distance'] = r['distance']

  assert len(r['legs']) == 1
  assert len(r['geometry']['coordinates']) == len(r['legs'][0]['annotation']['congestion_numeric']) + 1

  res['summary'] = r['legs'][0]['summary']
  res['incidents'] = r['legs'][0].get('incidents', [])
  res['closures'] = r['legs'][0].get('closures', [])
  res['step_coordinates'] = r['geometry']['coordinates']
  res['step_congestion'] = r['legs'][0]['annotation']['congestion_numeric']
  res['step_duration'] = r['legs'][0]['annotation']['duration']
  res['step_distance'] = r['legs'][0]['annotation']['distance']

  return res

def direction_routes(direction, additional):
  routes = api_request(direction)

  route = routes[0]
  route_alt = None
  if len(routes) > 1:
    route_alt = routes[1]
    if routes[0]['duration'] > routes[1]['duration']:
      route, route_alt = route_alt, route

  entry = additional.copy()

  entry['route'] = filter_route(route)
  entry['route_alt'] = filter_route(route_alt) if len(routes) > 1 else None

  return entry

def main(test=False, multi=False):
  departure = datetime.datetime.now().astimezone(tz=pytz.timezone('Europe/Amsterdam'))
  if departure.hour not in VALID_HOURS and not test:
    return

  directions = []
  if multi:
    for n, c in LOCS.items():
      directions.append((n, [c, WORK]))
  else:
    directions.append((None, [HOME, WORK]))

  entries = []
  for name, direction in directions:
    if departure.hour > 12:
      direction = direction[::-1]

    add_ = {
      'departure': departure.isoformat(),
      'is_weekend': departure.isoweekday() >= 6,
      'is_morning': departure.hour <= 12,
      'isoweekday': departure.isoweekday(),
      'hour': departure.hour,
      'minute': departure.minute,
    }
    if name is not None:
      add_['name']: name

    entries.append(direction_routes(direction, add_))

  res = json.dumps(entries)
  if test:
    print(res)
  else:
    log(res + '\n', 'multi.log' if multi else 'out.log')

if __name__ == '__main__':
  args = {
    'test': '--test' in sys.argv,
    'multi': '--multi' in sys.argv,
  }

  main(**args)
