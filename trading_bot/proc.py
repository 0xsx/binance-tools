# -*- coding: utf-8 -*-
"""
Defines a class for buffering real time trade stream features.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import multiprocessing
import traceback

from time import sleep



class AsyncRunnerProcess(multiprocessing.Process):
  """Implements a multiprocessing Process object that asynchronously executes a
  `Runner` object specified by the instantiating caller."""


  def __init__(self, app_state, config, runner_cls, **kwargs):
    multiprocessing.Process.__init__(self)

    self._app_state = app_state
    self._runner_cls = runner_cls
    self._config = config
    self._sleep_time = config["proc_update_res"] / 1000.



  def run(self):
    """Enters the main loop for the process."""

    try:
      runner = self._runner_cls(self._app_state, self._config)
      runner.on_start()

      while True:
        runner.on_update()
        if self._sleep_time > 0:
          sleep(self._sleep_time)

    except Exception as ex:
      self._app_state.error_msg = traceback.format_exc()
      self._app_state.fatal_error = True
      raise


