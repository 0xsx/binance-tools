# -*- coding: utf-8 -*-
"""
Defines the base class for asynchronous runners.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



class Runner(object):
  """Base class for asynchronously executed logic."""

  def __init__(self, app_state, config, **kwargs):
    self._app_state = app_state
    self._config = config

  def on_start(self, **kwargs):
    raise NotImplementedError

  def on_update(self, **kwargs):
    raise NotImplementedError

  