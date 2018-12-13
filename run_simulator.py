#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulates trade activity and estimates profits for specific trading pairs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import sys

from trading_bot.config import read_config_file
from trading_bot.proc import AsyncRunnerProcess
from trading_bot.reader import SavedStreamReader
from trading_bot.runners import AnalysisRunner
from trading_bot.runners import SimulatorRunner
from trading_bot.runners import TradeExecutorRunner
from trading_bot.state import AppState




_PROCESS_WAIT_TIMEOUT = 5

_PROCESSES = []
_APP_STATE = AppState()





def main(timestamp, trading_pair, model_pair, config_filename):
  """Entry point method."""

  config = read_config_file(config_filename)
  real_update_res = config["proc_update_res"]
  config["proc_update_res"] = 0
  



  _APP_STATE.trade_pairs = [trading_pair]
  _APP_STATE.connect_time = int(timestamp)
  _APP_STATE.connection_status = "CONNECTED"



  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, SimulatorRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, AnalysisRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, TradeExecutorRunner))



  for process in _PROCESSES:
    process.start()




  def __progress_callback(cur_date_str, final_date_str, cur_progress):
    sys.stdout.write("\r[ % 3d%% ] %s / %s" % (cur_progress, cur_date_str, final_date_str))
    sys.stdout.flush()


  try:
    reader = SavedStreamReader(_APP_STATE, timestamp, trading_pair,
                               config["data_store_dir"], real_update_res,
                               __progress_callback)
    reader.run()
    sys.stdout.write("\n")
    sys.stdout.flush()

  finally:
    for process in _PROCESSES:
      try:
        process.terminate()
        process.join(_PROCESS_WAIT_TIMEOUT)
      except Exception as e:
        print(e)









if __name__ == "__main__":
  import argparse
  from os import path

  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("timestamp", type=int, help="Timestamp of data files")
  parser.add_argument("trading_pair", help="Trading pair to use for simulation")
  parser.add_argument("model_pair", help="Trading pair to use for prediction")

  parser.add_argument("--config", default="config.json", type=str, metavar="f",
                      help="Configuration json file (default: config.json)")

  args = parser.parse_args()

  main(args.timestamp, args.trading_pair.lower(), args.model_pair.lower(),
       path.realpath(args.config))




