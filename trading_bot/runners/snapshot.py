# -*- coding: utf-8 -*-
"""
Defines a concrete Runner object.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import json
import pycurl

from io import BytesIO
from time import time

from trading_bot.runners.base import Runner




_REST_URL = "https://www.binance.com/api"



class SnapshotRunner(Runner):
  """Runner to periodically get updated order depth snapshots from the REST
  server."""


  def on_start(self, **kwargs):
    self._last_snapshot_times = {}




  def on_update(self, **kwargs):

    if self._app_state.connection_status != "CONNECTED":
      self._last_snapshot_times = {}
      return


    for pair in set(self._app_state.trade_pairs + self._app_state.save_pairs):

      try:
        last_snapshot_time = self._last_snapshot_times[pair]
      except KeyError:
        last_snapshot_time = 0

      start_time = int(time())

      if start_time - last_snapshot_time >= self._config["depth_snapshot_interval"]:

        uri = _REST_URL + "/v1/depth?symbol=%s&limit=100" % pair.upper()

        try:
          response = BytesIO()

          curl = pycurl.Curl()
          curl.setopt(pycurl.URL, uri)
          curl.setopt(pycurl.ENCODING, "gzip")
          curl.setopt(pycurl.TIMEOUT, self._config["request_timeout"])
          curl.setopt(pycurl.HTTPHEADER, ["Accept:application/json",
                                          "Accept-encoding:gzip"])
          curl.setopt(pycurl.HTTPGET, 1)
          curl.setopt(pycurl.WRITEFUNCTION, response.write)
          curl.perform()
          status_code = curl.getinfo(pycurl.HTTP_CODE)
          curl.close()

          if status_code == 429:
            self._app_state.connection_status = "RATE_LIMITED"
            return


          response_str = response.getvalue().decode("utf-8")
          response.close()

        
          response = json.loads(response_str)
          update_id = int(response["lastUpdateId"])

          bids = {}
          for level, quantity, _ in response["bids"]:
            bids[level] = float(quantity)

          asks = {}
          for level, quantity, _ in response["asks"]:
            asks[level] = float(quantity)


          self._last_snapshot_times[pair] = int(time())

          self._app_state._bid_snapshot_queue.put_nowait((pair, update_id, bids))
          self._app_state._ask_snapshot_queue.put_nowait((pair, update_id, asks))

        except: continue  # TODO Log errors somewhere.



