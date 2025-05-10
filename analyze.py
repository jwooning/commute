#!/usr/bin/env python

import os
import sys
import json
import datetime
import itertools
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use('tkagg')
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from main import load_locations

LOG_DIR = 'out'
DAYS = [None, 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saterday', 'sunday']

NestedDict = lambda: defaultdict(NestedDict)

def parse_data():
  res = NestedDict()

  path = os.path.join(os.path.dirname(__file__), LOG_DIR, 'out.log')
  with open(path, 'r') as f:
    for i, l in enumerate(f):
      try:
        json_ = json.loads(l)
      except Exception:
        print(f'JSON parse error on line {i+1}')
        raise

      locations = load_locations()

      assert len(json_) == len(locations['locations'])
      for i, e in enumerate(json_):
        if e['is_weekend']:
          continue

        name = list(locations['locations'].keys())[i]
        morning = 'morning' if e['is_morning'] else 'afternoon'
        day = e['isoweekday']
        time = datetime.datetime(year=1970, month=1, day=1, hour=e['hour'], minute=e['minute'])

        if isinstance(res[name][morning][time], defaultdict):
          res[name][morning][time] = []

        duration = e['route']['duration']

        res[name][morning][time].append(duration)

  return res

def analyze():
  data = parse_data()

  ymin = float('inf')
  ymax = float('-inf')
  for v in data.values():
    for vv in v.values():
      for vvv in vv.values():
        ymin = min(ymin, *vvv)
        ymax = max(ymax, *vvv)

  ymin -= 30
  ymax += 30

  if len(data) == 2:
    fig, axes = plt.subplots(1, 2)
    axes = [axes]
  elif len(data) in [7, 8]:
    fig, axes = plt.subplots(2, 4)
  else:
    raise ValueError()

  for idx, (k, v) in enumerate(data.items()):
    i = idx % 4
    j = idx // 4
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
  analyze()
