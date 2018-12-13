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



from trading_bot.runners.base import Runner





class TradeExecutorRunner(Runner):
  """Runner to execute and manage trade orders."""


  def on_start(self, **kwargs):
    pass




  def on_update(self, **kwargs):

    if self._app_state.connection_status != "CONNECTED":
      self.on_start()
      return





