# -*- coding: utf-8 -*-
"""
Defines a class for managing process-safe application state.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import multiprocessing


class AppState(object):
  """Encapsulates app state in a process-safe way. Property changes are
  propagated to the UI for all properties that do not start with _."""


  @property
  def latency(self):
    """Server latency in milliseconds."""
    return self._status_ns.latency

  @latency.setter
  def latency(self, value):
    self._dirty_lock.acquire()
    self._status_ns.latency = value
    self._is_dirty.latency = True
    self._dirty_lock.release()

  def _write_latency(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_LATENCY", "payload": self._status_ns.latency})





  @property
  def server_time(self):
    """Server time in milliseconds."""
    return self._status_ns.server_time

  @server_time.setter
  def server_time(self, value):
    self._dirty_lock.acquire()
    self._status_ns.server_time = value
    self._is_dirty.server_time = True
    self._dirty_lock.release()

  def _write_server_time(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_SERVER_TIME", "payload": self._status_ns.server_time})




  @property
  def connect_time(self):
    """Time in milliseconds the latest connection was opened."""
    return self._status_ns.connect_time

  @connect_time.setter
  def connect_time(self, value):
    self._dirty_lock.acquire()
    self._status_ns.connect_time = value
    self._is_dirty.connect_time = True
    self._dirty_lock.release()

  def _write_connect_time(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_CONNECT_TIME", "payload": self._status_ns.connect_time})





  @property
  def connection_status(self):
    """Whether the application is connected to the exchange server."""
    return self._status_ns.connection_status

  @connection_status.setter
  def connection_status(self, value):
    self._dirty_lock.acquire()
    if value not in ["NOT_CONNECTED", "CONNECTING", "CONNECTED", "RATE_LIMITED", "ERROR"]:
      raise ValueError("Invalid connection status: %s" % value)
    self._status_ns.connection_status = value
    self._is_dirty.connection_status = True
    self._dirty_lock.release()

  def _write_connection_status(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_CONNECTION_STATUS", "payload": self._status_ns.connection_status})





  @property
  def fatal_error(self):
    """Whether a fatal error has occurred."""
    return self._status_ns.fatal_error

  @fatal_error.setter
  def fatal_error(self, value):
    self._dirty_lock.acquire()
    self._status_ns.fatal_error = value
    self._is_dirty.fatal_error = True
    self._dirty_lock.release()

  def _write_fatal_error(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_FATAL_ERROR", "payload": self._status_ns.fatal_error})







  @property
  def error_msg(self):
    """The latest error message if one is set."""
    return self._status_ns.error_msg

  @error_msg.setter
  def error_msg(self, value):
    self._dirty_lock.acquire()
    self._status_ns.error_msg = value
    self._is_dirty.error_msg = True
    self._dirty_lock.release()

  def _write_error_msg(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_ERROR_MSG", "payload": self._status_ns.error_msg})



  @property
  def trade_pairs(self):
    """The list of symbol pairs used for trading."""
    return [x for x in self._trade_pairs_list]

  @trade_pairs.setter
  def trade_pairs(self, value):
    self._dirty_lock.acquire()
    del self._trade_pairs_list[:]
    self._trade_pairs_list.extend(value)
    self._is_dirty.trade_pairs = True
    self._dirty_lock.release()

  def _write_trade_pairs(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_TRADE_PAIRS", "payload": [x for x in self._trade_pairs_list]})





  @property
  def save_pairs(self):
    """The list of symbol pairs used for saving data."""
    return [x for x in self._save_pairs_list]

  @save_pairs.setter
  def save_pairs(self, value):
    self._dirty_lock.acquire()
    del self._save_pairs_list[:]
    self._save_pairs_list.extend(value)
    self._is_dirty.save_pairs = True
    self._dirty_lock.release()

  def _write_save_pairs(self, write_fns):
    for fn in write_fns:
      fn({"type": "SET_SAVE_PAIRS", "payload": [x for x in self._save_pairs_list]})









  @property
  def _ws_uri(self):
    """The stream URI that the socket stream runner listens to."""
    return self._private_strings.ws_uri

  @_ws_uri.setter
  def _ws_uri(self, value):
    self._private_strings.ws_uri = value



  @property
  def _bid_snapshot_queue(self):
    """The queue for buffering bid orderbook snapshots."""
    return self._private_bid_snapshot_queue


  @property
  def _ask_snapshot_queue(self):
    """The queue for buffering ask orderbook snapshots."""
    return self._private_ask_snapshot_queue


  @property
  def _bid_depth_event_queue(self):
    """The queue for buffering bid orderbook change events."""
    return self._private_bid_depth_event_queue


  @property
  def _ask_depth_event_queue(self):
    """The queue for buffering ask orderbook change events."""
    return self._private_ask_depth_event_queue


  @property
  def _orderbook_state_queue(self):
    """The queue for buffering updated orderbook states."""
    return self._private_orderbook_state_queue

  @property
  def _trade_queue(self):
    """The queue for buffering trades from the server."""
    return self._private_trade_queue




  @property
  def _executor_queue(self):
    """The queue for buffering trade execution events."""
    return self._private_executor_queue






  def __init__(self):
    mp_mgr = multiprocessing.Manager()


    
    self._is_dirty = mp_mgr.Namespace()
    self._dirty_lock = mp_mgr.Lock()


    self._status_ns = mp_mgr.Namespace()

    self._status_ns.latency = 0
    self._is_dirty.latency = False

    self._status_ns.server_time = 0
    self._is_dirty.server_time = False

    self._status_ns.connect_time = 0
    self._is_dirty.connect_time = False

    self._status_ns.connection_status = "NOT_CONNECTED"
    self._is_dirty.connection_status = False

    self._status_ns.fatal_error = False
    self._is_dirty.fatal_error = False

    self._status_ns.error_msg = None
    self._is_dirty.error_msg = False

    self._trade_pairs_list = mp_mgr.list()
    self._save_pairs_list = mp_mgr.list()


    self._private_strings = mp_mgr.Namespace()
    self._private_strings.ws_uri = ""

    self._private_bid_snapshot_queue = mp_mgr.Queue()
    self._private_ask_snapshot_queue = mp_mgr.Queue()

    self._private_bid_depth_event_queue = mp_mgr.Queue()
    self._private_ask_depth_event_queue = mp_mgr.Queue()

    self._private_orderbook_state_queue = mp_mgr.Queue()
    self._private_trade_queue = mp_mgr.Queue()

    self._private_executor_queue = mp_mgr.Queue()





  def write_updates(self, write_fns):

    self._dirty_lock.acquire()

    if self._is_dirty.latency:
      self._write_latency(write_fns)
      self._is_dirty.latency = False

    if self._is_dirty.server_time:
      self._write_server_time(write_fns)
      self._is_dirty.server_time = False

    if self._is_dirty.connect_time:
      self._write_connect_time(write_fns)
      self._is_dirty.connect_time = False

    if self._is_dirty.connection_status:
      self._write_connection_status(write_fns)
      self._is_dirty.connection_status = False

    if self._is_dirty.fatal_error:
      self._write_fatal_error(write_fns)
      self._is_dirty.fatal_error = False

    if self._is_dirty.error_msg:
      self._write_error_msg(write_fns)
      self._is_dirty.error_msg = False

    if self._is_dirty.trade_pairs:
      self._write_trade_pairs(write_fns)
      self._is_dirty.trade_pairs = False

    if self._is_dirty.save_pairs:
      self._write_save_pairs(write_fns)
      self._is_dirty.save_pairs = False

    self._dirty_lock.release()



  def write_all(self, write_fns):

    self._write_latency(write_fns)
    self._write_server_time(write_fns)
    self._write_connect_time(write_fns)
    self._write_connection_status(write_fns)
    self._write_fatal_error(write_fns)
    self._write_error_msg(write_fns)
    self._write_trade_pairs(write_fns)
    self._write_save_pairs(write_fns)

