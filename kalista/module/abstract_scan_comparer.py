#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging

from module.components.common_utils import print_approach_title

class AbstractScanComparer:

    def __init__(self, processor_key, sc_config):
        self.processor_key = processor_key
        self.sc_config = sc_config
        self._init()

    def scan(self):
        self_desc = self.self_desc()
        print_approach_title('- SCAN COMPARER ( %s ) # %s' % (self_desc['name'], self_desc['desc']))
        self._do_scan()
        logging.info('Done.')
        logging.info('')
        self._destroy()

    def self_desc(self):
        pass

    def stat(self):
        pass

    def _self_desc(self):
        pass

    def _init(self):
        pass

    def _do_scan(self):
        pass

    def _destroy(self):
        pass
