#!/usr/bin/env python

import os
import sys
import datetime
import json
import argparse

import pytz
import requests

class Config:
  def __init__(self, path):
    path = os.path.join(os.path.dirname(__file__), path)
    with open(path, 'r') as fp:
      data = json.load(fp)

      self.tz = pytz.timezone(data['timezone'])
      self.days = data['days']
      self.departs = data['departure_hours']
      self.returns = data['return_hours']
      self.work = data['work']
      self.locs = data['locations']

class Commute:
  log_path = None
  mapbox_token = None
  config = None
  test_mode = None

  def __init__(self, log_path, mapbox_token_path, config_path, test_mode):
    self.test_mode = test_mode
    self.log_path = log_path

    try:
      path = os.path.join(os.path.dirname(__file__), mapbox_token_path)
      with open(path, 'r') as fp:
        self.mapbox_token = fp.read().strip()
    except Exception:
      print(f'cannot read {mapbox_token_path}, must be manually added, see readme', file=sys.stderr)
      sys.exit(1)

    self.config = Config(config_path)

  def log(self, line):
    path = os.path.join(os.path.dirname(__file__), self.log_path)
    with open(path, 'a') as f:
      f.write(line)

  def api_request(self, coordinates):
    url = 'https://api.mapbox.com/directions/v5/mapbox/driving-traffic/'
    url += ';'.join([','.join([str(x) for x in coords]) for coords in coordinates])
    url += '?access_token=' + self.mapbox_token
    url += '&alternatives=true'
    url += '&annotations=distance,duration,congestion_numeric,closure'
    url += '&overview=full'
    url += '&geometries=geojson'

    resp = requests.get(url)

    if resp.status_code != 200:
      raise Exception(f'Failed api request: {resp.status_code}, {resp.text}')

    json_ = resp.json()
    return json_['routes']

  @staticmethod
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

  def direction_routes(self, direction, additional):
    routes = self.api_request(direction)

    route = routes[0]
    route_alt = None
    if len(routes) > 1:
      route_alt = routes[1]
      if routes[0]['duration'] > routes[1]['duration']:
        route, route_alt = route_alt, route

    entry = additional.copy()

    entry['route'] = Commute.filter_route(route)
    entry['route_alt'] = self.filter_route(route_alt) if len(routes) > 1 else None

    return entry

  def main(self):
    departure = datetime.datetime.now().astimezone(tz=self.config.tz)
    dt_valid = departure.isoweekday() in self.config.days and \
               (departure.hour in self.config.departs or departure.hour in self.config.returns)
    if not dt_valid and not self.test_mode:
      return

    directions = []
    for n, c in self.config.locs.items():
      directions.append((n, [c, self.config.work]))

    entries = []
    for name, direction in directions:
      if departure.hour in self.config.returns:
        direction = direction[::-1]

      add_ = {
        'departure': departure.isoformat(),
        'is_morning': departure.hour in self.config.departs,
        'isoweekday': departure.isoweekday(),
        'hour': departure.hour,
        'minute': departure.minute,
      }
      if name is not None:
        add_['name']: name

      entries.append(self.direction_routes(direction, add_))

    res = json.dumps(entries)
    if self.test_mode:
      print(res)
    else:
      self.log(res + '\n')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='Commute', description='analyze traffic for possible commutes')
  parser.add_argument('--test', action='store_true', help='output to terminal instead of log')
  parser.add_argument('--log', default='out/out.log', metavar='PATH', help='file where results are stored')
  parser.add_argument('--mapbox-token', default='mapbox_token.txt', metavar='PATH', help='file containing mapbox token')
  parser.add_argument('--config', default='config.json', metavar='PATH', help='configuration file path')

  args = parser.parse_args()

  comm = Commute(args.log, args.mapbox_token, args.config, args.test)
  comm.main()
