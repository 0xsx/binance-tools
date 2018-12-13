#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Starts the trading bot, market data downloader, and UI server.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import argparse
import os
import traceback
import uuid


import tornado.ioloop
import tornado.web
import tornado.websocket

from trading_bot.config import read_config_file
from trading_bot.proc import AsyncRunnerProcess
from trading_bot.runners import AnalysisRunner, ConnectionRunner, OrderBookRunner
from trading_bot.runners import SnapshotRunner, SocketStreamRunner, TradeExecutorRunner
from trading_bot.state import AppState


_PROCESS_WAIT_TIMEOUT = 5


_CONNECTED_CLIENTS = {}
_PROCESSES = []
_APP_STATE = AppState()



class WebHandler(tornado.web.RequestHandler):
  """Handler for hosting the UI web app."""

  def initialize(self, html_bytes, css_bytes, js_bytes):
    self._html_bytes = html_bytes
    self._css_bytes = css_bytes
    self._js_bytes = js_bytes

  def get(self, uri):
    if uri == "style.css":
      self.set_header("Content-Type", "text/css")
      self.write(self._css_bytes)
    elif uri == "app.js":
      self.set_header("Content-Type", "text/javascript")
      self.write(self._js_bytes)
    else:
      self.set_header("Content-Type", "text/html")
      self.write(self._html_bytes)





class SocketHandler(tornado.websocket.WebSocketHandler):
  """Handler for the UI websocket."""

  def open(self):
    self._cur_id = uuid.uuid4().hex
    _CONNECTED_CLIENTS[self._cur_id] = self
    _APP_STATE.write_all([self.write_message])

  def on_close(self):
    del _CONNECTED_CLIENTS[self._cur_id]








def main(config_filename):
  """Entry point method."""


  config = read_config_file(config_filename)
  _APP_STATE.trade_pairs = config["trade_pairs"]
  _APP_STATE.save_pairs = config["save_pairs"]

  with open(os.path.join("ui", "dist", "production", "index.html"), "rb") as f_in:
    html_bytes = f_in.read()
  with open(os.path.join("ui", "dist", "production", "style.css"), "rb") as f_in:
    css_bytes = f_in.read()
  with open(os.path.join("ui", "dist", "production", "app.js"), "rb") as f_in:
    js_bytes = f_in.read()

  app = tornado.web.Application([
    (r"/socket", SocketHandler),
    (r"/(.*)", WebHandler, {"html_bytes": html_bytes, "css_bytes": css_bytes,
                            "js_bytes": js_bytes}),
    
  ])

  

  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, ConnectionRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, SocketStreamRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, SnapshotRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, OrderBookRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, AnalysisRunner))
  _PROCESSES.append(AsyncRunnerProcess(_APP_STATE, config, TradeExecutorRunner))



  for process in _PROCESSES:
    process.start()
  



  io_loop = tornado.ioloop.IOLoop.current()

  def __update_main():
    """Callback to send updated state to clients and exit on fatal error."""
    write_fns = [_CONNECTED_CLIENTS[client_id].write_message
                 for client_id in _CONNECTED_CLIENTS]
    _APP_STATE.write_updates(write_fns)

    if _APP_STATE.fatal_error:
      io_loop.stop()
      raise RuntimeError(_APP_STATE.error_msg)


  update_callback = tornado.ioloop.PeriodicCallback(__update_main, config["proc_update_res"])

  try:
    app.listen(config["ui_host_port"], address=config["ui_host_ip"])

    update_callback.start()
    io_loop.start()
    io_loop.close()

  except KeyboardInterrupt:
    print("Interrupted by user. Exiting.")

  finally:
    for process in _PROCESSES:
      try:
        process.terminate()
        process.join(_PROCESS_WAIT_TIMEOUT)
      except Exception as e:
        print(e)

    update_callback.stop()
    io_loop.stop()









if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--config", default="config.json", type=str, metavar="f",
                      help="Configuration json file (default: config.json)")

  args = parser.parse_args()

  main(os.path.realpath(args.config))






