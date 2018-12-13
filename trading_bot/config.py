# -*- coding: utf-8 -*-
"""
Defines methods for reading and parsing config files.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import json





def read_config_file(config_filename):
  """Parses and verifies configuration parameters from the specified file."""

  config_str = ""
  with open(config_filename, "r") as f_in:
    for line in f_in:
      comment_pos = line.find("//")
      if comment_pos >= 0:
        newline = ""
      else:
        newline = "\n"
      config_str += line[:comment_pos] + newline

  config = json.loads(config_str)


  config["save_pairs"] = [pair.lower() for pair in config["save_pairs"]]
  config["trade_pairs"] = [pair.lower() for pair in config["trade_pairs"]]

  # TODO some parameter parsing and sanity checking is needed here

  return config







