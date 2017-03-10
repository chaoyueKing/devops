#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging

from module.abstract_scan_comparer import AbstractScanComparer


class ScanComparer(AbstractScanComparer):
    """
    This is a dummy scan comparer, it does nothing but for testing your executing environment.
    """

    def self_desc(self):
        self_desc = {
            'name': 'dummy',
            'cname': '测试用',
            'desc': 'just for testing environment'
        }
        return self_desc

    def stat(self):
        stat_template = 'test'
        return stat_template

    def _init(self):
        pass

    def _do_scan(self):
        logging.info('dummy scanning')
