# -*- coding: utf-8 -*-
"""
Defines an object for reading and broadcasting recorded trade data.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import datetime
import gzip
import json
import os

from time import sleep



_SLEEP_TIME = 0.0000001
_CALLBACK_FREQ = 100




class SavedStreamReader(object):
  """Defines an object for reading recorded trading stream data from files and
  broadcasting trading periods and order book depths. Streams and timestamps
  are broadcast as though they are running in real time but without real time delay."""


  def __init__(self, app_state, timestamp, trading_pair, data_store_dir,
               update_resolution, progress_callback_fn):
    data_dir = os.path.join(data_store_dir, "%d" % timestamp)
    self._app_state = app_state
    self._trades_filename = os.path.join(data_dir, "%d_%s_trades.txt.gz" % (timestamp, trading_pair))
    self._depth_filename = os.path.join(data_dir, "%d_%s_depth.txt.gz" % (timestamp, trading_pair))
    self._update_resolution = update_resolution
    self._progress_callback_fn = progress_callback_fn
    self._pending_depth_dict = None
    self._pair = trading_pair
    self._cur_update = 0



  def run(self):
    """Reads the recorded stream files for the initialized trading pair and
    broadcasts data to be consumed by the analysis process."""


    last_update_timestamp = 0


    # Read the final trade timestamp so we can report progress towards it.
    # Assumes the file has multiple lines and ends with a trailing newline.
    with gzip.open(self._trades_filename, "r") as trades_in:
      read_newline = False
      trades_in.seek(0, os.SEEK_END)
      position = trades_in.tell()
      line = b""
      while position >= 0:
        trades_in.seek(position)
        next_buffer = trades_in.read(1024)[::-1]

        line += next_buffer
        if read_newline and b"\n" in next_buffer:
          start = line.rfind(b"\n")
          progress_line = line[:start][::-1]
          progress_line = progress_line[:progress_line.find(b"\n")]
          break
        elif b"\n" in next_buffer:
          read_newline = True
        
        position -= 1024





    final_trade = json.loads(progress_line.decode("utf-8"))
    self._start_timestamp = None
    self._final_timestamp = final_trade["server_timestamp"]
    self._final_date_str = datetime.datetime.utcfromtimestamp(self._final_timestamp
                              // 1000).strftime("%Y-%m-%d %H:%M:%S")



    # Read and process trading activity from the beginning.
    with gzip.open(self._trades_filename, "rb") as trades_in:

      with gzip.open(self._depth_filename, "rb") as depth_in:

        while True:
          # Read current trade.
          line = trades_in.readline()
          if not line:
            break
          cur_trade_dict = json.loads(line)

          server_timestamp = cur_trade_dict["server_timestamp"]

          # Update stream to bring up to current time.
          if server_timestamp - last_update_timestamp >= self._update_resolution:
            if last_update_timestamp == 0:
              self._update(server_timestamp, depth_in)
            else:
              t = last_update_timestamp
              while True:
                t += self._update_resolution
                self._update(t, depth_in)
                if t >= server_timestamp:
                  break
              server_timestamp = t

            last_update_timestamp = server_timestamp


          while not self._app_state._trade_queue.empty():
            sleep(_SLEEP_TIME)
          self._app_state.server_time = server_timestamp
          self._app_state._trade_queue.put_nowait((self._pair, cur_trade_dict))










  def _update(self, server_timestamp, depth_file_in):
    """Called periodically to close and broadcast periods for analysis, and read
    new depth snapshots from the data file."""
    

    # Read and process all depths before current timestamp.
    if self._pending_depth_dict is not None:
      if self._pending_depth_dict["server_timestamp"] < server_timestamp:
        while not self._app_state._orderbook_state_queue.empty():
          sleep(_SLEEP_TIME)
        self._app_state.server_time = server_timestamp
        self._app_state._orderbook_state_queue.put_nowait((self._pair, self._pending_depth_dict))
        self._pending_depth_dict = None

    if self._pending_depth_dict is None:
      while True:
        line = depth_file_in.readline()
        if not line:
          break
        cur_depth_dict = json.loads(line)

        if cur_depth_dict["server_timestamp"] < server_timestamp:
          while not self._app_state._orderbook_state_queue.empty():
            sleep(_SLEEP_TIME)
          self._app_state.server_time = server_timestamp
          self._app_state._orderbook_state_queue.put_nowait((self._pair, cur_depth_dict))
        else:
          self._pending_depth_dict = cur_depth_dict
          break




    if self._start_timestamp is None:
      self._start_timestamp = self._app_state.server_time


    self._cur_update += 1
    if self._cur_update % _CALLBACK_FREQ == 0:

      cur_date_str = datetime.datetime.utcfromtimestamp(self._app_state.server_time
                                // 1000).strftime("%Y-%m-%d %H:%M:%S")
      
      cur_progress = 1. - ((self._final_timestamp - self._app_state.server_time)
                          / float(self._final_timestamp - self._start_timestamp))
      cur_progress = int(cur_progress * 100.)

      self._progress_callback_fn(cur_date_str, self._final_date_str, cur_progress)




  




