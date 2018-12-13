# -*- coding: utf-8 -*-
"""
Defines a concrete Runner object.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import json

from tornado import gen
from tornado import httpclient
from tornado import httputil
from tornado import ioloop
from tornado import websocket

from trading_bot.runners.base import Runner




class SocketClient(object):
  """Implements a client for a websocket connection that processes messages."""

   
  def __init__(self, url, on_open_fn, on_close_fn, on_msg_fn,
               connect_timeout, request_timeout, **kwargs):
    """Initializes a new websocket client."""

    self._url = url
    self._connect_timeout = connect_timeout
    self._request_timeout = request_timeout
    self._ws_connection = None
    self._on_connection_open = on_open_fn
    self._on_connection_close = on_close_fn
    self._on_message = on_msg_fn


  def connect(self, **kwargs):
    """Opens a connection to the websocket url."""

    if self._ws_connection is not None:
      raise RuntimeError("Websocket connection already open.")

    headers = httputil.HTTPHeaders({"Content-Type": "application/json"})
    request = httpclient.HTTPRequest(url=self._url, connect_timeout=self._connect_timeout,
                                     request_timeout=self._request_timeout,
                                     headers=headers)

    ws_future = websocket.websocket_connect(request)
    ws_future.add_done_callback(self._connect_callback)
    


  def _connect_callback(self, ws_future):
    if ws_future.exception() is None:
      self._ws_connection = ws_future.result()
      if self._on_connection_open:
        self._on_connection_open()
      self._read_socket()
    else:
      raise RuntimeError("Failed to connect to server: %s" % ws_future.exception())



  def send(self, msg, **kwargs):
    """Sends the specified raw message to the socket connection."""

    if self._ws_connection is None:
      raise RuntimeError("No websocket connection.")

    self._ws_connection.write_message(msg)



  def close(self, **kwargs):
    """Closes the open websocket connection."""

    if self._ws_connection is None:
      return

    if self._on_connection_close:
      self._on_connection_close()
    self._ws_connection.close()
    self._ws_connection = None


  @gen.coroutine
  def _read_socket(self):
    while True:
      if self._ws_connection is None:
        break
      msg = yield self._ws_connection.read_message()
      if msg is None:
        self.close()
        break

      if self._on_message:
        self._on_message(msg)







class SocketStreamRunner(Runner):
  """Runner for handling the connection to the exchange websocket stream."""

  def on_start(self, **kwargs):
    self._client = None
    self._ticker_lows = {}
    self._ticker_highs = {}
    self._ticker_vol = {}

    io_loop = ioloop.IOLoop.current()
    update_callback = ioloop.PeriodicCallback(self.on_update, self._config["proc_update_res"])

    try:
      update_callback.start()
      io_loop.start()
      io_loop.close()
    finally:
      update_callback.stop()
      io_loop.stop()




  def on_update(self, **kwargs):

    if (self._app_state.connection_status != "CONNECTED"
        or (self._app_state.server_time - self._app_state.connect_time) < 1000):
      if self._client:
        self._client.close()
        self._client = None

    elif (self._client is None and self._app_state.connection_status == "CONNECTED"
        and (self._app_state.server_time - self._app_state.connect_time) >= 1000):
      self._client = SocketClient(self._app_state._ws_uri, None, None,
                                  self.on_message, self._config["connect_timeout"],
                                  self._config["request_timeout"])
      self._client.connect()





  def on_message(self, msg):
    try:
      event = json.loads(msg)
    except: return

    data = event["data"]
    event_type = data["e"]

    try:
      server_timestamp = int(data["E"])
      if server_timestamp > self._app_state.server_time:
        self._app_state.server_time = server_timestamp
    except: return

    try:
      if event_type == "trade":
        self._process_trade_event(data)
      elif event_type == "24hrTicker":
        self._process_ticker_event(data)
      elif event_type == "depthUpdate":
        self._process_depth_event(data)
      elif event_type == "executionReport":
        self._process_execution_event(data)
      elif event_type == "outboundAccountInfo":
        self._process_account_event(data)
    except: return




  def _process_trade_event(self, data):
    pair = data["s"].lower()
    trade_timestamp = int(data["T"])
    price = float(data["p"])
    quantity = float(data["q"])
    is_buyer_maker = bool(data["m"])
    buyer_id = int(data["b"])
    seller_id = int(data["a"])

    cur_trade = {}
    cur_trade["trade_timestamp"] = trade_timestamp
    cur_trade["price"] = price
    cur_trade["quantity"] = quantity
    cur_trade["is_buyer_maker"] = is_buyer_maker
    cur_trade["buyer_id"] = buyer_id
    cur_trade["seller_id"] = seller_id
    cur_trade["server_timestamp"] = self._app_state.server_time
    try:
      cur_trade["low24"] = self._ticker_lows[pair]
    except KeyError:
      cur_trade["low24"] = 0
    try:
      cur_trade["high24"] = self._ticker_highs[pair]
    except KeyError:
      cur_trade["high24"] = 0
    try:
      cur_trade["vol24"] = self._ticker_vol[pair]
    except KeyError:
      cur_trade["vol24"] = 0


    self._app_state._trade_queue.put_nowait((pair, cur_trade))





  def _process_ticker_event(self, data):
    pair = data["s"].lower()

    self._ticker_lows[pair] = float(data["l"])
    self._ticker_highs[pair] = float(data["h"])
    self._ticker_vol[pair] = float(data["v"])






  def _process_depth_event(self, data):
    pair = data["s"].lower()
    min_update_id = int(data["u"]) - 1
    max_update_id = int(data["U"]) - 1

    bid_updates = {}
    for level, quantity, _ in data["b"]:
      bid_updates[level] = float(quantity)

    ask_updates = {}
    for level, quantity, _ in data["a"]:
      ask_updates[level] = float(quantity)

    self._app_state._bid_depth_event_queue.put_nowait((pair, min_update_id,
                                                      max_update_id, bid_updates))
    self._app_state._ask_depth_event_queue.put_nowait((pair, min_update_id,
                                                      max_update_id, ask_updates))






  def _process_execution_event(self, data):
    pair = data["s"].lower()






  def _process_account_event(self, data):
    
    pass







