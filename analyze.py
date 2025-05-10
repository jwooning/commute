#!/usr/bin/env python

import os
import json
import datetime
import argparse
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use('tkagg')
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from main import Commute

NestedDict = lambda: defaultdict(NestedDict)

class CommuteAnalyze:
  log_path = None

  work = None
  locs = None

  def __init__(self, log_path, locations_path):
    self.log_path = log_path

    self.work, self.locs = Commute.load_locations(locations_path)

  def parse_data(self):
    res = NestedDict()

    path = os.path.join(os.path.dirname(__file__), self.log_path)
    with open(path, 'r') as f:
      for i, l in enumerate(f):
        try:
          json_ = json.loads(l)
        except Exception:
          print(f'JSON parse error on line {i+1}')
          raise

        assert len(json_) == len(self.locs)
        for i, e in enumerate(json_):
          if e['is_weekend']:
            continue

          name = list(self.locs.keys())[i]
          morning = 'morning' if e['is_morning'] else 'afternoon'
          day = e['isoweekday']
          time = datetime.datetime(year=1970, month=1, day=1, hour=e['hour'], minute=e['minute'])

          if isinstance(res[name][morning][time], defaultdict):
            res[name][morning][time] = []

          duration = e['route']['duration']

          res[name][morning][time].append(duration)

    return res

  def analyze(self):
    data = self.parse_data()

    ymin = float('inf')
    ymax = float('-inf')
    for v in data.values():
      for vv in v.values():
        for vvv in vv.values():
          ymin = min(ymin, *vvv)
          ymax = max(ymax, *vvv)

    ymin -= 30
    ymax += 30

    ncols = int(np.ceil(np.sqrt(len(data))))
    nrows = int(np.ceil(len(data) / ncols))
    fig, axes = plt.subplots(nrows, ncols)
    if nrows == 1:
      axes = [axes]

    for idx, (k, v) in enumerate(data.items()):
      i = idx % ncols
      j = idx // ncols
      axes[j][i].set_title(k)

      for kk, vv in sorted(v.items(), key=lambda x: x[0]):
        vv = {kkk: vvv for kkk, vvv in sorted(vv.items(), key=lambda x: x[0])}
        yy = [np.mean(x)/60 for x in vv.values()]
        yyminerr = [np.std(x)/60 for x in vv.values()]
        yymaxerr = [np.std(x)/60 for x in vv.values()]

        axes[j][i].errorbar(list(vv.keys()), yy, yerr=(yyminerr, yymaxerr), label=kk)
        axes[j][i].set_xticklabels([x.strftime('%H:%M') for x in vv.keys()])
        axes[j][i].get_xaxis().set_major_formatter(mdates.DateFormatter('%H:%M'))
        axes[j][i].get_xaxis().set_major_locator(mdates.DayLocator())
        axes[j][i].set_ylim(ymin/60, ymax/60)
        axes[j][i].get_yaxis().set_visible(True)
        axes[j][i].grid(visible=True, which='major', axis='y')

        plt.setp(axes[j][i].xaxis.get_majorticklabels(), rotation=30)

      axes[j][i].legend()

    for ax in fig.get_axes():
      ax.label_outer()

    plt.show()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='CommuteAnalyze', description='analyze traffic for possible commutes')
  parser.add_argument('--log', default='out/out.log', metavar='PATH', help='file where results are stored')
  parser.add_argument('--locations', default='locations.json', metavar='PATH', help='file containing locations')

  args = parser.parse_args()

  comm = CommuteAnalyze(args.log, args.locations)
  comm.analyze()
