#!/usr/bin/python
# -*- coding: latin-1 -*-
# -----------------------------------------------------------------------------
# Copyright 2012-2013 Stephen Tiedemann <stephen.tiedemann@gmail.com>
#
# Licensed under the EUPL, Version 1.1 or - as soon they 
# will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the
# Licence.
# You may obtain a copy of the Licence at:
#
# http://www.osor.eu/eupl
#
# Unless required by applicable law or agreed to in
# writing, software distributed under the Licence is
# distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.
# See the Licence for the specific language governing
# permissions and limitations under the Licence.
# -----------------------------------------------------------------------------
import logging
log = logging.getLogger('root')

import os
import sys
import time
import os.path
import inspect
import argparse

import nfc

class CommandLineInterface(object):
    def __init__(self, argument_parser, groups=None):
        if groups is None: groups = "dbg p2p clf iop"
        for group in groups.split():
            eval("self.add_{0}_options".format(group))(argument_parser)
        
        argument_parser.add_argument(
            "-l", "--loop", action="store_true",
            help="restart after termination")
        
        self.options = argument_parser.parse_args()
        
        logformat = '%(message)s'
        verbosity = logging.ERROR if self.options.quiet else logging.INFO
        
        if self.options.debug:
            logformat = '%(levelname)-5s [%(name)s] %(message)s'
            if '' in self.options.debug:
                verbosity = logging.DEBUG
        
        logging.basicConfig(level=verbosity, format=logformat)

        if self.options.debug and 'nfc' in self.options.debug:
            verbosity = logging.DEBUG
            
        if self.options.logfile:
            logfile_format = \
                '%(asctime)s %(levelname)-5s [%(name)s] %(message)s'
            logfile = logging.FileHandler(self.options.logfile, "w")
            logfile.setFormatter(logging.Formatter(logfile_format))
            logfile.setLevel(logging.DEBUG)
            logging.getLogger('').addHandler(logfile)

        nfcpy_path = os.path.dirname(inspect.getfile(nfc))
        for name in os.listdir(nfcpy_path):
            if os.path.isdir(os.path.join(nfcpy_path, name)):
                logging.getLogger("nfc."+name).setLevel(verbosity)
            elif name.endswith(".py") and name != "__init__.py":
                logging.getLogger("nfc."+name[:-3]).setLevel(verbosity)
            
        if self.options.debug:
            for module in self.options.debug:
                log.info("enable debug output for module '{0}'".format(module))
                logging.getLogger(module).setLevel(logging.DEBUG)

    def add_dbg_options(self, argument_parser):
        group = argument_parser.add_argument_group()
        group.add_argument(
            "-q", "--quiet", dest="quiet", action="store_true",
            help="do not print anything except errors")
        group.add_argument(
            "-d", metavar="MODULE", dest="debug", action="append",
            help="print debug messages for MODULE, use '' for all")
        group.add_argument(
            "-f", dest="logfile", metavar="FILE",
            help="write log messages to file")
        
    def add_p2p_options(self, argument_parser):
        group = argument_parser.add_argument_group()
        group.add_argument(
            "--mode", choices=["t","target","i","initiator"], metavar="{t,i}",
            help="connect as 'target' or 'initiator' (default: both)")
        group.add_argument(
            "--miu", dest="miu", metavar="INT", type=int, default=1024,
            help="set LLCP Link MIU (default: %(default)s octets)")
        group.add_argument(
            "--lto", metavar="INT", type=int, default=500,
            help="set LLCP Link Timeout (default: %(default)s ms)")
        group.add_argument(
            "--listen-time", metavar="INT", type=int, default=250,
            help="set time to listen as target (default: %(default)s ms)")
        group.add_argument(
            "--no-aggregation", action="store_true",
            help="disable outbound packet aggregation")

    def add_clf_options(self, argument_parser):
        group = argument_parser.add_argument_group()
        group.add_argument(
            "--device", metavar="NAME", action="append",
            help="use specified contactless reader(s): "\
                "usb[:vendor[:product]] (vendor and product in hex), "\
                "usb[:bus[:dev]] (bus and device number in decimal), "\
                "tty[:(usb|com)[:port]] (usb virtual or com port)")
        
    def add_iop_options(self, argument_parser):
        group = argument_parser.add_mutually_exclusive_group()
        group.add_argument(
            "--quirks", action="store_true",
            help="support non-compliant implementations")
        #group.add_argument(
        #    "--strict", action="store_true",
        #    help="apply strict standards interpretation")
        
    def on_startup(self, llc):
        return True
    
    def on_connect(self, llc):
        return True
    
    def run_once(self):
        if self.options.device is None:
            self.options.device = ['']
            
        for device in self.options.device:
            try: clf = nfc.ContactlessFrontend(device)
            except LookupError: pass
            else: break
        else:
            log.info("no contactless frontend found")
            raise SystemExit(1)

        if self.options.mode is None:
            self.options.role = None
        elif self.options.mode in ('t', 'target'):
            self.options.role = 'target'
        elif self.options.mode in ('i', 'initiator'):
            self.options.role = 'initiator'
        
        p2p_options = {
            'on-startup': self.on_startup,
            'on-connect': self.on_connect,
            'role': self.options.role,
            'miu': self.options.miu,
            'lto': self.options.lto,
            'agf': not self.options.no_aggregation,
            }

        try:
            return clf.connect(p2p=p2p_options)
        finally:
            clf.close()
            
    def run(self):
        while self.run_once() and self.options.loop:
            pass
