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


import gzip
import json
import numpy as np
import os

from trading_bot.buffer import RealtimeTradeStreamBuffer
from trading_bot.parsing import parse_depth_state, parse_trade
from trading_bot.prediction import TradePredictionModel
from trading_bot.runners.base import Runner


_EPSILON = float(1e-6)
_FLOAT_DTYPE = "float32"




class AnalysisRunner(Runner):
  """Runner to analyze the current trades and orderbook to determine whether
  trades should be executed."""


  def on_start(self, **kwargs):
    self._last_closed_time_bin = 0
    self._time_bin_stats = {}
    self._realtime_streams = {}
    self._last_avg_prices = {}
    self._trade_models = {}
    self._buy_probs_histories = {}
    self._sell_probs_histories = {}




  def on_update(self, **kwargs):

    if self._app_state.connection_status != "CONNECTED":
      self.on_start()
      return



    # Empty trades queue and collect time bin stats.
    try:
      while True:
        pair, cur_trade = self._app_state._trade_queue.get_nowait()

        if pair in self._app_state.save_pairs:
          # Save trade data.
          connect_time = self._app_state.connect_time
          out_dir = os.path.join(self._config["data_store_dir"], "%d" % connect_time)
          out_file = os.path.join(out_dir, "%d_%s_trades.txt.gz" % (connect_time, pair))
          try:
            os.makedirs(out_dir)
          except OSError: pass
          with gzip.open(out_file, "ab") as f_out:
            f_out.write(b"%s\n" % json.dumps(cur_trade).encode("utf-8"))


        if pair in self._app_state.trade_pairs:
          try:
            bin_stats_dict = self._time_bin_stats[pair]
          except KeyError:
            bin_stats_dict = {}
            self._time_bin_stats[pair] = bin_stats_dict
          parse_trade(self._config["period_time"], cur_trade, bin_stats_dict)

    except queue.Empty: pass



    # Empty orderbook queue and update each realtime stream's orderbook records.
    try:
      while True:
        pair, cur_state = self._app_state._orderbook_state_queue.get_nowait()

        if pair in self._app_state.save_pairs:
          # Save depth data.
          connect_time = self._app_state.connect_time
          out_dir = os.path.join(self._config["data_store_dir"], "%d" % connect_time)
          out_file = os.path.join(out_dir, "%d_%s_depth.txt.gz" % (connect_time, pair))
          try:
            os.makedirs(out_dir)
          except OSError: pass
          with gzip.open(out_file, "ab") as f_out:
            f_out.write(b"%s\n" % json.dumps(cur_state).encode("utf-8"))

        if pair in self._app_state.trade_pairs:
          tup = parse_depth_state(self._config["num_depth_bins"], cur_state)

          try:
            realtime_stream = self._realtime_streams[pair]
          except KeyError:
            realtime_stream = RealtimeTradeStreamBuffer()
            self._realtime_streams[pair] = realtime_stream

          realtime_stream.update_order_book(*tup)
        
    except queue.Empty: pass



    # Close all time bins before the current open one and update each realtime
    # streams trade period records.
    cur_time_bin = (int(self._app_state.server_time
                        / float(self._config["period_time"]))
                    * self._config["period_time"])
    last_time_bin = cur_time_bin - int(self._config["period_time"])

    
    if last_time_bin > self._last_closed_time_bin:
      self._last_closed_time_bin = last_time_bin

      for pair in self._time_bin_stats:
        bin_stats = self._time_bin_stats[pair]

        try:
          realtime_stream = self._realtime_streams[pair]
        except KeyError:
          realtime_stream = RealtimeTradeStreamBuffer()
          self._realtime_streams[pair] = realtime_stream

        did_close = False
        for stats_time_bin in sorted(bin_stats.keys()):
          if stats_time_bin > last_time_bin:
            break

          total_quantity = np.sum(bin_stats[stats_time_bin][0])
          total_num_trades = len(bin_stats[stats_time_bin][0])
          weights = np.array(bin_stats[stats_time_bin][0]) / total_quantity
          avg_price = np.sum(np.array(bin_stats[stats_time_bin][1]) * weights)
          low_price = np.min(bin_stats[stats_time_bin][1])
          high_price = np.max(bin_stats[stats_time_bin][1])
          self._last_avg_prices[pair] = avg_price
          realtime_stream.update_trade_period(stats_time_bin, total_quantity,
                                              total_num_trades, avg_price,
                                              low_price, high_price)

          del bin_stats[stats_time_bin]
          did_close = True

        if not did_close:
          try:
            last_avg_price = self._last_avg_prices[pair]
          except KeyError:
            last_avg_price = 0
          total_quantity = 0.
          total_num_trades = 0
          avg_price = last_avg_price
          low_price = last_avg_price
          high_price = last_avg_price
          realtime_stream.update_trade_period(last_time_bin, total_quantity,
                                              total_num_trades, avg_price,
                                              low_price, high_price)



    # Unload any prediction models that are no longer needed.
    to_delete = set()
    for pair in self._trade_models:
      if pair not in self._app_state.trade_pairs:
        to_delete.add(pair)
    for pair in to_delete:
      self._trade_models[pair].unload()
      del self._trade_models[pair]





    # Analyze stream features and determine whether to trade at this instant.
    for pair in self._app_state.trade_pairs:

      try:
        realtime_stream = self._realtime_streams[pair]
      except KeyError:
        realtime_stream = RealtimeTradeStreamBuffer()
        self._realtime_streams[pair] = realtime_stream

      try:
        trade_model = self._trade_models[pair]
      except KeyError:
        trade_model = TradePredictionModel(pair)
        self._trade_models[pair] = trade_model


      feats_tup = realtime_stream.get_features_window()
      if feats_tup is not None:
        buy_probs = trade_model.predict_buy(*feats_tup)
        sell_probs = trade_model.predict_sell(*feats_tup)
      else:
        buy_probs = np.array([0.5, 0.5], dtype=_FLOAT_DTYPE)
        sell_probs = np.array([0.5, 0.5], dtype=_FLOAT_DTYPE)


      try:
        self._buy_probs_histories[pair][:-1] = self._buy_probs_histories[pair][1:]
        self._buy_probs_histories[pair][-1] = buy_probs
      except KeyError:
        self._buy_probs_histories[pair] = np.zeros((self._config["trade_history_length"], 2),
                                                   dtype=_FLOAT_DTYPE) + 0.5

      try:
        self._sell_probs_histories[pair][:-1] = self._sell_probs_histories[pair][1:]
        self._sell_probs_histories[pair][-1] = sell_probs
      except KeyError:
        self._sell_probs_histories[pair] = np.zeros((self._config["trade_history_length"], 2),
                                                    dtype=_FLOAT_DTYPE) + 0.5


    # Broadcast trade events for which the joint probability over all
    # history windows exceeds the defined threshold.
    for pair in self._app_state.trade_pairs:
      probs = np.prod(self._buy_probs_histories[pair], axis=0)
      probs /= (np.sum(probs) + _EPSILON)

      if probs[1] >= self._config["buy_threshold"]:
        # TODO broadcast buy event and timestamp and pair
        pass

      probs = np.prod(self._sell_probs_histories[pair], axis=0)
      probs /= (np.sum(probs) + _EPSILON)

      if probs[1] >= self._config["sell_threshold"]:
        # TODO broadcast sell event and timestamp and pair
        pass



