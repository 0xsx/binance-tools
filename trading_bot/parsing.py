# -*- coding: utf-8 -*-
"""
Defines methods for parsing objects and data types.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import json
import numpy as np

from collections import namedtuple


_FLOAT_DTYPE = "float32"
_EPSILON = float(1e-6)




def num_str_to_int_units(num_str, precision):
  """Converts a string containing a floating-point value to an integer in
  unit amounts with the specified precision."""

  try:
    int_part, frac_part = num_str.split(".")
  except ValueError:
    int_part = num_str
    frac_part = ""
  frac_part += "0" * (precision - len(frac_part))

  return int(int_part + frac_part)





def int_units_to_num_str(int_val, precision):
  """Converts the amount integer in unit amounts to a string with a floating-point
  value at the specified precision."""

  int_units_str = str(int_val)
  if len(int_units_str) < precision + 1:
    int_units_str = ("0" * (precision + 1 - len(int_units_str))) + int_units_str

  int_part = int_units_str[:-precision]
  frac_part = int_units_str[-precision:]

  return int_part + "." + frac_part







def parse_depth_state(num_depth_bins, cur_state):
  """Parses the depth state dictionary and constructs Numpy arrays for the
  current bids and asks, reduced to the specified number of depth bins."""
  
  all_asks = []
  ask_weights = []
  total_ask_qty = 0.
  for key in cur_state["asks"]:
    all_asks.append(float(key))
    ask_weights.append(cur_state["asks"][key])
    total_ask_qty += cur_state["asks"][key]

  all_bids = []
  bid_weights = []
  total_bid_qty = 0.
  for key in cur_state["bids"]:
    all_bids.append(float(key))
    bid_weights.append(cur_state["bids"][key])
    total_bid_qty += cur_state["bids"][key]



  qty_spread = total_ask_qty - total_bid_qty


  all_asks = np.array(all_asks, dtype=_FLOAT_DTYPE)
  all_bids = np.array(all_bids, dtype=_FLOAT_DTYPE)

  ask_weights = np.array(ask_weights, dtype=_FLOAT_DTYPE)
  if ask_weights.shape[0] > 0:
    ask_weights /= (np.max(ask_weights) + _EPSILON)
    avg_ask = np.average(all_asks, weights=ask_weights)
    std_ask = np.sqrt(np.average((all_asks-avg_ask)**2, weights=ask_weights))
  else:
    avg_ask = 0.
    std_ask = 0.

  bid_weights = np.array(bid_weights, dtype=_FLOAT_DTYPE)
  if bid_weights.shape[0] > 0:
    bid_weights /= (np.max(bid_weights) + _EPSILON)
    avg_bid = np.average(all_bids, weights=bid_weights)
    std_bid = np.sqrt(np.average((all_bids-avg_bid)**2, weights=bid_weights))
  else:
    avg_bid = 0.
    std_bid = 0.


  min_ask = avg_ask - 3*std_ask
  max_ask = avg_ask + 3*std_ask
  min_bid = avg_bid - 3*std_bid
  max_bid = avg_bid + 3*std_bid

  avg_spread = avg_ask - avg_bid


  ask_bin_edges = np.linspace(min_ask, max_ask, num=num_depth_bins-1)
  bid_bin_edges = np.linspace(min_bid, max_bid, num=num_depth_bins-1)


  ask_arr = np.zeros((num_depth_bins,), dtype=_FLOAT_DTYPE)
  for i in range(all_asks.shape[0]):
    bin_ind = min(num_depth_bins-1, np.digitize(all_asks[i], ask_bin_edges))
    ask_arr[bin_ind] += ask_weights[i]
  ask_arr /= (np.max(ask_arr) + _EPSILON)

  bid_arr = np.zeros((num_depth_bins,), dtype=_FLOAT_DTYPE)
  for i in range(all_bids.shape[0]):
    bin_ind = min(num_depth_bins-1, np.digitize(all_bids[i], bid_bin_edges))
    bid_arr[bin_ind] += bid_weights[i]
  bid_arr /= (np.max(bid_arr) + _EPSILON)


  return cur_state["server_timestamp"], bid_arr, ask_arr, avg_spread, qty_spread






def parse_trade(period_time, cur_trade, bin_stats_dict):
  """Parses the trade dictionary and accumulates trade statistics for the
  next update."""

  timestamp = cur_trade["trade_timestamp"]
  time_bin = int(timestamp / float(period_time)) * period_time

  try:
    bin_stats_dict[time_bin][0].append(cur_trade["quantity"])
    bin_stats_dict[time_bin][1].append(cur_trade["price"])
  except KeyError:
    bin_stats_dict[time_bin] = ([cur_trade["quantity"]], [cur_trade["price"]])






def parse_exchange_pair_infos(exchange_info_json_str):
  """Parses the exchange info json string retrieved from the exchange server and
  returns a dictionary of pair info objects describing trading pair parameters."""

  PairInfo = namedtuple("PairInfo", ["base_symbol", "quote_symbol", "base_precision",
                                     "base_step_size", "min_base_qty", "max_base_qty",
                                     "quote_precision", "quote_step_size",
                                     "min_quote_price", "max_quote_price",
                                     "min_notational_product"])

  exchange_info = json.loads(exchange_info_json_str)

  pair_infos = {}

  for trading_symbol in exchange_info["symbols"]:
    symbol_pair = trading_symbol["symbol"].lower()

    if trading_symbol["status"] == "TRADING":
      assert "LIMIT" in trading_symbol["orderTypes"]

      base_symbol = trading_symbol["baseAsset"].lower()
      base_precision = int(trading_symbol["baseAssetPrecision"])
      quote_symbol = trading_symbol["quoteAsset"].lower()
      quote_precision = int(trading_symbol["quotePrecision"])

      base_step_size = None
      min_base_qty = None
      max_base_qty = None
      quote_step_size = None
      min_quote_price = None
      max_quote_price = None
      min_notational_product = None

      for trade_filter in trading_symbol["filters"]:
        if trade_filter["filterType"] == "PRICE_FILTER":
          min_price_str = trade_filter["minPrice"]
          max_price_str = trade_filter["maxPrice"]
          step_size_str = trade_filter["tickSize"]
          min_quote_price = num_str_to_int_units(min_price_str, quote_precision)
          max_quote_price = num_str_to_int_units(max_price_str, quote_precision)
          quote_step_size = num_str_to_int_units(step_size_str, quote_precision)

        elif trade_filter["filterType"] == "LOT_SIZE":
          min_qty_str = trade_filter["minQty"]
          max_qty_str = trade_filter["maxQty"]
          step_size_str = trade_filter["stepSize"]
          min_base_qty = num_str_to_int_units(min_qty_str, base_precision)
          max_base_qty = num_str_to_int_units(max_qty_str, base_precision)
          base_step_size = num_str_to_int_units(step_size_str, base_precision)

        elif trade_filter["filterType"] == "MIN_NOTIONAL":
          min_notational_str = trade_filter["minNotional"]
          min_notational_product = num_str_to_int_units(min_notational_str,
                                                        quote_precision + base_precision)

      assert base_step_size is not None
      assert min_base_qty is not None
      assert max_base_qty is not None
      assert quote_step_size is not None
      assert min_quote_price is not None
      assert max_quote_price is not None
      assert min_notational_product is not None

      pair_info = PairInfo(base_symbol, quote_symbol, base_precision, base_step_size,
                           min_base_qty, max_base_qty, quote_precision, quote_step_size,
                           min_quote_price, max_quote_price, min_notational_product)

      pair_infos[symbol_pair] = pair_info



  return pair_infos




def parse_account_balance_info(account_info_json_str, balance_precision):
  """Parses the account info json string from the exchange server and returns
  account balances."""

  account_info = json.loads(account_info_json_str)

  free_balances = {}
  locked_balances = {}

  assert account_info["canTrade"]

  for balance in account_info["balances"]:
    asset = balance["asset"].lower()
    free_balances[asset] = num_str_to_int_units(balance["free"], balance_precision)
    locked_balances[asset] = num_str_to_int_units(balance["locked"], balance_precision)

  return free_balances, locked_balances











