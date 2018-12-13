# -*- coding: utf-8 -*-
"""
Defines a concrete Runner object.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


try:
  import Queue as queue
except ImportError:
  import queue


from time import time

from trading_bot.runners.base import Runner





_MAX_EVENT_BUFFER_SIZE = 100






class OrderBookRunner(Runner):
  """Runner to maintain and broadcast the current state of the bid and ask
  orderbook depths. Applies depth events to depth snapshots and pushes
  the current state to the orderbook queue."""


  def on_start(self, **kwargs):
    self._bid_events = {}
    self._ask_events = {}
    self._cur_bid_depths = {}
    self._cur_ask_depths = {}
    self._last_post_time = 0




  def on_update(self, **kwargs):

    if self._app_state.connection_status != "CONNECTED":
      self.on_start()
      return



    # Empty depth event queues and organize by symbol pair.
    try:
      while True:
        bid_updates = self._app_state._bid_depth_event_queue.get_nowait()
        pair = bid_updates[0]
        try:
          self._bid_events[pair].append(bid_updates)
        except KeyError:
          self._bid_events[pair] = [bid_updates]
    except queue.Empty: pass

    try:
      while True:
        ask_updates = self._app_state._ask_depth_event_queue.get_nowait()
        pair = ask_updates[0]
        try:
          self._ask_events[pair].append(ask_updates)
        except KeyError:
          self._ask_events[pair] = [ask_updates]
    except queue.Empty: pass

    for pair in self._bid_events:
      if len(self._bid_events[pair]) > _MAX_EVENT_BUFFER_SIZE:
        self._bid_events[pair] = self._bid_events[pair][-_MAX_EVENT_BUFFER_SIZE:]

    for pair in self._ask_events:
      if len(self._ask_events[pair]) > _MAX_EVENT_BUFFER_SIZE:
        self._ask_events[pair] = self._ask_events[pair][-_MAX_EVENT_BUFFER_SIZE:]





    # Update each symbol pair to the latest depth snapshots.
    try:
      while True:
        pair, update_id, bids = self._app_state._bid_snapshot_queue.get_nowait()
        self._cur_bid_depths[pair] = (update_id, bids)
    except queue.Empty: pass

    try:
      while True:
        pair, update_id, asks = self._app_state._ask_snapshot_queue.get_nowait()
        self._cur_ask_depths[pair] = (update_id, asks)
    except queue.Empty: pass





    # Update and post current orderbooks if time interval has passed.
    cur_time = int(time())

    if cur_time - self._last_post_time >= self._config["orderbook_interval"]:
      self._last_post_time = cur_time

      for pair in set(self._app_state.trade_pairs + self._app_state.save_pairs):

        # Update current bids.
        try:
          update_id, bids = self._cur_bid_depths[pair]
          bid_events = self._bid_events[pair]
        except KeyError:
          update_id = 0
          bids = {}
          bid_events = []

        first_ind = len(bid_events)
        for i in range(len(bid_events)):
          _, min_update_id, max_update_id, bid_updates = bid_events[i]

          if min_update_id >= update_id:
            if i < first_ind:
              first_ind = i

            if max_update_id <= update_id:
              bids.update(bid_updates)

        self._bid_events[pair] = bid_events[first_ind:]

        # Update current asks.
        try:
          update_id, asks = self._cur_ask_depths[pair]
          ask_events = self._ask_events[pair]
        except KeyError:
          update_id = 0
          asks = {}
          ask_events = []

        first_ind = len(ask_events)
        for i in range(len(ask_events)):
          _, min_update_id, max_update_id, ask_updates = ask_events[i]

          if min_update_id >= update_id:
            if i < first_ind:
              first_ind = i

            if max_update_id <= update_id:
              asks.update(ask_updates)

        self._ask_events[pair] = ask_events[first_ind:]


        # Post depth state.
        cur_state = {}
        cur_state["server_timestamp"] = self._app_state.server_time
        cur_state["asks"] = asks
        cur_state["bids"] = bids

        self._app_state._orderbook_state_queue.put_nowait((pair, cur_state))







    




