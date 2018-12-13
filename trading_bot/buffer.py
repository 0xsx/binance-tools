# -*- coding: utf-8 -*-
"""
Defines a class for buffering real time trade stream features.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



import numpy as np



_EPSILON = float(1e-6)
_FLOAT_DTYPE = "float32"



# Number of price bins for normalizing and discretizing depth snapshots.
_NUM_DEPTH_BINS = 16

  

# Parameters for technical indicator signals.
_DAYS_SHORT = 9
_DAYS_MED = 14
_DAYS_LONG = 26


_NUM_FEAT_PERIODS = 24



class RealtimeTradeStreamBuffer(object):
  """Models a stream of real time trading data with trading periods updated at
  regular, evenly-spaced intervals. Stream features are buffered over a
  window of recent history."""


  def __init__(self):
    self._last_order_book_timestamp = 0
    self._last_period_timestamp = 0

    self._last_avg_spread = 0.
    self._last_qty_spread = 0.

    self._last_bids = None
    self._last_asks = None

    self._cur_buffered_periods = 0
    


    self._bid_window = np.zeros((_NUM_DEPTH_BINS, _NUM_DEPTH_BINS),
                                dtype=_FLOAT_DTYPE)
    self._ask_window = np.zeros((_NUM_DEPTH_BINS, _NUM_DEPTH_BINS),
                                dtype=_FLOAT_DTYPE)


    self._num_feats = len(self.get_feat_labels())
    self._feats_window = np.zeros((_NUM_FEAT_PERIODS, self._num_feats),
                                  dtype=_FLOAT_DTYPE)



    self._days_short = _DAYS_SHORT
    self._ema_alpha_short = 2. / (self._days_short + 1)

    self._days_med = _DAYS_MED
    self._ema_alpha_med = 2. / (self._days_med + 1)

    self._days_long = _DAYS_LONG
    self._ema_alpha_long = 2. / (self._days_long + 1)


    self._price_ema_short = 0.
    self._price_ema_med = 0.
    self._price_ema_long = 0.

    self._up_avg_ema_short = 0.
    self._up_avg_ema_med = 0.
    self._up_avg_ema_long = 0.
    self._down_avg_ema_short = 0.
    self._down_avg_ema_med = 0.
    self._down_avg_ema_long = 0.

    self._pos_dir_ema_short = 0.
    self._pos_dir_ema_med = 0.
    self._pos_dir_ema_long = 0.
    self._neg_dir_ema_short = 0.
    self._neg_dir_ema_med = 0.
    self._neg_dir_ema_long = 0.

    self._tr_ema_short = 0.
    self._tr_ema_med = 0.
    self._tr_ema_long = 0.

    self._adx_ema_short = 0.
    self._adx_ema_med = 0.
    self._adx_ema_long = 0.


    self._num_buffer_periods = int(3.45 * (self._days_long + 1)) + 1

    self._price_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)
    self._quantity_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)

    self._lows_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)
    self._highs_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)

    self._up_avg_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)
    self._down_avg_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)

    self._pos_dir_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)
    self._neg_dir_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)

    self._tr_buffer = np.zeros((self._num_buffer_periods,), dtype=_FLOAT_DTYPE)



  def update_order_book(self, server_timestamp, bid_arr, ask_arr, avg_spread,
                        qty_spread):
    """Updates the stream buffer with the given order book data."""

    self._last_order_book_timestamp = server_timestamp
    self._last_avg_spread = avg_spread
    self._last_qty_spread = qty_spread

    self._bid_window[:-1, :] = self._bid_window[1:, :]
    self._bid_window[-1, :] = bid_arr

    self._ask_window[:-1, :] = self._ask_window[1:, :]
    self._ask_window[-1, :] = ask_arr



  def get_feat_labels(self):
    """Returns a list of strings containing labels for the feature window columns."""

    return ["price", "quantity", "orderbook_avg_spread", "orderbook_qty_spread",
            "percent_range_short", "percent_range_med", "percent_range_long", # Williams %R
            "rsi_short", "rsi_med", "rsi_long", "adx_short", "adx_med", "adx_long",
            "macd_short_med", "macd_short_long", "macd_med_long"]




  def _compute_features(self, feats_arr):
    """Computes all features for the latest period from all buffered
    periods and order books into the specified features array."""

    highest_high_short = np.max(self._highs_buffer[-self._days_short:])
    highest_high_med = np.max(self._highs_buffer[-self._days_med:])
    highest_high_long = np.max(self._highs_buffer[-self._days_long:])

    lowest_low_short = np.min(self._lows_buffer[-self._days_short:])
    lowest_low_med = np.min(self._lows_buffer[-self._days_med:])
    lowest_low_long = np.min(self._lows_buffer[-self._days_long:])

    percent_range_short = ((highest_high_short - self._price_buffer[-1])
                           / (highest_high_short - lowest_low_short + _EPSILON) * -100.)
    percent_range_med = ((highest_high_med - self._price_buffer[-1])
                           / (highest_high_med - lowest_low_med + _EPSILON) * -100.)
    percent_range_long = ((highest_high_long - self._price_buffer[-1])
                           / (highest_high_long - lowest_low_long + _EPSILON) * -100.)


    rsi_short = 100. - 100. / (1.+self._up_avg_ema_short/(self._down_avg_ema_short + _EPSILON))
    rsi_med = 100. - 100. / (1.+self._up_avg_ema_med/(self._down_avg_ema_med + _EPSILON))
    rsi_long = 100. - 100. / (1.+self._up_avg_ema_long/(self._down_avg_ema_long + _EPSILON))


    pos_di_short = 100. * self._pos_dir_ema_short / (self._tr_ema_short + _EPSILON)
    neg_di_short = 100. * self._neg_dir_ema_short / (self._tr_ema_short + _EPSILON)
    pos_di_med = 100. * self._pos_dir_ema_med / (self._tr_ema_med + _EPSILON)
    neg_di_med = 100. * self._neg_dir_ema_med / (self._tr_ema_med + _EPSILON)
    pos_di_long = 100. * self._pos_dir_ema_long / (self._tr_ema_long + _EPSILON)
    neg_di_long = 100. * self._neg_dir_ema_long / (self._tr_ema_long + _EPSILON)

    cur_adx_short = np.abs(pos_di_short - neg_di_short) / (pos_di_short + neg_di_short + _EPSILON)
    cur_adx_med = np.abs(pos_di_med - neg_di_med) / (pos_di_med + neg_di_med + _EPSILON)
    cur_adx_long = np.abs(pos_di_long - neg_di_long) / (pos_di_long + neg_di_long + _EPSILON)

    self._adx_ema_short = self._adx_ema_short + (self._ema_alpha_short
                            * (cur_adx_short - self._adx_ema_short))
    self._adx_ema_med = self._adx_ema_med + (self._ema_alpha_med
                            * (cur_adx_med - self._adx_ema_med))
    self._adx_ema_long = self._adx_ema_long + (self._ema_alpha_long
                            * (cur_adx_long - self._adx_ema_long))


    feats_arr[0] = self._price_buffer[-1]
    feats_arr[1] = self._quantity_buffer[-1]
    feats_arr[2] = self._last_avg_spread
    feats_arr[3] = self._last_qty_spread

    feats_arr[4] = percent_range_short
    feats_arr[5] = percent_range_med
    feats_arr[6] = percent_range_long

    feats_arr[7] = rsi_short
    feats_arr[8] = rsi_med
    feats_arr[9] = rsi_long

    feats_arr[10] = self._adx_ema_short * 100.
    feats_arr[11] = self._adx_ema_med * 100.
    feats_arr[12] = self._adx_ema_long * 100.

    feats_arr[13] = self._price_ema_short - self._price_ema_med
    feats_arr[14] = self._price_ema_short - self._price_ema_long
    feats_arr[15] = self._price_ema_med - self._price_ema_long

    




  def update_trade_period(self, server_period_timestamp, total_quantity,
                          total_num_trades, avg_price, low_price, high_price):
    """Updates the stream buffer with the given trading period data."""

    self._last_period_timestamp = server_period_timestamp

    last_avg = self._price_buffer[-1]
    last_low = self._lows_buffer[-1]
    last_high = self._highs_buffer[-1]


    # Update trade buffers.
    self._price_buffer[:-1] = self._price_buffer[1:]
    self._quantity_buffer[:-1] = self._quantity_buffer[1:]
    self._lows_buffer[:-1] = self._lows_buffer[1:]
    self._highs_buffer[:-1] = self._highs_buffer[1:]
    self._up_avg_buffer[:-1] = self._up_avg_buffer[1:]
    self._down_avg_buffer[:-1] = self._down_avg_buffer[1:]
    self._pos_dir_buffer[:-1] = self._pos_dir_buffer[1:]
    self._neg_dir_buffer[:-1] = self._neg_dir_buffer[1:]
    self._tr_buffer[:-1] = self._tr_buffer[1:]

    self._price_buffer[-1] = avg_price
    self._quantity_buffer[-1] = total_quantity
    self._lows_buffer[-1] = low_price
    self._highs_buffer[-1] = high_price
    self._tr_buffer[-1] = np.max([high_price - low_price,
                                  np.abs(high_price - last_avg),
                                  np.abs(low_price - last_avg)])

    if avg_price > last_avg:
      self._up_avg_buffer[-1] = avg_price - last_avg
      self._down_avg_buffer[-1] = 0
    else:
      self._up_avg_buffer[-1] = 0
      self._down_avg_buffer[-1] = last_avg - avg_price
    

    up_move = high_price - last_high
    down_move = last_low - low_price

    if up_move > down_move and up_move > 0:
      self._pos_dir_buffer[-1] = up_move
    else:
      self._pos_dir_buffer[-1] = 0

    if down_move > up_move and down_move > 0:
      self._neg_dir_buffer[-1] = down_move
    else:
      self._neg_dir_buffer[-1] = 0



    # Update exponential moving averages.
    self._price_ema_short = self._price_ema_short + (self._ema_alpha_short
                              * (self._price_buffer[-1] - self._price_ema_short))
    self._price_ema_med = self._price_ema_med + (self._ema_alpha_med
                            * (self._price_buffer[-1] - self._price_ema_med))
    self._price_ema_long = self._price_ema_long + (self._ema_alpha_long
                             * (self._price_buffer[-1] - self._price_ema_long))

    self._up_avg_ema_short = self._up_avg_ema_short + (self._ema_alpha_short
                               * (self._up_avg_buffer[-1] - self._up_avg_ema_short))
    self._up_avg_ema_med = self._up_avg_ema_med + (self._ema_alpha_med
                             * (self._up_avg_buffer[-1] - self._up_avg_ema_med))
    self._up_avg_ema_long = self._up_avg_ema_long + (self._ema_alpha_long
                              * (self._up_avg_buffer[-1] - self._up_avg_ema_long))
    self._down_avg_ema_short = self._down_avg_ema_short + (self._ema_alpha_short
                                 * (self._down_avg_buffer[-1] - self._down_avg_ema_short))
    self._down_avg_ema_med = self._down_avg_ema_med + (self._ema_alpha_med
                               * (self._down_avg_buffer[-1] - self._down_avg_ema_med))
    self._down_avg_ema_long = self._down_avg_ema_long + (self._ema_alpha_long
                                * (self._down_avg_buffer[-1] - self._down_avg_ema_long))

    self._pos_dir_ema_short = self._pos_dir_ema_short + (self._ema_alpha_short
                                * (self._pos_dir_buffer[-1] - self._pos_dir_ema_short))
    self._pos_dir_ema_med = self._pos_dir_ema_med + (self._ema_alpha_med
                              * (self._pos_dir_buffer[-1] - self._pos_dir_ema_med))
    self._pos_dir_ema_long = self._pos_dir_ema_long + (self._ema_alpha_long
                               * (self._pos_dir_buffer[-1] - self._pos_dir_ema_long))
    self._neg_dir_ema_short = self._neg_dir_ema_short + (self._ema_alpha_short
                                * (self._neg_dir_buffer[-1] - self._neg_dir_ema_short))
    self._neg_dir_ema_med = self._neg_dir_ema_med + (self._ema_alpha_med
                              * (self._neg_dir_buffer[-1] - self._neg_dir_ema_med))
    self._neg_dir_ema_long = self._neg_dir_ema_long + (self._ema_alpha_long
                               * (self._neg_dir_buffer[-1] - self._neg_dir_ema_long))

    self._tr_ema_short = self._tr_ema_short + (self._ema_alpha_short
                           * (self._tr_buffer[-1] - self._tr_ema_short))
    self._tr_ema_med = self._tr_ema_med + (self._ema_alpha_med
                         * (self._tr_buffer[-1] - self._tr_ema_med))
    self._tr_ema_long = self._tr_ema_long + (self._ema_alpha_long
                          * (self._tr_buffer[-1] - self._tr_ema_long))





    # Update feature vector window.
    self._feats_window[:-1, :] = self._feats_window[1:, :]
    self._compute_features(self._feats_window[-1, :])


    # Increment count of buffered periods only if orderbook is also already set.
    if (self._last_order_book_timestamp > 0
        and self._cur_buffered_periods < self._num_buffer_periods):
      self._cur_buffered_periods += 1







  def get_features_window(self):
    """Returns a tuple containing the latest server timestamp and a
    reference to the multidimensional array storing all features of the current
    feature window, if the trading period buffer is full. Otherwise, returns `None`."""

    if self._cur_buffered_periods >= self._num_buffer_periods:
      return (self._last_period_timestamp, self._feats_window,
              self._bid_window, self._ask_window)

    return None






