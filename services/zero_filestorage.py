#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BSD 3-Clause License

Copyright (c) 2022, Université Gustave-Eiffel
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import time
import zmq
import os
import threading
import collections
import datetime
import json

class ZeroMQThread(threading.Thread):
    def __init__(self, global_settings, name, address):
        threading.Thread.__init__(self)
        self.global_settings = global_settings
        self.name = name
        self.address = address

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(self.address)
        socket.subscribe("")
        while self.global_settings.running:
            json_data = socket.recv_json()
            self.global_settings.documents_stack.append([self.name, json_data])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='This program read json documents on zeromq channels'
                    ' and write in the specified folder', formatter_class=
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--input_address", nargs="+",
                        help="Address and file name for zero_record json"
                             " channel, you can provide it multiple times",
                        default=["tcp://127.0.0.1:10005/indicators"])
    parser.add_argument("-o", "--output_folder", help="Json output folder",
                        required=True, type=str)

    args = parser.parse_args()
    print("Configuration: " + repr(args))

    args.documents_stack = collections.deque()
    args.running = True
    try:
        for input_data in args.input_address:
            t_sep = input_data.rfind("/")
            t_name = input_data[t_sep+1:]
            t_address = input_data[:t_sep]
            t = ZeroMQThread(args, t_name, t_address)
            t.start()
        while args.running:
            while len(args.documents_stack) > 0:
                document_name, document_json = args.documents_stack.popleft()
                time_part = datetime.datetime.now().\
                    strftime("%Y_%m_%d.%Hh%Mm%S.%f")
                file_path = os.path.join(args.output_folder,
                                         document_name+"_%s.json" % time_part)
                with open(file_path, "w") as fp:
                    json.dump(document_json, fp, allow_nan=True)
            time.sleep(0.005)
    finally:
        args.running = False