# -*- coding: utf-8 -*-
"""
Defines a class for predicting trade position changes.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function




import numpy as np




_EPSILON = float(1e-6)
_FLOAT_DTYPE = "float32"




class TradePredictionModel(object):
  """Encapsulates a prediction model for determining whether to buy or
  sell based on features from trading signals."""


  def __init__(self, pair):

    pass



  def unload(self):
    pass




  def predict_buy(self, timestamp, feats_window, bid_window, ask_window):
    """Returns a probability distribution over two states: state 0 means
    hold and state 1 means buy."""

    return np.array([.5, .5], dtype=_FLOAT_DTYPE)



  def predict_sell(self, timestamp, feats_window, bid_window, ask_window):
    """Returns a probability distribution over two states: state 0 means
    hold and state 1 means sell."""

    return np.array([.5, .5], dtype=_FLOAT_DTYPE)






