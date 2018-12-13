# -*- coding: utf-8 -*-
"""
Defines a concrete Runner object.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import hashlib
import hmac
import json
import pycurl

from io import BytesIO
from time import time


from trading_bot.runners.base import Runner



_REST_URL = "https://www.binance.com/api"
_WS_URL = "wss://stream.binance.com:9443"



class ConnectionRunner(Runner):
  """Runner for handling the connection to the exchange server."""

  def on_start(self, **kwargs):
    self._rate_limit_start = None
    self._error_start = None
    self._last_server_ping_time = 0
    self._last_exchange_info_time = 0
    self._last_account_ping_time = 0
    self._time_drift = 0




  def on_update(self, **kwargs):
    cur_time_ms = int(time() * 1000)

    if self._app_state.connection_status == "NOT_CONNECTED":
      try:
        self._app_state.connection_status = "CONNECTING"
        self._establish_connection()
        self._last_server_ping_time = cur_time_ms
        self._last_exchange_info_time = cur_time_ms
        self._last_account_ping_time = cur_time_ms
        self._app_state.connect_time = int(cur_time_ms + self._time_drift)
        self._app_state.connection_status = "CONNECTED"
      except:
        self._app_state.connection_status = "ERROR"


    elif self._app_state.connection_status == "ERROR":
      if self._error_start == None:
        self._error_start = cur_time_ms
      elif cur_time_ms - self._error_start >= 30000:
        self._app_state.connection_status = "NOT_CONNECTED"


    elif self._app_state.connection_status == "RATE_LIMITED":
      if self._rate_limit_start == None:
        self._rate_limit_start = cur_time_ms
      elif cur_time_ms - self._rate_limit_start >= 60000:
        self._app_state.connection_status = "NOT_CONNECTED"


    elif self._app_state.connection_status == "CONNECTED":

      try:
        if cur_time_ms - self._last_account_ping_time >= 1200000:
          self._request_userdata_stream_ping()
          self._last_account_ping_time = cur_time_ms

        if cur_time_ms - self._last_exchange_info_time >= 600000:
          self._update_exchange_info()
          self._last_exchange_info_time = cur_time_ms
          self._last_server_ping_time = cur_time_ms
        elif cur_time_ms - self._last_server_ping_time >= 20000:
          self._update_server_time()
          self._last_server_ping_time = cur_time_ms
        else:
          self._app_state.server_time = int(cur_time_ms + self._time_drift)

        if ((self._app_state.server_time - self._app_state.connect_time) / 1000.
            >= self._config["max_session_time"]):
          # Force connection refresh if session limit is reached.
          self._app_state.connection_status = "NOT_CONNECTED"

      except:
        self._app_state.connection_status = "ERROR"








  def _request_timed_info(self, uri):
    """Issues an unsigned GET API request assuming the response is a serialized
    JSONobject containing a server timestamp, and resynchronizes the real server
    time with the app state server time."""

    t0 = time()

    response = BytesIO()

    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, uri)
    curl.setopt(pycurl.ENCODING, "gzip")
    curl.setopt(pycurl.TIMEOUT, self._config["request_timeout"])
    curl.setopt(pycurl.HTTPHEADER, ["Accept:application/json",
                                    "Accept-encoding:gzip"])
    curl.setopt(pycurl.HTTPGET, 1)
    curl.setopt(pycurl.WRITEFUNCTION, response.write)
    curl.perform()
    status_code = curl.getinfo(pycurl.HTTP_CODE)
    curl.close()

    if status_code == 429:
      self._app_state.connection_status = "RATE_LIMITED"
      return None


    response_str = response.getvalue().decode("utf-8")
    response.close()

    response = json.loads(response_str)

    latency_ms = int((time() - t0) * 1000)
    try:
      server_time_ms = response["serverTime"] + latency_ms // 2
    except KeyError:
      return None

    self._app_state.latency = int(0.5 * latency_ms + 0.5 * self._app_state.latency)
    self._app_state.server_time = server_time_ms
    self._time_drift = server_time_ms - (time() * 1000)

    return response





  def _request_account_info(self):
    """Requests information about the user account."""

    uri = _REST_URL + "/v3/account"

    get_params = ["recvWindow=%s" % self._config["account_recv_window"],
                  "timestamp=%d" % self._app_state.server_time]

    get_data_str = "&".join(get_params)


    # Sign request as required.
    hmac_msg = hmac.new(self._config["api_secret"].encode("utf-8"),
                        get_data_str.encode("utf-8"), hashlib.sha256)
    sig = hmac_msg.hexdigest()
    get_data_str += "&signature=%s" % sig

    uri += "?" + get_data_str

    response = BytesIO()

    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, uri)
    curl.setopt(pycurl.ENCODING, "gzip")
    curl.setopt(pycurl.TIMEOUT, self._config["request_timeout"])
    curl.setopt(pycurl.HTTPHEADER, ["Accept:application/json",
                                    "Accept-encoding:gzip",
                                    "X-MBX-APIKEY:%s" % self._config["api_key"]])
    curl.setopt(pycurl.HTTPGET, 1)
    curl.setopt(pycurl.WRITEFUNCTION, response.write)
    curl.perform()
    status_code = curl.getinfo(pycurl.HTTP_CODE)
    curl.close()

    if status_code == 429:
      self._app_state.connection_status = "RATE_LIMITED"
      return


    response_str = response.getvalue().decode("utf-8")
    response.close()

    response = json.loads(response_str)








  def _request_userdata_stream_open(self):
    """Requests a user data stream connection."""

    uri = _REST_URL + "/v1/userDataStream"

    response = BytesIO()

    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, uri)
    curl.setopt(pycurl.TIMEOUT, self._config["request_timeout"])
    curl.setopt(pycurl.HTTPHEADER, ["Accept:application/json",
                                    "X-MBX-APIKEY:%s" % self._config["api_key"]])
    curl.setopt(pycurl.POST, 1)
    curl.setopt(pycurl.POSTFIELDS, "")
    curl.setopt(pycurl.WRITEFUNCTION, response.write)
    curl.perform()
    status_code = curl.getinfo(pycurl.HTTP_CODE)
    curl.close()

    if status_code == 429:
      self._app_state.connection_status = "RATE_LIMITED"
      return


    response_str = response.getvalue().decode("utf-8")
    response.close()

    response = json.loads(response_str)

    self._user_listen_key = response["listenKey"]






  def _request_userdata_stream_ping(self):
    """Requests a user data stream keepalive ping."""

    uri = _REST_URL + "/v1/userDataStream"

    response = BytesIO()

    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, uri)
    curl.setopt(pycurl.TIMEOUT, self._config["request_timeout"])
    curl.setopt(pycurl.HTTPHEADER, ["Accept:application/json",
                                    "X-MBX-APIKEY:%s" % self._config["api_key"]])
    curl.setopt(pycurl.POST, 1)
    curl.setopt(pycurl.CUSTOMREQUEST, "PUT")
    curl.setopt(pycurl.POSTFIELDS, "listenKey=%s" % self._user_listen_key)
    curl.setopt(pycurl.WRITEFUNCTION, response.write)
    curl.perform()
    status_code = curl.getinfo(pycurl.HTTP_CODE)
    curl.close()

    if status_code == 429:
      self._app_state.connection_status = "RATE_LIMITED"
      return

    response_str = response.getvalue().decode("utf-8")
    response.close()








  def _update_exchange_info(self):
    """Resynchronizes the real server time with the app state server time and
    updates exchange details."""

    exchange_info = self._request_timed_info(_REST_URL + "/v1/exchangeInfo")
    
    if exchange_info:
      pass




  def _update_server_time(self):
    """Resynchronizes the real server time with the app state server time."""

    self._request_timed_info(_REST_URL + "/v1/time")





  def _establish_connection(self):
    """Opens a connection to the exchange server."""

    self._update_exchange_info()
    self._request_account_info()
    self._request_userdata_stream_open()


    # Construct websocket URI.
    stream_names = [self._user_listen_key]
    for pair in set(self._app_state.trade_pairs + self._app_state.save_pairs):
      stream_names.append(pair + "@trade")
      stream_names.append(pair + "@depth")
      stream_names.append(pair + "@ticker")

    self._app_state._ws_uri = _WS_URL + "/stream?streams=" + "/".join(stream_names)


